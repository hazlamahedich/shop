"""Tests for Null Store Provider.

Sprint Change 2026-02-13: Make Shopify Optional Integration

Tests the NullStoreProvider which is used when a merchant has not
connected an e-commerce store.
"""

import pytest
import asyncio

from app.services.ecommerce.null_provider import NullStoreProvider
from app.services.ecommerce.base import StoreNotConnectedError


class TestNullStoreProvider:
    """Tests for NullStoreProvider class."""

    @pytest.fixture
    def provider(self):
        """Create a NullStoreProvider instance for testing."""
        return NullStoreProvider()

    @pytest.fixture
    def custom_provider(self):
        """Create a NullStoreProvider with custom message."""
        return NullStoreProvider(message="Custom error message")

    # ==================== Basic Properties ====================

    def test_provider_name(self, provider):
        """Test that provider_name returns 'none'."""
        assert provider.provider_name == "none"

    def test_is_connected_returns_false(self, provider):
        """Test that is_connected always returns False."""
        assert provider.is_connected() is False

    def test_default_message(self, provider):
        """Test default error message."""
        assert "No e-commerce store connected" in provider._message

    def test_custom_message(self, custom_provider):
        """Test custom error message."""
        assert custom_provider._message == "Custom error message"

    # ==================== Product Operations ====================

    @pytest.mark.asyncio
    async def test_search_products_raises_error(self, provider):
        """Test that search_products raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError) as exc_info:
            await provider.search_products("shoes")

        assert "No e-commerce store connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_product_raises_error(self, provider):
        """Test that get_product raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.get_product("product-123")

    @pytest.mark.asyncio
    async def test_get_product_variants_raises_error(self, provider):
        """Test that get_product_variants raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.get_product_variants("product-123")

    # ==================== Cart Operations ====================

    @pytest.mark.asyncio
    async def test_create_cart_raises_error(self, provider):
        """Test that create_cart raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.create_cart()

    @pytest.mark.asyncio
    async def test_get_cart_raises_error(self, provider):
        """Test that get_cart raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.get_cart("cart-123")

    @pytest.mark.asyncio
    async def test_add_to_cart_raises_error(self, provider):
        """Test that add_to_cart raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.add_to_cart("cart-123", "variant-456")

    @pytest.mark.asyncio
    async def test_update_cart_item_raises_error(self, provider):
        """Test that update_cart_item raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.update_cart_item("cart-123", "variant-456", 2)

    @pytest.mark.asyncio
    async def test_remove_from_cart_raises_error(self, provider):
        """Test that remove_from_cart raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.remove_from_cart("cart-123", "variant-456")

    # ==================== Checkout Operations ====================

    @pytest.mark.asyncio
    async def test_create_checkout_url_raises_error(self, provider):
        """Test that create_checkout_url raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.create_checkout_url("cart-123")

    # ==================== Order Operations ====================

    @pytest.mark.asyncio
    async def test_get_order_raises_error(self, provider):
        """Test that get_order raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.get_order("order-123")

    @pytest.mark.asyncio
    async def test_get_order_by_checkout_token_raises_error(self, provider):
        """Test that get_order_by_checkout_token raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.get_order_by_checkout_token("token-123")

    @pytest.mark.asyncio
    async def test_update_order_status_raises_error(self, provider):
        """Test that update_order_status raises StoreNotConnectedError."""
        from app.services.ecommerce.base import OrderStatus

        with pytest.raises(StoreNotConnectedError):
            await provider.update_order_status(
                "order-123",
                OrderStatus.SHIPPED,
                tracking_number="TRACK123",
            )

    # ==================== Error Message Tests ====================

    @pytest.mark.asyncio
    async def test_error_includes_provider_name(self, provider):
        """Test that error includes the provider name."""
        with pytest.raises(StoreNotConnectedError) as exc_info:
            await provider.search_products("test")

        # The error should include provider name
        assert exc_info.value.provider == "none"

    @pytest.mark.asyncio
    async def test_custom_message_in_error(self, custom_provider):
        """Test that custom message appears in error."""
        with pytest.raises(StoreNotConnectedError) as exc_info:
            await custom_provider.search_products("test")

        assert "Custom error message" in str(exc_info.value)
