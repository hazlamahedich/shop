"""Story 11-9: Integration tests for conversation summarization flow.

Tests the complete flow from pattern detection through handler invocation,
LLM summarization, personality formatting, and response delivery.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.handlers.summarize_handler import SummarizeHandler
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    SessionShoppingState,
)
from app.services.intent.classification_schema import IntentType as ClassifierIntentType


def _make_history(customer_turns: int, bot_turns: int | None = None) -> list[dict]:
    if bot_turns is None:
        bot_turns = customer_turns
    history = []
    for i in range(customer_turns):
        history.append({"role": "customer", "content": f"Customer message {i}"})
    for i in range(bot_turns):
        history.append({"role": "bot", "content": f"Bot message {i}"})
    return history


def _make_merchant(
    onboarding_mode: str = "ecommerce",
    personality: PersonalityType = PersonalityType.FRIENDLY,
    bot_name: str = "Mantisbot",
) -> MagicMock:
    merchant = MagicMock()
    merchant.id = 1
    merchant.business_name = "Test Store"
    merchant.onboarding_mode = onboarding_mode
    merchant.personality = personality
    merchant.bot_name = bot_name
    return merchant


def _make_context(
    history: list[dict] | None = None,
    session_id: str = "test-session-123",
) -> ConversationContext:
    return ConversationContext(
        session_id=session_id,
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=history or [],
        shopping_state=SessionShoppingState(),
    )


@pytest.fixture
def handler():
    return SummarizeHandler()


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_llm():
    return AsyncMock()


class TestPatternDetectionToHandlerFlow:
    """Integration: pattern detection triggers handler correctly."""

    @pytest.mark.asyncio
    async def test_recap_triggers_handler(self, handler, mock_db, mock_llm):
        merchant = _make_merchant()
        context = _make_context(history=_make_history(5))
        with patch(
            "app.services.conversation.handlers.summarize_handler.ContextSummarizerService"
        ) as mock_svc_cls:
            mock_svc = AsyncMock()
            mock_svc.summarize_for_customer = AsyncMock(return_value="LLM Summary")
            mock_svc_cls.return_value = mock_svc
            with patch(
                "app.services.conversation.handlers.summarize_handler.PersonalityAwareResponseFormatter"
            ) as mock_fmt:
                mock_fmt.format_response.side_effect = ["Intro", "Closing"]
                result = await handler.handle(mock_db, merchant, mock_llm, "recap", context)
        assert result.intent == "summarize"
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_pattern_method_matches_recap(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        assert svc._check_summarize_pattern("recap") == ClassifierIntentType.SUMMARIZE

    @pytest.mark.asyncio
    async def test_pattern_method_no_false_positive(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        assert svc._check_summarize_pattern("summarize the return policy") is None


class TestSummarizationEndToEnd:
    """Full flow: pattern → handler → LLM → formatter → response."""

    @pytest.mark.asyncio
    async def test_full_ecommerce_flow(self, handler, mock_db, mock_llm):
        merchant = _make_merchant(onboarding_mode="ecommerce")
        context = _make_context(history=_make_history(5, 5))
        with patch(
            "app.services.conversation.handlers.summarize_handler.ContextSummarizerService"
        ) as mock_svc_cls:
            mock_svc = AsyncMock()
            mock_svc.summarize_for_customer = AsyncMock(
                return_value="🛍️ Products Discussed:\n- Shoes\n- Hats"
            )
            mock_svc_cls.return_value = mock_svc
            with patch(
                "app.services.conversation.handlers.summarize_handler.PersonalityAwareResponseFormatter"
            ) as mock_fmt:
                mock_fmt.format_response.side_effect = [
                    "Here's a quick recap!",
                    "Anything else?",
                ]
                result = await handler.handle(
                    mock_db, merchant, mock_llm, "summarize our conversation", context
                )
        assert result.intent == "summarize"
        assert "Here's a quick recap!" in result.message
        assert "🛍️ Products Discussed" in result.message
        assert "Anything else?" in result.message
        assert result.metadata["summary_generated"] is True
        assert result.metadata["summary_turn_count"] == 10

    @pytest.mark.asyncio
    async def test_full_general_flow(self, handler, mock_db, mock_llm):
        merchant = _make_merchant(
            onboarding_mode="general",
            personality=PersonalityType.PROFESSIONAL,
        )
        context = _make_context(history=_make_history(4, 4))
        with patch(
            "app.services.conversation.handlers.summarize_handler.ContextSummarizerService"
        ) as mock_svc_cls:
            mock_svc = AsyncMock()
            mock_svc.summarize_for_customer = AsyncMock(
                return_value="📝 Topics Covered:\n- Returns\n- Shipping"
            )
            mock_svc_cls.return_value = mock_svc
            with patch(
                "app.services.conversation.handlers.summarize_handler.PersonalityAwareResponseFormatter"
            ) as mock_fmt:
                mock_fmt.format_response.side_effect = [
                    "Here is a summary.",
                    "Is there anything else?",
                ]
                result = await handler.handle(
                    mock_db, merchant, mock_llm, "summarize this chat", context
                )
        assert result.intent == "summarize"
        assert "Here is a summary." in result.message
        assert "Returns" in result.message


class TestSummarizationWithLLMFailure:
    """Integration: LLM failure triggers fallback path."""

    @pytest.mark.asyncio
    async def test_llm_down_uses_fallback(self, handler, mock_db, mock_llm):
        merchant = _make_merchant()
        context = _make_context(history=_make_history(5))
        with patch(
            "app.services.conversation.handlers.summarize_handler.ContextSummarizerService"
        ) as mock_svc_cls:
            mock_svc = AsyncMock()
            mock_svc.summarize_for_customer = AsyncMock(
                side_effect=ConnectionError("LLM unavailable")
            )
            mock_svc_cls.return_value = mock_svc
            with patch(
                "app.services.conversation.handlers.summarize_handler.PersonalityAwareResponseFormatter"
            ) as mock_fmt:
                mock_fmt.format_response.side_effect = ["Intro", "Closing"]
                result = await handler.handle(mock_db, merchant, mock_llm, "summarize", context)
        assert result.intent == "summarize"
        assert result.message is not None
        assert len(result.message) > 0


class TestSummarizationShortConversationFlow:
    """Integration: short conversation returns formatted short message."""

    @pytest.mark.asyncio
    async def test_short_conversation_no_llm_call(self, handler, mock_db, mock_llm):
        merchant = _make_merchant()
        context = _make_context(history=_make_history(2, 2))
        with patch(
            "app.services.conversation.handlers.summarize_handler.ContextSummarizerService"
        ) as mock_svc_cls:
            result = await handler.handle(mock_db, merchant, mock_llm, "summarize", context)
            mock_svc_cls.assert_not_called()
        assert result.intent == "summarize"
        assert result.metadata["summary_turn_count"] == 4


class TestSummarizationAllStates:
    """Verify summarization works in all conversation states."""

    @pytest.mark.asyncio
    async def test_clarifying_state(self, handler, mock_db, mock_llm):
        merchant = _make_merchant()
        context = _make_context(history=_make_history(5))
        context.clarification_state.multi_turn_state = "CLARIFYING"
        with patch(
            "app.services.conversation.handlers.summarize_handler.ContextSummarizerService"
        ) as mock_svc_cls:
            mock_svc = AsyncMock()
            mock_svc.summarize_for_customer = AsyncMock(return_value="Summary")
            mock_svc_cls.return_value = mock_svc
            with patch(
                "app.services.conversation.handlers.summarize_handler.PersonalityAwareResponseFormatter"
            ) as mock_fmt:
                mock_fmt.format_response.side_effect = ["Intro", "Closing"]
                result = await handler.handle(mock_db, merchant, mock_llm, "recap", context)
        assert result.intent == "summarize"

    @pytest.mark.asyncio
    async def test_proactive_gathering_state(self, handler, mock_db, mock_llm):
        merchant = _make_merchant()
        context = _make_context(history=_make_history(5))
        context.gathering_state.active = True
        with patch(
            "app.services.conversation.handlers.summarize_handler.ContextSummarizerService"
        ) as mock_svc_cls:
            mock_svc = AsyncMock()
            mock_svc.summarize_for_customer = AsyncMock(return_value="Summary")
            mock_svc_cls.return_value = mock_svc
            with patch(
                "app.services.conversation.handlers.summarize_handler.PersonalityAwareResponseFormatter"
            ) as mock_fmt:
                mock_fmt.format_response.side_effect = ["Intro", "Closing"]
                result = await handler.handle(mock_db, merchant, mock_llm, "recap", context)
        assert result.intent == "summarize"
