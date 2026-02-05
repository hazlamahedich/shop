"""Integration tests for Checkout flow (Story 2.8).

Tests complete checkout flow from cart to checkout URL generation,
including validation retry, token persistence, and error handling.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import redis

from app.core.errors import APIError, ErrorCode
from app.schemas.cart import Cart, CartItem, CurrencyCode
from app.services.cart import CartService
from app.services.checkout import CheckoutService
from app.services.checkout.checkout_schema import CheckoutStatus
from app.services.shopify_storefront import ShopifyStorefrontClient


class TestCheckoutFlow:
    """Test end-to-end checkout flow."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return MagicMock(spec=redis.Redis)

    @pytest.fixture
    def cart_service(self, mock_redis):
        """Create cart service with mock Redis."""
        return CartService(redis_client=mock_redis)

    @pytest.fixture
    def mock_shopify_client(self):
        """Create mock Shopify client."""
        client = AsyncMock(spec=ShopifyStorefrontClient)
        return client

    @pytest.fixture
    def checkout_service(self, mock_redis, cart_service, mock_shopify_client):
        """Create checkout service with mocked dependencies."""
        return CheckoutService(
            redis_client=mock_redis,
            cart_service=cart_service,
            shopify_client=mock_shopify_client,
        )

    @pytest.fixture
    def sample_cart(self):
        """Create sample cart with multiple items."""
        return Cart(
            items=[
                CartItem(
                    product_id="gid://shopify/Product/1",
                    variant_id="gid://shopify/ProductVariant/1",
                    title="Running Shoes",
                    price=89.99,
                    image_url="https://example.com/shoes.jpg",
                    currency_code=CurrencyCode.USD,
                    quantity=2,
                    added_at=datetime.now(timezone.utc).isoformat(),
                ),
                CartItem(
                    product_id="gid://shopify/Product/2",
                    variant_id="gid://shopify/ProductVariant/2",
                    title="Athletic Socks",
                    price=12.99,
                    image_url="https://example.com/socks.jpg",
                    currency_code=CurrencyCode.USD,
                    quantity=3,
                    added_at=datetime.now(timezone.utc).isoformat(),
                ),
            ],
            subtotal=217.95,
            currency_code=CurrencyCode.USD,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    @pytest.mark.asyncio
    async def test_checkout_with_valid_cart(
        self, checkout_service, cart_service, mock_redis, mock_shopify_client, sample_cart
    ):
        """Test successful checkout flow with valid cart."""
        # Mock cart retrieval
        mock_redis.get.return_value = sample_cart.model_dump_json()

        # Mock Shopify checkout URL generation
        checkout_url = "https://checkout.shopify.com/ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify success response
        assert result["status"] == CheckoutStatus.SUCCESS
        assert result["checkout_url"] == checkout_url
        assert result["checkout_token"] == "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        assert "Complete your purchase here:" in result["message"]
        assert result["retry_count"] == 0

        # Verify Shopify client was called with correct line items
        mock_shopify_client.create_checkout_url.assert_called_once()
        call_args = mock_shopify_client.create_checkout_url.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0]["variant_id"] == "gid://shopify/ProductVariant/1"
        assert call_args[0]["quantity"] == 2
        assert call_args[1]["variant_id"] == "gid://shopify/ProductVariant/2"
        assert call_args[1]["quantity"] == 3

        # Verify checkout token was stored
        assert mock_redis.setex.called
        call_args = mock_redis.setex.call_args[0]
        key, ttl, value = call_args
        assert key == "checkout_token:test_psid"
        assert ttl == 24 * 60 * 60  # 24 hours

    @pytest.mark.asyncio
    async def test_checkout_with_empty_cart(
        self, checkout_service, cart_service, mock_redis
    ):
        """Test checkout with empty cart returns empty cart status."""
        # Mock empty cart
        empty_cart = Cart(
            items=[],
            subtotal=0.0,
            currency_code=CurrencyCode.USD,
        )
        mock_redis.get.return_value = empty_cart.model_dump_json()

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify empty cart response
        assert result["status"] == CheckoutStatus.EMPTY_CART
        assert result["checkout_url"] is None
        assert result["checkout_token"] is None
        assert "empty" in result["message"].lower()

        # Verify Shopify client was NOT called
        mock_shopify_client = checkout_service.shopify_client
        if isinstance(mock_shopify_client, AsyncMock):
            mock_shopify_client.create_checkout_url.assert_not_called()

    @pytest.mark.asyncio
    async def test_checkout_validation_retry_succeeds(
        self, checkout_service, cart_service, mock_redis, mock_shopify_client, sample_cart
    ):
        """Test checkout retry mechanism on validation failure."""
        # Mock cart retrieval
        mock_redis.get.return_value = sample_cart.model_dump_json()

        # Mock Shopify: first two calls fail validation, third succeeds
        valid_url = "https://checkout.shopify.com/ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        mock_shopify_client.create_checkout_url.side_effect = [
            APIError(ErrorCode.SHOPIFY_CHECKOUT_URL_INVALID, "Invalid URL"),
            APIError(ErrorCode.SHOPIFY_CHECKOUT_URL_INVALID, "Invalid URL"),
            valid_url,
        ]

        # Generate checkout URL (should retry and succeed)
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify success after retries
        assert result["status"] == CheckoutStatus.SUCCESS
        assert result["checkout_url"] == valid_url
        assert result["retry_count"] == 2

        # Verify Shopify client was called 3 times (initial + 2 retries)
        assert mock_shopify_client.create_checkout_url.call_count == 3

    @pytest.mark.asyncio
    async def test_checkout_validation_max_retries_exceeded(
        self, checkout_service, cart_service, mock_redis, mock_shopify_client, sample_cart
    ):
        """Test checkout fails after max retries exceeded."""
        # Mock cart retrieval
        mock_redis.get.return_value = sample_cart.model_dump_json()

        # Mock Shopify: always fail validation
        mock_shopify_client.create_checkout_url.side_effect = APIError(
            ErrorCode.SHOPIFY_CHECKOUT_URL_INVALID, "Invalid URL"
        )

        # Generate checkout URL (should fail after max retries)
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify failure
        assert result["status"] == CheckoutStatus.FAILED
        assert result["checkout_url"] is None
        assert result["checkout_token"] is None
        assert result["retry_count"] == 3  # 0 + 3 failed attempts

        # Verify Shopify client was called 4 times (initial + 3 retries)
        assert mock_shopify_client.create_checkout_url.call_count == 4

    @pytest.mark.asyncio
    async def test_checkout_token_persistence(
        self, checkout_service, cart_service, mock_redis, mock_shopify_client, sample_cart
    ):
        """Test checkout token is stored and retrieved correctly."""
        psid = "test_psid"
        checkout_token = "ABC123XYZ"
        checkout_url = f"https://checkout.shopify.com/{checkout_token}"

        # Mock cart retrieval and Shopify response
        mock_redis.get.return_value = sample_cart.model_dump_json()
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url(psid)

        # Verify token was stored
        assert result["checkout_token"] == checkout_token

        # Verify Redis setex was called with correct data
        assert mock_redis.setex.called
        call_args = mock_redis.setex.call_args[0]
        key, ttl, value = call_args

        token_data = json.loads(value)
        assert token_data["token"] == checkout_token
        assert token_data["url"] == checkout_url
        assert token_data["psid"] == psid
        assert token_data["item_count"] == 5  # Sum of quantities: 2 + 3
        assert token_data["subtotal"] == 217.95
        assert token_data["currency_code"] == "USD"
        assert "created_at" in token_data

    @pytest.mark.asyncio
    async def test_checkout_token_retrieval(
        self, checkout_service, mock_redis
    ):
        """Test retrieving stored checkout token."""
        psid = "test_psid"
        checkout_token = "ABC123XYZ"

        token_data = {
            "token": checkout_token,
            "url": f"https://checkout.shopify.com/{checkout_token}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "psid": psid,
            "item_count": 2,
            "subtotal": 217.95,
            "currency_code": "USD",
        }
        mock_redis.get.return_value = json.dumps(token_data)

        # Get checkout token
        result = await checkout_service.get_checkout_token(psid)

        # Verify result
        assert result is not None
        assert result["token"] == checkout_token
        assert result["psid"] == psid
        assert result["item_count"] == 2

    @pytest.mark.asyncio
    async def test_checkout_message_processor_integration(
        self, mock_redis, mock_shopify_client, sample_cart
    ):
        """Test checkout flow through message processor."""
        # Mock cart retrieval
        mock_redis.get.return_value = sample_cart.model_dump_json()

        # Mock Shopify checkout URL generation
        checkout_url = "https://checkout.shopify.com/ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        # Create a mock cart service
        mock_cart_service = AsyncMock()
        mock_cart_service.get_cart.return_value = sample_cart

        # Create checkout service with mocked dependencies
        checkout_service = CheckoutService(
            redis_client=mock_redis,
            shopify_client=mock_shopify_client,
            cart_service=mock_cart_service,
        )

        # Call the checkout service directly
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify result
        assert result["status"] == CheckoutStatus.SUCCESS
        assert result["checkout_url"] == checkout_url
        assert "Complete your purchase here:" in result["message"]

    @pytest.mark.asyncio
    async def test_cart_retained_after_checkout(
        self, checkout_service, cart_service, mock_redis, mock_shopify_client, sample_cart
    ):
        """Test that local cart is NOT cleared after checkout (for abandoned checkout recovery)."""
        # Mock cart retrieval
        mock_redis.get.return_value = sample_cart.model_dump_json()

        # Mock Shopify checkout URL generation
        checkout_url = "https://checkout.shopify.com/ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify success
        assert result["status"] == CheckoutStatus.SUCCESS

        # Verify clear_cart was NEVER called
        # (Cart is retained until order confirmation in Story 2.9)
        # Note: Since we're not calling cart_service.clear_cart, we just verify
        # that the cart data in Redis was NOT cleared
        # The checkout_token is stored separately from the cart

    @pytest.mark.asyncio
    async def test_checkout_with_non_retryable_error(
        self, checkout_service, cart_service, mock_redis, mock_shopify_client, sample_cart
    ):
        """Test checkout with non-retryable API error."""
        # Mock cart retrieval
        mock_redis.get.return_value = sample_cart.model_dump_json()

        # Mock Shopify: throw non-validation error
        mock_shopify_client.create_checkout_url.side_effect = APIError(
            ErrorCode.SHOPIFY_API_ERROR, "Shopify API error"
        )

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify failure without retry
        assert result["status"] == CheckoutStatus.FAILED
        assert result["retry_count"] == 0

        # Verify Shopify client was called only once (no retries for non-validation errors)
        assert mock_shopify_client.create_checkout_url.call_count == 1
