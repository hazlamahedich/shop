"""Unit tests for UnifiedConversationService.

Story 5-10: Widget Full App Integration
Story 5-11: Messenger Unified Service Migration
Task 1: Create UnifiedConversationService

Tests intent routing, handler selection, and confidence threshold fallback.

Priority Markers:
    @pytest.mark.p0 - Critical (run on every commit)
    @pytest.mark.p1 - High (run pre-merge)
    @pytest.mark.p2 - Medium (run nightly)
    @pytest.mark.p3 - Low (run weekly)

Test ID Format: {STORY}-{LEVEL}-{SEQ} (e.g., 5.11-UNIT-001)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from freezegun import freeze_time

    HAS_FREEZEGUN = True
except ImportError:
    HAS_FREEZEGUN = False

    def freeze_time(time_string, **kwargs):
        def decorator(func):
            import pytest

            return pytest.skip("freezegun not installed")(func)

        return decorator


from app.services.conversation.schemas import (
    Channel,
    ClarificationState,
    ConversationContext,
    ConversationResponse,
    HandoffState,
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


# ============================================================
# Consolidated mock_db fixtures (Fixes DRY violation)
# ============================================================


@pytest.fixture
def mock_db_with_merchant(mock_merchant: MagicMock) -> AsyncMock:
    """Create a mock database session that returns mock_merchant.

    Usage:
        async def test_x(self, mock_db_with_merchant: AsyncMock) -> None:
            response = await service.process_message(db=mock_db_with_merchant, ...)
    """
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_merchant
    mock_db.execute.return_value = mock_result
    return mock_db


@pytest.fixture
def mock_db_with_no_merchant() -> AsyncMock:
    """Create a mock database session that returns None (merchant not found).

    Usage:
        async def test_not_found(self, mock_db_with_no_merchant: AsyncMock) -> None:
            response = await service.process_message(db=mock_db_with_no_merchant, ...)
    """
    mock_db = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result
    return mock_db


@pytest.fixture
def frozen_time() -> datetime:
    """Return a fixed datetime for deterministic time tests.

    Usage:
        async def test_time_sensitive(self, frozen_time: datetime) -> None:
            past = frozen_time - timedelta(hours=1)
    """
    return datetime(2026, 2, 25, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def frozen_past_time(frozen_time: datetime) -> datetime:
    """Return a time 1 hour before frozen_time."""
    return frozen_time - timedelta(hours=1)


@pytest.fixture
def frozen_recent_time(frozen_time: datetime) -> datetime:
    """Return a time 5 minutes before frozen_time."""
    return frozen_time - timedelta(minutes=5)


@pytest.fixture
def frozen_future_time(frozen_time: datetime) -> datetime:
    """Return a time 1 hour after frozen_time."""
    return frozen_time + timedelta(hours=1)


class TestUnifiedConversationService:
    """Tests for UnifiedConversationService.

    Test IDs: 5.10-UNIT-001 through 5.10-UNIT-004
    Priority: P0 (Critical) - must pass on every commit
    """

    @pytest.mark.asyncio
    @pytest.mark.p0
    @pytest.mark.test_id("5.10-UNIT-001")
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
    @pytest.mark.p0
    @pytest.mark.test_id("5.10-UNIT-002")
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
            patch.object(service, "_check_budget_pause", return_value=None),
            patch.object(service, "_check_hybrid_mode", return_value=None),
            patch.object(service, "_check_handoff", return_value=None),
        ):
            response = await service.process_message(
                db=mock_db,
                context=widget_context,
                message="random unclear message",
            )

        assert response.intent == "unknown"
        assert response.confidence == 0.3

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.10-UNIT-003")
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
            patch.object(service, "_check_budget_pause", return_value=None),
            patch.object(service, "_check_hybrid_mode", return_value=None),
            patch.object(service, "_check_handoff", return_value=None),
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


class TestBudgetPause:
    """Tests for budget pause check (Story 5-11 GAP-6).

    Test IDs: 5.11-UNIT-005 through 5.11-UNIT-007
    Priority: P0 (Critical) - revenue impact if bot is paused incorrectly.
    """

    @pytest.mark.asyncio
    @pytest.mark.p0
    @pytest.mark.test_id("5.11-UNIT-005")
    async def test_paused_bot_returns_unavailable_message(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
        mock_merchant: MagicMock,
    ) -> None:
        """Test that paused bot returns unavailable message."""
        mock_db = AsyncMock(spec=AsyncSession)

        with (
            patch(
                "app.services.cost_tracking.budget_alert_service.BudgetAlertService"
            ) as mock_budget_service,
        ):
            mock_service_instance = AsyncMock()
            mock_service_instance.get_bot_paused_state = AsyncMock(
                return_value=(True, "budget_exceeded")
            )
            mock_budget_service.return_value = mock_service_instance

            response = await service._check_budget_pause(
                db=mock_db,
                context=widget_context,
                merchant=mock_merchant,
            )

        assert response is not None
        assert response.intent == "bot_paused"
        assert "unavailable" in response.message.lower()
        assert response.metadata.get("bot_paused") is True

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-UNIT-006")
    async def test_active_bot_processes_normally(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
        mock_merchant: MagicMock,
    ) -> None:
        """Test that active bot (not paused) proceeds normally."""
        mock_db = AsyncMock(spec=AsyncSession)

        with (
            patch(
                "app.services.cost_tracking.budget_alert_service.BudgetAlertService"
            ) as mock_budget_service,
        ):
            mock_service_instance = AsyncMock()
            mock_service_instance.get_bot_paused_state = AsyncMock(return_value=(False, None))
            mock_budget_service.return_value = mock_service_instance

            response = await service._check_budget_pause(
                db=mock_db,
                context=widget_context,
                merchant=mock_merchant,
            )

        assert response is None

    @pytest.mark.asyncio
    async def test_budget_check_exception_returns_none(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
        mock_merchant: MagicMock,
    ) -> None:
        """Test that budget check exception doesn't block processing."""
        mock_db = AsyncMock(spec=AsyncSession)

        with (
            patch(
                "app.services.cost_tracking.budget_alert_service.BudgetAlertService"
            ) as mock_budget_service,
        ):
            mock_budget_service.side_effect = Exception("Budget service unavailable")

            response = await service._check_budget_pause(
                db=mock_db,
                context=widget_context,
                merchant=mock_merchant,
            )

        assert response is None


