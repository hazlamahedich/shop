"""Tests for CheckoutService.

Tests checkout URL generation, validation retry logic, checkout token
storage and retrieval, and error handling.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis

from app.core.errors import APIError, ErrorCode
from app.schemas.cart import Cart, CartItem, CurrencyCode
from app.services.cart import CartService
from app.services.checkout import CheckoutService
from app.services.checkout.checkout_schema import CheckoutStatus
from app.services.shopify_storefront import ShopifyStorefrontClient


class TestCheckoutService:
    """Test CheckoutService URL generation and token management."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client with async methods."""
        mock_client = MagicMock()
        mock_client.get = AsyncMock()
        mock_client.setex = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_cart_service(self):
        """Create mock CartService."""
        return AsyncMock(spec=CartService)

    @pytest.fixture
    def mock_shopify_client(self):
        """Create mock Shopify client."""
        client = AsyncMock(spec=ShopifyStorefrontClient)
        return client

    @pytest.fixture
    def checkout_service(self, mock_redis, mock_cart_service, mock_shopify_client):
        """Create checkout service with mocked dependencies."""
        return CheckoutService(
            redis_client=mock_redis,
            cart_service=mock_cart_service,
            shopify_client=mock_shopify_client,
        )

    @pytest.fixture
    def sample_cart(self):
        """Create sample cart with items."""
        return Cart(
            items=[
                CartItem(
                    product_id="gid://shopify/Product/1",
                    variant_id="gid://shopify/ProductVariant/1",
                    title="Test Product",
                    price=29.99,
                    image_url="https://example.com/image.jpg",
                    currency_code=CurrencyCode.USD,
                    quantity=2,
                    added_at=datetime.now(timezone.utc).isoformat(),
                ),
                CartItem(
                    product_id="gid://shopify/Product/2",
                    variant_id="gid://shopify/ProductVariant/2",
                    title="Another Product",
                    price=49.99,
                    image_url="https://example.com/image2.jpg",
                    currency_code=CurrencyCode.USD,
                    quantity=1,
                    added_at=datetime.now(timezone.utc).isoformat(),
                ),
            ],
            subtotal=109.97,
            currency_code=CurrencyCode.USD,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    def test_get_checkout_token_key(self, checkout_service):
        """Test Redis key generation for checkout token."""
        key = checkout_service._get_checkout_token_key("test_psid_123")
        assert key == "checkout_token:test_psid_123"

    @pytest.mark.asyncio
    async def test_generate_checkout_url_success(
        self, checkout_service, mock_cart_service, mock_shopify_client, sample_cart
    ):
        """Test successful checkout URL generation."""
        # Mock cart retrieval
        mock_cart_service.get_cart.return_value = sample_cart

        # Mock Shopify client
        checkout_url = "https://checkout.shopify.com/ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify result
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
        assert call_args[1]["quantity"] == 1

        # Verify checkout token was stored
        assert checkout_service.redis.setex.called

    @pytest.mark.asyncio
    async def test_generate_checkout_url_empty_cart(
        self, checkout_service, mock_cart_service
    ):
        """Test checkout with empty cart."""
        # Mock empty cart
        empty_cart = Cart(
            items=[],
            subtotal=0.0,
            currency_code=CurrencyCode.USD,
        )
        mock_cart_service.get_cart.return_value = empty_cart

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify empty cart response
        assert result["status"] == CheckoutStatus.EMPTY_CART
        assert result["checkout_url"] is None
        assert result["checkout_token"] is None
        assert "empty" in result["message"].lower()

        # Verify Shopify client was NOT called
        checkout_service.shopify_client.create_checkout_url.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_checkout_url_cart_retrieval_failed(
        self, checkout_service, mock_cart_service
    ):
        """Test checkout when cart retrieval fails."""
        # Mock cart retrieval failure
        mock_cart_service.get_cart.side_effect = APIError(
            ErrorCode.CART_RETRIEVAL_FAILED, "Failed to retrieve cart"
        )

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify error response
        assert result["status"] == CheckoutStatus.FAILED
        assert result["checkout_url"] is None
        assert "Failed to retrieve your cart" in result["message"]

    @pytest.mark.asyncio
    async def test_generate_checkout_url_validation_retry(
        self, checkout_service, mock_cart_service, mock_shopify_client, sample_cart
    ):
        """Test retry logic on checkout URL validation failure."""
        # Mock cart retrieval
        mock_cart_service.get_cart.return_value = sample_cart

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
    async def test_generate_checkout_url_max_retries_exceeded(
        self, checkout_service, mock_cart_service, mock_shopify_client, sample_cart
    ):
        """Test failure after max retries exceeded."""
        # Mock cart retrieval
        mock_cart_service.get_cart.return_value = sample_cart

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
    async def test_generate_checkout_url_api_error(
        self, checkout_service, mock_cart_service, mock_shopify_client, sample_cart
    ):
        """Test checkout with non-retryable API error."""
        # Mock cart retrieval
        mock_cart_service.get_cart.return_value = sample_cart

        # Mock Shopify: throw non-validation error
        mock_shopify_client.create_checkout_url.side_effect = APIError(
            ErrorCode.SHOPIFY_API_ERROR, "Shopify API error"
        )

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify failure - non-validation errors break immediately
        assert result["status"] == CheckoutStatus.FAILED
        assert result["retry_count"] == 0

        # Verify Shopify client was called only once (no retries for non-validation errors)
        assert mock_shopify_client.create_checkout_url.call_count == 1

    @pytest.mark.asyncio
    async def test_extract_checkout_token_valid(self, checkout_service):
        """Test token extraction from valid checkout URL."""
        url = "https://checkout.shopify.com/ABCDEFGHIJKLMNOPQRSTUVWXYZ123456?key=value"
        token = checkout_service._extract_checkout_token(url)
        assert token == "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"

    @pytest.mark.asyncio
    async def test_extract_checkout_token_invalid(self, checkout_service):
        """Test token extraction from invalid URL with short token."""
        url = "https://invalid-url.com/abc"
        token = checkout_service._extract_checkout_token(url)
        assert token is None  # Token too short (< 5 chars)

    @pytest.mark.asyncio
    async def test_store_checkout_token(
        self, checkout_service, sample_cart
    ):
        """Test checkout token storage in Redis."""
        checkout_token = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        checkout_url = f"https://checkout.shopify.com/{checkout_token}"
        psid = "test_psid"

        # Store checkout token
        await checkout_service._store_checkout_token(
            psid=psid,
            checkout_token=checkout_token,
            checkout_url=checkout_url,
            cart=sample_cart,
        )

        # Verify Redis setex was called
        assert checkout_service.redis.setex.called

        # Verify the token data
        call_args = checkout_service.redis.setex.call_args[0]
        key, ttl, value = call_args

        assert key == "checkout_token:test_psid"
        assert ttl == checkout_service.CHECKOUT_TOKEN_TTL_HOURS * 60 * 60

        token_data = json.loads(value)
        assert token_data["token"] == checkout_token
        assert token_data["url"] == checkout_url
        assert token_data["psid"] == psid
        assert token_data["item_count"] == sample_cart.item_count
        assert token_data["subtotal"] == sample_cart.subtotal
        assert token_data["currency_code"] == sample_cart.currency_code.value
        assert "created_at" in token_data

    @pytest.mark.asyncio
    async def test_get_checkout_token_exists(self, checkout_service, mock_redis):
        """Test retrieving existing checkout token."""
        psid = "test_psid"
        checkout_token = "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"

        token_data = {
            "token": checkout_token,
            "url": f"https://checkout.shopify.com/{checkout_token}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "psid": psid,
            "item_count": 2,
            "subtotal": 109.97,
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
    async def test_get_checkout_token_not_found(self, checkout_service, mock_redis):
        """Test retrieving non-existent checkout token."""
        mock_redis.get.return_value = None

        # Get checkout token
        result = await checkout_service.get_checkout_token("test_psid")

        # Verify None returned
        assert result is None

    @pytest.mark.asyncio
    async def test_cart_retained_after_checkout(
        self, checkout_service, mock_cart_service, mock_shopify_client, sample_cart
    ):
        """Test that local cart is NOT cleared after checkout (for abandoned checkout recovery)."""
        # Mock cart retrieval
        mock_cart_service.get_cart.return_value = sample_cart

        # Mock Shopify client
        checkout_url = "https://checkout.shopify.com/ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify success
        assert result["status"] == CheckoutStatus.SUCCESS

        # Verify cart service clear_cart was NEVER called
        # (Cart is retained until order confirmation in Story 2.9)
        mock_cart_service.clear_cart.assert_not_called()

    @pytest.mark.asyncio
    async def test_checkout_token_ttl_24_hours(self, checkout_service, sample_cart):
        """Test that checkout token is stored with 24-hour TTL."""
        psid = "test_psid"
        checkout_token = "ABC123"
        checkout_url = f"https://checkout.shopify.com/{checkout_token}"

        # Store checkout token
        await checkout_service._store_checkout_token(
            psid=psid,
            checkout_token=checkout_token,
            checkout_url=checkout_url,
            cart=sample_cart,
        )

        # Verify TTL is 24 hours (86400 seconds)
        call_args = checkout_service.redis.setex.call_args[0]
        ttl = call_args[1]
        assert ttl == 24 * 60 * 60
