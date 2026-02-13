"""Tests for E-Commerce Abstraction Layer.

Sprint Change Proposal 2026-02-13: Make Shopify Optional Integration

Tests for:
- ECommerceProvider base models
- NullStoreProvider
- MockStoreProvider
- Provider factory functions
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.services.ecommerce.base import (
    Cart,
    CartItem,
    CurrencyCode,
    ECommerceProvider,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    ProductVariant,
    StoreNotConnectedError,
)
from app.services.ecommerce.null_provider import NullStoreProvider
from app.services.ecommerce.mock_provider import MockStoreProvider
from app.services.ecommerce.provider_factory import (
    StoreProvider,
    get_null_provider,
    get_mock_provider,
    get_provider,
    has_store_connected,
)


# ==================== StoreNotConnectedError Tests ====================

class TestStoreNotConnectedError:
    """Tests for StoreNotConnectedError exception."""

    def test_default_message(self):
        """Test default error message."""
        error = StoreNotConnectedError()
        assert "No e-commerce store connected" in error.message
        assert error.provider == "none"

    def test_custom_message(self):
        """Test custom error message."""
        error = StoreNotConnectedError(
            message="Custom error message",
            provider="shopify",
        )
        assert error.message == "Custom error message"
        assert error.provider == "shopify"

    def test_exception_inheritance(self):
        """Test that it inherits from Exception."""
        error = StoreNotConnectedError()
        assert isinstance(error, Exception)


# ==================== Data Model Tests ====================

class TestProductVariant:
    """Tests for ProductVariant model."""

    def test_create_variant(self):
        """Test creating a product variant."""
        variant = ProductVariant(
            id="variant_1",
            title="Small / Red",
            price=29.99,
            currency_code=CurrencyCode.USD,
            available=True,
        )
        assert variant.id == "variant_1"
        assert variant.price == 29.99
        assert variant.available is True

    def test_variant_with_options(self):
        """Test variant with options."""
        variant = ProductVariant(
            id="variant_1",
            title="Small / Red",
            price=29.99,
            options=[
                {"name": "Size", "value": "Small"},
                {"name": "Color", "value": "Red"},
            ],
        )
        assert len(variant.options) == 2


class TestProduct:
    """Tests for Product model."""

    def test_create_product(self):
        """Test creating a product."""
        product = Product(
            id="prod_1",
            title="Test Product",
            price_min=29.99,
            price_max=39.99,
        )
        assert product.id == "prod_1"
        assert product.title == "Test Product"
        assert product.price_min == 29.99
        assert product.available is True

    def test_product_with_variants(self):
        """Test product with variants."""
        product = Product(
            id="prod_1",
            title="Test Product",
            price_min=29.99,
            price_max=39.99,
            variants=[
                ProductVariant(id="v1", title="Small", price=29.99),
                ProductVariant(id="v2", title="Large", price=39.99),
            ],
        )
        assert len(product.variants) == 2


class TestCartItem:
    """Tests for CartItem model."""

    def test_create_cart_item(self):
        """Test creating a cart item."""
        item = CartItem(
            product_id="prod_1",
            variant_id="var_1",
            title="Test Item",
            price=29.99,
            quantity=2,
        )
        assert item.product_id == "prod_1"
        assert item.quantity == 2

    def test_cart_item_defaults(self):
        """Test cart item default values."""
        item = CartItem(
            product_id="prod_1",
            variant_id="var_1",
            title="Test",
            price=10.00,
        )
        assert item.quantity == 1
        assert item.currency_code == CurrencyCode.USD


class TestCart:
    """Tests for Cart model."""

    def test_create_cart(self):
        """Test creating a cart."""
        cart = Cart(id="cart_1")
        assert cart.id == "cart_1"
        assert cart.items == []
        assert cart.subtotal == 0.0

    def test_cart_with_items(self):
        """Test cart with items."""
        cart = Cart(
            id="cart_1",
            items=[
                CartItem(
                    product_id="p1",
                    variant_id="v1",
                    title="Item 1",
                    price=10.00,
                    quantity=2,
                ),
            ],
            subtotal=20.0,
            item_count=2,
        )
        assert len(cart.items) == 1
        assert cart.subtotal == 20.0


class TestOrder:
    """Tests for Order model."""

    def test_create_order(self):
        """Test creating an order."""
        order = Order(id="order_1")
        assert order.id == "order_1"
        assert order.status == OrderStatus.PENDING

    def test_order_with_tracking(self):
        """Test order with tracking info."""
        order = Order(
            id="order_1",
            status=OrderStatus.SHIPPED,
            tracking_number="TRACK123",
            tracking_url="https://track.example.com/TRACK123",
        )
        assert order.status == OrderStatus.SHIPPED
        assert order.tracking_number == "TRACK123"


# ==================== NullStoreProvider Tests ====================

class TestNullStoreProvider:
    """Tests for NullStoreProvider."""

    @pytest.fixture
    def provider(self):
        """Create a NullStoreProvider instance."""
        return NullStoreProvider()

    def test_provider_name(self, provider):
        """Test provider name is 'none'."""
        assert provider.provider_name == "none"

    def test_is_connected_returns_false(self, provider):
        """Test is_connected returns False."""
        assert provider.is_connected() is False

    @pytest.mark.asyncio
    async def test_search_products_raises_error(self, provider):
        """Test search_products raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError) as exc_info:
            await provider.search_products("shoes")
        assert "No e-commerce store connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_product_raises_error(self, provider):
        """Test get_product raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.get_product("prod_1")

    @pytest.mark.asyncio
    async def test_create_cart_raises_error(self, provider):
        """Test create_cart raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.create_cart()

    @pytest.mark.asyncio
    async def test_create_checkout_url_raises_error(self, provider):
        """Test create_checkout_url raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.create_checkout_url("cart_1")

    @pytest.mark.asyncio
    async def test_get_order_raises_error(self, provider):
        """Test get_order raises StoreNotConnectedError."""
        with pytest.raises(StoreNotConnectedError):
            await provider.get_order("order_1")


# ==================== MockStoreProvider Tests ====================

class TestMockStoreProvider:
    """Tests for MockStoreProvider."""

    @pytest.fixture
    def provider(self):
        """Create a MockStoreProvider instance."""
        return MockStoreProvider()

    def test_provider_name(self, provider):
        """Test provider name is 'mock'."""
        assert provider.provider_name == "mock"

    def test_is_connected_when_enabled(self, provider, monkeypatch):
        """Test is_connected returns True when IS_TESTING is set."""
        monkeypatch.setenv("IS_TESTING", "true")
        assert provider.is_connected() is True

    def test_is_connected_when_disabled(self, provider, monkeypatch):
        """Test is_connected returns False when not enabled."""
        monkeypatch.delenv("IS_TESTING", raising=False)
        monkeypatch.delenv("MOCK_STORE_ENABLED", raising=False)
        assert provider.is_connected() is False

    @pytest.mark.asyncio
    async def test_search_products_returns_mock_data(self, provider, monkeypatch):
        """Test search_products returns mock products."""
        monkeypatch.setenv("IS_TESTING", "true")
        results = await provider.search_products("shoes")
        assert len(results) > 0
        assert any("shoes" in p.title.lower() for p in results)

    @pytest.mark.asyncio
    async def test_search_products_with_limit(self, provider, monkeypatch):
        """Test search_products respects limit."""
        monkeypatch.setenv("IS_TESTING", "true")
        results = await provider.search_products("", limit=2)
        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_search_products_with_price_filter(self, provider, monkeypatch):
        """Test search_products with max_price filter."""
        monkeypatch.setenv("IS_TESTING", "true")
        results = await provider.search_products("", max_price=50.0)
        for product in results:
            assert product.price_min <= 50.0

    @pytest.mark.asyncio
    async def test_get_product_found(self, provider, monkeypatch):
        """Test get_product returns product if found."""
        monkeypatch.setenv("IS_TESTING", "true")
        product = await provider.get_product("mock_prod_001")
        assert product is not None
        assert product.title == "Running Shoes Pro"

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, provider, monkeypatch):
        """Test get_product returns None if not found."""
        monkeypatch.setenv("IS_TESTING", "true")
        product = await provider.get_product("nonexistent")
        assert product is None

    @pytest.mark.asyncio
    async def test_create_cart(self, provider, monkeypatch):
        """Test create_cart creates a cart."""
        monkeypatch.setenv("IS_TESTING", "true")
        cart = await provider.create_cart()
        assert cart.id.startswith("mock_cart_")
        assert len(cart.items) == 0

    @pytest.mark.asyncio
    async def test_add_to_cart(self, provider, monkeypatch):
        """Test add_to_cart adds items."""
        monkeypatch.setenv("IS_TESTING", "true")
        cart = await provider.create_cart()
        updated = await provider.add_to_cart(
            cart.id,
            "mock_var_001_a",
            quantity=2,
        )
        assert len(updated.items) == 1
        assert updated.items[0].quantity == 2
        assert updated.subtotal == 99.99 * 2

    @pytest.mark.asyncio
    async def test_update_cart_item(self, provider, monkeypatch):
        """Test update_cart_item updates quantity."""
        monkeypatch.setenv("IS_TESTING", "true")
        cart = await provider.create_cart()
        await provider.add_to_cart(cart.id, "mock_var_001_a", quantity=1)
        updated = await provider.update_cart_item(cart.id, "mock_var_001_a", quantity=3)
        assert updated.items[0].quantity == 3

    @pytest.mark.asyncio
    async def test_remove_from_cart(self, provider, monkeypatch):
        """Test remove_from_cart removes items."""
        monkeypatch.setenv("IS_TESTING", "true")
        cart = await provider.create_cart()
        await provider.add_to_cart(cart.id, "mock_var_001_a", quantity=1)
        updated = await provider.remove_from_cart(cart.id, "mock_var_001_a")
        assert len(updated.items) == 0

    @pytest.mark.asyncio
    async def test_create_checkout_url(self, provider, monkeypatch):
        """Test create_checkout_url generates URL."""
        monkeypatch.setenv("IS_TESTING", "true")
        cart = await provider.create_cart()
        await provider.add_to_cart(cart.id, "mock_var_001_a", quantity=1)
        url = await provider.create_checkout_url(cart.id)
        assert url.startswith("https://mock-checkout.example.com/checkout/")

    @pytest.mark.asyncio
    async def test_create_checkout_url_empty_cart_fails(self, provider, monkeypatch):
        """Test create_checkout_url fails for empty cart."""
        monkeypatch.setenv("IS_TESTING", "true")
        cart = await provider.create_cart()
        with pytest.raises(ValueError, match="empty cart"):
            await provider.create_checkout_url(cart.id)


# ==================== Provider Factory Tests ====================

class TestProviderFactory:
    """Tests for provider factory functions."""

    def test_get_null_provider_returns_singleton(self):
        """Test get_null_provider returns same instance."""
        provider1 = get_null_provider()
        provider2 = get_null_provider()
        assert provider1 is provider2

    def test_get_mock_provider_returns_singleton(self):
        """Test get_mock_provider returns same instance."""
        provider1 = get_mock_provider()
        provider2 = get_mock_provider()
        assert provider1 is provider2

    def test_get_provider_returns_null_for_none(self):
        """Test get_provider returns NullStoreProvider for NONE."""
        provider = get_provider(StoreProvider.NONE)
        assert isinstance(provider, NullStoreProvider)

    def test_get_provider_returns_mock_for_mock(self):
        """Test get_provider returns MockStoreProvider for MOCK."""
        provider = get_provider(StoreProvider.MOCK)
        assert isinstance(provider, MockStoreProvider)

    def test_has_store_connected_null_provider(self):
        """Test has_store_connected returns False for null provider."""
        result = has_store_connected(None)
        assert result is False

    def test_has_store_connected_mock_provider(self, monkeypatch):
        """Test has_store_connected returns True when mock enabled."""
        monkeypatch.setenv("IS_TESTING", "true")
        result = has_store_connected(None)
        assert result is True


# ==================== Integration Tests ====================

class TestECommerceIntegration:
    """Integration tests for e-commerce abstraction."""

    @pytest.mark.asyncio
    async def test_full_shopping_flow_with_mock(self, monkeypatch):
        """Test complete shopping flow with mock provider."""
        monkeypatch.setenv("IS_TESTING", "true")
        provider = get_mock_provider()

        # 1. Search for products
        products = await provider.search_products("shoes")
        assert len(products) > 0

        # 2. Get product details
        product = await provider.get_product(products[0].id)
        assert product is not None

        # 3. Create cart
        cart = await provider.create_cart()
        assert cart is not None

        # 4. Add item to cart
        variant_id = product.variants[0].id if product.variants else "mock_var_001_a"
        cart = await provider.add_to_cart(cart.id, variant_id, quantity=2)
        assert len(cart.items) == 1
        assert cart.item_count == 2

        # 5. Create checkout URL
        checkout_url = await provider.create_checkout_url(cart.id)
        assert checkout_url is not None

        # 6. Get order by checkout token
        token = checkout_url.split("/")[-1]
        order = await provider.get_order_by_checkout_token(token)
        assert order is not None

        # 7. Update order status
        updated_order = await provider.update_order_status(
            order.id,
            OrderStatus.CONFIRMED,
        )
        assert updated_order.status == OrderStatus.CONFIRMED

    @pytest.mark.asyncio
    async def test_null_provider_blocks_all_operations(self):
        """Test that NullStoreProvider blocks all operations."""
        provider = get_null_provider()

        # All operations should raise StoreNotConnectedError
        with pytest.raises(StoreNotConnectedError):
            await provider.search_products("test")

        with pytest.raises(StoreNotConnectedError):
            await provider.get_product("test")

        with pytest.raises(StoreNotConnectedError):
            await provider.create_cart()

        with pytest.raises(StoreNotConnectedError):
            await provider.get_order("test")
