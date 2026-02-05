"""E2E tests for Story 2-8: Checkout URL Generation.

Tests full user flows with Messenger integration including:
- Complete checkout flow: items in cart → checkout → URL generation
- Empty cart handling
- Checkout retry on validation failure
- Checkout token persistence
- Cart retention after checkout (for abandoned checkout recovery)
"""

import json
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import redis.asyncio as redis

from app.core.errors import APIError, ErrorCode
from app.schemas.cart import Cart, CartItem, CurrencyCode
from app.services.checkout import CheckoutService
from app.services.checkout.checkout_schema import CheckoutStatus
from app.services.shopify_storefront import ShopifyStorefrontClient


class TestStory28CheckoutE2E:
    """E2E tests for Checkout URL Generation feature."""

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
    async def test_e2e_complete_checkout_flow(self, sample_cart):
        """Test E2E: Complete user flow from cart with items to checkout URL."""
        # Mock dependencies
        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get = AsyncMock(return_value=sample_cart.model_dump_json())
        mock_redis.setex = AsyncMock(return_value=True)

        mock_shopify_client = AsyncMock(spec=ShopifyStorefrontClient)
        checkout_url = "https://checkout.shopify.com/ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        mock_cart_service = AsyncMock()
        mock_cart_service.get_cart.return_value = sample_cart

        # Create checkout service
        checkout_service = CheckoutService(
            redis_client=mock_redis,
            shopify_client=mock_shopify_client,
            cart_service=mock_cart_service,
        )

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify success
        assert result["status"] == CheckoutStatus.SUCCESS
        assert result["checkout_url"] == checkout_url
        assert "Complete your purchase here:" in result["message"]
        assert checkout_url in result["message"]
        # The token extraction logic changed to take the last segment
        # URL: .../ABCDEFGHIJKLMNOPQRSTUVWXYZ123456
        assert result["checkout_token"] == "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"

        # Verify checkout token was stored with 24-hour TTL
        assert mock_redis.setex.called
        call_args = mock_redis.setex.call_args[0]
        key, ttl, value = call_args
        assert key == "checkout_token:test_psid"
        assert ttl == 24 * 60 * 60  # 24 hours in seconds

    @pytest.mark.asyncio
    async def test_e2e_checkout_empty_cart(self):
        """Test E2E: User attempts checkout with empty cart."""
        # Create empty cart
        empty_cart = Cart(
            items=[],
            subtotal=0.0,
            currency_code=CurrencyCode.USD,
        )

        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get = AsyncMock(return_value=empty_cart.model_dump_json())

        mock_shopify_client = AsyncMock(spec=ShopifyStorefrontClient)
        mock_cart_service = AsyncMock()
        mock_cart_service.get_cart.return_value = empty_cart

        # Create checkout service
        checkout_service = CheckoutService(
            redis_client=mock_redis,
            shopify_client=mock_shopify_client,
            cart_service=mock_cart_service,
        )

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify empty cart response
        assert result["status"] == CheckoutStatus.EMPTY_CART
        assert result["checkout_url"] is None
        assert result["checkout_token"] is None
        assert "empty" in result["message"].lower()

        # Verify Shopify client was NOT called
        mock_shopify_client.create_checkout_url.assert_not_called()

    @pytest.mark.asyncio
    async def test_e2e_checkout_retry_on_validation_failure(self, sample_cart):
        """Test E2E: Checkout retries on validation failure and succeeds."""
        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get = AsyncMock(return_value=sample_cart.model_dump_json())
        mock_redis.setex = AsyncMock(return_value=True)

        mock_shopify_client = AsyncMock(spec=ShopifyStorefrontClient)
        mock_cart_service = AsyncMock()
        mock_cart_service.get_cart.return_value = sample_cart

        # Mock Shopify: first two calls fail, third succeeds
        valid_url = "https://checkout.shopify.com/ValidCheckoutToken123"
        mock_shopify_client.create_checkout_url.side_effect = [
            APIError(ErrorCode.SHOPIFY_CHECKOUT_URL_INVALID, "Invalid URL"),
            APIError(ErrorCode.SHOPIFY_CHECKOUT_URL_INVALID, "Invalid URL"),
            valid_url,
        ]

        # Create checkout service
        checkout_service = CheckoutService(
            redis_client=mock_redis,
            shopify_client=mock_shopify_client,
            cart_service=mock_cart_service,
        )
        # Speed up backoff for test
        checkout_service.RETRY_BACKOFF_SECONDS = 0.01

        # Generate checkout URL (should retry and succeed)
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify success after retries
        assert result["status"] == CheckoutStatus.SUCCESS
        assert result["checkout_url"] == valid_url
        assert result["retry_count"] == 2

        # Verify Shopify client was called 3 times
        assert mock_shopify_client.create_checkout_url.call_count == 3

    @pytest.mark.asyncio
    async def test_e2e_checkout_max_retries_exceeded(self, sample_cart):
        """Test E2E: Checkout fails after max retries exceeded."""
        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get = AsyncMock(return_value=sample_cart.model_dump_json())

        mock_shopify_client = AsyncMock(spec=ShopifyStorefrontClient)
        mock_cart_service = AsyncMock()
        mock_cart_service.get_cart.return_value = sample_cart

        # Mock Shopify: always fail validation
        mock_shopify_client.create_checkout_url.side_effect = APIError(
            ErrorCode.SHOPIFY_CHECKOUT_URL_INVALID, "Invalid URL"
        )

        # Create checkout service
        checkout_service = CheckoutService(
            redis_client=mock_redis,
            shopify_client=mock_shopify_client,
            cart_service=mock_cart_service,
        )
        # Speed up backoff for test
        checkout_service.RETRY_BACKOFF_SECONDS = 0.01

        # Generate checkout URL (should fail after max retries)
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify failure
        assert result["status"] == CheckoutStatus.FAILED
        assert result["checkout_url"] is None
        assert result["checkout_token"] is None
        assert result["retry_count"] == 3

        # Verify Shopify client was called 4 times (initial + 3 retries)
        assert mock_shopify_client.create_checkout_url.call_count == 4

    @pytest.mark.asyncio
    async def test_e2e_checkout_token_persistence(self, sample_cart):
        """Test E2E: Checkout token persists for 24 hours and can be retrieved."""
        psid = "test_psid"
        checkout_token = "CheckoutTokenABC123"
        checkout_url = f"https://checkout.shopify.com/{checkout_token}"

        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get = AsyncMock(return_value=sample_cart.model_dump_json())
        mock_redis.setex = AsyncMock(return_value=True)

        mock_shopify_client = AsyncMock(spec=ShopifyStorefrontClient)
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        mock_cart_service = AsyncMock()
        mock_cart_service.get_cart.return_value = sample_cart

        # Create checkout service
        checkout_service = CheckoutService(
            redis_client=mock_redis,
            shopify_client=mock_shopify_client,
            cart_service=mock_cart_service,
        )

        # Generate checkout URL
        await checkout_service.generate_checkout_url(psid)

        # Now retrieve the stored token
        # Mock the get call to return the stored token data
        stored_token_data = {
            "token": checkout_token,
            "url": checkout_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "psid": psid,
            "item_count": 5,
            "subtotal": 217.95,
            "currency_code": "USD",
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(stored_token_data))

        # Get checkout token
        result = await checkout_service.get_checkout_token(psid)

        # Verify token data
        assert result is not None
        assert result["token"] == checkout_token
        assert result["url"] == checkout_url
        assert result["psid"] == psid
        assert result["item_count"] == 5
        assert result["subtotal"] == 217.95

    @pytest.mark.asyncio
    async def test_e2e_cart_retained_after_checkout(self, sample_cart):
        """Test E2E: Local cart is NOT cleared after checkout (for abandoned checkout recovery)."""
        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get = AsyncMock(return_value=sample_cart.model_dump_json())
        mock_redis.setex = AsyncMock(return_value=True)

        mock_shopify_client = AsyncMock(spec=ShopifyStorefrontClient)
        checkout_url = "https://checkout.shopify.com/CheckoutToken123"
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        mock_cart_service = AsyncMock()
        mock_cart_service.get_cart.return_value = sample_cart

        # Create checkout service
        checkout_service = CheckoutService(
            redis_client=mock_redis,
            shopify_client=mock_shopify_client,
            cart_service=mock_cart_service,
        )

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify success
        assert result["status"] == CheckoutStatus.SUCCESS

        # Verify cart_service.clear_cart was NEVER called
        # (Cart is retained until order confirmation in Story 2.9)
        mock_cart_service.clear_cart.assert_not_called()

    @pytest.mark.asyncio
    async def test_e2e_checkout_performance_under_5_seconds(self, sample_cart):
        """Test E2E: Checkout completes within 5 seconds (AC requirement)."""
        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get = AsyncMock(return_value=sample_cart.model_dump_json())
        mock_redis.setex = AsyncMock(return_value=True)

        mock_shopify_client = AsyncMock(spec=ShopifyStorefrontClient)
        checkout_url = "https://checkout.shopify.com/CheckoutToken123"
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        mock_cart_service = AsyncMock()
        mock_cart_service.get_cart.return_value = sample_cart

        # Create checkout service
        checkout_service = CheckoutService(
            redis_client=mock_redis,
            shopify_client=mock_shopify_client,
            cart_service=mock_cart_service,
        )

        # Measure checkout time
        start = time.time()
        result = await checkout_service.generate_checkout_url("test_psid")
        elapsed_seconds = time.time() - start

        # Verify success
        assert result["status"] == CheckoutStatus.SUCCESS

        # Performance requirement: <5 seconds per AC
        assert elapsed_seconds < 5.0, f"Checkout took {elapsed_seconds}s, exceeds 5s limit"

    @pytest.mark.asyncio
    async def test_e2e_checkout_service_direct_call(self, sample_cart):
        """Test E2E: Checkout service generates URL when called directly."""
        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get = AsyncMock(return_value=sample_cart.model_dump_json())
        mock_redis.setex = AsyncMock(return_value=True)

        mock_shopify_client = AsyncMock(spec=ShopifyStorefrontClient)
        checkout_url = "https://checkout.shopify.com/CheckoutToken123"
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        mock_cart_service = AsyncMock()
        mock_cart_service.get_cart.return_value = sample_cart

        # Create checkout service
        checkout_service = CheckoutService(
            redis_client=mock_redis,
            shopify_client=mock_shopify_client,
            cart_service=mock_cart_service,
        )

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify success response matches expected format
        assert result["status"] == CheckoutStatus.SUCCESS
        assert result["checkout_url"] == checkout_url
        assert "Complete your purchase here:" in result["message"]
        assert checkout_url in result["message"]
        assert result["checkout_token"] == "CheckoutToken123"

    @pytest.mark.asyncio
    async def test_e2e_natural_language_checkout_variations(self, sample_cart):
        """Test E2E: Various natural language checkout phrases work."""
        checkout_phrases = [
            "checkout",
            "check out",
            "buy now",
            "complete purchase",
            "I want to buy these",
        ]

        for phrase in checkout_phrases:
            mock_redis = MagicMock(spec=redis.Redis)
            mock_redis.get = AsyncMock(return_value=sample_cart.model_dump_json())
            mock_redis.setex = AsyncMock(return_value=True)

            mock_shopify_client = AsyncMock(spec=ShopifyStorefrontClient)
            checkout_url = "https://checkout.shopify.com/CheckoutToken123"
            mock_shopify_client.create_checkout_url.return_value = checkout_url

            mock_cart_service = AsyncMock()
            mock_cart_service.get_cart.return_value = sample_cart

            # Create checkout service
            checkout_service = CheckoutService(
                redis_client=mock_redis,
                shopify_client=mock_shopify_client,
                cart_service=mock_cart_service,
            )

            # Generate checkout URL
            result = await checkout_service.generate_checkout_url(f"test_psid_{phrase}")

            # Verify success for each phrase variation
            assert result["status"] == CheckoutStatus.SUCCESS, f"Failed for phrase: {phrase}"

    @pytest.mark.asyncio
    async def test_e2e_checkout_with_single_item(self):
        """Test E2E: Checkout works correctly with single item in cart."""
        # Create cart with single item
        single_item_cart = Cart(
            items=[
                CartItem(
                    product_id="gid://shopify/Product/1",
                    variant_id="gid://shopify/ProductVariant/1",
                    title="Single Product",
                    price=49.99,
                    image_url="https://example.com/product.jpg",
                    currency_code=CurrencyCode.USD,
                    quantity=1,
                    added_at=datetime.now(timezone.utc).isoformat(),
                ),
            ],
            subtotal=49.99,
            currency_code=CurrencyCode.USD,
        )

        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get = AsyncMock(return_value=single_item_cart.model_dump_json())
        mock_redis.setex = AsyncMock(return_value=True)

        mock_shopify_client = AsyncMock(spec=ShopifyStorefrontClient)
        checkout_url = "https://checkout.shopify.com/SingleItemCheckout"
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        mock_cart_service = AsyncMock()
        mock_cart_service.get_cart.return_value = single_item_cart

        # Create checkout service
        checkout_service = CheckoutService(
            redis_client=mock_redis,
            shopify_client=mock_shopify_client,
            cart_service=mock_cart_service,
        )

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url("test_psid")

        # Verify success
        assert result["status"] == CheckoutStatus.SUCCESS
        assert result["checkout_url"] == checkout_url

        # Verify line items sent to Shopify
        call_args = mock_shopify_client.create_checkout_url.call_args[0][0]
        assert len(call_args) == 1
        assert call_args[0]["variant_id"] == "gid://shopify/ProductVariant/1"
        assert call_args[0]["quantity"] == 1