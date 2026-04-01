"""Integration tests for _check_multi_turn_state orchestration path.

Story 11-2: Tests the integration path through UnifiedConversationService
that routes messages through the multi-turn state machine, classifier,
and constraint accumulator. This is the critical untested orchestration path.
"""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.multi_turn.schemas import (
    MessageType,
    MultiTurnConfig,
    MultiTurnState,
    MultiTurnStateEnum,
)


class MockClarificationState:
    def __init__(
        self,
        multi_turn_state: str = "IDLE",
        turn_count: int = 0,
        accumulated_constraints: dict | None = None,
        questions_asked: list | None = None,
        pending_questions: list | None = None,
        original_query: str | None = None,
        invalid_response_count: int = 0,
    ):
        self.multi_turn_state = multi_turn_state
        self.turn_count = turn_count
        self.accumulated_constraints = accumulated_constraints or {}
        self.questions_asked = questions_asked or []
        self.pending_questions = pending_questions or []
        self.original_query = original_query
        self.invalid_response_count = invalid_response_count
        self.last_question = None
        self.last_type = None

    def model_dump(self):
        return {
            "multi_turn_state": self.multi_turn_state,
            "turn_count": self.turn_count,
            "accumulated_constraints": self.accumulated_constraints,
            "questions_asked": self.questions_asked,
            "pending_questions": self.pending_questions,
            "original_query": self.original_query,
            "invalid_response_count": self.invalid_response_count,
        }


class MockConversationContext:
    def __init__(
        self,
        conversation_id: int = 1,
        session_id: str = "test-session",
        clarification_state: MockClarificationState | None = None,
    ):
        self.conversation_id = conversation_id
        self.session_id = session_id
        self.clarification_state = clarification_state or MockClarificationState()


class MockMerchant:
    def __init__(self, id: int = 1, onboarding_mode: str = "ecommerce"):
        self.id = id
        self.onboarding_mode = onboarding_mode


class MockConversation:
    def __init__(self, context_data: dict | None = None):
        self.context = context_data or {}
        self.id = 1


class MockDB:
    def __init__(self):
        self.committed = False

    async def commit(self):
        self.committed = True

    async def execute(self, *args, **kwargs):
        result = MagicMock()
        result.scalar_one_or_none.return_value = MockConversation()
        return result


@pytest.fixture
def mock_service():
    svc = MagicMock()
    svc._get_conversation = AsyncMock(return_value=MockConversation())
    return svc


def _make_clarifying_context(
    original_query: str = "running shoes",
    pending_questions: list | None = None,
    accumulated_constraints: dict | None = None,
    turn_count: int = 0,
) -> MockConversationContext:
    cs = MockClarificationState(
        multi_turn_state="CLARIFYING",
        turn_count=turn_count,
        accumulated_constraints=accumulated_constraints or {},
        questions_asked=[],
        pending_questions=pending_questions or ["budget", "size"],
        original_query=original_query,
    )
    return MockConversationContext(clarification_state=cs)


def _make_refine_context(
    original_query: str = "running shoes",
    accumulated_constraints: dict | None = None,
    turn_count: int = 2,
) -> MockConversationContext:
    cs = MockClarificationState(
        multi_turn_state="REFINE_RESULTS",
        turn_count=turn_count,
        accumulated_constraints=accumulated_constraints or {"category": "shoes"},
        questions_asked=["budget"],
        pending_questions=[],
        original_query=original_query,
    )
    return MockConversationContext(clarification_state=cs)


