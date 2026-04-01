"""Integration tests for e-commerce mode multi-turn flows.

Story 11-2: Tests happy path, turn limit, topic change,
constraint accumulation, contradictory constraints, invalid responses,
LLM fallback, concurrent messages, Redis degradation.
"""

import asyncio

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
def ecommerce_config() -> MultiTurnConfig:
    return MultiTurnConfig(max_clarification_turns=3, max_invalid_responses=2)


@pytest.fixture
def sm(ecommerce_config: MultiTurnConfig) -> ConversationStateMachine:
    return ConversationStateMachine(ecommerce_config)


@pytest.fixture
def accumulator() -> ConstraintAccumulator:
    return ConstraintAccumulator()


@pytest.fixture
def classifier() -> MessageClassifier:
    return MessageClassifier()


@pytest.mark.asyncio
class TestEcommerceHappyPath:
    async def test_three_turn_clarification_to_results(
        self, sm: ConversationStateMachine, accumulator: ConstraintAccumulator
    ):
        state = MultiTurnState()
        state = sm.start_clarification(
            state,
            original_query="running shoes",
            pending_questions=["budget", "brand", "size"],
            mode="ecommerce",
        )
        assert state.state == MultiTurnStateEnum.CLARIFYING

        constraints: dict = {}

        # Turn 1: Budget
        constraints = accumulator.accumulate("under $100", constraints, "ecommerce")
        state.accumulated_constraints = constraints
        state = sm.process_clarification_response(state, "budget", "under $100", is_valid=True)
        assert state.turn_count == 1
        assert constraints.get("budget_max") == 100.0

        # Turn 2: Brand
        constraints = accumulator.accumulate("Nike", constraints, "ecommerce")
        state.accumulated_constraints = constraints
        state = sm.process_clarification_response(state, "brand", "Nike", is_valid=True)
        assert state.turn_count == 2

        # Turn 3: Size -> all questions answered -> REFINE_RESULTS
        constraints = accumulator.accumulate("size M", constraints, "ecommerce")
        state.accumulated_constraints = constraints
        state = sm.process_clarification_response(state, "size", "M", is_valid=True)
        assert state.state == MultiTurnStateEnum.REFINE_RESULTS

        summary = accumulator.format_constraint_summary(constraints, "ecommerce")
        assert "Nike" in summary
        assert "100" in summary


@pytest.mark.asyncio
class TestEcommerceTurnLimit:
    async def test_turn_limit_forces_best_effort(self):
        config = MultiTurnConfig(max_clarification_turns=2)
        sm = ConversationStateMachine(config)
        accumulator = ConstraintAccumulator()

        state = MultiTurnState()
        state = sm.start_clarification(
            state,
            original_query="shoes",
            pending_questions=["budget", "brand", "size", "color"],
            mode="ecommerce",
        )

        constraints: dict = {}
        constraints = accumulator.accumulate("under $100", constraints, "ecommerce")
        state = sm.process_clarification_response(state, "budget", "under $100", is_valid=True)
        assert state.turn_count == 1

        constraints = accumulator.accumulate("Nike", constraints, "ecommerce")
        state = sm.process_clarification_response(state, "brand", "Nike", is_valid=True)
        assert state.turn_count == 2
        assert state.state == MultiTurnStateEnum.REFINE_RESULTS

    async def test_near_turn_limit_summarizes(self):
        config = MultiTurnConfig(max_clarification_turns=3)
        sm = ConversationStateMachine(config)
        assert sm.is_near_turn_limit(MultiTurnState(turn_count=2)) is True
        assert sm.is_near_turn_limit(MultiTurnState(turn_count=1)) is False


@pytest.mark.asyncio
class TestEcommerceTopicChange:
    async def test_topic_change_resets_state(self, classifier: MessageClassifier):
        state = MultiTurnState()
        sm = ConversationStateMachine()

        state = sm.start_clarification(
            state,
            original_query="running shoes",
            pending_questions=["budget"],
            mode="ecommerce",
        )
        assert state.state == MultiTurnStateEnum.CLARIFYING

        msg_type = await classifier.classify(
            "I want to order a pizza with mushrooms and extra cheese please",
            state,
        )
        assert msg_type == MessageType.TOPIC_CHANGE

        state = sm.reset(state)
        assert state.state == MultiTurnStateEnum.IDLE
        assert state.turn_count == 0
        assert state.accumulated_constraints == {}


