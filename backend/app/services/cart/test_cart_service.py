"""Tests for CartService.

Tests cart CRUD operations, quantity increment, validation,
TTL, and performance requirements.
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import redis

from app.core.errors import APIError, ErrorCode
from app.schemas.cart import Cart, CartItem, CurrencyCode
from app.services.cart import CartService


class TestCartService:
    """Test CartService CRUD operations."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return MagicMock(spec=redis.Redis)

    @pytest.fixture
    def cart_service(self, mock_redis):
        """Create cart service with mock Redis."""
        return CartService(redis_client=mock_redis)

    def test_get_cart_key(self, cart_service):
        """Test Redis key generation."""
        key = cart_service._get_cart_key("test_psid_123")
        assert key == "cart:test_psid_123"

    @pytest.mark.asyncio
    async def test_get_empty_cart(self, cart_service, mock_redis):
        """Test getting cart when no cart exists."""
        mock_redis.get.return_value = None

        cart = await cart_service.get_cart("test_psid")

        assert cart.items == []
        assert cart.subtotal == 0.0
        assert cart.currency_code == CurrencyCode.USD
        assert cart.is_empty is True

    @pytest.mark.asyncio
    async def test_get_existing_cart(self, cart_service, mock_redis):
        """Test getting existing cart from Redis."""
        cart_data = {
            "items": [
                {
                    "productId": "prod_1",
                    "variantId": "var_1",
                    "title": "Test Product",
                    "price": 29.99,
                    "imageUrl": "https://example.com/image.jpg",
                    "currencyCode": "USD",
                    "quantity": 2,
                    "addedAt": "2024-01-15T10:00:00Z"
                }
            ],
            "subtotal": 59.98,
            "currencyCode": "USD",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:05:00Z"
        }
        mock_redis.get.return_value = json.dumps(cart_data)

        cart = await cart_service.get_cart("test_psid")

        assert len(cart.items) == 1
        assert cart.items[0].title == "Test Product"
        assert cart.items[0].quantity == 2
        assert cart.subtotal == 59.98

    @pytest.mark.asyncio
    async def test_add_item_to_empty_cart(self, cart_service, mock_redis):
        """Test adding item to empty cart."""
        mock_redis.get.return_value = None  # No existing cart
        mock_redis.setex.return_value = True

        cart = await cart_service.add_item(
            psid="test_psid",
            product_id="prod_1",
            variant_id="var_1",
            title="Test Product",
            price=29.99,
            image_url="https://example.com/image.jpg",
            quantity=1
        )

        assert len(cart.items) == 1
        assert cart.items[0].quantity == 1
        assert cart.subtotal == 29.99
        assert cart.updated_at is not None
        assert cart.created_at is not None

        # Verify Redis save was called
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_duplicate_item_increments_quantity(self, cart_service, mock_redis):
        """Test adding duplicate item increments quantity."""
        # First call - empty cart
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        await cart_service.add_item(
            psid="test_psid",
            product_id="prod_1",
            variant_id="var_1",
            title="Test Product",
            price=29.99,
            image_url="https://example.com/image.jpg",
            quantity=1
        )

        # Second call - return existing cart
        existing_cart_data = {
            "items": [
                {
                    "productId": "prod_1",
                    "variantId": "var_1",
                    "title": "Test Product",
                    "price": 29.99,
                    "imageUrl": "https://example.com/image.jpg",
                    "currencyCode": "USD",
                    "quantity": 1,
                    "addedAt": "2024-01-15T10:00:00Z"
                }
            ],
            "subtotal": 29.99,
            "currencyCode": "USD",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
        mock_redis.get.return_value = json.dumps(existing_cart_data)

        cart = await cart_service.add_item(
            psid="test_psid",
            product_id="prod_1",
            variant_id="var_1",
            title="Test Product",
            price=29.99,
            image_url="https://example.com/image.jpg",
            quantity=1
        )

        assert len(cart.items) == 1
        assert cart.items[0].quantity == 2
        assert cart.subtotal == 59.98

    @pytest.mark.asyncio
    async def test_add_item_max_quantity_limit(self, cart_service, mock_redis):
        """Test that quantity caps at MAX_QUANTITY (10)."""
        # Existing cart with quantity 9
        existing_cart_data = {
            "items": [
                {
                    "productId": "prod_1",
                    "variantId": "var_1",
                    "title": "Test Product",
                    "price": 29.99,
                    "imageUrl": "https://example.com/image.jpg",
                    "currencyCode": "USD",
                    "quantity": 9,
                    "addedAt": "2024-01-15T10:00:00Z"
                }
            ],
            "subtotal": 269.91,
            "currencyCode": "USD",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
        mock_redis.get.return_value = json.dumps(existing_cart_data)
        mock_redis.setex.return_value = True

        cart = await cart_service.add_item(
            psid="test_psid",
            product_id="prod_1",
            variant_id="var_1",
            title="Test Product",
            price=29.99,
            image_url="https://example.com/image.jpg",
            quantity=5  # Try to add 5 more
        )

        # Should cap at MAX_QUANTITY (10)
        assert cart.items[0].quantity == 10

    @pytest.mark.asyncio
    async def test_remove_item(self, cart_service, mock_redis):
        """Test removing item from cart."""
        existing_cart_data = {
            "items": [
                {
                    "productId": "prod_1",
                    "variantId": "var_1",
                    "title": "Product 1",
                    "price": 10.0,
                    "imageUrl": "https://example.com/img1.jpg",
                    "currencyCode": "USD",
                    "quantity": 2
                },
                {
                    "productId": "prod_2",
                    "variantId": "var_2",
                    "title": "Product 2",
                    "price": 20.0,
                    "imageUrl": "https://example.com/img2.jpg",
                    "currencyCode": "USD",
                    "quantity": 1
                }
            ],
            "subtotal": 40.0,
            "currencyCode": "USD",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
        mock_redis.get.return_value = json.dumps(existing_cart_data)
        mock_redis.setex.return_value = True

        cart = await cart_service.remove_item("test_psid", "var_1")

        assert len(cart.items) == 1
        assert cart.items[0].variant_id == "var_2"
        assert cart.subtotal == 20.0

    @pytest.mark.asyncio
    async def test_update_quantity(self, cart_service, mock_redis):
        """Test updating item quantity."""
        existing_cart_data = {
            "items": [
                {
                    "productId": "prod_1",
                    "variantId": "var_1",
                    "title": "Test Product",
                    "price": 29.99,
                    "imageUrl": "https://example.com/image.jpg",
                    "currencyCode": "USD",
                    "quantity": 2
                }
            ],
            "subtotal": 59.98,
            "currencyCode": "USD",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
        mock_redis.get.return_value = json.dumps(existing_cart_data)
        mock_redis.setex.return_value = True

        cart = await cart_service.update_quantity("test_psid", "var_1", 5)

        assert cart.items[0].quantity == 5
        assert cart.subtotal == 149.95

    @pytest.mark.asyncio
    async def test_update_quantity_invalid(self, cart_service):
        """Test that invalid quantity raises error."""
        with pytest.raises(APIError) as exc_info:
            await cart_service.update_quantity("test_psid", "var_1", 0)

        assert exc_info.value.code == ErrorCode.INVALID_QUANTITY

        with pytest.raises(APIError) as exc_info:
            await cart_service.update_quantity("test_psid", "var_1", 11)

        assert exc_info.value.code == ErrorCode.INVALID_QUANTITY

    @pytest.mark.asyncio
    async def test_update_quantity_item_not_found(self, cart_service, mock_redis):
        """Test updating quantity of non-existent item."""
        mock_redis.get.return_value = json.dumps({
            "items": [],
            "subtotal": 0.0,
            "currencyCode": "USD"
        })

        with pytest.raises(APIError) as exc_info:
            await cart_service.update_quantity("test_psid", "var_1", 2)

        assert exc_info.value.code == ErrorCode.ITEM_NOT_FOUND

    @pytest.mark.asyncio
    async def test_clear_cart(self, cart_service, mock_redis):
        """Test clearing cart."""
        mock_redis.delete.return_value = 1

        await cart_service.clear_cart("test_psid")

        mock_redis.delete.assert_called_once_with("cart:test_psid")

    @pytest.mark.asyncio
    async def test_cart_retrieval_failed(self, cart_service, mock_redis):
        """Test error handling when cart retrieval fails."""
        mock_redis.get.side_effect = Exception("Redis connection failed")

        with pytest.raises(APIError) as exc_info:
            await cart_service.get_cart("test_psid")

        assert exc_info.value.code == ErrorCode.CART_RETRIEVAL_FAILED

    @pytest.mark.asyncio
    async def test_cart_add_failed(self, cart_service, mock_redis):
        """Test error handling when add operation fails."""
        mock_redis.get.return_value = None
        mock_redis.setex.side_effect = Exception("Redis write failed")

        with pytest.raises(APIError) as exc_info:
            await cart_service.add_item(
                psid="test_psid",
                product_id="prod_1",
                variant_id="var_1",
                title="Test",
                price=10.0,
                image_url="https://example.com/image.jpg"
            )

        assert exc_info.value.code == ErrorCode.CART_ADD_FAILED

    @pytest.mark.asyncio
    async def test_add_to_cart_performance(self, cart_service, mock_redis):
        """Test add-to-cart completes within 500ms."""
        import time

        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        start = time.time()
        await cart_service.add_item(
            psid="test_psid",
            product_id="prod_1",
            variant_id="var_1",
            title="Test Product",
            price=29.99,
            image_url="https://example.com/image.jpg"
        )
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 500, f"Add to cart took {elapsed_ms}ms, must be <500ms"

    @pytest.mark.asyncio
    async def test_multiple_items_subtotal_calculation(self, cart_service, mock_redis):
        """Test subtotal calculation with multiple items."""
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        # Add first item
        await cart_service.add_item(
            psid="test_psid",
            product_id="prod_1",
            variant_id="var_1",
            title="Product 1",
            price=10.0,
            image_url="https://example.com/img1.jpg",
            quantity=2
        )

        # Mock returns the cart we just saved
        saved_cart = {
            "items": [
                {
                    "productId": "prod_1",
                    "variantId": "var_1",
                    "title": "Product 1",
                    "price": 10.0,
                    "imageUrl": "https://example.com/img1.jpg",
                    "currencyCode": "USD",
                    "quantity": 2
                }
            ],
            "subtotal": 20.0,
            "currencyCode": "USD",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }
        mock_redis.get.return_value = json.dumps(saved_cart)

        # Add second item
        cart = await cart_service.add_item(
            psid="test_psid",
            product_id="prod_2",
            variant_id="var_2",
            title="Product 2",
            price=15.0,
            image_url="https://example.com/img2.jpg",
            quantity=3
        )

        assert len(cart.items) == 2
        assert cart.subtotal == 65.0  # (10 * 2) + (15 * 3)

    @pytest.mark.asyncio
    async def test_cart_ttl_set_on_save(self, cart_service, mock_redis):
        """Test that cart is saved with correct TTL."""
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        await cart_service.add_item(
            psid="test_psid",
            product_id="prod_1",
            variant_id="var_1",
            title="Test Product",
            price=29.99,
            image_url="https://example.com/image.jpg"
        )

        # Verify setex was called with correct TTL (24 hours)
        # The call_args are (key, ttl, value)
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == CartService.CART_TTL_SECONDS
