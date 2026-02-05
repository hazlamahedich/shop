"""Integration tests for Add to Cart flow.

Tests button tap → cart → confirmation flow with proper
integration between webhooks, message processor, and cart service.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis

from app.api.webhooks.facebook import process_webhook_message, send_messenger_response
from app.schemas.messaging import FacebookWebhookPayload
from app.services.messaging.message_processor import MessageProcessor
from app.services.cart import CartService
from app.schemas.cart import CartItem, CurrencyCode


class TestAddToCartFlow:
    """Test end-to-end add to cart flow."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return MagicMock(spec=redis.Redis)

    @pytest.fixture
    def cart_service(self, mock_redis):
        """Create cart service with mock Redis."""
        return CartService(redis_client=mock_redis)

    @pytest.fixture
    def sample_product_search_context(self):
        """Sample product search results in context."""
        return {
            "last_search_results": {
                "products": [
                    {
                        "id": "prod_123",
                        "title": "Running Shoes",
                        "handle": "running-shoes",
                        "price": 89.99,
                        "images": [{"url": "https://example.com/shoes.jpg"}],
                        "variants": [
                            {
                                "id": "var_456",
                                "price": 89.99,
                                "currency_code": "USD",
                                "available_for_sale": True,
                                "selected_options": {"Size": "10", "Color": "Red"}
                            }
                        ]
                    }
                ],
                "total_count": 1
            }
        }

    @pytest.mark.asyncio
    async def test_add_to_cart_button_postback(
        self, cart_service, mock_redis, sample_product_search_context
    ):
        """Test add to cart via button postback."""
        # Setup mock Redis
        mock_redis.get.return_value = None  # No existing cart
        mock_redis.setex.return_value = True

        # Create webhook payload with postback
        payload = FacebookWebhookPayload(**{
            "object": "page",
            "entry": [{
                "id": "123456",
                "time": 1234567890,
                "messaging": [{
                    "sender": {"id": "test_psid_123"},
                    "postback": {
                        "payload": "ADD_TO_CART:prod_123:var_456"
                    }
                }]
            }]
        })

        # Mock context manager to return product search results
        with patch(
            "app.services.messaging.message_processor.ConversationContextManager"
        ) as mock_context_mgr:
            mock_instance = mock_context_mgr.return_value
            mock_instance.get_context = AsyncMock(return_value=sample_product_search_context)
            # Mock Redis client on context manager
            mock_instance.redis = mock_redis

            processor = MessageProcessor()
            response = await processor.process_postback(payload)

        # Verify response
        assert response.recipient_id == "test_psid_123"
        assert "Added" in response.text
        assert "Running Shoes" in response.text
        assert "89.99" in response.text

    @pytest.mark.asyncio
    async def test_add_to_cart_duplicate_increments_quantity(
        self, cart_service, mock_redis, sample_product_search_context
    ):
        """Test adding duplicate item increments quantity."""
        # Existing cart with one item
        existing_cart = {
            "items": [{
                "productId": "prod_123",
                "variantId": "var_456",
                "title": "Running Shoes",
                "price": 89.99,
                "imageUrl": "https://example.com/shoes.jpg",
                "currencyCode": "USD",
                "quantity": 1,
                "addedAt": "2024-01-15T10:00:00Z"
            }],
            "subtotal": 89.99,
            "currencyCode": "USD",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }

        mock_redis.get.return_value = json.dumps(existing_cart)
        mock_redis.setex.return_value = True

        # Create webhook payload with postback
        payload = FacebookWebhookPayload(**{
            "object": "page",
            "entry": [{
                "id": "123456",
                "time": 1234567890,
                "messaging": [{
                    "sender": {"id": "test_psid_123"},
                    "postback": {
                        "payload": "ADD_TO_CART:prod_123:var_456"
                    }
                }]
            }]
        })

        # Mock context manager to return product search results
        with patch(
            "app.services.messaging.message_processor.ConversationContextManager"
        ) as mock_context_mgr:
            mock_instance = mock_context_mgr.return_value
            mock_instance.get_context = AsyncMock(return_value=sample_product_search_context)
            # Mock Redis client on context manager
            mock_instance.redis = mock_redis

            processor = MessageProcessor()
            response = await processor.process_postback(payload)

        # Verify response indicates addition
        assert "Added" in response.text
        assert "Running Shoes" in response.text

    @pytest.mark.asyncio
    async def test_add_to_cart_out_of_stock(
        self, mock_redis, sample_product_search_context
    ):
        """Test add to cart fails for out of stock items."""
        # Modify product to be out of stock
        out_of_stock_context = {
            "last_search_results": {
                "products": [
                    {
                        "id": "prod_123",
                        "title": "Running Shoes",
                        "price": 89.99,
                        "images": [{"url": "https://example.com/shoes.jpg"}],
                        "variants": [
                            {
                                "id": "var_456",
                                "price": 89.99,
                                "currency_code": "USD",
                                "available_for_sale": False,  # Out of stock
                                "selected_options": {"Size": "10", "Color": "Red"}
                            }
                        ]
                    }
                ]
            }
        }

        # Create webhook payload
        payload = FacebookWebhookPayload(**{
            "object": "page",
            "entry": [{
                "id": "123456",
                "time": 1234567890,
                "messaging": [{
                    "sender": {"id": "test_psid_123"},
                    "postback": {
                        "payload": "ADD_TO_CART:prod_123:var_456"
                    }
                }]
            }]
        })

        # Mock context manager
        with patch(
            "app.services.messaging.message_processor.ConversationContextManager"
        ) as mock_context_mgr:
            mock_instance = mock_context_mgr.return_value
            mock_instance.get_context = AsyncMock(return_value=out_of_stock_context)

            processor = MessageProcessor()
            response = await processor.process_postback(payload)

        # Verify out of stock message
        assert "out of stock" in response.text.lower()

    @pytest.mark.asyncio
    async def test_add_to_cart_invalid_postback_format(self):
        """Test invalid postback format is handled gracefully."""
        # Create webhook payload with invalid postback
        payload = FacebookWebhookPayload(**{
            "object": "page",
            "entry": [{
                "id": "123456",
                "time": 1234567890,
                "messaging": [{
                    "sender": {"id": "test_psid_123"},
                    "postback": {
                        "payload": "INVALID_FORMAT"
                    }
                }]
            }]
        })

        processor = MessageProcessor()
        response = await processor.process_postback(payload)

        # Verify error message
        assert "didn't understand" in response.text

    @pytest.mark.asyncio
    async def test_add_to_cart_product_not_found(
        self, mock_redis, sample_product_search_context
    ):
        """Test add to cart when product is not in context."""
        # Create webhook payload with non-existent product
        payload = FacebookWebhookPayload(**{
            "object": "page",
            "entry": [{
                "id": "123456",
                "time": 1234567890,
                "messaging": [{
                    "sender": {"id": "test_psid_123"},
                    "postback": {
                        "payload": "ADD_TO_CART:prod_999:var_999"
                    }
                }]
            }]
        })

        # Mock context manager
        with patch(
            "app.services.messaging.message_processor.ConversationContextManager"
        ) as mock_context_mgr:
            mock_instance = mock_context_mgr.return_value
            mock_instance.get_context = AsyncMock(return_value=sample_product_search_context)

            processor = MessageProcessor()
            response = await processor.process_postback(payload)

        # Verify not found message
        assert "couldn't find" in response.text

    @pytest.mark.asyncio
    async def test_cart_persists_across_operations(
        self, cart_service, mock_redis
    ):
        """Test cart data persists correctly across operations."""
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        # Add item
        cart = await cart_service.add_item(
            psid="test_psid",
            product_id="prod_1",
            variant_id="var_1",
            title="Test Product",
            price=29.99,
            image_url="https://example.com/image.jpg",
            quantity=2
        )

        assert cart.items[0].quantity == 2
        assert cart.subtotal == 59.98

        # Verify setex was called
        assert mock_redis.setex.called