@pytest.mark.asyncio
class TestOrchestrationIdleReturnsNone:
    async def test_idle_state_returns_none(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        with patch.object(UnifiedConversationService, "__init__", lambda self: None):
            svc = UnifiedConversationService()

        context = MockConversationContext(
            clarification_state=MockClarificationState(multi_turn_state="IDLE")
        )
        merchant = MockMerchant()
        db = MockDB()

        result = await svc._check_multi_turn_state(db, context, merchant, "hello")
        assert result is None

    async def test_complete_state_returns_none(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        with patch.object(UnifiedConversationService, "__init__", lambda self: None):
            svc = UnifiedConversationService()

        context = MockConversationContext(
            clarification_state=MockClarificationState(multi_turn_state="COMPLETE")
        )
        merchant = MockMerchant()
        db = MockDB()

        result = await svc._check_multi_turn_state(db, context, merchant, "new question")
        assert result is None

    async def test_no_conversation_id_returns_none(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        with patch.object(UnifiedConversationService, "__init__", lambda self: None):
            svc = UnifiedConversationService()

        context = MockConversationContext(conversation_id=None)
        context.clarification_state = MockClarificationState(multi_turn_state="CLARIFYING")
        merchant = MockMerchant()
        db = MockDB()

        result = await svc._check_multi_turn_state(db, context, merchant, "test")
        assert result is None


@pytest.mark.asyncio
class TestOrchestrationTopicChange:
    async def test_topic_change_resets_state_and_returns_none(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        with patch.object(UnifiedConversationService, "__init__", lambda self: None):
            svc = UnifiedConversationService()
        svc._get_conversation = AsyncMock(return_value=MockConversation())

        context = _make_clarifying_context(original_query="running shoes")
        merchant = MockMerchant()
        db = MockDB()

        result = await svc._check_multi_turn_state(
            db,
            context,
            merchant,
            "I want to order a pizza with extra cheese and mushrooms please",
        )
        assert result is None
        assert context.clarification_state.multi_turn_state == "IDLE"
        assert context.clarification_state.turn_count == 0
        assert context.clarification_state.accumulated_constraints == {}


@pytest.mark.asyncio
class TestOrchestrationInvalidResponse:
    async def test_invalid_response_returns_rephrase_message(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        with patch.object(UnifiedConversationService, "__init__", lambda self: None):
            svc = UnifiedConversationService()
        svc._get_conversation = AsyncMock(return_value=MockConversation())

        context = _make_clarifying_context()
        merchant = MockMerchant()
        db = MockDB()

        result = await svc._check_multi_turn_state(db, context, merchant, "asdf")
        assert result is not None
        assert "rephrasing" in result.message.lower() or "didn't" in result.message.lower()
        assert context.clarification_state.invalid_response_count == 1

    async def test_max_invalid_responses_forces_refine(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        with patch.object(UnifiedConversationService, "__init__", lambda self: None):
            svc = UnifiedConversationService()
        svc._get_conversation = AsyncMock(return_value=MockConversation())

        context = _make_clarifying_context()
        context.clarification_state.invalid_response_count = 1
        merchant = MockMerchant()
        db = MockDB()

        result = await svc._check_multi_turn_state(db, context, merchant, "asdf")
        assert result is not None
        assert context.clarification_state.multi_turn_state == "REFINE_RESULTS"


@pytest.mark.asyncio
class TestOrchestrationConstraintAddition:
    async def test_constraint_addition_transitions_to_refine(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        with patch.object(UnifiedConversationService, "__init__", lambda self: None):
            svc = UnifiedConversationService()
        svc._get_conversation = AsyncMock(return_value=MockConversation())

        context = _make_clarifying_context()
        merchant = MockMerchant()
        db = MockDB()

        result = await svc._check_multi_turn_state(db, context, merchant, "under $150")
        assert result is not None
        assert "refine" in result.message.lower() or "got it" in result.message.lower()
        assert context.clarification_state.multi_turn_state == "REFINE_RESULTS"

    async def test_constraint_addition_in_refine_state(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        with patch.object(UnifiedConversationService, "__init__", lambda self: None):
            svc = UnifiedConversationService()
        svc._get_conversation = AsyncMock(return_value=MockConversation())

        context = _make_refine_context()
        merchant = MockMerchant()
        db = MockDB()

        result = await svc._check_multi_turn_state(db, context, merchant, "size L")
        assert result is not None
        assert context.clarification_state.multi_turn_state == "REFINE_RESULTS"


@pytest.mark.asyncio
class TestOrchestrationClarificationResponse:
    async def test_clarification_response_accumulates_and_continues(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        with patch.object(UnifiedConversationService, "__init__", lambda self: None):
            svc = UnifiedConversationService()
        svc._get_conversation = AsyncMock(return_value=MockConversation())

        context = _make_clarifying_context(
            pending_questions=["budget", "size", "color"],
            turn_count=0,
        )
        merchant = MockMerchant()
        db = MockDB()

        result = await svc._check_multi_turn_state(db, context, merchant, "Nike")
        assert result is not None
        assert context.clarification_state.turn_count == 1

    async def test_near_turn_limit_transitions_to_refine(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        with patch.object(UnifiedConversationService, "__init__", lambda self: None):
            svc = UnifiedConversationService()
        svc._get_conversation = AsyncMock(return_value=MockConversation())

        context = _make_clarifying_context(
            pending_questions=["color"],
            turn_count=2,
        )
        merchant = MockMerchant()
        db = MockDB()

        result = await svc._check_multi_turn_state(db, context, merchant, "red")
        assert result is not None
        assert context.clarification_state.multi_turn_state == "REFINE_RESULTS"


@pytest.mark.asyncio
class TestOrchestrationGeneralMode:
    async def test_general_mode_uses_general_constraints(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        with patch.object(UnifiedConversationService, "__init__", lambda self: None):
            svc = UnifiedConversationService()
        svc._get_conversation = AsyncMock(return_value=MockConversation())

        cs = MockClarificationState(
            multi_turn_state="CLARIFYING",
            turn_count=0,
            accumulated_constraints={},
            questions_asked=[],
            pending_questions=["severity", "timeframe"],
            original_query="account problem",
        )
        context = MockConversationContext(clarification_state=cs)
        merchant = MockMerchant(onboarding_mode="general")
        db = MockDB()

        result = await svc._check_multi_turn_state(db, context, merchant, "urgent")
        assert result is not None
        assert "severity" in context.clarification_state.accumulated_constraints
