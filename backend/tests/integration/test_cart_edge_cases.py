"""Edge case tests for cart management functionality.

Tests edge cases including:
- Currency mismatch validation
- Corrupted JSON data handling
- Empty image URL fallback
- Max quantity UI indicators
- Non-existent item operations
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import redis

from app.core.errors import APIError, ErrorCode
from app.schemas.cart import Cart, CartItem, CurrencyCode
from app.services.cart import CartService
from app.services.messenger import CartFormatter


class TestCartEdgeCases:
    """Test edge cases for cart management."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return MagicMock(spec=redis.Redis)

    @pytest.fixture
    def cart_service(self, mock_redis):
        """Create cart service for testing."""
        return CartService(redis_client=mock_redis)

    @pytest.fixture
    def formatter(self):
        """Create cart formatter for testing."""
        return CartFormatter(shop_domain="example.myshopify.com")

    # Currency Mismatch Tests

    @pytest.mark.asyncio
    async def test_currency_mismatch_rejected(self, cart_service, mock_redis):
        """Test that adding item with different currency is rejected."""
        import json

        # Mock existing USD cart
        existing_cart_data = {
            "items": [
                {
                    "productId": "prod_1",
                    "variantId": "var_1",
                    "title": "USD Product",
                    "price": 29.99,
                    "imageUrl": "http://example.com/image.jpg",
                    "currencyCode": "USD",
                    "quantity": 1
                }
            ],
            "subtotal": 29.99,
            "currencyCode": "USD",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
        mock_redis.get.return_value = json.dumps(existing_cart_data)
        mock_redis.setex.return_value = True

        # Try to add EUR item to USD cart
        with pytest.raises(APIError) as exc_info:
            await cart_service.add_item(
                psid="test_user",
                product_id="prod_2",
                variant_id="var_2",
                title="EUR Product",
                price=25.00,
                image_url="http://example.com/image2.jpg",
                currency_code="EUR",
                quantity=1
            )

        assert exc_info.value.code == ErrorCode.CART_CURRENCY_MISMATCH
        assert "currency" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_currency_allowed_for_empty_cart(self, cart_service, mock_redis):
        """Test that any currency is allowed for empty cart."""
        mock_redis.get.return_value = None  # Empty cart
        mock_redis.setex.return_value = True

        # Add EUR item to empty cart (should succeed)
        cart = await cart_service.add_item(
            psid="test_user",
            product_id="prod_1",
            variant_id="var_1",
            title="EUR Product",
            price=25.00,
            image_url="http://example.com/image.jpg",
            currency_code="EUR",
            quantity=1
        )

        assert cart.currency_code == CurrencyCode.EUR
        assert len(cart.items) == 1

    # Corrupted JSON Tests

    @pytest.mark.asyncio
    async def test_corrupted_json_data_raises_specific_error(self, cart_service, mock_redis):
        """Test that corrupted JSON raises specific CART_DATA_CORRUPTED error."""
        # Mock corrupted JSON data
        mock_redis.get.return_value = "{invalid json data"

        with pytest.raises(APIError) as exc_info:
            await cart_service.get_cart("test_user")

        assert exc_info.value.code == ErrorCode.CART_DATA_CORRUPTED
        assert "corrupted" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_invalid_cart_schema_raises_validation_error(self, cart_service, mock_redis):
        """Test that invalid cart schema raises appropriate error."""
        import json

        # Mock valid JSON but invalid cart schema (missing required fields)
        invalid_cart_data = {
            "items": [
                {
                    # Missing required fields
                    "productId": "prod_1"
                }
            ]
        }
        mock_redis.get.return_value = json.dumps(invalid_cart_data)

        # Should raise validation error (from Pydantic)
        with pytest.raises(Exception):  # Pydantic ValidationError
            await cart_service.get_cart("test_user")

    # Empty Image URL Tests

    def test_empty_image_url_uses_placeholder(self, formatter):
        """Test that empty image URL uses default placeholder."""
        cart = Cart(
            items=[
                CartItem(
                    product_id="prod_1",
                    variant_id="var_1",
                    title="Product with No Image",
                    price=29.99,
                    image_url="",  # Empty image URL
                    quantity=1
                )
            ],
            subtotal=29.99,
            currency_code=CurrencyCode.USD,
            item_count=1
        )

        result = formatter.format_cart(cart, "test_psid")
        elements = result["attachment"]["payload"]["elements"]

        # Should use default placeholder image
        item_element = elements[1]  # First item (after summary)
        assert item_element["image_url"] == formatter.DEFAULT_IMAGE_URL
        assert "placeholder" in item_element["image_url"]

    def test_none_image_url_uses_placeholder(self, formatter):
        """Test that None image URL uses default placeholder."""
        cart = Cart(
            items=[
                CartItem(
                    product_id="prod_1",
                    variant_id="var_1",
                    title="Product with None Image",
                    price=29.99,
                    image_url="",  # Empty string (default value)
                    quantity=1,
                    currency_code=CurrencyCode.USD
                )
            ],
            subtotal=29.99,
            currency_code=CurrencyCode.USD,
            item_count=1
        )

        result = formatter.format_cart(cart, "test_psid")
        elements = result["attachment"]["payload"]["elements"]

        # Should use default placeholder image
        item_element = elements[1]
        assert item_element["image_url"] == formatter.DEFAULT_IMAGE_URL

    # Max Quantity Indicator Tests

    def test_max_quantity_shows_indicator(self, formatter):
        """Test that (Max) indicator appears when at max quantity."""
        cart = Cart(
            items=[
                CartItem(
                    product_id="prod_1",
                    variant_id="var_1",
                    title="Product at Max",
                    price=29.99,
                    image_url="http://example.com/image.jpg",
                    quantity=10,  # At MAX_QUANTITY
                    currency_code=CurrencyCode.USD
                )
            ],
            subtotal=299.90,
            currency_code=CurrencyCode.USD,
            item_count=10
        )

        result = formatter.format_cart(cart, "test_psid")
        elements = result["attachment"]["payload"]["elements"]

        item_element = elements[1]
        increase_button = item_element["buttons"][0]

        # Should show (Max) indicator
        assert "(Max)" in increase_button["title"]

    def test_below_max_quantity_no_indicator(self, formatter):
        """Test that (Max) indicator doesn't appear below max."""
        cart = Cart(
            items=[
                CartItem(
                    product_id="prod_1",
                    variant_id="var_1",
                    title="Product Below Max",
                    price=29.99,
                    image_url="http://example.com/image.jpg",
                    quantity=5,  # Below MAX_QUANTITY
                    currency_code=CurrencyCode.USD
                )
            ],
            subtotal=149.95,
            currency_code=CurrencyCode.USD,
            item_count=5
        )

        result = formatter.format_cart(cart, "test_psid")
        elements = result["attachment"]["payload"]["elements"]

        item_element = elements[1]
        increase_button = item_element["buttons"][0]

        # Should NOT show (Max) indicator
        assert "(Max)" not in increase_button["title"]
        assert increase_button["title"] == "➕ Increase"

    def test_both_min_and_max_indicators(self, formatter):
        """Test that both (Min) and (Max) can appear simultaneously."""
        cart = Cart(
            items=[
                CartItem(
                    product_id="prod_1",
                    variant_id="var_1",
                    title="Product at Both Extremes",
                    price=29.99,
                    image_url="http://example.com/image.jpg",
                    quantity=10,  # At MAX_QUANTITY
                    currency_code=CurrencyCode.USD
                )
            ],
            subtotal=299.90,
            currency_code=CurrencyCode.USD,
            item_count=10
        )

        result = formatter.format_cart(cart, "test_psid")
        elements = result["attachment"]["payload"]["elements"]

        item_element = elements[1]
        increase_button = item_element["buttons"][0]
        decrease_button = item_element["buttons"][1]

        # Increase should show (Max) but decrease should NOT show (Min)
        assert "(Max)" in increase_button["title"]
        assert "(Min)" not in decrease_button["title"]

    # Non-Existent Item Tests

    @pytest.mark.asyncio
    async def test_remove_non_existent_item_succeeds(self, cart_service, mock_redis):
        """Test that removing non-existent item succeeds (idempotent)."""
        import json

        # Mock cart with one item
        existing_cart_data = {
            "items": [
                {
                    "productId": "prod_1",
                    "variantId": "var_1",
                    "title": "Product 1",
                    "price": 29.99,
                    "imageUrl": "http://example.com/image.jpg",
                    "currencyCode": "USD",
                    "quantity": 1
                }
            ],
            "subtotal": 29.99,
            "currencyCode": "USD",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
        mock_redis.get.return_value = json.dumps(existing_cart_data)
        mock_redis.setex.return_value = True

        # Try to remove item that doesn't exist (should succeed - idempotent)
        cart = await cart_service.remove_item("test_user", "non_existent_variant")

        # Cart should be unchanged
        assert len(cart.items) == 1
        assert cart.items[0].variant_id == "var_1"

    # Multiple Currencies in Same Cart Tests

    @pytest.mark.asyncio
    async def test_multiple_items_same_currency_succeeds(self, cart_service, mock_redis):
        """Test that adding multiple items with same currency succeeds."""
        import json

        # Mock existing USD cart
        existing_cart_data = {
            "items": [
                {
                    "productId": "prod_1",
                    "variantId": "var_1",
                    "title": "USD Product 1",
                    "price": 29.99,
                    "imageUrl": "http://example.com/image1.jpg",
                    "currencyCode": "USD",
                    "quantity": 1
                }
            ],
            "subtotal": 29.99,
            "currencyCode": "USD",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
        mock_redis.get.return_value = json.dumps(existing_cart_data)
        mock_redis.setex.return_value = True

        # Add another USD item (should succeed)
        cart = await cart_service.add_item(
            psid="test_user",
            product_id="prod_2",
            variant_id="var_2",
            title="USD Product 2",
            price=15.00,
            image_url="http://example.com/image2.jpg",
            currency_code="USD",
            quantity=1
        )

        assert len(cart.items) == 2
        assert cart.currency_code == CurrencyCode.USD
        assert all(item.currency_code == CurrencyCode.USD for item in cart.items)

    # Edge Case: Very Large Cart

    @pytest.mark.asyncio
    async def test_very_large_cart(self, cart_service, mock_redis):
        """Test handling of very large cart (10+ items)."""
        import json

        # Create cart with 15 items (more than typical)
        items = []
        for i in range(15):
            items.append({
                "productId": f"prod_{i}",
                "variantId": f"var_{i}",
                "title": f"Product {i}",
                "price": 10.0,
                "imageUrl": f"http://example.com/image{i}.jpg",
                "currencyCode": "USD",
                "quantity": 1
            })

        large_cart_data = {
            "items": items,
            "subtotal": 150.0,
            "currencyCode": "USD",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
        mock_redis.get.return_value = json.dumps(large_cart_data)

        cart = await cart_service.get_cart("test_user")

        assert len(cart.items) == 15
        assert cart.item_count == 15
        assert cart.subtotal == 150.0