class TestHybridMode:
    """Tests for hybrid mode detection (Story 5-11 GAP-5).

    Test IDs: 5.11-UNIT-008 through 5.11-UNIT-011
    Priority: P1 (Important) - affects bot response behavior in hybrid channels.
    """

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-UNIT-008")
    async def test_no_response_without_bot_mention(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
    ) -> None:
        """Test that bot stays silent when hybrid mode is active without @bot."""
        mock_db = AsyncMock(spec=AsyncSession)
        widget_context.hybrid_mode_enabled = True

        response = await service._check_hybrid_mode(
            db=mock_db,
            context=widget_context,
            message="hello there",
        )

        assert response is not None
        assert response.intent == "hybrid_mode_silent"
        assert response.message == ""
        assert response.metadata.get("hybrid_mode") is True

    @pytest.mark.asyncio
    async def test_response_with_bot_mention(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
    ) -> None:
        """Test that bot responds when hybrid mode is active WITH @bot mention."""
        mock_db = AsyncMock(spec=AsyncSession)
        widget_context.hybrid_mode_enabled = True

        response = await service._check_hybrid_mode(
            db=mock_db,
            context=widget_context,
            message="@bot hello there",
        )

        assert response is None

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-UNIT-010")
    @freeze_time("2026-02-25T12:00:00", tz_offset=0)
    async def test_expired_hybrid_mode_disabled(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
    ) -> None:
        """Test that expired hybrid mode allows normal processing."""
        from datetime import datetime, timedelta, timezone

        mock_db = AsyncMock(spec=AsyncSession)
        widget_context.hybrid_mode_enabled = True
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        widget_context.hybrid_mode_expires_at = past_time.isoformat()

        response = await service._check_hybrid_mode(
            db=mock_db,
            context=widget_context,
            message="hello there",
        )

        assert response is None

    @pytest.mark.asyncio
    async def test_hybrid_mode_disabled_returns_none(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
    ) -> None:
        """Test that disabled hybrid mode proceeds normally."""
        mock_db = AsyncMock(spec=AsyncSession)
        widget_context.hybrid_mode_enabled = False

        response = await service._check_hybrid_mode(
            db=mock_db,
            context=widget_context,
            message="hello there",
        )

        assert response is None