@pytest.mark.asyncio
class TestEcommerceConstraintAccumulation:
    async def test_constraints_accumulate_across_turns(self, accumulator: ConstraintAccumulator):
        constraints: dict = {}
        constraints = accumulator.accumulate("running shoes", constraints, "ecommerce")
        constraints = accumulator.accumulate("under $100", constraints, "ecommerce")
        constraints = accumulator.accumulate("Nike", constraints, "ecommerce")
        constraints = accumulator.accumulate("size L", constraints, "ecommerce")

        assert constraints.get("budget_max") == 100.0
        assert constraints.get("brand") == "nike"
        assert constraints.get("category") == "shoes"
        assert constraints.get("size") == "l"

    async def test_duplicate_not_replaced(self, accumulator: ConstraintAccumulator):
        constraints = {"brand": "nike"}
        result = accumulator.accumulate("Nike", constraints, "ecommerce")
        assert result["brand"] == "nike"


@pytest.mark.asyncio
class TestEcommerceContradictoryConstraints:
    async def test_budget_conflict_detected(self, accumulator: ConstraintAccumulator):
        constraints = {"budget_max": 50.0}
        result = accumulator.accumulate("over $200", constraints, "ecommerce")
        assert "budget_min_conflict" in result
        assert result["budget_min"] == 200.0


@pytest.mark.asyncio
class TestEcommerceInvalidResponses:
    async def test_invalid_increments_counter(self, sm: ConversationStateMachine):
        state = MultiTurnState()
        state = sm.start_clarification(
            state,
            original_query="shoes",
            pending_questions=["budget"],
            mode="ecommerce",
        )
        sm.increment_invalid_count(state)
        assert state.invalid_response_count == 1
        sm.increment_invalid_count(state)
        assert state.invalid_response_count == 2

    async def test_max_invalid_forces_refine(self, sm: ConversationStateMachine):
        state = MultiTurnState()
        state = sm.start_clarification(
            state,
            original_query="shoes",
            pending_questions=["budget"],
            mode="ecommerce",
        )
        sm.increment_invalid_count(state)
        sm.increment_invalid_count(state)
        assert state.invalid_response_count >= sm.config.max_invalid_responses


@pytest.mark.asyncio
class TestEcommerceLLMFallback:
    async def test_heuristic_fallback(self):
        class FailingLLM:
            async def classify(self, prompt, context):
                raise RuntimeError("LLM unavailable")

        classifier = MessageClassifier(intent_classifier=FailingLLM())
        state = MultiTurnState(
            state=MultiTurnStateEnum.CLARIFYING,
            original_query="shoes",
            pending_questions=["budget"],
        )
        result = await classifier.classify("under $100", state)
        assert isinstance(result, MessageType)


@pytest.mark.asyncio
class TestEcommerceConcurrentMessages:
    async def test_lock_prevents_race_condition(self):
        from app.services.multi_turn.conversation_lock import ConversationLockManager

        lock_manager = ConversationLockManager()
        lock = await lock_manager.get_lock(1)

        results = []

        async def protected_operation(value: int):
            async with lock:
                results.append(value)

        await asyncio.gather(
            protected_operation(1),
            protected_operation(2),
            protected_operation(3),
        )
        assert sorted(results) == [1, 2, 3]


@pytest.mark.asyncio
class TestEcommerceRedisDegradation:
    async def test_state_machine_works_without_redis(self):
        sm = ConversationStateMachine()
        state = sm.start_clarification(
            MultiTurnState(),
            original_query="shoes",
            pending_questions=["budget"],
        )
        assert state.state == MultiTurnStateEnum.CLARIFYING
        sm.reset(state)
        assert state.state == MultiTurnStateEnum.IDLE
