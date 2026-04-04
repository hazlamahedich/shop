"""Unit tests for Story 11-9 defense-in-depth: SUMMARIZE bypass in multi-turn handler.

P0: Verify that summarize requests during active multi-turn clarification
are NOT swallowed by the multi-turn handler and instead route to the summarize handler.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.conversation.schemas import (
    Channel,
    ClarificationState,
    ConversationContext,
    SessionShoppingState,
)
from app.services.intent.classification_schema import IntentType as ClassifierIntentType


def _make_context(
    multi_turn_state: str = "IDLE",
    session_id: str = "test-session-123",
) -> ConversationContext:
    return ConversationContext(
        session_id=session_id,
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=[
            {"role": "customer", "content": "I want shoes"},
            {"role": "bot", "content": "What kind of shoes?"},
            {"role": "customer", "content": "Running shoes"},
            {"role": "bot", "content": "Any budget range?"},
        ],
        shopping_state=SessionShoppingState(),
        clarification_state=ClarificationState(
            multi_turn_state=multi_turn_state,
            turn_count=2,
        ),
    )


class TestSummarizeBypassInMultiTurn:
    """P0: Verify SUMMARIZE patterns bypass multi-turn during active states."""

    @pytest.mark.asyncio
    async def test_recap_bypasses_clarifying_state(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        context = _make_context(multi_turn_state="CLARIFYING")
        result = await svc._check_multi_turn_state(
            db=AsyncMock(),
            context=context,
            merchant=MagicMock(),
            message="recap",
        )
        assert result is None, (
            "recap during CLARIFYING should return None to fall through to summarize handler"
        )

    @pytest.mark.asyncio
    async def test_summarize_bypasses_collecting_constraints(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        context = _make_context(multi_turn_state="COLLECTING_CONSTRAINTS")
        result = await svc._check_multi_turn_state(
            db=AsyncMock(),
            context=context,
            merchant=MagicMock(),
            message="summarize our conversation",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_what_did_we_discuss_bypasses_multi_turn(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        context = _make_context(multi_turn_state="CLARIFYING")
        result = await svc._check_multi_turn_state(
            db=AsyncMock(),
            context=context,
            merchant=MagicMock(),
            message="what did we discuss?",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_idle_state_returns_none_regardless(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        context = _make_context(multi_turn_state="IDLE")
        result = await svc._check_multi_turn_state(
            db=AsyncMock(),
            context=context,
            merchant=MagicMock(),
            message="recap",
        )
        assert result is None, "IDLE state should always return None regardless of message"

    @pytest.mark.asyncio
    async def test_complete_state_returns_none_regardless(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        context = _make_context(multi_turn_state="COMPLETE")
        result = await svc._check_multi_turn_state(
            db=AsyncMock(),
            context=context,
            merchant=MagicMock(),
            message="summarize",
        )
        assert result is None, "COMPLETE state should always return None"

    @pytest.mark.asyncio
    async def test_refresh_memory_bypasses_clarifying(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        context = _make_context(multi_turn_state="CLARIFYING")
        result = await svc._check_multi_turn_state(
            db=AsyncMock(),
            context=context,
            merchant=MagicMock(),
            message="refresh my memory",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_catch_me_up_bypasses_clarifying(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        svc = UnifiedConversationService.__new__(UnifiedConversationService)
        context = _make_context(multi_turn_state="CLARIFYING")
        result = await svc._check_multi_turn_state(
            db=AsyncMock(),
            context=context,
            merchant=MagicMock(),
            message="catch me up",
        )
        assert result is None
