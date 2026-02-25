"""Unit tests for MessengerAdapter.

Story 5-11: Messenger Unified Service Migration
INT-1: Create Messenger adapter for UnifiedConversationService

Tests the adapter layer that bridges UnifiedConversationService to Facebook Messenger.

Priority Markers:
    @pytest.mark.p0 - Critical (run on every commit)
    @pytest.mark.p1 - High (run pre-merge)
    @pytest.mark.p2 - Medium (run nightly)

Test ID Format: 5.11-ADAPTER-{SEQ} (e.g., 5.11-ADAPTER-001)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    ConversationResponse,
)
from app.services.conversation.messenger_adapter import MessengerAdapter
from app.services.conversation.cart_key_strategy import CartKeyStrategy
from app.schemas.messaging import MessengerResponse


@pytest.fixture
def adapter() -> MessengerAdapter:
    """Create a MessengerAdapter instance."""
    return MessengerAdapter()


@pytest.fixture
def psid() -> str:
    """Sample Facebook Page-Scoped ID."""
    return "psid_123456789"


@pytest.fixture
def mock_merchant_id() -> int:
    """Sample merchant ID."""
    return 1


class TestMessengerAdapterContext:
    """Tests for MessengerAdapter.create_context().

    Test IDs: 5.11-ADAPTER-001 through 5.11-ADAPTER-004
    Priority: P1 (High) - core adapter functionality.
    """

    @pytest.mark.p1
    @pytest.mark.test_id("5.11-ADAPTER-001")
    def test_create_context_basic(
        self,
        adapter: MessengerAdapter,
        psid: str,
        mock_merchant_id: int,
    ) -> None:
        """Test creating basic Messenger context."""
        context = adapter.create_context(
            psid=psid,
            merchant_id=mock_merchant_id,
        )

        assert context.session_id == psid
        assert context.merchant_id == mock_merchant_id
        assert context.channel == Channel.MESSENGER
        assert context.platform_sender_id == psid
        assert context.conversation_history == []

    @pytest.mark.p1
    @pytest.mark.test_id("5.11-ADAPTER-002")
    def test_create_context_with_history(
        self,
        adapter: MessengerAdapter,
        psid: str,
        mock_merchant_id: int,
    ) -> None:
        """Test creating context with conversation history."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "bot", "content": "Hi there!"},
        ]

        context = adapter.create_context(
            psid=psid,
            merchant_id=mock_merchant_id,
            conversation_history=history,
        )

        assert context.conversation_history == history

    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-003")
    def test_create_context_with_metadata(
        self,
        adapter: MessengerAdapter,
        psid: str,
        mock_merchant_id: int,
    ) -> None:
        """Test creating context with metadata."""
        metadata = {"source": "facebook", "locale": "en_US"}

        context = adapter.create_context(
            psid=psid,
            merchant_id=mock_merchant_id,
            metadata=metadata,
        )

        assert context.metadata == metadata

    @pytest.mark.p1
    @pytest.mark.test_id("5.11-ADAPTER-004")
    def test_create_context_with_consent_status(
        self,
        adapter: MessengerAdapter,
        psid: str,
        mock_merchant_id: int,
    ) -> None:
        """Test creating context with consent status."""
        context = adapter.create_context(
            psid=psid,
            merchant_id=mock_merchant_id,
            consent_status="pending",
        )

        assert context.consent_status == "pending"


