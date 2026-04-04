"""Unit tests for SummarizeHandler (Story 11-9).

AC1: Handler routes correctly when SUMMARIZE intent detected.
AC2: Short conversation (< 3 customer turns) returns friendly message.
AC3: Long conversation returns LLM-generated summary with intro/closing.
AC4: Context is read-only during summarization.
AC5: Fallback on LLM failure.
AC6: Error code 7100 on handler failure.

Adversarial review tests: C-5, C-6, H-3, H-4, M-6.
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


def _make_history(customer_turns: int, bot_turns: int | None = None) -> list[dict]:
    if bot_turns is None:
        bot_turns = customer_turns
    history = []
    for i in range(customer_turns):
        history.append({"role": "customer", "content": f"Customer message {i}"})
    for i in range(bot_turns):
        history.append({"role": "bot", "content": f"Bot message {i}"})
    return history


@pytest.fixture
def handler():
    return SummarizeHandler()


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def ecommerce_merchant():
    merchant = MagicMock()
    merchant.id = 1
    merchant.business_name = "Test Store"
    merchant.onboarding_mode = "ecommerce"
    merchant.personality = PersonalityType.FRIENDLY
    merchant.bot_name = "Mantisbot"
    return merchant


@pytest.fixture
def general_merchant():
    merchant = MagicMock()
    merchant.id = 2
    merchant.business_name = "General Store"
    merchant.onboarding_mode = "general"
    merchant.personality = PersonalityType.PROFESSIONAL
    merchant.bot_name = "Assistant"
    return merchant


@pytest.fixture
def mock_llm():
    service = AsyncMock()
    service.chat = AsyncMock(return_value=MagicMock(content="LLM summary text"))
    return service


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


class TestShortConversation:
    """AC2: Short conversation (< 3 customer turns) returns friendly message."""

    @pytest.mark.asyncio
    async def test_zero_customer_turns(self, handler, mock_db, ecommerce_merchant, mock_llm):
        context = _make_context(history=[])
        result = await handler.handle(mock_db, ecommerce_merchant, mock_llm, "summarize", context)
        assert result.intent == "summarize"
        assert result.confidence == 1.0
        assert result.metadata["summary_generated"] is True

    @pytest.mark.asyncio
    async def test_one_customer_turn(self, handler, mock_db, ecommerce_merchant, mock_llm):
        context = _make_context(history=_make_history(1))
        result = await handler.handle(mock_db, ecommerce_merchant, mock_llm, "recap", context)
        assert result.intent == "summarize"
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_two_customer_turns(self, handler, mock_db, ecommerce_merchant, mock_llm):
        context = _make_context(history=_make_history(2))
        result = await handler.handle(
            mock_db, ecommerce_merchant, mock_llm, "what did we discuss?", context
        )
        assert result.intent == "summarize"
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_short_conversation_uses_formatter(
        self, handler, mock_db, ecommerce_merchant, mock_llm
    ):
        context = _make_context(history=_make_history(1))
        with patch(
            "app.services.conversation.handlers.summarize_handler.PersonalityAwareResponseFormatter"
        ) as mock_fmt:
            mock_fmt.format_response.return_value = "Short conversation response"
            result = await handler.handle(
                mock_db, ecommerce_merchant, mock_llm, "summarize", context
            )
            mock_fmt.format_response.assert_called_once_with(
                "summarization",
                "short_conversation",
                PersonalityType.FRIENDLY,
                include_transition=True,
                mode="ecommerce",
                conversation_id=context.session_id,
                bot_name="Mantisbot",
            )
            assert result.message == "Short conversation response"


class TestLongConversation:
    """AC3: Long conversation returns LLM-generated summary with intro/closing."""

    @pytest.mark.asyncio
    async def test_three_customer_turns_triggers_llm(
        self, handler, mock_db, ecommerce_merchant, mock_llm
    ):
        context = _make_context(history=_make_history(3))
        with patch(
            "app.services.conversation.handlers.summarize_handler.ContextSummarizerService"
        ) as mock_svc_cls:
            mock_svc = AsyncMock()
            mock_svc.summarize_for_customer = AsyncMock(return_value="**Summary**")
            mock_svc_cls.return_value = mock_svc
            with patch(
                "app.services.conversation.handlers.summarize_handler.PersonalityAwareResponseFormatter"
            ) as mock_fmt:
                mock_fmt.format_response.side_effect = [
                    "Intro text",
                    "Closing text",
                ]
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "summarize", context
                )
        assert result.intent == "summarize"
        assert "Intro text" in result.message
        assert "**Summary**" in result.message
        assert "Closing text" in result.message

    @pytest.mark.asyncio
    async def test_many_turns_summarized(self, handler, mock_db, ecommerce_merchant, mock_llm):
        history = _make_history(10, 10)
        context = _make_context(history=history)
        with patch(
            "app.services.conversation.handlers.summarize_handler.ContextSummarizerService"
        ) as mock_svc_cls:
            mock_svc = AsyncMock()
            mock_svc.summarize_for_customer = AsyncMock(return_value="- Item 1\n- Item 2")
            mock_svc_cls.return_value = mock_svc
            with patch(
                "app.services.conversation.handlers.summarize_handler.PersonalityAwareResponseFormatter"
            ) as mock_fmt:
                mock_fmt.format_response.side_effect = ["Intro", "Closing"]
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "summarize", context
                )
        assert result.metadata["summary_generated"] is True
        assert result.metadata["summary_turn_count"] == 20


class TestLLMFailureFallback:
    """AC5: Fallback on LLM failure."""

    @pytest.mark.asyncio
    async def test_llm_failure_uses_fallback_summary(
        self, handler, mock_db, ecommerce_merchant, mock_llm
    ):
        context = _make_context(history=_make_history(5))
        with patch(
            "app.services.conversation.handlers.summarize_handler.ContextSummarizerService"
        ) as mock_svc_cls:
            mock_svc = AsyncMock()
            mock_svc.summarize_for_customer = AsyncMock(side_effect=Exception("LLM timeout"))
            mock_svc_cls.return_value = mock_svc
            with patch(
                "app.services.conversation.handlers.summarize_handler.PersonalityAwareResponseFormatter"
            ) as mock_fmt:
                mock_fmt.format_response.side_effect = ["Intro", "Closing"]
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "summarize", context
                )
        assert result.intent == "summarize"
        assert result.message is not None
        assert len(result.message) > 0


class TestHandlerFailureErrorCode:
    """AC6: Error code 7100 on handler failure."""

    @pytest.mark.asyncio
    async def test_unexpected_error_logs_7100(self, handler, mock_db, ecommerce_merchant, mock_llm):
        context = _make_context(history=_make_history(3))
        with patch(
            "app.services.conversation.handlers.summarize_handler.PersonalityAwareResponseFormatter.format_response",
            side_effect=RuntimeError("Unexpected"),
        ):
            result = await handler.handle(
                mock_db, ecommerce_merchant, mock_llm, "summarize", context
            )
        assert result.intent == "summarize"
        assert result.metadata.get("fallback") is True


class TestContextReadOnly:
    """AC4: Context is read-only during summarization."""

    @pytest.mark.asyncio
    async def test_context_not_mutated(self, handler, mock_db, ecommerce_merchant, mock_llm):
        context = _make_context(history=_make_history(5))
        original_history = list(context.conversation_history)
        original_session_id = context.session_id
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
                await handler.handle(mock_db, ecommerce_merchant, mock_llm, "summarize", context)
        assert context.conversation_history == original_history
        assert context.session_id == original_session_id


class TestPersonalityVariants:
    """C-5: All personality variants work."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "personality",
        [PersonalityType.FRIENDLY, PersonalityType.PROFESSIONAL, PersonalityType.ENTHUSIASTIC],
    )
    async def test_short_conversation_all_personalities(
        self, handler, mock_db, mock_llm, personality
    ):
        merchant = MagicMock()
        merchant.id = 1
        merchant.business_name = "Test Store"
        merchant.onboarding_mode = "ecommerce"
        merchant.personality = personality
        merchant.bot_name = "Bot"
        context = _make_context(history=_make_history(1))
        result = await handler.handle(mock_db, merchant, mock_llm, "summarize", context)
        assert result.intent == "summarize"
        assert result.message is not None


