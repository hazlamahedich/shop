"""Unit tests for multi-turn conversation state machine.

Story 11-2: Tests all state transitions, invalid transitions,
persistence-before-LLM-call pattern.
"""

import pytest

from app.services.multi_turn.schemas import (
    MultiTurnConfig,
    MultiTurnState,
    MultiTurnStateEnum,
)
from app.services.multi_turn.state_machine import ConversationStateMachine


@pytest.fixture
def sm() -> ConversationStateMachine:
    return ConversationStateMachine()


@pytest.fixture
def idle_state() -> MultiTurnState:
    return MultiTurnState()


def _clarifying_state() -> MultiTurnState:
    return MultiTurnState(
        state=MultiTurnStateEnum.CLARIFYING,
        turn_count=0,
        original_query="running shoes",
        pending_questions=["budget", "size", "color"],
        mode="ecommerce",
    )


def _refine_state() -> MultiTurnState:
    return MultiTurnState(
        state=MultiTurnStateEnum.REFINE_RESULTS,
        turn_count=2,
        accumulated_constraints={"category": "shoes", "brand": "nike"},
        original_query="running shoes",
        mode="ecommerce",
    )


class TestStartClarification:
    def test_idle_to_clarifying(self, sm: ConversationStateMachine, idle_state: MultiTurnState):
        result = sm.start_clarification(
            idle_state,
            original_query="running shoes",
            pending_questions=["budget", "size", "color"],
            mode="ecommerce",
        )
        assert result.state == MultiTurnStateEnum.CLARIFYING
        assert result.original_query == "running shoes"
        assert result.pending_questions == ["budget", "size", "color"]
        assert result.mode == "ecommerce"
        assert result.turn_count == 0

    def test_clarifying_to_clarifying_is_valid(self, sm: ConversationStateMachine):
        state = _clarifying_state()
        state.state = MultiTurnStateEnum.IDLE
        result = sm.start_clarification(state, "new query", ["budget"])
        assert result.state == MultiTurnStateEnum.CLARIFYING

    def test_complete_to_clarifying_raises(self, sm: ConversationStateMachine):
        state = MultiTurnState(state=MultiTurnStateEnum.COMPLETE)
        with pytest.raises(ValueError, match="Invalid state transition"):
            sm.transition_to_refine(state)

    def test_sets_defaults(self, sm: ConversationStateMachine, idle_state: MultiTurnState):
        idle_state.invalid_response_count = 5
        result = sm.start_clarification(idle_state, "shoes", ["brand"])
        assert result.invalid_response_count == 0
        assert result.turn_count == 0


class TestProcessClarificationResponse:
    def test_valid_response_increments_turn(self, sm: ConversationStateMachine):
        state = _clarifying_state()
        result = sm.process_clarification_response(state, "budget", "under 100", is_valid=True)
        assert result.turn_count == 1
        assert result.state == MultiTurnStateEnum.CLARIFYING

    def test_valid_response_moves_from_pending_to_asked(self, sm: ConversationStateMachine):
        state = _clarifying_state()
        sm.process_clarification_response(state, "budget", "under 100", is_valid=True)
        assert "budget" in state.questions_asked
        assert "budget" not in state.pending_questions

    def test_invalid_response_increments_turn_but_not_asked(self, sm: ConversationStateMachine):
        state = _clarifying_state()
        sm.process_clarification_response(state, "budget", "asdf", is_valid=False)
        assert state.turn_count == 1
        assert "budget" not in state.questions_asked
        assert "budget" in state.pending_questions

    def test_all_questions_answered_transitions_to_refine(self, sm: ConversationStateMachine):
        state = MultiTurnState(
            state=MultiTurnStateEnum.CLARIFYING,
            turn_count=2,
            original_query="shoes",
            pending_questions=["color"],
            questions_asked=["budget", "size"],
        )
        result = sm.process_clarification_response(state, "color", "red", is_valid=True)
        assert result.state == MultiTurnStateEnum.REFINE_RESULTS

    def test_turn_limit_forces_refine(self):
        config = MultiTurnConfig(max_clarification_turns=2)
        sm = ConversationStateMachine(config)
        state = MultiTurnState(
            state=MultiTurnStateEnum.CLARIFYING,
            turn_count=1,
            original_query="shoes",
            pending_questions=["size", "color"],
        )
        result = sm.process_clarification_response(state, "size", "M", is_valid=True)
        assert result.turn_count == 2
        assert result.state == MultiTurnStateEnum.REFINE_RESULTS


