"""Unit tests for message classifier.

Story 11-2: Tests all message types, LLM fallback to heuristic,
invalid response detection.
"""

import pytest

from app.services.multi_turn.message_classifier import MessageClassifier
from app.services.multi_turn.schemas import (
    MessageType,
    MultiTurnState,
    MultiTurnStateEnum,
)


@pytest.fixture
def classifier() -> MessageClassifier:
    return MessageClassifier()


def _clarifying_state() -> MultiTurnState:
    return MultiTurnState(
        state=MultiTurnStateEnum.CLARIFYING,
        original_query="running shoes",
        pending_questions=["budget"],
        accumulated_constraints={"category": "shoes"},
    )


def _refine_state() -> MultiTurnState:
    return MultiTurnState(
        state=MultiTurnStateEnum.REFINE_RESULTS,
        original_query="running shoes",
        accumulated_constraints={"category": "shoes", "brand": "nike"},
    )


class TestNewQueryDetection:
    @pytest.mark.asyncio
    async def test_idle_state_returns_new_query(self, classifier: MessageClassifier):
        state = MultiTurnState()
        result = await classifier.classify("hello", state)
        assert result == MessageType.NEW_QUERY

    @pytest.mark.asyncio
    async def test_no_original_query_returns_new_query(self, classifier: MessageClassifier):
        state = MultiTurnState(
            state=MultiTurnStateEnum.CLARIFYING,
            original_query=None,
        )
        result = await classifier.classify("something", state)
        assert result == MessageType.NEW_QUERY


class TestTopicChangeDetection:
    @pytest.mark.asyncio
    async def test_completely_different_topic(self, classifier: MessageClassifier):
        state = _clarifying_state()
        result = await classifier.classify(
            "I want to order a pizza with extra cheese and mushrooms",
            state,
        )
        assert result == MessageType.TOPIC_CHANGE

    @pytest.mark.asyncio
    async def test_short_non_keyword_message_in_refine(self, classifier: MessageClassifier):
        state = _refine_state()
        result = await classifier.classify(
            "what about weather forecast for tomorrow",
            state,
        )
        assert result in (MessageType.TOPIC_CHANGE, MessageType.NEW_QUERY)


class TestInvalidResponseDetection:
    @pytest.mark.asyncio
    async def test_empty_string(self, classifier: MessageClassifier):
        state = _clarifying_state()
        result = await classifier.classify("", state)
        assert result == MessageType.INVALID_RESPONSE

    @pytest.mark.asyncio
    async def test_single_char(self, classifier: MessageClassifier):
        state = _clarifying_state()
        result = await classifier.classify("a", state)
        assert result == MessageType.INVALID_RESPONSE

    @pytest.mark.asyncio
    async def test_known_invalid(self, classifier: MessageClassifier):
        state = _clarifying_state()
        for msg in ["asdf", "idk", "whatever", "n/a", "huh", "?"]:
            result = await classifier.classify(msg, state)
            assert result == MessageType.INVALID_RESPONSE, f"Expected INVALID_RESPONSE for '{msg}'"

    @pytest.mark.asyncio
    async def test_too_short(self, classifier: MessageClassifier):
        state = _clarifying_state()
        result = await classifier.classify("x", state)
        assert result == MessageType.INVALID_RESPONSE


class TestConstraintAdditionDetection:
    @pytest.mark.asyncio
    async def test_price_constraint(self, classifier: MessageClassifier):
        state = _refine_state()
        result = await classifier.classify("under $150", state)
        assert result == MessageType.CONSTRAINT_ADDITION

    @pytest.mark.asyncio
    async def test_size_constraint(self, classifier: MessageClassifier):
        state = _refine_state()
        result = await classifier.classify("size L", state)
        assert result == MessageType.CONSTRAINT_ADDITION

    @pytest.mark.asyncio
    async def test_urgency_constraint(self, classifier: MessageClassifier):
        state = MultiTurnState(
            state=MultiTurnStateEnum.CLARIFYING,
            original_query="need help with account",
            accumulated_constraints={"issue_type": "account"},
        )
        result = await classifier.classify("it's urgent", state)
        assert result in (MessageType.CONSTRAINT_ADDITION, MessageType.CLARIFICATION_RESPONSE)


class TestClarificationResponseDetection:
    @pytest.mark.asyncio
    async def test_normal_response_in_clarifying(self, classifier: MessageClassifier):
        state = _clarifying_state()
        result = await classifier.classify("yes I want them", state)
        assert result in (
            MessageType.CLARIFICATION_RESPONSE,
            MessageType.CONSTRAINT_ADDITION,
            MessageType.TOPIC_CHANGE,
        )


class TestLLMFallbackToHeuristic:
    @pytest.mark.asyncio
    async def test_failing_llm_falls_back(self):
        class FailingLLM:
            async def classify(self, prompt, context):
                raise RuntimeError("LLM unavailable")

        classifier = MessageClassifier(intent_classifier=FailingLLM())
        state = _clarifying_state()
        result = await classifier.classify("under $100", state)
        assert isinstance(result, MessageType)
        assert result != MessageType.NEW_QUERY

    @pytest.mark.asyncio
    async def test_no_llm_uses_heuristic(self, classifier: MessageClassifier):
        state = _clarifying_state()
        result = await classifier.classify("under $100", state)
        assert isinstance(result, MessageType)


class TestHeuristicTopicChange:
    def test_unrelated_keywords(self, classifier: MessageClassifier):
        assert (
            classifier._is_topic_change(
                "I want to order a pizza with extra cheese and mushrooms",
                "running shoes",
            )
            is True
        )

    def test_related_keywords(self, classifier: MessageClassifier):
        assert classifier._is_topic_change("running shoes", "running shoes") is False

    def test_short_related_message(self, classifier: MessageClassifier):
        assert classifier._is_topic_change("yes", "running shoes") is False
