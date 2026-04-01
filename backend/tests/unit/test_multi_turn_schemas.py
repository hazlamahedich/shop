"""Unit tests for multi-turn schemas.

Story 11-2: Tests schema validation, config bounds (min 2, max 5).
"""

import pytest

from app.services.multi_turn.schemas import (
    ClarificationTurn,
    EcommerceConstraints,
    GeneralConstraints,
    MessageType,
    MultiTurnConfig,
    MultiTurnState,
    MultiTurnStateEnum,
)


class TestMessageType:
    def test_all_values(self):
        assert MessageType.NEW_QUERY == "new_query"
        assert MessageType.CLARIFICATION_RESPONSE == "clarification_response"
        assert MessageType.CONSTRAINT_ADDITION == "constraint_addition"
        assert MessageType.TOPIC_CHANGE == "topic_change"
        assert MessageType.INVALID_RESPONSE == "invalid_response"


class TestMultiTurnStateEnum:
    def test_all_values(self):
        assert MultiTurnStateEnum.IDLE == "IDLE"
        assert MultiTurnStateEnum.CLARIFYING == "CLARIFYING"
        assert MultiTurnStateEnum.REFINE_RESULTS == "REFINE_RESULTS"
        assert MultiTurnStateEnum.COMPLETE == "COMPLETE"


class TestMultiTurnConfig:
    def test_defaults(self):
        config = MultiTurnConfig()
        assert config.max_clarification_turns == 3
        assert config.max_invalid_responses == 2

    def test_min_bound(self):
        config = MultiTurnConfig(max_clarification_turns=2)
        assert config.max_clarification_turns == 2

    def test_max_bound(self):
        config = MultiTurnConfig(max_clarification_turns=5)
        assert config.max_clarification_turns == 5

    def test_below_min_raises(self):
        with pytest.raises(Exception):
            MultiTurnConfig(max_clarification_turns=1)

    def test_above_max_raises(self):
        with pytest.raises(Exception):
            MultiTurnConfig(max_clarification_turns=6)

    def test_zero_invalid_raises(self):
        with pytest.raises(Exception):
            MultiTurnConfig(max_invalid_responses=0)


class TestMultiTurnState:
    def test_defaults(self):
        state = MultiTurnState()
        assert state.state == MultiTurnStateEnum.IDLE
        assert state.turn_count == 0
        assert state.accumulated_constraints == {}
        assert state.questions_asked == []
        assert state.pending_questions == []
        assert state.original_query is None
        assert state.invalid_response_count == 0
        assert state.mode == "ecommerce"
        assert state.clarification_turns == []

    def test_custom_values(self):
        state = MultiTurnState(
            state=MultiTurnStateEnum.CLARIFYING,
            turn_count=2,
            accumulated_constraints={"brand": "nike"},
            questions_asked=["budget"],
            pending_questions=["size"],
            original_query="shoes",
            invalid_response_count=1,
            mode="general",
        )
        assert state.state == MultiTurnStateEnum.CLARIFYING
        assert state.turn_count == 2
        assert state.accumulated_constraints == {"brand": "nike"}

    def test_serialization(self):
        state = MultiTurnState(
            state=MultiTurnStateEnum.CLARIFYING,
            original_query="test",
        )
        dumped = state.model_dump()
        assert dumped["state"] == MultiTurnStateEnum.CLARIFYING
        assert dumped["original_query"] == "test"

    def test_negative_turn_count_raises(self):
        with pytest.raises(Exception):
            MultiTurnState(turn_count=-1)


class TestClarificationTurn:
    def test_defaults(self):
        turn = ClarificationTurn(
            question_asked="What's your budget?",
            constraint_name="budget",
        )
        assert turn.user_response is None
        assert turn.is_valid is False

    def test_valid_turn(self):
        turn = ClarificationTurn(
            question_asked="What's your budget?",
            constraint_name="budget",
            user_response="under $100",
            is_valid=True,
        )
        assert turn.is_valid is True


class TestEcommerceConstraints:
    def test_defaults(self):
        constraints = EcommerceConstraints()
        assert constraints.budget_min is None
        assert constraints.budget_max is None
        assert constraints.brand is None

    def test_with_alias(self):
        constraints = EcommerceConstraints(budgetMin=50.0, productType="running")
        assert constraints.budget_min == 50.0
        assert constraints.product_type == "running"

    def test_populate_by_name(self):
        constraints = EcommerceConstraints(budget_min=50.0)
        assert constraints.budget_min == 50.0


class TestGeneralConstraints:
    def test_defaults(self):
        constraints = GeneralConstraints()
        assert constraints.issue_type is None
        assert constraints.severity is None

    def test_with_alias(self):
        constraints = GeneralConstraints(issueType="login", resolutionAttempts=["restart"])
        assert constraints.issue_type == "login"
        assert constraints.resolution_attempts == ["restart"]
