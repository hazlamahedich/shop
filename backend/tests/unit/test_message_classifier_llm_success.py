"""Unit tests for LLM-based message classification success path.

Story 11-2: Tests LLM high-confidence classification, confidence threshold
boundary, label mapping, and graceful degradation when confidence is low.
"""

import pytest

from app.services.multi_turn.message_classifier import MessageClassifier
from app.services.multi_turn.schemas import (
    MessageType,
    MultiTurnState,
    MultiTurnStateEnum,
)


class MockLLMResult:
    def __init__(self, intent_value: str, confidence: float):
        self.intent = type("Intent", (), {"value": intent_value})()
        self.confidence = confidence


class MockLLM:
    def __init__(
        self,
        results: dict[str, MockLLMResult] | None = None,
        default_result: MockLLMResult | None = None,
    ):
        self._results = results or {}
        self._default = default_result
        self.calls: list[tuple[str, dict]] = []

    async def classify(self, prompt: str, context: dict):
        self.calls.append((prompt, context))
        if self._default:
            return self._default
        for key, result in self._results.items():
            if key in prompt:
                return result
        return MockLLMResult("new_query", 0.3)


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


class TestLLMHighConfidenceClassification:
    @pytest.mark.asyncio
    async def test_classifies_clarification_response(self):
        llm = MockLLM(default_result=MockLLMResult("clarification_response", 0.9))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _clarifying_state()
        result = await classifier.classify("under $100", state, {})
        assert result == MessageType.CLARIFICATION_RESPONSE

    @pytest.mark.asyncio
    async def test_classifies_new_query(self):
        llm = MockLLM(default_result=MockLLMResult("new_query", 0.95))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _clarifying_state()
        result = await classifier.classify("I want something completely different", state, {})
        assert result == MessageType.NEW_QUERY

    @pytest.mark.asyncio
    async def test_classifies_constraint_addition(self):
        llm = MockLLM(default_result=MockLLMResult("constraint_addition", 0.85))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _refine_state()
        result = await classifier.classify("and it should be red", state, {})
        assert result == MessageType.CONSTRAINT_ADDITION

    @pytest.mark.asyncio
    async def test_classifies_topic_change(self):
        llm = MockLLM(default_result=MockLLMResult("topic_change", 0.92))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _clarifying_state()
        result = await classifier.classify("I want to order a pizza", state, {})
        assert result == MessageType.TOPIC_CHANGE


class TestLLMConfidenceThreshold:
    @pytest.mark.asyncio
    async def test_high_confidence_returns_llm_result(self):
        llm = MockLLM(default_result=MockLLMResult("clarification_response", 0.7))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _clarifying_state()
        result = await classifier.classify("yes I want them", state, {})
        assert result == MessageType.CLARIFICATION_RESPONSE

    @pytest.mark.asyncio
    async def test_exact_threshold_returns_llm_result(self):
        llm = MockLLM(default_result=MockLLMResult("new_query", 0.7))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _clarifying_state()
        result = await classifier.classify("something", state, {})
        assert result == MessageType.NEW_QUERY

    @pytest.mark.asyncio
    async def test_below_threshold_falls_back_to_heuristic(self):
        llm = MockLLM(default_result=MockLLMResult("new_query", 0.69))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _clarifying_state()
        result = await classifier.classify("under $100", state, {})
        assert result == MessageType.CONSTRAINT_ADDITION

    @pytest.mark.asyncio
    async def test_very_low_confidence_falls_back(self):
        llm = MockLLM(default_result=MockLLMResult("topic_change", 0.1))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _clarifying_state()
        result = await classifier.classify("yes", state, {})
        assert result == MessageType.CLARIFICATION_RESPONSE

    @pytest.mark.asyncio
    async def test_zero_confidence_falls_back(self):
        llm = MockLLM(default_result=MockLLMResult("new_query", 0.0))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _clarifying_state()
        result = await classifier.classify("under $100", state, {})
        assert result == MessageType.CONSTRAINT_ADDITION


class TestLLMLabelMapping:
    @pytest.mark.asyncio
    async def test_all_valid_labels_mapped(self):
        labels = [
            ("new_query", MessageType.NEW_QUERY),
            ("clarification_response", MessageType.CLARIFICATION_RESPONSE),
            ("constraint_addition", MessageType.CONSTRAINT_ADDITION),
            ("topic_change", MessageType.TOPIC_CHANGE),
        ]
        for label, expected_type in labels:
            llm = MockLLM(default_result=MockLLMResult(label, 0.9))
            classifier = MessageClassifier(intent_classifier=llm)
            state = _clarifying_state()
            result = await classifier.classify("test message", state, {})
            assert result == expected_type, f"Label '{label}' should map to {expected_type}"

    @pytest.mark.asyncio
    async def test_unknown_label_falls_back_to_heuristic(self):
        llm = MockLLM(default_result=MockLLMResult("unknown_label", 0.9))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _clarifying_state()
        result = await classifier.classify("under $100", state, {})
        assert result == MessageType.CONSTRAINT_ADDITION


class TestLLMPromptConstruction:
    @pytest.mark.asyncio
    async def test_prompt_contains_original_query(self):
        llm = MockLLM(default_result=MockLLMResult("new_query", 0.8))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _clarifying_state()
        await classifier.classify("test", state, {"extra": "context"})
        assert len(llm.calls) == 1
        assert "running shoes" in llm.calls[0][0]
        assert "test" in llm.calls[0][0]

    @pytest.mark.asyncio
    async def test_prompt_contains_state_info(self):
        llm = MockLLM(default_result=MockLLMResult("new_query", 0.8))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _clarifying_state()
        await classifier.classify("hello", state)
        prompt = llm.calls[0][0]
        assert "CLARIFYING" in prompt or "clarifying" in prompt.lower()

    @pytest.mark.asyncio
    async def test_context_passed_to_llm(self):
        llm = MockLLM(default_result=MockLLMResult("new_query", 0.8))
        classifier = MessageClassifier(intent_classifier=llm)
        state = _clarifying_state()
        ctx = {"user_id": "123"}
        await classifier.classify("hello", state, ctx)
        assert llm.calls[0][1] == ctx


class TestLLMExceptionHandling:
    @pytest.mark.asyncio
    async def test_llm_exception_falls_back_gracefully(self):
        class ExceptionLLM:
            async def classify(self, prompt, context):
                raise ConnectionError("LLM service down")

        classifier = MessageClassifier(intent_classifier=ExceptionLLM())
        state = _clarifying_state()
        result = await classifier.classify("under $100", state)
        assert result == MessageType.CONSTRAINT_ADDITION

    @pytest.mark.asyncio
    async def test_llm_timeout_falls_back(self):
        class TimeoutLLM:
            async def classify(self, prompt, context):
                raise TimeoutError("LLM timed out")

        classifier = MessageClassifier(intent_classifier=TimeoutLLM())
        state = _clarifying_state()
        result = await classifier.classify("yes", state)
        assert isinstance(result, MessageType)
