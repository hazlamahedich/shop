"""Tests for cart Pydantic schemas.

Tests CartItem and Cart validation, camelCase aliases,
subtotal calculation, and item count computation.
"""

import pytest
from app.schemas.cart import Cart, CartItem, CurrencyCode


class TestCartItem:
    """Test CartItem schema validation."""

    def test_cart_item_creation_with_defaults(self):
        """Test creating cart item with default values."""
        item = CartItem(
            product_id="gid://shopify/Product/123",
            variant_id="gid://shopify/ProductVariant/456",
            title="Test Product",
            price=29.99,
            image_url="https://example.com/image.jpg"
        )

        assert item.product_id == "gid://shopify/Product/123"
        assert item.variant_id == "gid://shopify/ProductVariant/456"
        assert item.title == "Test Product"
        assert item.price == 29.99
        assert item.image_url == "https://example.com/image.jpg"
        assert item.currency_code == CurrencyCode.USD
        assert item.quantity == 1
        assert item.added_at is None

    def test_cart_item_with_all_fields(self):
        """Test creating cart item with all fields."""
        item = CartItem(
            product_id="prod_1",
            variant_id="var_1",
            title="Full Product",
            price=99.99,
            image_url="https://example.com/full.jpg",
            currency_code=CurrencyCode.EUR,
            quantity=3,
            added_at="2024-01-15T10:30:00Z"
        )

        assert item.quantity == 3
        assert item.currency_code == CurrencyCode.EUR
        assert item.added_at == "2024-01-15T10:30:00Z"

    def test_cart_item_price_must_be_positive(self):
        """Test that price must be positive."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CartItem(
                product_id="prod_1",
                variant_id="var_1",
                title="Invalid Product",
                price=0,
                image_url="https://example.com/image.jpg"
            )

        with pytest.raises(ValidationError):
            CartItem(
                product_id="prod_1",
                variant_id="var_1",
                title="Negative Price",
                price=-10.0,
                image_url="https://example.com/image.jpg"
            )

    def test_cart_item_quantity_validation(self):
        """Test quantity validation (1-10)."""
        # Minimum boundary
        item = CartItem(
            product_id="prod_1",
            variant_id="var_1",
            title="Test",
            price=10.0,
            image_url="https://example.com/image.jpg",
            quantity=1
        )
        assert item.quantity == 1

        with pytest.raises(ValueError):
            CartItem(
                product_id="prod_1",
                variant_id="var_1",
                title="Test",
                price=10.0,
                image_url="https://example.com/image.jpg",
                quantity=0
            )

        # Maximum boundary
        item = CartItem(
            product_id="prod_1",
            variant_id="var_1",
            title="Test",
            price=10.0,
            image_url="https://example.com/image.jpg",
            quantity=10
        )
        assert item.quantity == 10

        with pytest.raises(ValueError):
            CartItem(
                product_id="prod_1",
                variant_id="var_1",
                title="Test",
                price=10.0,
                image_url="https://example.com/image.jpg",
                quantity=11
            )

    def test_cart_item_camel_case_serialization(self):
        """Test that cart item serializes with camelCase."""
        item = CartItem(
            product_id="prod_1",
            variant_id="var_1",
            title="Test Product",
            price=29.99,
            image_url="https://example.com/image.jpg"
        )

        data = item.model_dump(by_alias=True)

        assert "productId" in data
        assert "variantId" in data
        assert "imageUrl" in data
        assert "currencyCode" in data
        assert "productId" not in str(item.model_dump())
        assert "variantId" not in str(item.model_dump())


class TestCart:
    """Test Cart schema validation."""

    def test_empty_cart_creation(self):
        """Test creating empty cart."""
        cart = Cart()

        assert cart.items == []
        assert cart.subtotal == 0.0
        assert cart.currency_code == CurrencyCode.USD
        assert cart.item_count == 0
        assert cart.is_empty is True

    def test_cart_with_items(self):
        """Test creating cart with items."""
        items = [
            CartItem(
                product_id="prod_1",
                variant_id="var_1",
                title="Product 1",
                price=10.0,
                image_url="https://example.com/img1.jpg",
                quantity=2
            ),
            CartItem(
                product_id="prod_2",
                variant_id="var_2",
                title="Product 2",
                price=20.0,
                image_url="https://example.com/img2.jpg",
                quantity=1
            )
        ]

        cart = Cart(items=items, subtotal=40.0)

        assert len(cart.items) == 2
        assert cart.subtotal == 40.0
        assert cart.item_count == 3  # 2 + 1
        assert cart.is_empty is False

    def test_cart_item_count_calculation(self):
        """Test that item_count is calculated from items."""
        items = [
            CartItem(
                product_id="prod_1",
                variant_id="var_1",
                title="Product 1",
                price=10.0,
                image_url="https://example.com/img1.jpg",
                quantity=3
            ),
            CartItem(
                product_id="prod_2",
                variant_id="var_2",
                title="Product 2",
                price=20.0,
                image_url="https://example.com/img2.jpg",
                quantity=2
            )
        ]

        cart = Cart(items=items)

        # item_count should be sum of quantities
        assert cart.item_count == 5  # 3 + 2

    def test_cart_subtotal_validation(self):
        """Test subtotal validation (must be >= 0)."""
        # Valid subtotal
        cart = Cart(subtotal=0.0)
        assert cart.subtotal == 0.0

        cart = Cart(subtotal=100.0)
        assert cart.subtotal == 100.0

        # Invalid subtotal
        with pytest.raises(ValueError):
            Cart(subtotal=-10.0)

    def test_cart_camel_case_serialization(self):
        """Test that cart serializes with camelCase."""
        items = [
            CartItem(
                product_id="prod_1",
                variant_id="var_1",
                title="Product 1",
                price=10.0,
                image_url="https://example.com/img1.jpg"
            )
        ]

        cart = Cart(items=items, subtotal=10.0)

        data = cart.model_dump(by_alias=True)

        assert "currencyCode" in data
        assert "itemCount" in data
        assert "createdAt" in data
        assert "updatedAt" in data

    def test_cart_is_empty_property(self):
        """Test is_empty property."""
        # Empty cart
        cart = Cart()
        assert cart.is_empty is True

        # Cart with items
        items = [
            CartItem(
                product_id="prod_1",
                variant_id="var_1",
                title="Product 1",
                price=10.0,
                image_url="https://example.com/img1.jpg"
            )
        ]
        cart = Cart(items=items)
        assert cart.is_empty is False
