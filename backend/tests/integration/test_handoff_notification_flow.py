"""Integration tests for handoff notification flow.

Story 4-6: Handoff Notifications

Tests cover:
- Handoff triggers → alert appears in database
- Urgency detection integration
- Email notification integration
- End-to-end flow validation
"""

from __future__ import annotations

import json
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class MockRedis:
    """Mock Redis client for testing."""

    def __init__(self):
        self.data = {}
        self.expirations = {}

    async def get(self, key: str):
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.data[key] = value
        if ex:
            self.expirations[key] = ex

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


class MockConversation:
    """Mock Conversation model for testing."""

    def __init__(
        self,
        id: int = 1,
        merchant_id: int = 1,
        platform_sender_id: str = "psid_123",
        handoff_reason: str = "keyword",
    ):
        self.id = id
        self.merchant_id = merchant_id
        self.platform_sender_id = platform_sender_id
        self.handoff_reason = handoff_reason
        self.handoff_triggered_at = datetime.now(UTC)


class MockHandoffAlert:
    """Mock HandoffAlert model for testing."""

    def __init__(
        self,
        id: int = 1,
        merchant_id: int = 1,
        conversation_id: int = 1,
        urgency_level: str = "low",
    ):
        self.id = id
        self.merchant_id = merchant_id
        self.conversation_id = conversation_id
        self.urgency_level = urgency_level
        self.is_read = False


class TestUrgencyDetectionIntegration:
    """Tests for urgency detection with handoff reason."""

    @pytest.mark.asyncio
    async def test_keyword_handoff_produces_low_urgency(self, monkeypatch):
        """Test that keyword handoff reason produces LOW urgency."""
        from app.core.config import settings
        from app.services.handoff.notification_service import HandoffNotificationService
        from app.schemas.handoff import HandoffReason

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        mock_db = AsyncMock()
        service = HandoffNotificationService(db=mock_db, redis=None)

        urgency = await service.determine_urgency(
            handoff_reason=HandoffReason.KEYWORD,
            recent_messages=None,
        )

        assert urgency.value == "low"
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_low_confidence_produces_medium_urgency(self, monkeypatch):
        """Test that low_confidence handoff reason produces MEDIUM urgency."""
        from app.core.config import settings
        from app.services.handoff.notification_service import HandoffNotificationService
        from app.schemas.handoff import HandoffReason

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        mock_db = AsyncMock()
        service = HandoffNotificationService(db=mock_db, redis=None)

        urgency = await service.determine_urgency(
            handoff_reason=HandoffReason.LOW_CONFIDENCE,
            recent_messages=None,
        )

        assert urgency.value == "medium"
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_checkout_context_produces_high_urgency(self, monkeypatch):
        """Test that checkout context produces HIGH urgency."""
        from app.core.config import settings
        from app.services.handoff.notification_service import HandoffNotificationService
        from app.schemas.handoff import HandoffReason

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        mock_db = AsyncMock()
        service = HandoffNotificationService(db=mock_db, redis=None)

        urgency = await service.determine_urgency(
            handoff_reason=HandoffReason.KEYWORD,
            recent_messages=["I need help with my checkout"],
        )

        assert urgency.value == "high"
        settings.cache_clear()


class TestNotificationContentIntegration:
    """Tests for notification content formatting."""

    @pytest.mark.asyncio
    async def test_notification_content_includes_all_fields(self):
        """Test notification content includes all required fields."""
        from app.services.handoff.notification_service import HandoffNotificationService
        from app.schemas.handoff import UrgencyLevel

        mock_db = AsyncMock()
        service = HandoffNotificationService(db=mock_db, redis=None)

        content = service.format_notification_content(
            customer_name="John Doe",
            customer_id="psid_456",
            conversation_preview=["Hello", "I need help", "Thanks"],
            wait_time_seconds=90,
            handoff_reason="low_confidence",
            urgency=UrgencyLevel.MEDIUM,
        )

        assert content["customer_name"] == "John Doe"
        assert content["customer_id"] == "psid_456"
        assert len(content["conversation_preview"]) == 3
        assert content["wait_time_seconds"] == 90
        assert content["urgency"] == "medium"


