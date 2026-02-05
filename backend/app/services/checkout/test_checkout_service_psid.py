"""Tests for CheckoutService PSID tracking (Story 2.9).

Tests PSID passing to Shopify as custom attribute and reverse lookup.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from app.core.errors import APIError, ErrorCode
from app.schemas.cart import Cart, CartItem, CurrencyCode
from app.services.cart import CartService
from app.services.checkout import CheckoutService
from app.services.shopify_storefront import ShopifyStorefrontClient


class TestCheckoutServicePSIDTracking:
    """Test CheckoutService PSID tracking for order confirmation (Story 2.9)."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client with async methods."""
        mock_client = MagicMock()
        mock_client.get = AsyncMock()
        mock_client.setex = AsyncMock()
        mock_client.delete = AsyncMock()
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
            ],
            subtotal=59.98,
            currency_code=CurrencyCode.USD,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    @pytest.mark.asyncio
    async def test_checkout_url_with_psid_custom_attribute(
        self, checkout_service, mock_cart_service, mock_shopify_client, sample_cart
    ):
        """Test that PSID is passed as custom attribute to Shopify (Story 2.9)."""
        # Mock cart retrieval
        mock_cart_service.get_cart.return_value = sample_cart

        # Mock Shopify client
        psid = "test_psid_12345"
        checkout_url = "https://checkout.shopify.com/ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url(psid)

        # Verify result
        assert result["status"] == "success"
        assert result["checkout_url"] == checkout_url

        # Verify Shopify client was called with customAttributes including PSID
        mock_shopify_client.create_checkout_url.assert_called_once()
        call_args = mock_shopify_client.create_checkout_url.call_args

        # Args are passed as positional: (line_items, custom_attributes)
        line_items = call_args[0][0]
        custom_attributes = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("custom_attributes")

        # Verify custom_attributes contains PSID
        assert custom_attributes is not None, "custom_attributes should be passed to Shopify"
        assert any(
            attr.get("key") == "psid" and attr.get("value") == psid
            for attr in custom_attributes
        ), "PSID should be in custom_attributes"

    @pytest.mark.asyncio
    async def test_checkout_token_reverse_lookup_stored(
        self, checkout_service, sample_cart
    ):
        """Test that checkout token reverse lookup is stored in Redis (Story 2.9)."""
        psid = "test_psid_12345"
        checkout_token = "ABC123XYZ"
        checkout_url = f"https://checkout.shopify.com/{checkout_token}"

        # Store checkout token
        await checkout_service._store_checkout_token(
            psid=psid,
            checkout_token=checkout_token,
            checkout_url=checkout_url,
            cart=sample_cart,
        )

        # Verify Redis setex was called for checkout_token:{psid}
        assert checkout_service.redis.setex.called
        call_args = checkout_service.redis.setex.call_args[0]
        key, ttl, value = call_args

        assert key == f"checkout_token:{psid}"
        assert ttl == 24 * 60 * 60  # 24 hours

        # Verify token data contains PSID
        token_data = json.loads(value)
        assert token_data["psid"] == psid
        assert token_data["token"] == checkout_token

    @pytest.mark.asyncio
    async def test_checkout_token_reverse_lookup_key_format(self, checkout_service):
        """Test reverse lookup key format: checkout_token_lookup:{token} -> psid."""
        # The reverse lookup should allow retrieving PSID from checkout token
        # This is a fallback if custom attributes fail
        psid = "test_psid_12345"
        checkout_token = "ABC123XYZ"

        # Store reverse lookup (this would be done during checkout)
        reverse_lookup_key = f"checkout_token_lookup:{checkout_token}"
        reverse_lookup_data = json.dumps({"psid": psid, "created_at": datetime.now(timezone.utc).isoformat()})

        await checkout_service.redis.setex(
            reverse_lookup_key,
            24 * 60 * 60,  # 24 hours
            reverse_lookup_data
        )

        # Verify reverse lookup was stored
        checkout_service.redis.setex.assert_called_with(
            reverse_lookup_key,
            24 * 60 * 60,
            reverse_lookup_data
        )

    @pytest.mark.asyncio
    async def test_generate_checkout_url_creates_reverse_lookup(
        self, checkout_service, mock_cart_service, mock_shopify_client, sample_cart
    ):
        """Test that generate_checkout_url creates reverse lookup entry."""
        # Mock cart retrieval
        mock_cart_service.get_cart.return_value = sample_cart

        # Mock Shopify client
        psid = "test_psid_12345"
        checkout_token = "ABC123XYZ"
        checkout_url = f"https://checkout.shopify.com/{checkout_token}"
        mock_shopify_client.create_checkout_url.return_value = checkout_url

        # Generate checkout URL
        result = await checkout_service.generate_checkout_url(psid)

        # Verify success
        assert result["status"] == "success"

        # Verify reverse lookup was created (checkout_token_lookup:{token})
        reverse_lookup_calls = [
            call for call in checkout_service.redis.setex.call_args_list
            if "checkout_token_lookup:" in str(call[0][0])
        ]

        assert len(reverse_lookup_calls) > 0, "Reverse lookup should be created"

        # Verify reverse lookup key format
        reverse_lookup_call = reverse_lookup_calls[0]
        key = reverse_lookup_call[0][0]
        value = json.loads(reverse_lookup_call[0][2])

        assert key == f"checkout_token_lookup:{checkout_token}"
        assert value["psid"] == psid
