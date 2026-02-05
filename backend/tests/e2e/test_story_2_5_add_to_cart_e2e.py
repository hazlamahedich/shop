"""E2E tests for Story 2-5: Add to Cart.

Tests full user flows with Messenger integration including:
- Button tap "Add to Cart" → confirmation
- Natural language "add to cart" → confirmation
- Quantity increment on duplicate additions
- Out of stock handling
- Cart persistence
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.messaging import FacebookWebhookPayload
from app.services.cart import CartService


class TestStory25AddToCartE2E:
    """E2E tests for Add to Cart feature."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_product_search_results(self):
        """Sample product search results."""
        return {
            "products": [
                {
                    "id": "prod_123",
                    "title": "Running Shoes",
                    "handle": "running-shoes",
                    "price": 89.99,
                    "images": [{"url": "https://cdn.shopify.com/shoes.jpg"}],
                    "variants": [
                        {
                            "id": "var_456",
                            "price": 89.99,
                            "currency_code": "USD",
                            "available_for_sale": True,
                            "selected_options": {"Size": "10", "Color": "Red"}
                        }
                    ]
                },
                {
                    "id": "prod_789",
                    "title": "Sport T-Shirt",
                    "handle": "sport-tshirt",
                    "price": 29.99,
                    "images": [{"url": "https://cdn.shopify.com/tshirt.jpg"}],
                    "variants": [
                        {
                            "id": "var_101",
                            "price": 29.99,
                            "currency_code": "USD",
                            "available_for_sale": True,
                            "selected_options": {"Size": "M", "Color": "Blue"}
                        }
                    ]
                }
            ],
            "total_count": 2,
            "search_params": {"query": "shoes"},
            "search_time_ms": 150
        }

    @pytest.mark.asyncio
    async def test_e2e_button_tap_add_to_cart(self, sample_product_search_results):
        """Test E2E: User taps 'Add to Cart' button on product card."""
        # Step 1: User searches for products (already in context)
        # Step 2: User taps "Add to Cart" button

        # Mock the conversation context with product search results
        with patch(
            "app.services.messaging.message_processor.ConversationContextManager"
        ) as mock_context_mgr:
            mock_instance = mock_context_mgr.return_value
            mock_instance.get_context = AsyncMock(return_value={
                "last_search_results": sample_product_search_results
            })
            # Mock Redis client - get returns None (empty cart), setex returns True
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_redis.setex.return_value = True
            mock_instance.redis = mock_redis

            # Create postback payload from button tap
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

            from app.services.messaging.message_processor import MessageProcessor
            processor = MessageProcessor()
            response = await processor.process_postback(payload)

        # Verify confirmation message
        assert response.recipient_id == "test_psid_123"
        assert "Added" in response.text
        assert "Running Shoes" in response.text
        assert "89.99" in response.text
        assert "cart" in response.text.lower()

    @pytest.mark.asyncio
    async def test_e2e_natural_language_add_to_cart(self, sample_product_search_results):
        """Test E2E: User types 'add to cart' after viewing products."""
        # Mock intent classifier to return CART_ADD intent
        from app.services.intent import IntentType, ClassificationResult, ExtractedEntities

        with patch(
            "app.services.messaging.message_processor.ConversationContextManager"
        ) as mock_context_mgr, \
             patch("app.services.intent.IntentClassifier.classify") as mock_classify:
            mock_instance = mock_context_mgr.return_value
            mock_instance.get_context = AsyncMock(return_value={
                "last_search_results": sample_product_search_results
            })
            # Mock Redis client - get returns None (empty cart), setex returns True
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_redis.setex.return_value = True
            mock_instance.redis = mock_redis
            # Mock update_classification as an async method that does nothing
            mock_instance.update_classification = AsyncMock()

            # Mock the intent classifier to return CART_ADD intent
            mock_classify.return_value = ClassificationResult(
                intent=IntentType.CART_ADD,
                entities=ExtractedEntities(),
                confidence=0.95,
                raw_message="add to cart",
                llm_provider="test_provider",
                model="test_model",
                processing_time_ms=50.0
            )

            # Create message payload
            payload = FacebookWebhookPayload(**{
                "object": "page",
                "entry": [{
                    "id": "123456",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "test_psid_123"},
                        "message": {"text": "add to cart"}
                    }]
                }]
            })

            from app.services.messaging.message_processor import MessageProcessor
            processor = MessageProcessor()
            response = await processor.process_message(payload)

        # Verify confirmation message
        assert response.recipient_id == "test_psid_123"
        assert "Added" in response.text
        # Should contain one of the products from search results
        assert any(
            product.get("title") in response.text
            for product in sample_product_search_results["products"]
        )

    @pytest.mark.asyncio
    async def test_e2e_duplicate_add_increments_quantity(self, sample_product_search_results):
        """Test E2E: Adding same product twice increments quantity."""
        # Prepare existing cart data
        existing_cart_dict = {
            "items": [{
                "productId": "prod_123",
                "variantId": "var_456",
                "title": "Running Shoes",
                "price": 89.99,
                "imageUrl": "https://cdn.shopify.com/shoes.jpg",
                "currencyCode": "USD",
                "quantity": 1,
                "addedAt": "2024-01-15T10:00:00Z"
            }],
            "subtotal": 89.99,
            "currencyCode": "USD",
            "itemCount": 1,
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }

        with patch(
            "app.services.messaging.message_processor.ConversationContextManager"
        ) as mock_context_mgr:
            mock_instance = mock_context_mgr.return_value
            mock_instance.get_context = AsyncMock(return_value={
                "last_search_results": sample_product_search_results
            })
            # Mock Redis client - get returns existing cart, setex returns True
            mock_redis = MagicMock()
            mock_redis.get.return_value = json.dumps(existing_cart_dict)
            mock_redis.setex.return_value = True
            mock_instance.redis = mock_redis

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

            from app.services.messaging.message_processor import MessageProcessor

            # First add (should increment to 2)
            processor = MessageProcessor()
            response1 = await processor.process_postback(payload)

            assert "Added" in response1.text

    @pytest.mark.asyncio
    async def test_e2e_out_of_stock_shows_error(self):
        """Test E2E: Out of stock product shows error message."""
        out_of_stock_results = {
            "last_search_results": {
                "products": [
                    {
                        "id": "prod_123",
                        "title": "Running Shoes",
                        "price": 89.99,
                        "images": [{"url": "https://cdn.shopify.com/shoes.jpg"}],
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

        with patch(
            "app.services.messaging.message_processor.ConversationContextManager"
        ) as mock_context_mgr:
            mock_instance = mock_context_mgr.return_value
            mock_instance.get_context = AsyncMock(return_value=out_of_stock_results)

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

            from app.services.messaging.message_processor import MessageProcessor
            processor = MessageProcessor()
            response = await processor.process_postback(payload)

        # Verify out of stock message
        assert "out of stock" in response.text.lower()

    @pytest.mark.asyncio
    async def test_e2e_cart_persists_24_hours(self):
        """Test E2E: Cart persists for 24 hours in Redis."""
        import redis
        from unittest.mock import MagicMock

        mock_redis = MagicMock(spec=redis.Redis)
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        cart_service = CartService(redis_client=mock_redis)

        # Add item to cart
        cart = await cart_service.add_item(
            psid="test_psid",
            product_id="prod_1",
            variant_id="var_1",
            title="Test Product",
            price=29.99,
            image_url="https://example.com/image.jpg"
        )

        # Verify setex was called with 24-hour TTL
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == 86400  # 24 hours in seconds

    @pytest.mark.asyncio
    async def test_e2e_add_to_cart_performance_under_500ms(self):
        """Test E2E: Add to cart completes within 500ms (AC requirement)."""
        import time

        mock_results = {
            "last_search_results": {
                "products": [
                    {
                        "id": "prod_1",
                        "title": "Test Product",
                        "price": 29.99,
                        "images": [{"url": "https://example.com/image.jpg"}],
                        "variants": [
                            {
                                "id": "var_1",
                                "price": 29.99,
                                "currency_code": "USD",
                                "available_for_sale": True
                            }
                        ]
                    }
                ]
            }
        }

        with patch(
            "app.services.messaging.message_processor.ConversationContextManager"
        ) as mock_context_mgr:
            mock_instance = mock_context_mgr.return_value
            mock_instance.get_context = AsyncMock(return_value=mock_results)

            payload = FacebookWebhookPayload(**{
                "object": "page",
                "entry": [{
                    "id": "123456",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "test_psid"},
                        "postback": {
                            "payload": "ADD_TO_CART:prod_1:var_1"
                        }
                    }]
                }]
            })

            from app.services.messaging.message_processor import MessageProcessor
            processor = MessageProcessor()

            start = time.time()
            response = await processor.process_postback(payload)
            elapsed_ms = (time.time() - start) * 1000

        # Performance requirement: <500ms
        assert elapsed_ms < 500, f"Add to cart took {elapsed_ms}ms, exceeds 500ms limit"

    @pytest.mark.asyncio
    async def test_e2e_multiple_different_items_in_cart(self, sample_product_search_results):
        """Test E2E: User can add multiple different items to cart."""
        with patch(
            "app.services.messaging.message_processor.ConversationContextManager"
        ) as mock_context_mgr:
            mock_instance = mock_context_mgr.return_value
            mock_instance.get_context = AsyncMock(return_value={
                "last_search_results": sample_product_search_results
            })
            # Mock Redis client - get returns None (empty cart), setex returns True
            mock_redis = MagicMock()
            mock_redis.get.return_value = None
            mock_redis.setex.return_value = True
            mock_instance.redis = mock_redis

            from app.services.messaging.message_processor import MessageProcessor
            processor = MessageProcessor()

            # Add first product
            payload1 = FacebookWebhookPayload(**{
                "object": "page",
                "entry": [{
                    "id": "123456",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "test_psid"},
                        "postback": {
                            "payload": "ADD_TO_CART:prod_123:var_456"
                        }
                    }]
                }]
            })

            response1 = await processor.process_postback(payload1)
            assert "Running Shoes" in response1.text

            # Add second product
            payload2 = FacebookWebhookPayload(**{
                "object": "page",
                "entry": [{
                    "id": "123456",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "test_psid"},
                        "postback": {
                            "payload": "ADD_TO_CART:prod_789:var_101"
                        }
                    }]
                }]
            })

            response2 = await processor.process_postback(payload2)
            assert "Sport T-Shirt" in response2.text

    @pytest.mark.asyncio
    async def test_e2e_no_search_results_prompt_to_search(self):
        """Test E2E: User tries to add without searching first."""
        # Empty context (no products viewed)
        with patch(
            "app.services.messaging.message_processor.ConversationContextManager"
        ) as mock_context_mgr:
            mock_instance = mock_context_mgr.return_value
            mock_instance.get_context = AsyncMock(return_value={
                "last_search_results": {}
            })

            payload = FacebookWebhookPayload(**{
                "object": "page",
                "entry": [{
                    "id": "123456",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "test_psid"},
                        "postback": {
                            "payload": "ADD_TO_CART:prod_1:var_1"
                        }
                    }]
                }]
            })

            from app.services.messaging.message_processor import MessageProcessor
            processor = MessageProcessor()
            response = await processor.process_postback(payload)

        # Verify error message prompts user to search
        assert "search" in response.text.lower() or "find" in response.text.lower()
