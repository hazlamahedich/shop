"""Unit tests for COMPLETE state transitions in the state machine.

Story 11-2: Tests COMPLETE->IDLE and COMPLETE->CLARIFYING transitions,
and the reset-after-complete pattern.
"""

import pytest

from app.services.multi_turn.schemas import (
    MultiTurnConfig,
    MultiTurnState,
    MultiTurnStateEnum,
)
from app.services.multi_turn.state_machine import ConversationStateMachine, VALID_TRANSITIONS


@pytest.fixture
def sm() -> ConversationStateMachine:
    return ConversationStateMachine()


def _complete_state() -> MultiTurnState:
    return MultiTurnState(
        state=MultiTurnStateEnum.COMPLETE,
        turn_count=3,
        original_query="running shoes",
        accumulated_constraints={"category": "shoes", "brand": "nike", "budget_max": 100.0},
        questions_asked=["budget", "brand", "size"],
        pending_questions=[],
        mode="ecommerce",
    )


class TestCompleteToIdle:
    def test_reset_from_complete_goes_to_idle(self, sm: ConversationStateMachine):
        state = _complete_state()
        result = sm.reset(state)
        assert result.state == MultiTurnStateEnum.IDLE
        assert result.turn_count == 0
        assert result.accumulated_constraints == {}
        assert result.original_query is None
        assert result.pending_questions == []
        assert result.questions_asked == []
        assert result.clarification_turns == []

    def test_complete_to_idle_is_valid_transition(self):
        assert "IDLE" in VALID_TRANSITIONS["COMPLETE"]

    def test_complete_to_idle_clears_all_fields(self, sm: ConversationStateMachine):
        state = _complete_state()
        state.invalid_response_count = 2
        state.clarification_turns = [
            {
                "question_asked": "Budget?",
                "constraint_name": "budget",
                "user_response": "100",
                "is_valid": True,
            }
        ]
        result = sm.reset(state)
        assert result.invalid_response_count == 0
        assert result.clarification_turns == []


class TestCompleteToClarifying:
    def test_complete_to_clarifying_is_valid_transition(self):
        assert "CLARIFYING" in VALID_TRANSITIONS["COMPLETE"]

    def test_complete_to_refine_results_not_allowed(self):
        assert "REFINE_RESULTS" not in VALID_TRANSITIONS["COMPLETE"]

    def test_start_clarification_from_complete_is_valid(self, sm: ConversationStateMachine):
        state = _complete_state()
        result = sm.start_clarification(state, "new query", ["budget"])
        assert result.state == MultiTurnStateEnum.CLARIFYING
        assert result.original_query == "new query"

    def test_transition_to_refine_from_complete_raises(self, sm: ConversationStateMachine):
        state = _complete_state()
        with pytest.raises(ValueError, match="Invalid state transition"):
            sm.transition_to_refine(state)

    def test_complete_to_complete_not_allowed(self):
        assert "COMPLETE" not in VALID_TRANSITIONS["COMPLETE"]

    def test_complete_to_idle_via_reset_then_clarifying(self, sm: ConversationStateMachine):
        state = _complete_state()
        state = sm.reset(state)
        assert state.state == MultiTurnStateEnum.IDLE

        state = sm.start_clarification(
            state,
            original_query="winter jacket",
            pending_questions=["budget", "color"],
            mode="ecommerce",
        )
        assert state.state == MultiTurnStateEnum.CLARIFYING
        assert state.original_query == "winter jacket"
        assert state.pending_questions == ["budget", "color"]


class TestCompleteTransitionTable:
    def test_all_complete_transitions_are_valid(self):
        allowed = VALID_TRANSITIONS["COMPLETE"]
        assert allowed == {"IDLE", "CLARIFYING"}

    def test_complete_cannot_transition_to_itself(self):
        assert "COMPLETE" not in VALID_TRANSITIONS["COMPLETE"]

    def test_complete_cannot_transition_to_refine(self):
        assert "REFINE_RESULTS" not in VALID_TRANSITIONS["COMPLETE"]


class TestFullCycleCompleteResetNewFlow:
    def test_full_cycle_idle_clarifying_refine_complete_idle_clarifying(self):
        sm = ConversationStateMachine()

        state = MultiTurnState()
        state = sm.start_clarification(state, "shoes", ["budget", "brand"], "ecommerce")
        assert state.state == MultiTurnStateEnum.CLARIFYING

        state = sm.process_clarification_response(state, "budget", "under 100", is_valid=True)
        assert state.state == MultiTurnStateEnum.CLARIFYING

        state = sm.process_clarification_response(state, "brand", "Nike", is_valid=True)
        assert state.state == MultiTurnStateEnum.REFINE_RESULTS

        state = sm.complete(state)
        assert state.state == MultiTurnStateEnum.COMPLETE

        state = sm.reset(state)
        assert state.state == MultiTurnStateEnum.IDLE
        assert state.accumulated_constraints == {}

        state = sm.start_clarification(state, "jacket", ["color"], "ecommerce")
        assert state.state == MultiTurnStateEnum.CLARIFYING
        assert state.original_query == "jacket"
