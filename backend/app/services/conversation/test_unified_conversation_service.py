"""Unit tests for UnifiedConversationService.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService

Tests intent routing, handler selection, and confidence threshold fallback.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    ConversationResponse,
    IntentType,
)
from app.services.conversation.unified_conversation_service import UnifiedConversationService
from app.services.conversation.cart_key_strategy import CartKeyStrategy
from app.services.intent.classification_schema import (
    ClassificationResult,
    ExtractedEntities,
    IntentType as ClassifierIntentType,
)


@pytest.fixture
def service() -> UnifiedConversationService:
    """Create a UnifiedConversationService instance."""
    return UnifiedConversationService()


@pytest.fixture
def widget_context() -> ConversationContext:
    """Create a widget conversation context."""
    return ConversationContext(
        session_id="test-widget-session-uuid",
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=[],
    )


@pytest.fixture
def messenger_context() -> ConversationContext:
    """Create a messenger conversation context."""
    return ConversationContext(
        session_id="psid_123456789",
        merchant_id=1,
        channel=Channel.MESSENGER,
        platform_sender_id="psid_123456789",
        conversation_history=[],
    )


@pytest.fixture
def preview_context() -> ConversationContext:
    """Create a preview conversation context."""
    return ConversationContext(
        session_id="preview-session",
        merchant_id=1,
        channel=Channel.PREVIEW,
        user_id=1,
        conversation_history=[],
    )


@pytest.fixture
def mock_merchant() -> MagicMock:
    """Create a mock merchant."""
    merchant = MagicMock()
    merchant.id = 1
    merchant.bot_name = "Test Bot"
    merchant.business_name = "Test Store"
    merchant.bot_personality_type = "friendly"
    merchant.business_description = "A test store"
    merchant.use_custom_greeting = False
    merchant.llm_configuration = None
    return merchant


@pytest.fixture
def mock_classification_greeting() -> ClassificationResult:
    """Create a greeting classification result."""
    return ClassificationResult(
        intent=ClassifierIntentType.GREETING,
        confidence=0.95,
        entities=ExtractedEntities(),
        raw_message="Hello",
        llm_provider="test",
        model="test-model",
        processing_time_ms=50,
    )


@pytest.fixture
def mock_classification_search() -> ClassificationResult:
    """Create a product search classification result."""
    return ClassificationResult(
        intent=ClassifierIntentType.PRODUCT_SEARCH,
        confidence=0.85,
        entities=ExtractedEntities(category="shoes", budget=100.0),
        raw_message="Show me shoes under $100",
        llm_provider="test",
        model="test-model",
        processing_time_ms=50,
    )


@pytest.fixture
def mock_classification_low_confidence() -> ClassificationResult:
    """Create a low confidence classification result."""
    return ClassificationResult(
        intent=ClassifierIntentType.UNKNOWN,
        confidence=0.3,
        entities=ExtractedEntities(),
        raw_message="random unclear message",
        llm_provider="test",
        model="test-model",
        processing_time_ms=50,
    )


class TestUnifiedConversationService:
    """Tests for UnifiedConversationService."""

    @pytest.mark.asyncio
    async def test_process_message_returns_response(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
        mock_merchant: MagicMock,
        mock_classification_greeting: ClassificationResult,
    ) -> None:
        """Test that process_message returns a ConversationResponse."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant
        mock_db.execute.return_value = mock_result

        with (
            patch.object(service, "_classify_intent", return_value=mock_classification_greeting),
            patch.object(service, "_get_merchant_llm", return_value=MagicMock()),
        ):
            response = await service.process_message(
                db=mock_db,
                context=widget_context,
                message="Hello",
            )

        assert isinstance(response, ConversationResponse)
        assert response.message is not None
        assert response.intent is not None

    @pytest.mark.asyncio
    async def test_low_confidence_falls_back_to_llm(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
        mock_merchant: MagicMock,
        mock_classification_low_confidence: ClassificationResult,
    ) -> None:
        """Test that low confidence triggers LLM fallback."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant
        mock_db.execute.return_value = mock_result

        mock_llm = MagicMock()
        mock_llm.chat = AsyncMock(return_value=MagicMock(content="LLM response"))

        with (
            patch.object(
                service, "_classify_intent", return_value=mock_classification_low_confidence
            ),
            patch.object(service, "_get_merchant_llm", return_value=mock_llm),
        ):
            response = await service.process_message(
                db=mock_db,
                context=widget_context,
                message="random unclear message",
            )

        assert response.intent == "unknown"
        assert response.confidence == 0.3

    @pytest.mark.asyncio
    async def test_intent_routing_to_search_handler(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
        mock_merchant: MagicMock,
        mock_classification_search: ClassificationResult,
    ) -> None:
        """Test that product_search intent routes to search handler."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_merchant
        mock_db.execute.return_value = mock_result

        with (
            patch.object(service, "_classify_intent", return_value=mock_classification_search),
            patch.object(service, "_get_merchant_llm", return_value=MagicMock()),
            patch.object(
                service._handlers["search"],
                "handle",
                return_value=ConversationResponse(
                    message="Here are some shoes",
                    intent="product_search",
                    confidence=0.85,
                    products=[],
                ),
            ) as mock_handle,
        ):
            response = await service.process_message(
                db=mock_db,
                context=widget_context,
                message="Show me shoes under $100",
            )

        mock_handle.assert_called_once()
        assert response.intent == "product_search"

    @pytest.mark.asyncio
    async def test_merchant_not_found_raises_error(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
    ) -> None:
        """Test that missing merchant raises APIError."""
        from app.core.errors import APIError, ErrorCode

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(APIError) as exc_info:
            await service.process_message(
                db=mock_db,
                context=widget_context,
                message="Hello",
            )

        assert exc_info.value.code == ErrorCode.MERCHANT_NOT_FOUND