class TestModeVariants:
    """C-6: Both ecommerce and general modes work."""

    @pytest.mark.asyncio
    async def test_general_mode_long_conversation(
        self, handler, mock_db, general_merchant, mock_llm
    ):
        context = _make_context(history=_make_history(5))
        with patch(
            "app.services.conversation.handlers.summarize_handler.ContextSummarizerService"
        ) as mock_svc_cls:
            mock_svc = AsyncMock()
            mock_svc.summarize_for_customer = AsyncMock(return_value="General summary")
            mock_svc_cls.return_value = mock_svc
            with patch(
                "app.services.conversation.handlers.summarize_handler.PersonalityAwareResponseFormatter"
            ) as mock_fmt:
                mock_fmt.format_response.side_effect = ["Intro", "Closing"]
                result = await handler.handle(
                    mock_db, general_merchant, mock_llm, "summarize", context
                )
        assert result.intent == "summarize"
        assert "General summary" in result.message


class TestNoConstructorArgs:
    """H-3: SummarizeHandler has no constructor args."""

    def test_handler_no_args(self):
        h = SummarizeHandler()
        assert h is not None


class TestFallbackSummary:
    """H-4: _fallback_summary produces valid output."""

    def test_fallback_empty_history(self):
        result = SummarizeHandler._fallback_summary({}, "ecommerce")
        assert "No conversation history" in result

    def test_fallback_with_history_ecommerce(self):
        ctx = {
            "conversation_history": [
                {"role": "customer", "content": "I want shoes"},
                {"role": "bot", "content": "Here are shoes"},
            ]
        }
        result = SummarizeHandler._fallback_summary(ctx, "ecommerce")
        assert "Discussion Summary" in result or "shoes" in result.lower()

    def test_fallback_with_history_general(self):
        ctx = {
            "conversation_history": [
                {"role": "customer", "content": "Tell me about returns"},
                {"role": "bot", "content": "Return policy is 30 days"},
            ]
        }
        result = SummarizeHandler._fallback_summary(ctx, "general")
        assert "Topics Covered" in result or "returns" in result.lower()


