from __future__ import annotations

import pytest

from app.services.multi_turn.schemas import MultiTurnConfig, MultiTurnState, MultiTurnStateEnum
from app.services.multi_turn.state_machine import ConversationStateMachine


@pytest.fixture
def sm() -> ConversationStateMachine:
    return ConversationStateMachine(MultiTurnConfig())


@pytest.fixture
def state() -> MultiTurnState:
    return MultiTurnState()


class TestStartProactiveGathering:
    def test_from_idle_to_proactive_gathering(
        self, sm: ConversationStateMachine, state: MultiTurnState
    ) -> None:
        result = sm.start_proactive_gathering(state, "red shoes", ["budget", "color"], "ecommerce")
        assert result.state == MultiTurnStateEnum.PROACTIVE_GATHERING
        assert result.original_query == "red shoes"
        assert result.pending_questions == ["budget", "color"]
        assert result.mode == "ecommerce"
        assert result.turn_count == 0

    def test_cannot_start_from_clarifying(
        self, sm: ConversationStateMachine, state: MultiTurnState
    ) -> None:
        sm.start_clarification(state, "test", ["budget"], "ecommerce")
        with pytest.raises(
            ValueError, match="Cannot start proactive gathering while in CLARIFYING"
        ):
            sm.start_proactive_gathering(state, "test", ["budget"], "ecommerce")

    def test_can_start_after_complete(
        self, sm: ConversationStateMachine, state: MultiTurnState
    ) -> None:
        sm.start_proactive_gathering(state, "test", ["budget"], "ecommerce")
        sm.complete_proactive_gathering(state)
        assert state.state == MultiTurnStateEnum.COMPLETE
        fresh = MultiTurnState()
        sm.start_proactive_gathering(fresh, "test", ["budget"], "ecommerce")
        assert fresh.state == MultiTurnStateEnum.PROACTIVE_GATHERING


class TestIncrementGatheringRound:
    def test_increment_increases_turn_count(
        self, sm: ConversationStateMachine, state: MultiTurnState
    ) -> None:
        sm.start_proactive_gathering(state, "test", ["budget", "color"], "ecommerce")
        assert state.turn_count == 0
        sm.increment_gathering_round(state)
        assert state.turn_count == 1
        sm.increment_gathering_round(state)
        assert state.turn_count == 2

    def test_cannot_increment_from_idle(
        self, sm: ConversationStateMachine, state: MultiTurnState
    ) -> None:
        with pytest.raises(ValueError, match="Cannot increment gathering round"):
            sm.increment_gathering_round(state)


class TestCompleteProactiveGathering:
    def test_complete_from_proactive_gathering(
        self, sm: ConversationStateMachine, state: MultiTurnState
    ) -> None:
        sm.start_proactive_gathering(state, "test", ["budget"], "ecommerce")
        result = sm.complete_proactive_gathering(state)
        assert result.state == MultiTurnStateEnum.COMPLETE

    def test_cannot_complete_from_idle(
        self, sm: ConversationStateMachine, state: MultiTurnState
    ) -> None:
        with pytest.raises(ValueError, match="Invalid state transition"):
            sm.complete_proactive_gathering(state)

    def test_cannot_complete_from_clarifying(
        self, sm: ConversationStateMachine, state: MultiTurnState
    ) -> None:
        sm.start_clarification(state, "test", ["budget"], "ecommerce")
        with pytest.raises(ValueError, match="Invalid state transition"):
            sm.complete_proactive_gathering(state)


class TestProactiveGatheringTransitions:
    def test_proactive_gathering_self_transition(
        self, sm: ConversationStateMachine, state: MultiTurnState
    ) -> None:
        sm.start_proactive_gathering(state, "test", ["budget", "color"], "ecommerce")
        sm.increment_gathering_round(state)
        assert state.state == MultiTurnStateEnum.PROACTIVE_GATHERING

    def test_proactive_gathering_to_complete(
        self, sm: ConversationStateMachine, state: MultiTurnState
    ) -> None:
        sm.start_proactive_gathering(state, "test", ["budget"], "ecommerce")
        sm.complete_proactive_gathering(state)
        assert state.state == MultiTurnStateEnum.COMPLETE

    def test_complete_to_idle_via_reset(
        self, sm: ConversationStateMachine, state: MultiTurnState
    ) -> None:
        sm.start_proactive_gathering(state, "test", ["budget"], "ecommerce")
        sm.complete_proactive_gathering(state)
        assert state.state == MultiTurnStateEnum.COMPLETE
        sm.reset(state)
        assert state.state == MultiTurnStateEnum.IDLE

    def test_cannot_start_proactive_gathering_from_clarifying(
        self, sm: ConversationStateMachine, state: MultiTurnState
    ) -> None:
        sm.start_clarification(state, "test", ["budget"], "ecommerce")
        with pytest.raises(ValueError, match="Cannot start proactive gathering"):
            sm.start_proactive_gathering(state, "test", ["budget"], "ecommerce")