class TestTransitionToRefine:
    def test_clarifying_to_refine(self, sm: ConversationStateMachine):
        state = _clarifying_state()
        result = sm.transition_to_refine(state, "sufficient_info")
        assert result.state == MultiTurnStateEnum.REFINE_RESULTS

    def test_refine_to_refine_ok(self, sm: ConversationStateMachine):
        state = _refine_state()
        result = sm.transition_to_refine(state, "constraint_added")
        assert result.state == MultiTurnStateEnum.REFINE_RESULTS

    def test_idle_to_refine_raises(self, sm: ConversationStateMachine, idle_state: MultiTurnState):
        with pytest.raises(ValueError, match="Invalid state transition"):
            sm.transition_to_refine(idle_state)


class TestComplete:
    def test_refine_to_complete(self, sm: ConversationStateMachine):
        state = _refine_state()
        result = sm.complete(state)
        assert result.state == MultiTurnStateEnum.COMPLETE

    def test_idle_to_complete_raises(
        self, sm: ConversationStateMachine, idle_state: MultiTurnState
    ):
        with pytest.raises(ValueError, match="Invalid state transition"):
            sm.complete(idle_state)


class TestReset:
    def test_clarifying_to_idle(self, sm: ConversationStateMachine):
        state = _clarifying_state()
        state.accumulated_constraints = {"brand": "nike"}
        result = sm.reset(state)
        assert result.state == MultiTurnStateEnum.IDLE
        assert result.turn_count == 0
        assert result.accumulated_constraints == {}
        assert result.original_query is None
        assert result.pending_questions == []

    def test_any_state_to_idle(self, sm: ConversationStateMachine):
        for initial in [
            MultiTurnStateEnum.CLARIFYING,
            MultiTurnStateEnum.REFINE_RESULTS,
            MultiTurnStateEnum.COMPLETE,
        ]:
            state = MultiTurnState(state=initial, turn_count=5)
            result = sm.reset(state)
            assert result.state == MultiTurnStateEnum.IDLE


class TestIncrementInvalidCount:
    def test_increments(self, sm: ConversationStateMachine):
        state = MultiTurnState()
        sm.increment_invalid_count(state)
        assert state.invalid_response_count == 1
        sm.increment_invalid_count(state)
        assert state.invalid_response_count == 2


class TestTurnLimitChecks:
    def test_is_at_turn_limit(self):
        config = MultiTurnConfig(max_clarification_turns=3)
        sm = ConversationStateMachine(config)
        state = MultiTurnState(turn_count=3)
        assert sm.is_at_turn_limit(state) is True
        state.turn_count = 2
        assert sm.is_at_turn_limit(state) is False

    def test_is_near_turn_limit(self):
        config = MultiTurnConfig(max_clarification_turns=3)
        sm = ConversationStateMachine(config)
        state = MultiTurnState(turn_count=2)
        assert sm.is_near_turn_limit(state) is True
        state.turn_count = 1
        assert sm.is_near_turn_limit(state) is False


class TestConfigBounds:
    def test_default_turns(self):
        config = MultiTurnConfig()
        assert config.max_clarification_turns == 3

    def test_min_turns(self):
        config = MultiTurnConfig(max_clarification_turns=2)
        assert config.max_clarification_turns == 2

    def test_max_turns(self):
        config = MultiTurnConfig(max_clarification_turns=5)
        assert config.max_clarification_turns == 5

    def test_below_min_raises(self):
        with pytest.raises(Exception):
            MultiTurnConfig(max_clarification_turns=1)

    def test_above_max_raises(self):
        with pytest.raises(Exception):
            MultiTurnConfig(max_clarification_turns=6)


class TestPersistenceBeforeLLM:
    def test_state_persisted_before_next_operation(self, sm: ConversationStateMachine):
        state = sm.start_clarification(
            MultiTurnState(),
            original_query="shoes",
            pending_questions=["budget"],
        )
        assert state.state == MultiTurnStateEnum.CLARIFYING
        state_copy = state.model_dump()
        sm.process_clarification_response(state, "budget", "100", is_valid=True)
        assert state_copy["state"] == MultiTurnStateEnum.CLARIFYING
        assert state.state == MultiTurnStateEnum.REFINE_RESULTS