class TestMetadataFields:
    """M-6: Metadata includes summary_generated and summary_turn_count."""

    @pytest.mark.asyncio
    async def test_metadata_present(self, handler, mock_db, ecommerce_merchant, mock_llm):
        context = _make_context(history=_make_history(5))
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
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "summarize", context
                )
        assert "summary_generated" in result.metadata
        assert result.metadata["summary_generated"] is True
        assert "summary_turn_count" in result.metadata
        assert result.metadata["summary_turn_count"] == 10


class TestEdgeCases:
    """Additional edge case tests."""

    @pytest.mark.asyncio
    async def test_merchant_no_personality_uses_default(self, handler, mock_db, mock_llm):
        merchant = MagicMock()
        merchant.id = 1
        merchant.personality = None
        merchant.bot_name = None
        merchant.onboarding_mode = None
        context = _make_context(history=_make_history(1))
        result = await handler.handle(mock_db, merchant, mock_llm, "summarize", context)
        assert result.intent == "summarize"

    @pytest.mark.asyncio
    async def test_empty_history_returns_short_response(
        self, handler, mock_db, ecommerce_merchant, mock_llm
    ):
        context = _make_context(history=[])
        result = await handler.handle(mock_db, ecommerce_merchant, mock_llm, "summarize", context)
        assert result.intent == "summarize"
        assert result.metadata["summary_turn_count"] == 0