class TestHandoffDetection:
    """Tests for handoff detection (Story 5-11 GAP-1).

    Test IDs: 5.11-UNIT-012 through 5.11-UNIT-015
    Priority: P1 (Important) - critical for user experience when bot can't help.
    """

    @pytest.mark.asyncio
    @pytest.mark.p1
    @pytest.mark.test_id("5.11-UNIT-012")
    async def test_low_confidence_increments_counter(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
        mock_merchant: MagicMock,
    ) -> None:
        """Test that low confidence increments consecutive counter."""
        mock_db = AsyncMock(spec=AsyncSession)

        with (
            patch.object(service, "_get_conversation", return_value=None),
            patch("app.services.handoff.detector.HandoffDetector") as mock_detector_class,
            patch("redis.asyncio") as mock_redis,
        ):
            mock_redis_client = AsyncMock()
            mock_redis.from_url.return_value = mock_redis_client
            mock_detector = AsyncMock()
            mock_detector.detect.return_value = MagicMock(
                should_handoff=False,
                reason=None,
                confidence_count=1,
                matched_keyword=None,
                loop_count=0,
            )
            mock_detector_class.return_value = mock_detector

            initial_count = widget_context.handoff_state.consecutive_low_confidence

            await service._check_handoff(
                db=mock_db,
                context=widget_context,
                merchant=mock_merchant,
                message="unclear message",
                confidence=0.3,
                intent_name="unknown",
            )

            assert widget_context.handoff_state.consecutive_low_confidence == initial_count + 1

    @pytest.mark.asyncio
    async def test_high_confidence_resets_counter(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
        mock_merchant: MagicMock,
    ) -> None:
        """Test that high confidence resets consecutive counter."""
        mock_db = AsyncMock(spec=AsyncSession)
        widget_context.handoff_state.consecutive_low_confidence = 2

        with (
            patch.object(service, "_get_conversation", return_value=None),
            patch("app.services.handoff.detector.HandoffDetector") as mock_detector_class,
            patch("redis.asyncio") as mock_redis,
        ):
            mock_redis_client = AsyncMock()
            mock_redis.from_url.return_value = mock_redis_client
            mock_detector = AsyncMock()
            mock_detector.detect.return_value = MagicMock(
                should_handoff=False,
                reason=None,
                confidence_count=0,
                matched_keyword=None,
                loop_count=0,
            )
            mock_detector_class.return_value = mock_detector

            await service._check_handoff(
                db=mock_db,
                context=widget_context,
                merchant=mock_merchant,
                message="show me shoes",
                confidence=0.9,
                intent_name="product_search",
            )

            assert widget_context.handoff_state.consecutive_low_confidence == 0

    @pytest.mark.asyncio
    async def test_handoff_triggered_returns_response(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
        mock_merchant: MagicMock,
    ) -> None:
        """Test that handoff trigger returns handoff response."""
        from app.services.handoff.detector import HandoffReason

        mock_db = AsyncMock(spec=AsyncSession)

        with (
            patch.object(service, "_get_conversation", return_value=None),
            patch.object(service, "_update_conversation_handoff_status", return_value=None),
            patch.object(
                service, "_get_handoff_message", return_value="Connecting you to support..."
            ),
            patch("app.services.handoff.detector.HandoffDetector") as mock_detector_class,
            patch("redis.asyncio") as mock_redis,
        ):
            mock_redis_client = AsyncMock()
            mock_redis.from_url.return_value = mock_redis_client
            mock_detector = AsyncMock()
            mock_detector.detect.return_value = MagicMock(
                should_handoff=True,
                reason=HandoffReason.LOW_CONFIDENCE,
                confidence_count=3,
                matched_keyword=None,
                loop_count=0,
            )
            mock_detector_class.return_value = mock_detector

            response = await service._check_handoff(
                db=mock_db,
                context=widget_context,
                merchant=mock_merchant,
                message="unclear message",
                confidence=0.3,
                intent_name="unknown",
            )

        assert response is not None
        assert response.intent == "human_handoff"
        assert "support" in response.message.lower()

    @pytest.mark.asyncio
    async def test_handoff_check_exception_returns_none(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
        mock_merchant: MagicMock,
    ) -> None:
        """Test that handoff check exception doesn't block processing."""
        mock_db = AsyncMock(spec=AsyncSession)

        with (
            patch("redis.asyncio") as mock_redis,
        ):
            mock_redis.from_url.side_effect = Exception("Redis unavailable")

            response = await service._check_handoff(
                db=mock_db,
                context=widget_context,
                merchant=mock_merchant,
                message="hello",
                confidence=0.8,
                intent_name="greeting",
            )

        assert response is None


