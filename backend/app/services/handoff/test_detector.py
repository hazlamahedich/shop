"""Unit tests for HandoffDetector service.

Tests cover:
- Keyword detection with various case/whitespace combinations
- Keyword detection does NOT trigger on partial matches
- Confidence counter increment/reset logic
- Clarification loop state tracking
- IS_TESTING mode returns deterministic results
"""

from __future__ import annotations

import json
import os

import pytest

from app.core.config import settings
from app.schemas.handoff import HandoffReason
from app.services.handoff.detector import (
    HANDOFF_KEYWORDS,
    HandoffDetector,
)


class MockRedis:
    """Mock Redis client for testing."""

    def __init__(self):
        self.data = {}
        self.expirations = {}

    async def get(self, key: str):
        return self.data.get(key)

    async def set(self, key: str, value: str):
        self.data[key] = value

    async def setex(self, key: str, ttl: int, value: str):
        self.data[key] = value
        self.expirations[key] = ttl

    async def incr(self, key: str) -> int:
        current = int(self.data.get(key, 0) or 0)
        current += 1
        self.data[key] = str(current)
        return current

    async def expire(self, key: str, ttl: int):
        self.expirations[key] = ttl

    async def delete(self, key: str):
        self.data.pop(key, None)
        self.expirations.pop(key, None)


@pytest.fixture
def mock_redis():
    """Provide mock Redis client."""
    return MockRedis()


class TestKeywordDetection:
    """Tests for keyword-based handoff detection."""

    @pytest.mark.asyncio
    async def test_keyword_trigger_human(self, mock_redis, monkeypatch):
        """Test that 'human' triggers handoff."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="I want to talk to a human",
            conversation_id=1,
        )
        assert result.should_handoff is True
        assert result.reason == HandoffReason.KEYWORD
        assert result.matched_keyword == "human"
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_keyword_trigger_agent(self, mock_redis, monkeypatch):
        """Test that 'agent' triggers handoff."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="Can I speak to an agent?",
            conversation_id=1,
        )
        assert result.should_handoff is True
        assert result.reason == HandoffReason.KEYWORD
        assert result.matched_keyword == "agent"
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_keyword_trigger_case_insensitive(self, mock_redis, monkeypatch):
        """Test keyword detection is case-insensitive."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="I NEED A HUMAN PLEASE",
            conversation_id=1,
        )
        assert result.should_handoff is True
        assert result.reason == HandoffReason.KEYWORD
        assert result.matched_keyword == "human"
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_keyword_trigger_customer_service(self, mock_redis, monkeypatch):
        """Test 'customer service' multi-word keyword."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="Let me talk to customer service",
            conversation_id=1,
        )
        assert result.should_handoff is True
        assert result.reason == HandoffReason.KEYWORD
        assert result.matched_keyword == "customer service"
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_keyword_no_partial_match_humanity(self, mock_redis, monkeypatch):
        """Test 'humanity' does NOT trigger 'human' keyword."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="I love humanity and helping people",
            conversation_id=1,
        )
        assert result.should_handoff is False
        assert result.reason is None
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_keyword_no_partial_match_persona(self, mock_redis, monkeypatch):
        """Test 'persona' does NOT trigger 'person' keyword."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="I have a cool persona online",
            conversation_id=1,
        )
        assert result.should_handoff is False
        assert result.reason is None
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_keyword_no_partial_match_agency(self, mock_redis, monkeypatch):
        """Test 'agency' does NOT trigger 'agent' keyword."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="I work for an agency downtown",
            conversation_id=1,
        )
        assert result.should_handoff is False
        assert result.reason is None
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_keyword_with_punctuation(self, mock_redis, monkeypatch):
        """Test keyword detection works with punctuation."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="Help! I need a human!!!",
            conversation_id=1,
        )
        assert result.should_handoff is True
        assert result.reason == HandoffReason.KEYWORD
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_keyword_at_message_start(self, mock_redis, monkeypatch):
        """Test keyword at start of message."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="Human please help me",
            conversation_id=1,
        )
        assert result.should_handoff is True
        assert result.reason == HandoffReason.KEYWORD
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_keyword_at_message_end(self, mock_redis, monkeypatch):
        """Test keyword at end of message."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="Please connect me to human",
            conversation_id=1,
        )
        assert result.should_handoff is True
        assert result.reason == HandoffReason.KEYWORD
        settings.cache_clear()