class TestEmailRateLimitingIntegration:
    """Tests for email rate limiting across urgency levels."""

    @pytest.mark.asyncio
    async def test_different_urgency_allows_separate_emails(self):
        """Test that different urgency levels have separate rate limits."""
        from app.services.handoff.notification_service import HandoffNotificationService

        mock_redis = MockRedis()
        mock_db = AsyncMock()
        service = HandoffNotificationService(db=mock_db, redis=mock_redis)

        # Mark low urgency as sent
        await service._mark_email_sent(merchant_id=1, urgency="low")

        # Medium urgency should still be allowed
        can_send_medium = await service._can_send_email(merchant_id=1, urgency="medium")
        assert can_send_medium is True

        # High urgency should still be allowed
        can_send_high = await service._can_send_email(merchant_id=1, urgency="high")
        assert can_send_high is True

    @pytest.mark.asyncio
    async def test_same_urgency_blocked_after_send(self):
        """Test that same urgency level is blocked after sending."""
        from app.services.handoff.notification_service import HandoffNotificationService

        mock_redis = MockRedis()
        mock_db = AsyncMock()
        service = HandoffNotificationService(db=mock_db, redis=mock_redis)

        # Mark as sent
        await service._mark_email_sent(merchant_id=1, urgency="high")

        # Should be blocked
        can_send = await service._can_send_email(merchant_id=1, urgency="high")
        assert can_send is False


class TestEndToEndFlow:
    """Tests for end-to-end handoff notification flow."""

    @pytest.mark.asyncio
    async def test_handoff_flow_produces_correct_notification_data(self, monkeypatch):
        """Test that handoff flow produces correct notification data structure."""
        from app.core.config import settings
        from app.services.handoff.notification_service import HandoffNotificationService
        from app.schemas.handoff import HandoffReason, UrgencyLevel

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        mock_db = AsyncMock()
        mock_redis = MockRedis()
        service = HandoffNotificationService(db=mock_db, redis=mock_redis)

        # Step 1: Determine urgency
        urgency = await service.determine_urgency(
            handoff_reason=HandoffReason.CLARIFICATION_LOOP,
            recent_messages=["Help with product"],
        )
        assert urgency == UrgencyLevel.MEDIUM

        # Step 2: Format notification content
        content = service.format_notification_content(
            customer_name="Test Customer",
            customer_id="psid_test",
            conversation_preview=["Message 1", "Message 2"],
            wait_time_seconds=30,
            handoff_reason="clarification_loop",
            urgency=urgency,
        )

        # Step 3: Verify content structure
        assert content["urgency"] == "medium"
        assert content["urgency_emoji"] == "🟡"
        assert content["customer_name"] == "Test Customer"
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_high_urgency_with_checkout_context(self, monkeypatch):
        """Test complete flow for HIGH urgency with checkout context."""
        from app.core.config import settings
        from app.services.handoff.notification_service import HandoffNotificationService
        from app.schemas.handoff import HandoffReason, UrgencyLevel

        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        mock_db = AsyncMock()
        mock_redis = MockRedis()
        service = HandoffNotificationService(db=mock_db, redis=mock_redis)

        # Customer mentioned checkout
        recent_messages = [
            "I want to buy this product",
            "How do I proceed to checkout?",
            "I need help with my order",
        ]

        urgency = await service.determine_urgency(
            handoff_reason=HandoffReason.KEYWORD,
            recent_messages=recent_messages,
        )
        assert urgency == UrgencyLevel.HIGH

        content = service.format_notification_content(
            customer_name="Checkout Customer",
            customer_id="psid_checkout",
            conversation_preview=recent_messages,
            wait_time_seconds=10,
            handoff_reason="keyword",
            urgency=urgency,
        )

        assert content["urgency"] == "high"
        assert content["urgency_emoji"] == "🔴"
        assert content["urgency_label"] == "HIGH"
        settings.cache_clear()


class TestIS_TESTINGMode:
    """Tests for IS_TESTING mode behavior."""

    @pytest.mark.asyncio
    async def test_is_testing_returns_low_urgency(self):
        """Test IS_TESTING mode returns LOW urgency regardless of context."""
        import os
        from app.core.config import settings
        from app.services.handoff.notification_service import HandoffNotificationService
        from app.schemas.handoff import HandoffReason

        settings.cache_clear()
        os.environ["IS_TESTING"] = "true"
        settings.cache_clear()

        mock_db = AsyncMock()
        service = HandoffNotificationService(db=mock_db, redis=None)

        urgency = await service.determine_urgency(
            handoff_reason=HandoffReason.LOW_CONFIDENCE,
            recent_messages=["I need checkout help"],
        )

        assert urgency.value == "low"

        os.environ["IS_TESTING"] = "false"
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_is_testing_bypasses_notifications(self):
        """Test IS_TESTING mode bypasses notification sending."""
        import os
        from app.core.config import settings
        from app.services.handoff.notification_service import HandoffNotificationService
        from app.schemas.handoff import UrgencyLevel

        settings.cache_clear()
        os.environ["IS_TESTING"] = "true"
        settings.cache_clear()

        mock_db = AsyncMock()
        service = HandoffNotificationService(db=mock_db, redis=None)

        result = await service.send_notifications(
            merchant_id=1,
            conversation_id=1,
            urgency=UrgencyLevel.HIGH,
            notification_content={},
            email_provider=None,
        )

        assert result["dashboard"] is True
        assert result["email"] is True

        os.environ["IS_TESTING"] = "false"
        settings.cache_clear()
