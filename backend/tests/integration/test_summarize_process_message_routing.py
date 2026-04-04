"""Integration tests for process_message() → SUMMARIZE routing (Story 11-9 GAP 3).

Tests that the UnifiedConversationService.process_message() correctly detects
SUMMARIZE patterns and routes them to the SummarizeHandler, bypassing
multi-turn, FAQ, proactive gathering, and general-mode fallback.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.schemas import (
    Channel,
    ClarificationState,
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
    merchant.embedding_provider = None
    merchant.embedding_model = None
    return merchant


def _make_context(
    history: list[dict] | None = None,
    session_id: str = "test-session-routing",
    multi_turn_state: str = "IDLE",
) -> ConversationContext:
    return ConversationContext(
        session_id=session_id,
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=history or [],
        shopping_state=SessionShoppingState(),
        clarification_state=ClarificationState(
            multi_turn_state=multi_turn_state,
            turn_count=0,
        ),
    )


class TestProcessMessageSummarizeRouting:
    """P1: process_message() routes SUMMARIZE patterns to SummarizeHandler."""

    @pytest.mark.asyncio
    async def test_recap_routes_to_summarize_handler(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        mock_db = AsyncMock()
        merchant = _make_merchant()
        context = _make_context(history=_make_history(5))

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        svc.db = None
        svc.track_costs = False
        svc.rag_context_builder = None
        svc.logger = MagicMock()
        svc.general_mode_fallback_handler = MagicMock()

        mock_summarize_handler = AsyncMock()
        mock_response = MagicMock()
        mock_response.intent = "summarize"
        mock_response.message = "Here's a recap!"
        mock_response.confidence = 1.0
        mock_response.metadata = {}
        mock_summarize_handler.handle = AsyncMock(return_value=mock_response)

        svc._handlers = {"summarize": mock_summarize_handler}

        with patch.object(svc, "_load_merchant", AsyncMock(return_value=merchant)):
            result = await svc.process_message(mock_db, context, "recap")

        mock_summarize_handler.handle.assert_called_once()
        assert result.intent == "summarize"

    @pytest.mark.asyncio
    async def test_summarize_our_conversation_routes_correctly(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        mock_db = AsyncMock()
        merchant = _make_merchant()
        context = _make_context(history=_make_history(5))

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        svc.db = None
        svc.track_costs = False
        svc.rag_context_builder = None
        svc.logger = MagicMock()
        svc.general_mode_fallback_handler = MagicMock()

        mock_summarize_handler = AsyncMock()
        mock_response = MagicMock()
        mock_response.intent = "summarize"
        mock_response.message = "Summary of our chat"
        mock_response.confidence = 0.98
        mock_response.metadata = {}
        mock_summarize_handler.handle = AsyncMock(return_value=mock_response)

        svc._handlers = {"summarize": mock_summarize_handler}

        with patch.object(svc, "_load_merchant", AsyncMock(return_value=merchant)):
            result = await svc.process_message(mock_db, context, "summarize our conversation")

        mock_summarize_handler.handle.assert_called_once()
        assert result.intent == "summarize"

    @pytest.mark.asyncio
    async def test_non_summarize_pattern_does_not_route_to_handler(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        mock_db = AsyncMock()
        merchant = _make_merchant()
        context = _make_context(history=_make_history(5))

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        svc.db = None
        svc.track_costs = False
        svc.rag_context_builder = None
        svc.logger = MagicMock()
        svc.general_mode_fallback_handler = MagicMock()

        mock_summarize_handler = AsyncMock()
        mock_summarize_handler.handle = AsyncMock()

        svc._handlers = {
            "summarize": mock_summarize_handler,
            "llm": AsyncMock(),
            "greeting": AsyncMock(),
        }

        with patch.object(svc, "_load_merchant", AsyncMock(return_value=merchant)):
            with patch.object(svc, "_is_simple_greeting", return_value=False):
                pattern_result = svc._check_summarize_pattern("summarize the return policy")
                assert pattern_result is None, (
                    "summarize the return policy should NOT match SUMMARIZE pattern"
                )

    @pytest.mark.asyncio
    async def test_routing_priority_before_multi_turn(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        mock_db = AsyncMock()
        merchant = _make_merchant()
        context = _make_context(
            history=_make_history(5),
            multi_turn_state="CLARIFYING",
        )

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        svc.db = None
        svc.track_costs = False
        svc.rag_context_builder = None
        svc.logger = MagicMock()
        svc.general_mode_fallback_handler = MagicMock()

        mock_summarize_handler = AsyncMock()
        mock_response = MagicMock()
        mock_response.intent = "summarize"
        mock_response.message = "Summary during multi-turn"
        mock_response.confidence = 1.0
        mock_response.metadata = {}
        mock_summarize_handler.handle = AsyncMock(return_value=mock_response)

        mock_multi_turn = AsyncMock()
        mock_multi_turn.handle = AsyncMock()

        svc._handlers = {
            "summarize": mock_summarize_handler,
            "clarification": mock_multi_turn,
        }

        with patch.object(svc, "_load_merchant", AsyncMock(return_value=merchant)):
            result = await svc.process_message(mock_db, context, "catch me up")

        mock_summarize_handler.handle.assert_called_once()
        mock_multi_turn.handle.assert_not_called()

    @pytest.mark.asyncio
    async def test_general_mode_summarize_not_bypassed(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        mock_db = AsyncMock()
        merchant = _make_merchant(onboarding_mode="general")
        context = _make_context(history=_make_history(4))

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        svc.db = None
        svc.track_costs = False
        svc.rag_context_builder = None
        svc.logger = MagicMock()
        svc.general_mode_fallback_handler = MagicMock()

        mock_summarize_handler = AsyncMock()
        mock_response = MagicMock()
        mock_response.intent = "summarize"
        mock_response.message = "General mode summary"
        mock_response.confidence = 1.0
        mock_response.metadata = {}
        mock_summarize_handler.handle = AsyncMock(return_value=mock_response)

        svc._handlers = {
            "summarize": mock_summarize_handler,
            "general_mode_fallback": AsyncMock(),
        }

        with patch.object(svc, "_load_merchant", AsyncMock(return_value=merchant)):
            result = await svc.process_message(mock_db, context, "refresh my memory")

        mock_summarize_handler.handle.assert_called_once()
        assert result.intent == "summarize"