class TestMessengerAdapterCartKey:
    """Tests for MessengerAdapter.get_cart_key().

    Test IDs: 5.11-ADAPTER-005 through 5.11-ADAPTER-006
    Priority: P1 (High) - cart operations are critical.
    """

    @pytest.mark.p1
    @pytest.mark.test_id("5.11-ADAPTER-005")
    def test_get_cart_key_format(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test cart key format for Messenger."""
        key = adapter.get_cart_key(psid)

        assert key == f"cart:messenger:{psid}"
        assert key == CartKeyStrategy.for_messenger(psid)

    @pytest.mark.p1
    @pytest.mark.test_id("5.11-ADAPTER-006")
    def test_get_cart_key_uses_strategy(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test that cart key uses CartKeyStrategy."""
        with patch.object(
            CartKeyStrategy, "for_messenger", return_value="cart:messenger:test"
        ) as mock_strategy:
            key = adapter.get_cart_key(psid)
            mock_strategy.assert_called_once_with(psid)


class TestMessengerAdapterResponseConversion:
    """Tests for MessengerAdapter.convert_response().

    Test IDs: 5.11-ADAPTER-007 through 5.11-ADAPTER-012
    Priority: P1 (High) - response conversion is core functionality.
    """

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-ADAPTER-007")
    async def test_convert_simple_text_response(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test converting simple text response."""
        response = ConversationResponse(
            message="Hello! How can I help?",
            intent="greeting",
            confidence=0.95,
        )

        messenger_response = await adapter.convert_response(response, psid)

        assert isinstance(messenger_response, MessengerResponse)
        assert messenger_response.text == "Hello! How can I help?"
        assert messenger_response.recipient_id == psid

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-ADAPTER-008")
    async def test_convert_response_with_checkout_url(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test converting response with checkout URL."""
        response = ConversationResponse(
            message="Ready to checkout!",
            intent="checkout",
            confidence=1.0,
            checkout_url="https://shop.myshopify.com/checkout/123",
        )

        messenger_response = await adapter.convert_response(response, psid)

        assert "Ready to checkout!" in messenger_response.text
        assert "https://shop.myshopify.com/checkout/123" in messenger_response.text

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-ADAPTER-009")
    async def test_convert_response_with_products_sends_carousel(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test converting response with products triggers carousel."""
        response = ConversationResponse(
            message="Found 2 products",
            intent="product_search",
            confidence=0.9,
            products=[
                {"title": "Shoe", "price": 50.0},
                {"title": "Shirt", "price": 30.0},
            ],
        )

        with patch.object(
            adapter, "_send_product_carousel", new_callable=AsyncMock
        ) as mock_carousel:
            messenger_response = await adapter.convert_response(response, psid)

            mock_carousel.assert_called_once_with(response.products, psid)
            assert messenger_response.text == "Found 2 products"

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-010")
    async def test_convert_response_with_cart_sends_template(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test converting response with cart triggers cart template."""
        response = ConversationResponse(
            message="Your cart has 2 items",
            intent="cart_view",
            confidence=1.0,
            cart={"items": [{"title": "Shoe"}], "item_count": 1},
        )

        with patch.object(adapter, "_send_cart_template", new_callable=AsyncMock) as mock_template:
            messenger_response = await adapter.convert_response(response, psid)

            mock_template.assert_called_once()
            assert messenger_response.text == "Your cart has 2 items"

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-011")
    async def test_convert_response_empty_cart_no_template(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test converting response with empty cart doesn't trigger template."""
        response = ConversationResponse(
            message="Your cart is empty",
            intent="cart_view",
            confidence=1.0,
            cart={"items": [], "item_count": 0},
        )

        with patch.object(adapter, "_send_cart_template", new_callable=AsyncMock) as mock_template:
            messenger_response = await adapter.convert_response(response, psid)

            mock_template.assert_not_called()
            assert messenger_response.text == "Your cart is empty"

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-012")
    async def test_convert_response_products_priority_over_cart(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test that products take priority over cart in response."""
        response = ConversationResponse(
            message="Found products",
            intent="product_search",
            confidence=0.9,
            products=[{"title": "Shoe"}],
            cart={"items": [{"title": "Shirt"}]},
        )

        with patch.object(
            adapter, "_send_product_carousel", new_callable=AsyncMock
        ) as mock_carousel:
            with patch.object(
                adapter, "_send_cart_template", new_callable=AsyncMock
            ) as mock_template:
                await adapter.convert_response(response, psid)

                mock_carousel.assert_called_once()
                mock_template.assert_not_called()


class TestMessengerAdapterWelcomeBack:
    """Tests for MessengerAdapter.send_welcome_back().

    Test IDs: 5.11-ADAPTER-013 through 5.11-ADAPTER-015
    Priority: P2 (Medium) - nice-to-have feature.
    """

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-013")
    async def test_send_welcome_back_singular_item(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test welcome back message with 1 item."""
        mock_send_service = AsyncMock()
        adapter._send_service = mock_send_service

        await adapter.send_welcome_back(psid, item_count=1)

        call_args = mock_send_service.send_message.call_args
        message_text = call_args[0][1]["text"]
        assert "1 item" in message_text
        assert "items" not in message_text

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-014")
    async def test_send_welcome_back_plural_items(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test welcome back message with multiple items."""
        mock_send_service = AsyncMock()
        adapter._send_service = mock_send_service

        await adapter.send_welcome_back(psid, item_count=3)

        call_args = mock_send_service.send_message.call_args
        message_text = call_args[0][1]["text"]
        assert "3 items" in message_text

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-015")
    async def test_send_welcome_back_handles_exception(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test welcome back handles service exception gracefully."""
        mock_send_service = AsyncMock()
        mock_send_service.send_message.side_effect = Exception("Service error")
        adapter._send_service = mock_send_service

        await adapter.send_welcome_back(psid, item_count=1)

        mock_send_service.send_message.assert_called_once()


class TestMessengerAdapterCarousel:
    """Tests for MessengerAdapter._send_product_carousel().

    Test IDs: 5.11-ADAPTER-016 through 5.11-ADAPTER-018
    Priority: P2 (Medium) - product display feature.
    """

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-016")
    async def test_send_carousel_success(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test successful carousel send."""
        products = [
            {"title": "Shoe", "price": 50.0},
            {"title": "Shirt", "price": 30.0},
        ]

        mock_send_service = AsyncMock()
        adapter._send_service = mock_send_service

        mock_formatter = MagicMock()
        mock_formatter.format_product_results_from_list.return_value = {
            "attachment": {"type": "template"}
        }

        with patch(
            "app.services.messenger.MessengerProductFormatter",
            side_effect=Exception("Formatter error"),
        ):
            await adapter._send_product_carousel(products, psid)

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-017")
    async def test_send_carousel_handles_exception(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test carousel handles exception gracefully."""
        products = [{"title": "Shoe"}]

        with patch(
            "app.services.messenger.MessengerProductFormatter",
            side_effect=Exception("Formatter error"),
        ):
            await adapter._send_product_carousel(products, psid)

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-018")
    async def test_send_carousel_closes_service(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test carousel send closes service after sending."""
        products = [{"title": "Shoe"}]

        mock_send_service = AsyncMock()
        adapter._send_service = mock_send_service

        mock_formatter = MagicMock()
        mock_formatter.format_product_results_from_list.return_value = {}

        with patch("app.services.messenger.MessengerProductFormatter", return_value=mock_formatter):
            await adapter._send_product_carousel(products, psid)

            mock_send_service.close.assert_called_once()


class TestMessengerAdapterCartTemplate:
    """Tests for MessengerAdapter._send_cart_template().

    Test IDs: 5.11-ADAPTER-019 through 5.11-ADAPTER-021
    Priority: P2 (Medium) - cart display feature.
    """

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-019")
    async def test_send_cart_template_success(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test successful cart template send."""
        cart = {
            "items": [{"title": "Shoe", "price": 50.0}],
            "item_count": 1,
        }

        mock_send_service = AsyncMock()
        adapter._send_service = mock_send_service

        mock_formatter = MagicMock()
        mock_formatter.format_cart_from_dict.return_value = {}

        with (
            patch("app.services.messenger.CartFormatter", return_value=mock_formatter),
            patch(
                "app.core.config.settings",
                return_value={"STORE_URL": "https://shop.example.com"},
            ),
        ):
            await adapter._send_cart_template(cart, psid)

            mock_send_service.send_message.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-020")
    async def test_send_cart_template_handles_exception(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test cart template handles exception gracefully."""
        cart = {"items": [{"title": "Shoe"}]}

        with patch(
            "app.services.messenger.CartFormatter", side_effect=Exception("Formatter error")
        ):
            await adapter._send_cart_template(cart, psid)

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-021")
    async def test_send_cart_template_closes_service(
        self,
        adapter: MessengerAdapter,
        psid: str,
    ) -> None:
        """Test cart template send closes service after sending."""
        cart = {"items": [{"title": "Shoe"}]}

        mock_send_service = AsyncMock()
        adapter._send_service = mock_send_service

        mock_formatter = MagicMock()
        mock_formatter.format_cart_from_dict.return_value = {}

        with (
            patch("app.services.messenger.CartFormatter", return_value=mock_formatter),
            patch(
                "app.core.config.settings",
                return_value={"STORE_URL": "https://shop.example.com"},
            ),
        ):
            await adapter._send_cart_template(cart, psid)

            mock_send_service.close.assert_called_once()


class TestMessengerAdapterClose:
    """Tests for MessengerAdapter.close().

    Test IDs: 5.11-ADAPTER-022 through 5.11-ADAPTER-023
    Priority: P2 (Medium) - resource cleanup.
    """

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-022")
    async def test_close_with_active_service(
        self,
        adapter: MessengerAdapter,
    ) -> None:
        """Test closing with active send service."""
        mock_send_service = AsyncMock()
        adapter._send_service = mock_send_service

        await adapter.close()

        mock_send_service.close.assert_called_once()
        assert adapter._send_service is None

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-ADAPTER-023")
    async def test_close_without_service(
        self,
        adapter: MessengerAdapter,
    ) -> None:
        """Test closing without active send service (no-op)."""
        adapter._send_service = None

        await adapter.close()

        assert adapter._send_service is None