class TestConfidenceDetection:
    """Tests for low confidence-based handoff detection."""

    @pytest.mark.asyncio
    async def test_confidence_increment_on_low(self, mock_redis, monkeypatch):
        """Test confidence counter increments on low score."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="test message",
            conversation_id=1,
            confidence_score=0.30,
        )
        assert result.should_handoff is False
        assert result.confidence_count == 1
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_confidence_reset_on_high(self, mock_redis, monkeypatch):
        """Test confidence counter resets on high score."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        mock_redis.data["handoff:confidence:1:count"] = "2"

        result = await detector.detect(
            message="test message",
            conversation_id=1,
            confidence_score=0.80,
        )
        assert result.should_handoff is False
        assert result.confidence_count == 0
        assert "handoff:confidence:1:count" not in mock_redis.data
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_confidence_trigger_at_threshold(self, mock_redis, monkeypatch):
        """Test handoff triggers after 3 consecutive low confidence scores."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result1 = await detector.detect(
            message="msg1",
            conversation_id=1,
            confidence_score=0.30,
        )
        assert result1.confidence_count == 1
        assert result1.should_handoff is False

        result2 = await detector.detect(
            message="msg2",
            conversation_id=1,
            confidence_score=0.40,
        )
        assert result2.confidence_count == 2
        assert result2.should_handoff is False

        result3 = await detector.detect(
            message="msg3",
            conversation_id=1,
            confidence_score=0.20,
        )
        assert result3.should_handoff is True
        assert result3.reason == HandoffReason.LOW_CONFIDENCE
        assert result3.confidence_count == 3
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_confidence_no_trigger_without_redis(self, monkeypatch):
        """Test confidence detection requires Redis for state."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=None)

        result = await detector.detect(
            message="test message",
            conversation_id=1,
            confidence_score=0.20,
        )
        assert result.should_handoff is False
        assert result.confidence_count == 0
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_confidence_no_trigger_when_none(self, mock_redis, monkeypatch):
        """Test no trigger when confidence score is None."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="test message",
            conversation_id=1,
            confidence_score=None,
        )
        assert result.should_handoff is False
        assert result.confidence_count == 0
        settings.cache_clear()


class TestClarificationLoopDetection:
    """Tests for clarification loop-based handoff detection."""

    @pytest.mark.asyncio
    async def test_loop_increment_same_type(self, mock_redis, monkeypatch):
        """Test loop counter increments for same clarification type."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="test",
            conversation_id=1,
            clarification_type="budget",
        )
        assert result.should_handoff is False
        assert result.loop_count == 1
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_loop_reset_on_different_type(self, mock_redis, monkeypatch):
        """Test loop counter resets when clarification type changes."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        state = {"type": "color", "count": 2}
        mock_redis.data["clarification:1:state"] = json.dumps(state)

        result = await detector.detect(
            message="test",
            conversation_id=1,
            clarification_type="size",
        )
        assert result.should_handoff is False
        assert result.loop_count == 1
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_loop_trigger_at_threshold(self, mock_redis, monkeypatch):
        """Test handoff triggers after 3 same-type clarifications."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result1 = await detector.detect(
            message="msg1",
            conversation_id=1,
            clarification_type="budget",
        )
        assert result1.loop_count == 1
        assert result1.should_handoff is False

        result2 = await detector.detect(
            message="msg2",
            conversation_id=1,
            clarification_type="budget",
        )
        assert result2.loop_count == 2
        assert result2.should_handoff is False

        result3 = await detector.detect(
            message="msg3",
            conversation_id=1,
            clarification_type="budget",
        )
        assert result3.should_handoff is True
        assert result3.reason == HandoffReason.CLARIFICATION_LOOP
        assert result3.loop_count == 3
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_loop_no_trigger_without_redis(self, monkeypatch):
        """Test loop detection requires Redis for state."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=None)

        result = await detector.detect(
            message="test",
            conversation_id=1,
            clarification_type="budget",
        )
        assert result.should_handoff is False
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_loop_no_trigger_when_none(self, mock_redis, monkeypatch):
        """Test no trigger when clarification type is None."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="test",
            conversation_id=1,
            clarification_type=None,
        )
        assert result.should_handoff is False
        settings.cache_clear()


class TestIsTestingMode:
    """Tests for IS_TESTING mode behavior."""

    @pytest.mark.asyncio
    async def test_is_testing_returns_no_handoff(self, mock_redis):
        """Test IS_TESTING=true returns no handoff."""
        settings.cache_clear()
        os.environ["IS_TESTING"] = "true"
        settings.cache_clear()

        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="I want to talk to a human",
            conversation_id=1,
        )
        assert result.should_handoff is False
        assert result.reason is None

        os.environ["IS_TESTING"] = "false"
        settings.cache_clear()


class TestResetState:
    """Tests for state reset functionality."""

    @pytest.mark.asyncio
    async def test_reset_state_clears_all(self, mock_redis, monkeypatch):
        """Test reset_state clears all handoff state."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        mock_redis.data["handoff:confidence:1:count"] = "2"
        mock_redis.data["clarification:1:state"] = json.dumps({"type": "budget", "count": 2})

        await detector.reset_state(1)

        assert "handoff:confidence:1:count" not in mock_redis.data
        assert "clarification:1:state" not in mock_redis.data
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_reset_state_no_redis(self, monkeypatch):
        """Test reset_state is safe without Redis."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=None)

        await detector.reset_state(1)
        settings.cache_clear()


class TestNoFalsePositives:
    """Tests ensuring no false positives on normal conversations."""

    @pytest.mark.asyncio
    async def test_normal_conversation_no_trigger(self, mock_redis, monkeypatch):
        """Test normal conversation does not trigger handoff."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        messages = [
            "Hello, I'm looking for shoes",
            "Do you have red ones?",
            "What's the price?",
            "Great, I'll take them!",
        ]

        for msg in messages:
            result = await detector.detect(
                message=msg,
                conversation_id=1,
                confidence_score=0.85,
            )
            assert result.should_handoff is False
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_no_trigger_on_partial_word_match(self, mock_redis, monkeypatch):
        """Test that 'managers' does NOT trigger 'manager' keyword (word boundaries)."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message="I'm looking for product managers at your company",
            conversation_id=1,
        )
        assert result.should_handoff is False
        assert result.reason is None
        settings.cache_clear()


class TestAllKeywords:
    """Test all defined keywords trigger handoff."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("keyword", HANDOFF_KEYWORDS)
    async def test_all_keywords_trigger(self, mock_redis, monkeypatch, keyword):
        """Test that each defined keyword triggers handoff."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()
        detector = HandoffDetector(redis_client=mock_redis)

        result = await detector.detect(
            message=f"I need a {keyword} please",
            conversation_id=1,
        )
        assert result.should_handoff is True
        assert result.reason == HandoffReason.KEYWORD
        settings.cache_clear()
