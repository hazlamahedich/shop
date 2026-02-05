"""E2E tests for Story 2.6: View and Manage Cart.

Tests complete cart management flows including:
- User types "cart" to view cart
- User removes item from cart
- User adjusts item quantity
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.cart import Cart, CartItem, CurrencyCode
from app.services.messaging.message_processor import MessageProcessor
from app.schemas.messaging import FacebookWebhookPayload
from app.services.intent import IntentType, ClassificationResult, ExtractedEntities


class TestStory26CartManagementE2E:
    """E2E tests for Story 2.6 cart management."""

    @pytest.fixture
    def message_processor(self):
        """Create message processor for testing."""
        return MessageProcessor()

    @pytest.mark.asyncio
    async def test_user_types_cart_to_view_cart(self, message_processor):
        """E2E: User types 'cart' to view cart contents.

        Given: User has items in cart
        When: User types "cart"
        Then: Bot displays cart summary with items and total
        """
        psid = "test_user_e2e_1"

        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # Mock cart with multiple items
            mock_cart = Cart(
                items=[
                    CartItem(
                        product_id="prod_1",
                        variant_id="var_1",
                        title="Running Shoes",
                        price=89.99,
                        image_url="http://example.com/shoes.jpg",
                        quantity=2,
                        currency_code=CurrencyCode.USD
                    ),
                    CartItem(
                        product_id="prod_2",
                        variant_id="var_2",
                        title="Sport Socks",
                        price=12.99,
                        image_url="http://example.com/socks.jpg",
                        quantity=3,
                        currency_code=CurrencyCode.USD
                    )
                ],
                subtotal=218.95,  # (89.99 * 2) + (12.99 * 3)
                currency_code=CurrencyCode.USD,
                item_count=5
            )

            with patch('app.services.messaging.message_processor.CartService') as MockCartService:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_cart.return_value = mock_cart
                MockCartService.return_value = mock_service_instance

                with patch('app.services.messaging.message_processor.MessengerSendService') as MockSendService:
                    mock_send_instance = AsyncMock()
                    MockSendService.return_value = mock_send_instance

                    # User types "cart"
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

                    response = await message_processor._route_response(psid, classification, {})

                    # Verify cart was retrieved
                    mock_service_instance.get_cart.assert_called_once_with(psid)

                    # Verify cart display was sent
                    mock_send_instance.send_message.assert_called_once()
                    call_args = mock_send_instance.send_message.call_args
                    message_payload = call_args[0][1]

                    # Verify cart display structure
                    assert "attachment" in message_payload
                    elements = message_payload["attachment"]["payload"]["elements"]
                    # Should have: summary + 2 items + checkout reminder = 4 elements
                    assert len(elements) == 4

                    # Verify cart summary
                    assert "Your Cart" in elements[0]["title"]
                    assert "5 items" in elements[0]["title"]
                    assert "$218.95" in elements[0]["subtitle"]

    @pytest.mark.asyncio
    async def test_user_removes_item_from_cart(self, message_processor):
        """E2E: User removes item from cart via Remove button.

        Given: User has items in cart
        When: User taps "Remove" button on an item
        Then: Item is removed and cart is updated
        """
        psid = "test_user_e2e_2"

        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # Mock cart with item to remove
            mock_cart = Cart(
                items=[
                    CartItem(
                        product_id="prod_1",
                        variant_id="var_1",
                        title="Item to Remove",
                        price=29.99,
                        image_url="http://example.com/item.jpg",
                        quantity=1
                    ),
                    CartItem(
                        product_id="prod_2",
                        variant_id="var_2",
                        title="Item to Keep",
                        price=49.99,
                        image_url="http://example.com/item2.jpg",
                        quantity=1
                    )
                ],
                subtotal=79.98,
                currency_code=CurrencyCode.USD,
                item_count=2
            )

            # Mock updated cart after removal
            mock_cart_after_removal = Cart(
                items=[
                    CartItem(
                        product_id="prod_2",
                        variant_id="var_2",
                        title="Item to Keep",
                        price=49.99,
                        image_url="http://example.com/item2.jpg",
                        quantity=1
                    )
                ],
                subtotal=49.99,
                currency_code=CurrencyCode.USD,
                item_count=1
            )

            with patch('app.services.messaging.message_processor.CartService') as MockCartService:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_cart.return_value = mock_cart
                mock_service_instance.remove_item.return_value = mock_cart_after_removal
                MockCartService.return_value = mock_service_instance
                MockCartService.MAX_QUANTITY = 10

                with patch('app.services.messaging.message_processor.MessengerSendService') as MockSendService:
                    mock_send_instance = AsyncMock()
                    MockSendService.return_value = mock_send_instance

                    # User taps Remove button
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

                    # Verify item was removed
                    mock_service_instance.remove_item.assert_called_once_with(psid, "var_1")

                    # Verify updated cart was sent
                    mock_send_instance.send_message.assert_called_once()

                    # Verify confirmation message
                    assert "Removed" in response.text
                    assert "Item to Remove" in response.text

    @pytest.mark.asyncio
    async def test_user_adjusts_item_quantity(self, message_processor):
        """E2E: User adjusts item quantity via +/- buttons.

        Given: User has item in cart
        When: User taps + or - button
        Then: Quantity is adjusted and subtotal is updated
        """
        psid = "test_user_e2e_3"

        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # Mock cart with item at quantity 2
            mock_cart = Cart(
                items=[
                    CartItem(
                        product_id="prod_1",
                        variant_id="var_1",
                        title="Test Product",
                        price=25.00,
                        image_url="http://example.com/product.jpg",
                        quantity=2
                    )
                ],
                subtotal=50.00,
                currency_code=CurrencyCode.USD,
                item_count=2
            )

            # Mock cart after increasing quantity
            mock_cart_increased = Cart(
                items=[
                    CartItem(
                        product_id="prod_1",
                        variant_id="var_1",
                        title="Test Product",
                        price=25.00,
                        image_url="http://example.com/product.jpg",
                        quantity=3
                    )
                ],
                subtotal=75.00,
                currency_code=CurrencyCode.USD,
                item_count=3
            )

            with patch('app.services.messaging.message_processor.CartService') as MockCartService:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_cart.return_value = mock_cart
                mock_service_instance.update_quantity.return_value = mock_cart_increased
                MockCartService.return_value = mock_service_instance
                MockCartService.MAX_QUANTITY = 10

                with patch('app.services.messaging.message_processor.MessengerSendService') as MockSendService:
                    mock_send_instance = AsyncMock()
                    MockSendService.return_value = mock_send_instance

                    # User taps + button
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

                    # Verify quantity was updated
                    mock_service_instance.update_quantity.assert_called_once_with(psid, "var_1", 3)

                    # Verify updated cart was sent
                    mock_send_instance.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_quantity_limits_prevented(self, message_processor):
        """E2E: Quantity limits are enforced (1-10).

        Given: User has item in cart
        When: User tries to adjust beyond limits
        Then: Quantity stays within valid range
        """
        psid = "test_user_e2e_4"

        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # Mock cart with item at minimum quantity (1)
            mock_cart = Cart(
                items=[
                    CartItem(
                        product_id="prod_1",
                        variant_id="var_1",
                        title="Test Product",
                        price=25.00,
                        image_url="http://example.com/product.jpg",
                        quantity=1
                    )
                ],
                subtotal=25.00,
                currency_code=CurrencyCode.USD,
                item_count=1
            )

            # Mock cart at maximum quantity (10)
            mock_cart_max = Cart(
                items=[
                    CartItem(
                        product_id="prod_1",
                        variant_id="var_1",
                        title="Test Product",
                        price=25.00,
                        image_url="http://example.com/product.jpg",
                        quantity=10
                    )
                ],
                subtotal=250.00,
                currency_code=CurrencyCode.USD,
                item_count=10
            )

            with patch('app.services.messaging.message_processor.CartService') as MockCartService:
                from app.core.errors import APIError, ErrorCode

                # Test minimum limit (cannot go below 1)
                mock_service_instance = AsyncMock()
                mock_service_instance.get_cart.return_value = mock_cart
                mock_service_instance.update_quantity.side_effect = APIError(
                    code=ErrorCode.INVALID_QUANTITY,
                    message="Quantity must be between 1 and 10"
                )
                MockCartService.return_value = mock_service_instance
                MockCartService.MAX_QUANTITY = 10

                # Try to decrease below minimum
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

                # Verify update was attempted but hit limit
                mock_service_instance.update_quantity.assert_called_once()

                # Should return error message
                assert "error" in response.text.lower() or "try again" in response.text.lower()

    @pytest.mark.asyncio
    async def test_empty_cart_shows_browse_options(self, message_processor):
        """E2E: Empty cart shows browse/search options.

        Given: User has empty cart
        When: User types "cart" or taps "View Cart"
        Then: Bot shows friendly message with browse/search options
        """
        psid = "test_user_e2e_5"

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

                    # User views cart
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

                    response = await message_processor._route_response(psid, classification, {})

                    # Verify cart was retrieved
                    mock_service_instance.get_cart.assert_called_once_with(psid)

                    # Verify empty cart message was sent
                    mock_send_instance.send_message.assert_called_once()
                    call_args = mock_send_instance.send_message.call_args
                    message_payload = call_args[0][1]

                    # Verify empty cart template
                    template_type = message_payload["attachment"]["payload"]["template_type"]
                    assert template_type == "button"
                    text = message_payload["attachment"]["payload"]["text"]
                    assert "Your cart is empty" in text
                    assert "Let's find some products" in text

                    # Verify browse/search buttons
                    buttons = message_payload["attachment"]["payload"]["buttons"]
                    button_payloads = [b["payload"] for b in buttons]
                    assert "browse_products" in button_payloads
                    assert "search_products" in button_payloads

    @pytest.mark.asyncio
    async def test_cart_displays_checkout_and_continue_shopping(self, message_processor):
        """E2E: Cart displays Checkout and Continue Shopping buttons.

        Given: User has items in cart
        When: User views cart
        Then: Cart shows Checkout and Continue Shopping buttons
        """
        psid = "test_user_e2e_6"

        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # Mock cart with items
            mock_cart = Cart(
                items=[
                    CartItem(
                        product_id="prod_1",
                        variant_id="var_1",
                        title="Test Product",
                        price=29.99,
                        image_url="http://example.com/product.jpg",
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
                MockCartService.return_value = mock_service_instance

                with patch('app.services.messaging.message_processor.MessengerSendService') as MockSendService:
                    mock_send_instance = AsyncMock()
                    MockSendService.return_value = mock_send_instance

                    # User views cart
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

                    response = await message_processor._route_response(psid, classification, {})

                    # Verify cart was sent
                    mock_send_instance.send_message.assert_called_once()
                    call_args = mock_send_instance.send_message.call_args
                    message_payload = call_args[0][1]

                    # Verify buttons in cart summary
                    elements = message_payload["attachment"]["payload"]["elements"]
                    summary_buttons = elements[0]["buttons"]
                    button_titles = [b["title"] for b in summary_buttons]
                    assert any("Continue Shopping" in title for title in button_titles)
                    assert any("Checkout" in title for title in button_titles)

                    # Verify buttons in checkout reminder
                    checkout_buttons = elements[-1]["buttons"]
                    button_titles = [b["title"] for b in checkout_buttons]
                    assert any("Continue Shopping" in title for title in button_titles)
                    assert any("Checkout" in title for title in button_titles)

    @pytest.mark.asyncio
    async def test_continue_shopping_returns_to_search(self, message_processor):
        """E2E: Continue Shopping button returns to product search.

        Given: User views cart
        When: User taps "Continue Shopping" button
        Then: Bot prompts for product search
        """
        psid = "test_user_e2e_7"

        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # User taps Continue Shopping button
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
                                    "payload": "continue_shopping",
                                    "title": "Continue Shopping"
                                }
                            }
                        ]
                    }
                ]
            )

            response = await message_processor.process_postback(webhook_payload)

            # Verify helpful message for product search
            assert "help you find" in response.text.lower()
            assert "product" in response.text.lower() or "category" in response.text.lower()

    @pytest.mark.asyncio
    async def test_cart_item_shows_all_required_elements(self, message_processor):
        """E2E: Cart item shows image, title, quantity, price, remove button, quantity buttons.

        Given: User has item in cart
        When: User views cart
        Then: Each item shows all required elements
        """
        psid = "test_user_e2e_8"

        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # Mock cart
            mock_cart = Cart(
                items=[
                    CartItem(
                        product_id="prod_1",
                        variant_id="var_1",
                        title="Premium Widget",
                        price=99.99,
                        image_url="http://example.com/widget.jpg",
                        quantity=2
                    )
                ],
                subtotal=199.98,
                currency_code=CurrencyCode.USD,
                item_count=2
            )

            with patch('app.services.messaging.message_processor.CartService') as MockCartService:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_cart.return_value = mock_cart
                MockCartService.return_value = mock_service_instance

                with patch('app.services.messaging.message_processor.MessengerSendService') as MockSendService:
                    mock_send_instance = AsyncMock()
                    MockSendService.return_value = mock_send_instance

                    # User views cart
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

                    response = await message_processor._route_response(psid, classification, {})

                    # Verify cart was sent
                    mock_send_instance.send_message.assert_called_once()
                    call_args = mock_send_instance.send_message.call_args
                    message_payload = call_args[0][1]

                    # Verify item element structure
                    elements = message_payload["attachment"]["payload"]["elements"]
                    item_element = elements[1]  # First item (after summary)

                    # Verify title
                    assert item_element["title"] == "Premium Widget"

                    # Verify subtitle with quantity and price
                    assert "Qty: 2" in item_element["subtitle"]
                    assert "$99.99" in item_element["subtitle"]
                    assert "Total:" in item_element["subtitle"]

                    # Verify image
                    assert item_element["image_url"] == "http://example.com/widget.jpg"

                    # Verify buttons: Increase, Decrease, Remove
                    buttons = item_element["buttons"]
                    assert len(buttons) == 3
                    button_payloads = [b["payload"] for b in buttons]
                    assert "increase_quantity:var_1" in button_payloads
                    assert "decrease_quantity:var_1" in button_payloads
                    assert "remove_item:var_1" in button_payloads

    @pytest.mark.asyncio
    async def test_multiple_cart_items_display_correctly(self, message_processor):
        """E2E: Multiple cart items display correctly with individual controls.

        Given: User has multiple items in cart
        When: User views cart
        Then: Each item has its own remove/quantity buttons
        """
        psid = "test_user_e2e_9"

        with patch.object(message_processor.context_manager, 'get_context') as mock_get_context:
            mock_get_context.return_value = {}

            # Mock cart with 3 items
            mock_cart = Cart(
                items=[
                    CartItem(
                        product_id="prod_1",
                        variant_id="var_1",
                        title="Product A",
                        price=10.00,
                        image_url="http://example.com/a.jpg",
                        quantity=1
                    ),
                    CartItem(
                        product_id="prod_2",
                        variant_id="var_2",
                        title="Product B",
                        price=20.00,
                        image_url="http://example.com/b.jpg",
                        quantity=2
                    ),
                    CartItem(
                        product_id="prod_3",
                        variant_id="var_3",
                        title="Product C",
                        price=30.00,
                        image_url="http://example.com/c.jpg",
                        quantity=1
                    )
                ],
                subtotal=80.00,  # 10 + (20*2) + 30
                currency_code=CurrencyCode.USD,
                item_count=4
            )

            with patch('app.services.messaging.message_processor.CartService') as MockCartService:
                mock_service_instance = AsyncMock()
                mock_service_instance.get_cart.return_value = mock_cart
                MockCartService.return_value = mock_service_instance

                with patch('app.services.messaging.message_processor.MessengerSendService') as MockSendService:
                    mock_send_instance = AsyncMock()
                    MockSendService.return_value = mock_send_instance

                    # User views cart
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

                    response = await message_processor._route_response(psid, classification, {})

                    # Verify cart was sent
                    mock_send_instance.send_message.assert_called_once()
                    call_args = mock_send_instance.send_message.call_args
                    message_payload = call_args[0][1]

                    # Verify all items are displayed
                    elements = message_payload["attachment"]["payload"]["elements"]
                    # Should have: summary + 3 items + checkout reminder = 5 elements
                    assert len(elements) == 5

                    # Verify each item has correct variant_id in button payloads
                    for i, variant_id in enumerate(["var_1", "var_2", "var_3"], 1):
                        item_element = elements[i]
                        buttons = item_element["buttons"]
                        button_payloads = [b["payload"] for b in buttons]
                        # All buttons should reference the correct variant_id
                        assert all(variant_id in payload for payload in button_payloads)
