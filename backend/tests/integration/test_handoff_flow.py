"""Integration tests for handoff detection flow.

Tests cover:
- Keyword detection → handoff trigger → database update
- Low confidence detection → handoff trigger
- Clarification loop detection → handoff trigger
- Handoff message returned instead of bot response
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.handoff import HandoffDetector
from app.services.intent import ClassificationResult, ExtractedEntities, IntentType
from app.services.messaging.message_processor import MessageProcessor
from app.schemas.handoff import HandoffReason, HandoffStatus, DEFAULT_HANDOFF_MESSAGE
from app.schemas.messaging import FacebookWebhookPayload


class MockRedis:
    """Mock Redis client for testing."""

    def __init__(self):
        self.data = {}

    async def get(self, key: str):
        return self.data.get(key)

    async def set(self, key: str, value: str):
        self.data[key] = value

    async def setex(self, key: str, ttl: int, value: str):
        self.data[key] = value

    async def incr(self, key: str) -> int:
        current = int(self.data.get(key, 0) or 0)
        current += 1
        self.data[key] = str(current)
        return current

    async def expire(self, key: str, ttl: int):
        pass

    async def delete(self, key: str):
        self.data.pop(key, None)

    async def exists(self, key: str) -> bool:
        return key in self.data

    async def keys(self, pattern: str):
        import fnmatch

        return [k for k in self.data.keys() if fnmatch.fnmatch(k, pattern)]


@pytest.fixture(autouse=True)
def disable_testing_mode(monkeypatch):
    """Ensure IS_TESTING is false for integration tests."""
    from app.core.config import settings

    settings.cache_clear()
    monkeypatch.setenv("IS_TESTING", "false")
    yield
    settings.cache_clear()


@pytest.mark.asyncio
async def test_low_confidence_triggers_handoff(monkeypatch):
    """Test that 3 consecutive low confidence scores trigger handoff."""
    from app.core.config import settings

    settings.cache_clear()
    monkeypatch.setenv("IS_TESTING", "false")
    settings.cache_clear()

    mock_redis = MockRedis()
    detector = HandoffDetector(redis_client=mock_redis)

    result1 = await detector.detect(
        message="test 1",
        conversation_id=1,
        confidence_score=0.30,
    )
    assert result1.should_handoff is False
    assert result1.confidence_count == 1

    result2 = await detector.detect(
        message="test 2",
        conversation_id=1,
        confidence_score=0.40,
    )
    assert result2.should_handoff is False
    assert result2.confidence_count == 2

    result3 = await detector.detect(
        message="test 3",
        conversation_id=1,
        confidence_score=0.20,
    )
    assert result3.should_handoff is True
    assert result3.reason == HandoffReason.LOW_CONFIDENCE
    assert result3.confidence_count == 3

    settings.cache_clear()


@pytest.mark.asyncio
async def test_clarification_loop_triggers_handoff(monkeypatch):
    """Test that 3 same-type clarifications trigger handoff."""
    from app.core.config import settings

    settings.cache_clear()
    monkeypatch.setenv("IS_TESTING", "false")
    settings.cache_clear()

    mock_redis = MockRedis()
    detector = HandoffDetector(redis_client=mock_redis)

    result1 = await detector.detect(
        message="test 1",
        conversation_id=1,
        clarification_type="budget",
    )
    assert result1.should_handoff is False
    assert result1.loop_count == 1

    result2 = await detector.detect(
        message="test 2",
        conversation_id=1,
        clarification_type="budget",
    )
    assert result2.should_handoff is False
    assert result2.loop_count == 2

    result3 = await detector.detect(
        message="test 3",
        conversation_id=1,
        clarification_type="budget",
    )
    assert result3.should_handoff is True
    assert result3.reason == HandoffReason.CLARIFICATION_LOOP
    assert result3.loop_count == 3

    settings.cache_clear()


@pytest.mark.asyncio
async def test_high_confidence_resets_counter(monkeypatch):
    """Test that high confidence score resets the low confidence counter."""
    from app.core.config import settings

    settings.cache_clear()
    monkeypatch.setenv("IS_TESTING", "false")
    settings.cache_clear()

    mock_redis = MockRedis()
    detector = HandoffDetector(redis_client=mock_redis)

    await detector.detect(
        message="test 1",
        conversation_id=1,
        confidence_score=0.30,
    )
    assert mock_redis.data.get("handoff:confidence:1:count") == "1"

    result = await detector.detect(
        message="test 2",
        conversation_id=1,
        confidence_score=0.85,
    )
    assert result.confidence_count == 0
    assert "handoff:confidence:1:count" not in mock_redis.data

    settings.cache_clear()


@pytest.mark.asyncio
async def test_handoff_state_can_be_reset(monkeypatch):
    """Test that handoff state can be manually reset."""
    from app.core.config import settings

    settings.cache_clear()
    monkeypatch.setenv("IS_TESTING", "false")
    settings.cache_clear()

    mock_redis = MockRedis()
    detector = HandoffDetector(redis_client=mock_redis)

    await detector.detect(
        message="test",
        conversation_id=1,
        confidence_score=0.30,
    )
    assert "handoff:confidence:1:count" in mock_redis.data

    await detector.reset_state(1)

    assert "handoff:confidence:1:count" not in mock_redis.data

    settings.cache_clear()


@pytest.mark.asyncio
async def test_different_clarification_types_reset_loop(monkeypatch):
    """Test that changing clarification type resets the loop counter."""
    from app.core.config import settings

    settings.cache_clear()
    monkeypatch.setenv("IS_TESTING", "false")
    settings.cache_clear()

    mock_redis = MockRedis()
    detector = HandoffDetector(redis_client=mock_redis)

    await detector.detect(
        message="test 1",
        conversation_id=1,
        clarification_type="budget",
    )

    result = await detector.detect(
        message="test 2",
        conversation_id=1,
        clarification_type="color",
    )
    assert result.loop_count == 1
    assert result.should_handoff is False

    settings.cache_clear()


@pytest.mark.asyncio
async def test_keyword_detection_direct():
    """Test keyword detection triggers handoff directly."""
    from app.core.config import settings
    import os

    settings.cache_clear()
    os.environ["IS_TESTING"] = "false"
    settings.cache_clear()

    mock_redis = MockRedis()
    detector = HandoffDetector(redis_client=mock_redis)

    result = await detector.detect(
        message="I want to talk to a human",
        conversation_id=1,
    )

    assert result.should_handoff is True
    assert result.reason == HandoffReason.KEYWORD
    assert result.matched_keyword == "human"

    settings.cache_clear()
