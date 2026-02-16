"""Tests for HandoffFlowService.

Story 4-6: Handoff Notifications

Tests the handoff flow orchestrator that connects:
- HandoffDetector (detection)
- HandoffAlert (database storage)
- HandoffNotificationService (notifications)
"""

from __future__ import annotations

from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.handoff import HandoffReason, HandoffResult, UrgencyLevel


class MockRedis:
    """Mock Redis client for testing."""

    def __init__(self):
        self.data = {}

    async def get(self, key: str):
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.data[key] = value

    async def incr(self, key: str) -> int:
        current = int(self.data.get(key, 0) or 0) + 1
        self.data[key] = str(current)
        return current

    async def expire(self, key: str, ttl: int):
        pass

    async def delete(self, key: str):
        self.data.pop(key, None)

    async def setex(self, key: str, ttl: int, value: str):
        self.data[key] = value


class MockMessage:
    """Mock Message model."""

    def __init__(self, content: str, role: str = "user"):
        self.content = content
        self.role = role


class MockConversation:
    """Mock Conversation model."""

    def __init__(
        self,
        id: int = 1,
        merchant_id: int = 1,
        platform_sender_id: str = "psid_123",
        handoff_reason: str | None = None,
        messages: list | None = None,
    ):
        self.id = id
        self.merchant_id = merchant_id
        self.platform_sender_id = platform_sender_id
        self.handoff_reason = handoff_reason
        self.messages = messages or []
        self.customer_name = None


class MockDetector:
    """Mock HandoffDetector."""

    def __init__(self, should_handoff: bool = False, reason: HandoffReason | None = None):
        self._should_handoff = should_handoff
        self._reason = reason

    async def detect(
        self,
        message: str,
        conversation_id: int,
        confidence_score: float | None = None,
        clarification_type: str | None = None,
    ) -> HandoffResult:
        return HandoffResult(
            should_handoff=self._should_handoff,
            reason=self._reason,
        )


class MockHandoffAlert:
    """Mock HandoffAlert model."""

    _id_counter = 0

    def __init__(
        self,
        merchant_id: int = 1,
        conversation_id: int = 1,
        urgency_level: str = "low",
    ):
        MockHandoffAlert._id_counter += 1
        self.id = MockHandoffAlert._id_counter
        self.merchant_id = merchant_id
        self.conversation_id = conversation_id
        self.urgency_level = urgency_level
        self.is_read = False
        self.created_at = datetime.now(UTC)