class TestReturningShopper:
    """Tests for returning shopper detection (Story 5-11 GAP-7).

    Test IDs: 5.11-UNIT-016 through 5.11-UNIT-019
    Priority: P2 (Secondary) - nice-to-have feature for personalization.
    """

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-UNIT-016")
    async def test_returning_shopper_detected(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
    ) -> None:
        """Test that returning shopper is detected after threshold."""
        from datetime import datetime, timedelta, timezone

        mock_db = AsyncMock(spec=AsyncSession)
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        widget_context.metadata["last_activity_at"] = past_time.isoformat()
        widget_context.is_returning_shopper = False

        await service._check_returning_shopper(
            db=mock_db,
            context=widget_context,
        )

        assert widget_context.is_returning_shopper is True

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-UNIT-017")
    @freeze_time("2026-02-25T12:00:00", tz_offset=0)
    async def test_new_shopper_not_marked_returning(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
    ) -> None:
        """Test that new shopper is not marked as returning."""
        from datetime import datetime, timedelta, timezone

        mock_db = AsyncMock(spec=AsyncSession)
        recent_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        widget_context.metadata["last_activity_at"] = recent_time.isoformat()
        widget_context.is_returning_shopper = False

        await service._check_returning_shopper(
            db=mock_db,
            context=widget_context,
        )

        assert widget_context.is_returning_shopper is False

    @pytest.mark.asyncio
    async def test_already_returning_shopper_unchanged(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
    ) -> None:
        """Test that already-marked returning shopper stays true."""
        mock_db = AsyncMock(spec=AsyncSession)
        widget_context.is_returning_shopper = True

        await service._check_returning_shopper(
            db=mock_db,
            context=widget_context,
        )

        assert widget_context.is_returning_shopper is True

    @pytest.mark.asyncio
    @pytest.mark.p2
    @pytest.mark.test_id("5.11-UNIT-019")
    @freeze_time("2026-02-25T12:00:00", tz_offset=0)
    async def test_last_activity_updated(
        self,
        service: UnifiedConversationService,
        widget_context: ConversationContext,
    ) -> None:
        """Test that last_activity_at is updated."""
        mock_db = AsyncMock(spec=AsyncSession)
        widget_context.last_activity_at = None

        await service._check_returning_shopper(
            db=mock_db,
            context=widget_context,
        )

        assert widget_context.last_activity_at is not None


class TestClarificationState:
    """Tests for clarification state schema (Story 5-11 GAP-3).

    P1: Important - supports clarification flow functionality.
    """

    def test_clarification_state_defaults(self) -> None:
        """Test default clarification state values."""
        state = ClarificationState()

        assert state.active is False
        assert state.attempt_count == 0
        assert state.questions_asked == []
        assert state.last_question is None
        assert state.last_type is None

    def test_clarification_state_with_values(self) -> None:
        """Test clarification state with custom values."""
        state = ClarificationState(
            active=True,
            attempt_count=2,
            questions_asked=["category", "budget"],
            last_question="What's your budget?",
            last_type="budget",
        )

        assert state.active is True
        assert state.attempt_count == 2
        assert len(state.questions_asked) == 2
        assert state.last_question == "What's your budget?"
        assert state.last_type == "budget"


class TestHandoffState:
    """Tests for handoff state schema (Story 5-11 GAP-1).

    P1: Important - supports handoff detection functionality.
    """

    def test_handoff_state_defaults(self) -> None:
        """Test default handoff state values."""
        state = HandoffState()

        assert state.consecutive_low_confidence == 0
        assert state.last_handoff_check is None

    def test_handoff_state_with_values(self) -> None:
        """Test handoff state with custom values."""
        state = HandoffState(
            consecutive_low_confidence=2,
            last_handoff_check="2024-01-01T12:00:00Z",
        )

        assert state.consecutive_low_confidence == 2
        assert state.last_handoff_check == "2024-01-01T12:00:00Z"


class TestConversationContextNewFields:
    """Tests for new ConversationContext fields (Story 5-11).

    P1: Important - validates schema extensions.
    """

    def test_consent_status_field(self) -> None:
        """Test consent_status field."""
        context = ConversationContext(
            session_id="test-session",
            merchant_id=1,
            channel=Channel.WIDGET,
            consent_status="pending",
        )

        assert context.consent_status == "pending"

    def test_pending_consent_product_field(self) -> None:
        """Test pending_consent_product field."""
        product = {"id": "123", "title": "Test Product"}
        context = ConversationContext(
            session_id="test-session",
            merchant_id=1,
            channel=Channel.WIDGET,
            pending_consent_product=product,
        )

        assert context.pending_consent_product == product

    def test_hybrid_mode_fields(self) -> None:
        """Test hybrid mode fields."""
        from datetime import datetime, timezone

        expires = datetime.now(timezone.utc).isoformat()
        context = ConversationContext(
            session_id="test-session",
            merchant_id=1,
            channel=Channel.MESSENGER,
            hybrid_mode_enabled=True,
            hybrid_mode_expires_at=expires,
        )

        assert context.hybrid_mode_enabled is True
        assert context.hybrid_mode_expires_at == expires

    def test_clarification_state_nested(self) -> None:
        """Test nested clarification_state."""
        context = ConversationContext(
            session_id="test-session",
            merchant_id=1,
            channel=Channel.WIDGET,
            clarification_state=ClarificationState(active=True, attempt_count=1),
        )

        assert context.clarification_state.active is True
        assert context.clarification_state.attempt_count == 1

    def test_handoff_state_nested(self) -> None:
        """Test nested handoff_state."""
        context = ConversationContext(
            session_id="test-session",
            merchant_id=1,
            channel=Channel.MESSENGER,
            handoff_state=HandoffState(consecutive_low_confidence=2),
        )

        assert context.handoff_state.consecutive_low_confidence == 2
