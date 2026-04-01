"""Integration tests for general mode multi-turn flows.

Story 11-2: Tests general mode clarification, issue type tracking,
severity/timeframe accumulation, routing to resolution.
"""

import pytest

from app.services.multi_turn.constraint_accumulator import ConstraintAccumulator
from app.services.multi_turn.message_classifier import MessageClassifier
from app.services.multi_turn.schemas import (
    MessageType,
    MultiTurnConfig,
    MultiTurnState,
    MultiTurnStateEnum,
)
from app.services.multi_turn.state_machine import ConversationStateMachine


@pytest.fixture
def general_config() -> MultiTurnConfig:
    return MultiTurnConfig(max_clarification_turns=3, max_invalid_responses=2)


@pytest.fixture
def sm(general_config: MultiTurnConfig) -> ConversationStateMachine:
    return ConversationStateMachine(general_config)


@pytest.fixture
def accumulator() -> ConstraintAccumulator:
    return ConstraintAccumulator()


@pytest.fixture
def classifier() -> MessageClassifier:
    return MessageClassifier()


@pytest.mark.asyncio
class TestGeneralHappyPath:
    async def test_three_turn_issue_clarification(
        self, sm: ConversationStateMachine, accumulator: ConstraintAccumulator
    ):
        state = MultiTurnState()
        state = sm.start_clarification(
            state,
            original_query="I have a problem with my account",
            pending_questions=["issue_type", "severity", "timeframe"],
            mode="general",
        )
        assert state.state == MultiTurnStateEnum.CLARIFYING
        assert state.mode == "general"

        constraints: dict = {}

        # Turn 1: Issue type
        constraints = accumulator.accumulate("login problem", constraints, "general")
        state.accumulated_constraints = constraints
        state = sm.process_clarification_response(state, "issue_type", "login", is_valid=True)
        assert state.turn_count == 1
        assert constraints.get("issue_type") == "login"

        # Turn 2: Severity
        constraints = accumulator.accumulate("urgent", constraints, "general")
        state.accumulated_constraints = constraints
        state = sm.process_clarification_response(state, "severity", "urgent", is_valid=True)
        assert state.turn_count == 2

        # Turn 3: Timeframe -> all answered -> REFINE_RESULTS
        constraints = accumulator.accumulate("started today", constraints, "general")
        state.accumulated_constraints = constraints
        state = sm.process_clarification_response(state, "timeframe", "today", is_valid=True)
        assert state.state == MultiTurnStateEnum.REFINE_RESULTS

        summary = accumulator.format_constraint_summary(constraints, "general")
        assert "login" in summary
        assert "urgent" in summary
        assert "today" in summary


@pytest.mark.asyncio
class TestGeneralModeConstraintTypes:
    async def test_severity_extraction(self, accumulator: ConstraintAccumulator):
        for text in ["urgent", "critical", "minor", "high priority"]:
            result = accumulator.accumulate(text, {}, "general")
            assert "severity" in result, f"Expected severity from '{text}'"

    async def test_timeframe_extraction(self, accumulator: ConstraintAccumulator):
        for text in ["today", "yesterday", "right now"]:
            result = accumulator.accumulate(text, {}, "general")
            assert "timeframe" in result, f"Expected timeframe from '{text}'"

    async def test_issue_type_extraction(self, accumulator: ConstraintAccumulator):
        for text in ["login", "payment issue", "shipping problem"]:
            result = accumulator.accumulate(text, {}, "general")
            assert "issue_type" in result, f"Expected issue_type from '{text}'"


@pytest.mark.asyncio
class TestGeneralTurnLimit:
    async def test_forces_best_effort_after_limit(self):
        config = MultiTurnConfig(max_clarification_turns=2)
        sm = ConversationStateMachine(config)
        accumulator = ConstraintAccumulator()

        state = MultiTurnState()
        state = sm.start_clarification(
            state,
            original_query="account problem",
            pending_questions=["issue_type", "severity", "timeframe"],
            mode="general",
        )

        constraints: dict = {}
        constraints = accumulator.accumulate("login", constraints, "general")
        state = sm.process_clarification_response(state, "issue_type", "login", is_valid=True)

        constraints = accumulator.accumulate("urgent", constraints, "general")
        state = sm.process_clarification_response(state, "severity", "urgent", is_valid=True)

        assert state.state == MultiTurnStateEnum.REFINE_RESULTS
        summary = accumulator.format_constraint_summary(constraints, "general")
        assert "login" in summary
        assert "urgent" in summary


@pytest.mark.asyncio
class TestGeneralTopicChange:
    async def test_switch_to_ecommerce_resets(self, classifier: MessageClassifier):
        state = MultiTurnState()
        sm = ConversationStateMachine()

        state = sm.start_clarification(
            state,
            original_query="account problem",
            pending_questions=["severity"],
            mode="general",
        )

        msg_type = await classifier.classify(
            "I want to buy running shoes under 100 dollars",
            state,
        )
        assert msg_type == MessageType.TOPIC_CHANGE

        state = sm.reset(state)
        assert state.state == MultiTurnStateEnum.IDLE
        assert state.turn_count == 0
        assert state.accumulated_constraints == {}


@pytest.mark.asyncio
class TestGeneralInvalidResponses:
    async def test_invalid_in_general_mode(self, classifier: MessageClassifier):
        state = MultiTurnState(
            state=MultiTurnStateEnum.CLARIFYING,
            original_query="account problem",
            mode="general",
            pending_questions=["severity"],
        )
        result = await classifier.classify("asdf", state)
        assert result == MessageType.INVALID_RESPONSE

    async def test_max_invalid_forces_results(self):
        config = MultiTurnConfig(max_invalid_responses=2)
        sm = ConversationStateMachine(config)

        state = MultiTurnState()
        state = sm.start_clarification(
            state,
            original_query="problem",
            pending_questions=["severity"],
            mode="general",
        )

        sm.increment_invalid_count(state)
        sm.increment_invalid_count(state)
        assert state.invalid_response_count >= config.max_invalid_responses


@pytest.mark.asyncio
class TestGeneralConstraintAccumulation:
    async def test_accumulates_across_turns(self, accumulator: ConstraintAccumulator):
        constraints: dict = {}
        constraints = accumulator.accumulate("login problem", constraints, "general")
        constraints = accumulator.accumulate("urgent", constraints, "general")
        constraints = accumulator.accumulate("started today", constraints, "general")

        assert constraints.get("issue_type") == "login"
        assert constraints.get("severity") == "urgent"
        assert constraints.get("timeframe") == "today"


@pytest.mark.asyncio
class TestGeneralRoutingToResolution:
    async def test_complete_flow_routes_to_resolution(self):
        sm = ConversationStateMachine()
        accumulator = ConstraintAccumulator()

        state = MultiTurnState()
        state = sm.start_clarification(
            state,
            original_query="payment failed",
            pending_questions=["issue_type"],
            mode="general",
        )

        constraints = accumulator.accumulate("payment issue", {}, "general")
        state.accumulated_constraints = constraints
        state = sm.process_clarification_response(state, "issue_type", "payment", is_valid=True)

        assert state.state == MultiTurnStateEnum.REFINE_RESULTS
        state = sm.complete(state)
        assert state.state == MultiTurnStateEnum.COMPLETE
