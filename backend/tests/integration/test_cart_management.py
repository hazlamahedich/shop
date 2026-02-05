"""Integration tests for cart management functionality.

Tests the full cart management flow including:
- Viewing cart after adding items
- Removing items from cart
- Adjusting item quantities
- Cart display updates
- Postback handling for remove/quantity actions
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator

import pytest
import redis

from app.schemas.cart import Cart, CartItem, CurrencyCode
from app.services.cart import CartService
from app.services.messenger import CartFormatter
from app.services.messaging.message_processor import MessageProcessor
from app.schemas.messaging import FacebookWebhookPayload


class TestCartManagementIntegration:
    """Integration tests for cart management flow."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return MagicMock(spec=redis.Redis)

    @pytest.fixture
    def cart_service(self, mock_redis):
        """Create cart service for testing."""
        return CartService(redis_client=mock_redis)

    @pytest.fixture
    def message_processor(self):
        """Create message processor for testing."""
        return MessageProcessor()

    @pytest.fixture
    def sample_cart_items(self):
        """Create sample cart items for testing."""
        return [
            CartItem(
                product_id="prod_1",
                variant_id="var_1",
                title="Test Product 1",
                price=29.99,
                image_url="http://example.com/image1.jpg",
                quantity=2,
                currency_code=CurrencyCode.USD,
                added_at=datetime.now(timezone.utc).isoformat()
            ),
            CartItem(
                product_id="prod_2",
                variant_id="var_2",
                title="Test Product 2",
                price=49.99,
                image_url="http://example.com/image2.jpg",
                quantity=1,
                currency_code=CurrencyCode.USD,
                added_at=datetime.now(timezone.utc).isoformat()
            )
        ]

    @pytest.mark.asyncio
    async def test_view_cart_after_adding_items(self, cart_service, sample_cart_items, mock_redis):
        """Test viewing cart after adding items via CartService."""
        psid = "test_user_123"
        import json

        # Mock get to return None initially (empty cart)
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        # Add items to cart (simplified for mock test)
        for item in sample_cart_items:
            cart = await cart_service.add_item(
                psid=psid,
                product_id=item.product_id,
                variant_id=item.variant_id,
                title=item.title,
                price=item.price,
                image_url=item.image_url,
                currency_code=item.currency_code.value,
                quantity=item.quantity
            )

        # Format cart for display
        formatter = CartFormatter(shop_domain="example.myshopify.com")

        # Create a test cart to format
        test_cart = Cart(
            items=sample_cart_items,
            subtotal=109.97,
            currency_code=CurrencyCode.USD,
            item_count=3
        )

        message_payload = formatter.format_cart(test_cart, psid)

        # Verify message structure
        assert "attachment" in message_payload
        elements = message_payload["attachment"]["payload"]["elements"]
        assert len(elements) == 4  # summary + 2 items + checkout

    @pytest.mark.asyncio
    async def test_remove_item_updates_cart_display(self, cart_service, mock_redis):
        """Test removing item updates cart display correctly."""
        import json
        psid = "test_user_456"

        # Mock existing cart with two items
        existing_cart_data = {
            "items": [
                {
                    "productId": "prod_1",
                    "variantId": "var_1",
                    "title": "Product to Remove",
                    "price": 29.99,
                    "imageUrl": "http://example.com/image.jpg",
                    "currencyCode": "USD",
                    "quantity": 2
                },
                {
                    "productId": "prod_2",
                    "variantId": "var_2",
                    "title": "Product to Keep",
                    "price": 49.99,
                    "imageUrl": "http://example.com/image2.jpg",
                    "currencyCode": "USD",
                    "quantity": 1
                }
            ],
            "subtotal": 109.97,
            "currencyCode": "USD",
            "createdAt": "2024-01-15T10:00:00Z",
            "updatedAt": "2024-01-15T10:00:00Z"
        }

        mock_redis.get.return_value = json.dumps(existing_cart_data)
        mock_redis.setex.return_value = True

        # Remove first item
        cart = await cart_service.remove_item(psid, "var_1")

        # Verify removal
        assert cart.item_count == 1
        assert len(cart.items) == 1

    @pytest.mark.asyncio
    async def test_quantity_adjustment_updates_subtotal(self, cart_service, mock_redis):
        """Test quantity adjustment updates subtotal correctly."""
        import json
        psid = "test_user_789"

        # Mock existing cart
        existing_cart_data = {
            "items": [
                {
                    "productId": "prod_1",
                    "variantId": "var_1",
                    "title": "Test Product",
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

        # Increase to 3
        cart = await cart_service.update_quantity(psid, "var_1", 3)
        assert cart.items[0].quantity == 3
        assert cart.subtotal == 89.97  # 29.99 * 3

    @pytest.mark.asyncio
    async def test_remove_item_postback_handling(self, message_processor):
        """Test remove item postback is handled correctly."""
        psid = "test_user_remove"

        # Mock the cart service and send service
        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # Create a mock cart
            mock_cart = Cart(
                items=[
                    CartItem(
                        product_id="prod_1",
                        variant_id="var_1",
                        title="Product to Remove",
                        price=29.99,
                        image_url="http://example.com/image.jpg",
                        quantity=1
                    )
                ],
                subtotal=29.99,
                currency_code=CurrencyCode.USD,
                item_count=1
            )

            with patch('app.services.messaging.message_processor.CartService') as MockCartService:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_cart.return_value = mock_cart
                mock_service_instance.remove_item.return_value = Cart(
                    items=[],
                    subtotal=0.0,
                    currency_code=CurrencyCode.USD,
                    item_count=0
                )
                MockCartService.return_value = mock_service_instance
                MockCartService.MAX_QUANTITY = 10

                with patch('app.services.messaging.message_processor.MessengerSendService') as MockSendService:
                    mock_send_instance = AsyncMock()
                    MockSendService.return_value = mock_send_instance

                    # Create webhook payload properly with all required fields
                    webhook_payload = FacebookWebhookPayload(
                        object="page",
                        entry=[
                            {
                                "id": "PAGE_ID",
                                "time": 1234567890,
                                "messaging": [
                                    {
                                        "sender": {"id": psid},
                                        "recipient": {"id": "PAGE_ID"},
                                        "timestamp": 1234567890,
                                        "postback": {
                                            "payload": "remove_item:var_1",
                                            "title": "Remove"
                                        }
                                    }
                                ]
                            }
                        ]
                    )

                    response = await message_processor.process_postback(webhook_payload)

                    # Verify remove was called
                    mock_service_instance.remove_item.assert_called_once_with(psid, "var_1")

                    # Verify send was called (for updated cart display)
                    mock_send_instance.send_message.assert_called_once()
                    mock_send_instance.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_increase_quantity_postback_handling(self, message_processor):
        """Test increase quantity postback is handled correctly."""
        psid = "test_user_increase"

        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # Create a mock cart
            mock_cart = Cart(
                items=[
                    CartItem(
                        product_id="prod_1",
                        variant_id="var_1",
                        title="Test Product",
                        price=29.99,
                        image_url="http://example.com/image.jpg",
                        quantity=2
                    )
                ],
                subtotal=59.98,
                currency_code=CurrencyCode.USD,
                item_count=2
            )

            with patch('app.services.messaging.message_processor.CartService') as MockCartService:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_cart.return_value = mock_cart
                mock_service_instance.update_quantity.return_value = Cart(
                    items=[
                        CartItem(
                            product_id="prod_1",
                            variant_id="var_1",
                            title="Test Product",
                            price=29.99,
                            image_url="http://example.com/image.jpg",
                            quantity=3
                        )
                    ],
                    subtotal=89.97,
                    currency_code=CurrencyCode.USD,
                    item_count=3
                )
                MockCartService.return_value = mock_service_instance
                MockCartService.MAX_QUANTITY = 10

                with patch('app.services.messaging.message_processor.MessengerSendService') as MockSendService:
                    mock_send_instance = AsyncMock()
                    MockSendService.return_value = mock_send_instance

                    webhook_payload = FacebookWebhookPayload(
                        object="page",
                        entry=[
                            {
                                "id": "PAGE_ID",
                                "time": 1234567890,
                                "messaging": [
                                    {
                                        "sender": {"id": psid},
                                        "recipient": {"id": "PAGE_ID"},
                                        "timestamp": 1234567890,
                                        "postback": {
                                            "payload": "increase_quantity:var_1",
                                            "title": "Increase"
                                        }
                                    }
                                ]
                            }
                        ]
                    )

                    response = await message_processor.process_postback(webhook_payload)

                    # Verify update_quantity was called
                    mock_service_instance.update_quantity.assert_called_once_with(psid, "var_1", 3)

                    # Verify send was called (for updated cart display)
                    mock_send_instance.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_decrease_quantity_postback_handling(self, message_processor):
        """Test decrease quantity postback is handled correctly."""
        psid = "test_user_decrease"

        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # Create a mock cart
            mock_cart = Cart(
                items=[
                    CartItem(
                        product_id="prod_1",
                        variant_id="var_1",
                        title="Test Product",
                        price=29.99,
                        image_url="http://example.com/image.jpg",
                        quantity=3
                    )
                ],
                subtotal=89.97,
                currency_code=CurrencyCode.USD,
                item_count=3
            )

            with patch('app.services.messaging.message_processor.CartService') as MockCartService:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_cart.return_value = mock_cart
                mock_service_instance.update_quantity.return_value = Cart(
                    items=[
                        CartItem(
                            product_id="prod_1",
                            variant_id="var_1",
                            title="Test Product",
                            price=29.99,
                            image_url="http://example.com/image.jpg",
                            quantity=2
                        )
                    ],
                    subtotal=59.98,
                    currency_code=CurrencyCode.USD,
                    item_count=2
                )
                MockCartService.return_value = mock_service_instance
                MockCartService.MAX_QUANTITY = 10

                with patch('app.services.messaging.message_processor.MessengerSendService') as MockSendService:
                    mock_send_instance = AsyncMock()
                    MockSendService.return_value = mock_send_instance

                    webhook_payload = FacebookWebhookPayload(
                        object="page",
                        entry=[
                            {
                                "id": "PAGE_ID",
                                "time": 1234567890,
                                "messaging": [
                                    {
                                        "sender": {"id": psid},
                                        "recipient": {"id": "PAGE_ID"},
                                        "timestamp": 1234567890,
                                        "postback": {
                                            "payload": "decrease_quantity:var_1",
                                            "title": "Decrease"
                                        }
                                    }
                                ]
                            }
                        ]
                    )

                    response = await message_processor.process_postback(webhook_payload)

                    # Verify update_quantity was called
                    mock_service_instance.update_quantity.assert_called_once_with(psid, "var_1", 2)

                    # Verify send was called (for updated cart display)
                    mock_send_instance.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_view_cart_intent_routing(self, message_processor):
        """Test CART_VIEW intent is routed correctly."""
        psid = "test_user_view"

        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # Mock empty cart
            mock_cart = Cart(
                items=[],
                subtotal=0.0,
                currency_code=CurrencyCode.USD,
                item_count=0
            )

            with patch('app.services.messaging.message_processor.CartService') as MockCartService:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_cart.return_value = mock_cart
                MockCartService.return_value = mock_service_instance

                with patch('app.services.messaging.message_processor.MessengerSendService') as MockSendService:
                    mock_send_instance = AsyncMock()
                    MockSendService.return_value = mock_send_instance

                    # Create classification for CART_VIEW intent
                    from app.services.intent import IntentType, ClassificationResult, ExtractedEntities
                    classification = ClassificationResult(
                        intent=IntentType.CART_VIEW,
                        confidence=0.95,
                        entities=ExtractedEntities(),
                        raw_message="cart",
                        reasoning="Cart view request",
                        llm_provider="test",
                        model="test-model",
                        processing_time_ms=50.0
                    )

                    # Route the response
                    response = await message_processor._route_response(psid, classification, {})

                    # Verify get_cart was called
                    mock_service_instance.get_cart.assert_called_once_with(psid)

                    # Verify send was called
                    mock_send_instance.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_quantity_limits_enforced(self, cart_service):
        """Test quantity min/max limits are enforced."""
        from app.core.errors import APIError

        # Try to set below minimum (should fail)
        with pytest.raises(APIError):
            await cart_service.update_quantity("test_user_limits", "var_1", 0)

        # Try to set above maximum (should fail)
        with pytest.raises(APIError):
            await cart_service.update_quantity("test_user_limits", "var_1", 11)

    @pytest.mark.asyncio
    async def test_empty_cart_displays_correctly(self, message_processor):
        """Test empty cart displays friendly message."""
        psid = "test_user_empty"

        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # Mock empty cart
            mock_cart = Cart(
                items=[],
                subtotal=0.0,
                currency_code=CurrencyCode.USD,
                item_count=0
            )

            with patch('app.services.messaging.message_processor.CartService') as MockCartService:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_cart.return_value = mock_cart
                MockCartService.return_value = mock_service_instance

                with patch('app.services.messaging.message_processor.MessengerSendService') as MockSendService:
                    mock_send_instance = AsyncMock()
                    MockSendService.return_value = mock_send_instance

                    # Create classification for CART_VIEW intent
                    from app.services.intent import IntentType, ClassificationResult, ExtractedEntities
                    classification = ClassificationResult(
                        intent=IntentType.CART_VIEW,
                        confidence=0.95,
                        entities=ExtractedEntities(),
                        raw_message="cart",
                        reasoning="Cart view request",
                        llm_provider="test",
                        model="test-model",
                        processing_time_ms=50.0
                    )

                    # Route the response
                    response = await message_processor._route_response(psid, classification, {})

                    # Verify the empty cart message was sent
                    call_args = mock_send_instance.send_message.call_args
                    message_payload = call_args[0][1]

                    # Check that it's the empty cart template
                    template_type = message_payload["attachment"]["payload"]["template_type"]
                    assert template_type == "button"
                    text = message_payload["attachment"]["payload"]["text"]
                    assert "Your cart is empty" in text