class TestHandoffFlowService:
    """Tests for HandoffFlowService."""

    @pytest.mark.asyncio
    async def test_no_handoff_when_detector_returns_false(self, monkeypatch):
        """Test that no action is taken when detector returns should_handoff=False."""
        from app.services.handoff.handoff_flow_service import HandoffFlowService

        mock_db = AsyncMock()
        mock_redis = MockRedis()
        mock_detector = MockDetector(should_handoff=False, reason=None)

        service = HandoffFlowService(
            db=mock_db,
            redis=mock_redis,
            detector=mock_detector,
        )

        conversation = MockConversation()
        result = await service.process_handoff(
            conversation=conversation,
            message="Hello",
            confidence_score=0.8,
        )

        assert result.should_handoff is False
        assert mock_db.add.call_count == 0

    @pytest.mark.asyncio
    async def test_creates_alert_on_handoff_keyword(self, monkeypatch):
        """Test that HandoffAlert is created when handoff is triggered."""
        from app.services.handoff.handoff_flow_service import HandoffFlowService
        from app.core.config import settings

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        created_alerts = []

        def mock_add(obj):
            """Sync function to track created alerts."""
            obj.id = len(created_alerts) + 1
            created_alerts.append(obj)

        mock_db = AsyncMock()
        mock_db.add = mock_add  # db.add is sync, not async
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_redis = MockRedis()
        mock_detector = MockDetector(should_handoff=True, reason=HandoffReason.KEYWORD)

        service = HandoffFlowService(
            db=mock_db,
            redis=mock_redis,
            detector=mock_detector,
        )

        conversation = MockConversation(messages=[MockMessage("I need a human")])
        result = await service.process_handoff(
            conversation=conversation,
            message="I need a human",
        )

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "true")

        assert result.should_handoff is True
        assert result.reason == HandoffReason.KEYWORD
        assert len(created_alerts) == 1
        assert created_alerts[0].urgency_level == "low"

    @pytest.mark.asyncio
    async def test_high_urgency_with_checkout_context(self, monkeypatch):
        """Test that checkout context results in HIGH urgency alert."""
        from app.services.handoff.handoff_flow_service import HandoffFlowService
        from app.core.config import settings

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        created_alerts = []

        def mock_add(obj):
            """Sync function to track created alerts."""
            obj.id = len(created_alerts) + 1
            created_alerts.append(obj)

        mock_db = AsyncMock()
        mock_db.add = mock_add  # db.add is sync, not async
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_redis = MockRedis()
        mock_detector = MockDetector(should_handoff=True, reason=HandoffReason.KEYWORD)

        service = HandoffFlowService(
            db=mock_db,
            redis=mock_redis,
            detector=mock_detector,
        )

        conversation = MockConversation(
            messages=[
                MockMessage("I want to buy this"),
                MockMessage("How do I checkout?"),
                MockMessage("Help me!"),
            ]
        )

        result = await service.process_handoff(
            conversation=conversation,
            message="I need a human",
        )

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "true")

        assert result.should_handoff is True
        assert len(created_alerts) == 1
        assert created_alerts[0].urgency_level == "high"

    @pytest.mark.asyncio
    async def test_medium_urgency_with_low_confidence(self, monkeypatch):
        """Test that low_confidence reason results in MEDIUM urgency."""
        from app.services.handoff.handoff_flow_service import HandoffFlowService
        from app.core.config import settings

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        created_alerts = []

        def mock_add(obj):
            """Sync function to track created alerts."""
            obj.id = len(created_alerts) + 1
            created_alerts.append(obj)

        mock_db = AsyncMock()
        mock_db.add = mock_add  # db.add is sync, not async
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        mock_redis = MockRedis()
        mock_detector = MockDetector(should_handoff=True, reason=HandoffReason.LOW_CONFIDENCE)

        service = HandoffFlowService(
            db=mock_db,
            redis=mock_redis,
            detector=mock_detector,
        )

        conversation = MockConversation()
        result = await service.process_handoff(
            conversation=conversation,
            message="I'm confused",
            confidence_score=0.3,
        )

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "true")

        assert result.should_handoff is True
        assert len(created_alerts) == 1
        assert created_alerts[0].urgency_level == "medium"

    @pytest.mark.asyncio
    async def test_is_testing_mode_skips_alert_creation(self, monkeypatch):
        """Test that IS_TESTING mode skips alert creation."""
        from app.services.handoff.handoff_flow_service import HandoffFlowService

        monkeypatch.setenv("IS_TESTING", "true")

        mock_db = AsyncMock()
        mock_redis = MockRedis()
        mock_detector = MockDetector(should_handoff=True, reason=HandoffReason.KEYWORD)

        service = HandoffFlowService(
            db=mock_db,
            redis=mock_redis,
            detector=mock_detector,
        )

        conversation = MockConversation()
        result = await service.process_handoff(
            conversation=conversation,
            message="I need a human",
        )

        assert result.should_handoff is True
        assert mock_db.add.call_count == 0


class TestGetRecentMessages:
    """Tests for _get_recent_messages helper."""

    @pytest.mark.asyncio
    async def test_returns_last_three_messages(self):
        """Test that only last 3 messages are returned."""
        from app.services.handoff.handoff_flow_service import HandoffFlowService

        mock_db = AsyncMock()
        service = HandoffFlowService(db=mock_db, redis=None)

        conversation = MockConversation(
            messages=[
                MockMessage("Message 1"),
                MockMessage("Message 2"),
                MockMessage("Message 3"),
                MockMessage("Message 4"),
                MockMessage("Message 5"),
            ]
        )

        result = await service._get_recent_messages(conversation, limit=3)

        assert len(result) == 3
        assert result == ["Message 3", "Message 4", "Message 5"]

    @pytest.mark.asyncio
    async def test_handles_empty_messages(self):
        """Test handling of conversation with no messages."""
        from app.services.handoff.handoff_flow_service import HandoffFlowService

        mock_db = AsyncMock()
        service = HandoffFlowService(db=mock_db, redis=None)

        conversation = MockConversation(messages=[])
        result = await service._get_recent_messages(conversation)

        assert result == []