class TestCartKeyStrategy:
    """Tests for CartKeyStrategy."""

    def test_for_messenger(self) -> None:
        """Test messenger cart key generation."""
        key = CartKeyStrategy.for_messenger("psid_123456")
        assert key == "cart:messenger:psid_123456"

    def test_for_widget(self) -> None:
        """Test widget cart key generation."""
        key = CartKeyStrategy.for_widget("session-uuid-123")
        assert key == "cart:widget:session-uuid-123"

    def test_for_preview(self) -> None:
        """Test preview cart key generation."""
        key = CartKeyStrategy.for_preview(merchant_id=1, user_id=2)
        assert key == "cart:preview:1:2"

    def test_get_key_for_widget_context(self, widget_context: ConversationContext) -> None:
        """Test context-based key for widget."""
        key = CartKeyStrategy.get_key_for_context(widget_context)
        assert key == f"cart:widget:{widget_context.session_id}"

    def test_get_key_for_messenger_context(self, messenger_context: ConversationContext) -> None:
        """Test context-based key for messenger."""
        key = CartKeyStrategy.get_key_for_context(messenger_context)
        assert key == f"cart:messenger:{messenger_context.platform_sender_id}"

    def test_get_key_for_preview_context(self, preview_context: ConversationContext) -> None:
        """Test context-based key for preview."""
        key = CartKeyStrategy.get_key_for_context(preview_context)
        assert key == f"cart:preview:{preview_context.merchant_id}:{preview_context.user_id}"

    def test_parse_messenger_key(self) -> None:
        """Test parsing messenger cart key."""
        channel, identifier = CartKeyStrategy.parse("cart:messenger:psid_123")
        assert channel == "messenger"
        assert identifier == "psid_123"

    def test_parse_widget_key(self) -> None:
        """Test parsing widget cart key."""
        channel, identifier = CartKeyStrategy.parse("cart:widget:uuid-123")
        assert channel == "widget"
        assert identifier == "uuid-123"


class TestConversationContext:
    """Tests for ConversationContext schema."""

    def test_widget_context_creation(self) -> None:
        """Test creating widget context."""
        context = ConversationContext(
            session_id="test-session",
            merchant_id=1,
            channel=Channel.WIDGET,
            conversation_history=[{"role": "user", "content": "Hello"}],
        )

        assert context.session_id == "test-session"
        assert context.merchant_id == 1
        assert context.channel == "widget"
        assert len(context.conversation_history) == 1

    def test_messenger_context_with_psid(self) -> None:
        """Test messenger context with PSID."""
        context = ConversationContext(
            session_id="session-id",
            merchant_id=1,
            channel=Channel.MESSENGER,
            platform_sender_id="psid_123456789",
        )

        assert context.platform_sender_id == "psid_123456789"

    def test_preview_context_with_user_id(self) -> None:
        """Test preview context with user ID."""
        context = ConversationContext(
            session_id="preview-session",
            merchant_id=1,
            channel=Channel.PREVIEW,
            user_id=42,
        )

        assert context.user_id == 42


class TestConversationResponse:
    """Tests for ConversationResponse schema."""

    def test_basic_response(self) -> None:
        """Test creating basic response."""
        response = ConversationResponse(
            message="Hello there!",
            intent="greeting",
            confidence=0.95,
        )

        assert response.message == "Hello there!"
        assert response.intent == "greeting"
        assert response.confidence == 0.95
        assert response.checkout_url is None
        assert response.fallback is False

    def test_response_with_products(self) -> None:
        """Test response with products."""
        products = [
            {"title": "Shoe", "price": 50.0},
            {"title": "Shirt", "price": 30.0},
        ]
        response = ConversationResponse(
            message="Found 2 products",
            intent="product_search",
            confidence=0.9,
            products=products,
        )

        assert response.products is not None
        assert len(response.products) == 2

    def test_response_with_checkout_url(self) -> None:
        """Test response with checkout URL."""
        response = ConversationResponse(
            message="Here's your checkout link",
            intent="checkout",
            confidence=1.0,
            checkout_url="https://shop.myshopify.com/checkout/123",
        )

        assert response.checkout_url == "https://shop.myshopify.com/checkout/123"

    def test_response_with_fallback(self) -> None:
        """Test fallback response."""
        response = ConversationResponse(
            message="Service degraded",
            intent="checkout",
            confidence=1.0,
            fallback=True,
            fallback_url="https://shop.myshopify.com",
        )

        assert response.fallback is True
        assert response.fallback_url == "https://shop.myshopify.com"

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        response = ConversationResponse(
            message="Hello",
            intent="greeting",
            confidence=0.9,
            metadata={"key": "value"},
        )

        result = response.to_dict()

        assert isinstance(result, dict)
        assert result["message"] == "Hello"
        assert result["intent"] == "greeting"
        assert result["confidence"] == 0.9
        assert result["metadata"]["key"] == "value"
