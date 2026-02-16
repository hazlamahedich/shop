"""Unit tests for HandoffNotificationService.

Story 4-6: Handoff Notifications

Tests cover:
- Urgency detection logic (HIGH/MEDIUM/LOW)
- Notification content formatting
- Email rate limiting (24h per urgency level)
- IS_TESTING mode returns deterministic results
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.schemas.handoff import HandoffReason, UrgencyLevel, URGENCY_EMOJI
from app.services.handoff.notification_service import (
    HandoffNotificationService,
    HANDOFF_EMAIL_RATE_KEY,
    EMAIL_RATE_TTL,
    CHECKOUT_KEYWORD,
)


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

    async def delete(self, key: str):
        self.data.pop(key, None)
        self.expirations.pop(key, None)


@pytest.fixture
def mock_db():
    """Provide mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_redis():
    """Provide mock Redis client."""
    return MockRedis()


@pytest.fixture
def notification_service(mock_db, mock_redis):
    """Provide notification service with mocked dependencies."""
    return HandoffNotificationService(db=mock_db, redis=mock_redis)


class TestDetermineUrgency:
    """Tests for urgency level determination."""

    @pytest.mark.asyncio
    async def test_urgency_low_for_keyword(self, notification_service, monkeypatch):
        """Test keyword handoff reason returns LOW urgency."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        urgency = await notification_service.determine_urgency(
            handoff_reason=HandoffReason.KEYWORD,
            recent_messages=None,
        )
        assert urgency == UrgencyLevel.LOW
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_urgency_medium_for_low_confidence(self, notification_service, monkeypatch):
        """Test low_confidence handoff reason returns MEDIUM urgency."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        urgency = await notification_service.determine_urgency(
            handoff_reason=HandoffReason.LOW_CONFIDENCE,
            recent_messages=None,
        )
        assert urgency == UrgencyLevel.MEDIUM
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_urgency_medium_for_clarification_loop(self, notification_service, monkeypatch):
        """Test clarification_loop handoff reason returns MEDIUM urgency."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        urgency = await notification_service.determine_urgency(
            handoff_reason=HandoffReason.CLARIFICATION_LOOP,
            recent_messages=None,
        )
        assert urgency == UrgencyLevel.MEDIUM
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_urgency_high_with_checkout_context(self, notification_service, monkeypatch):
        """Test HIGH urgency when 'checkout' mentioned in recent messages."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        recent_messages = [
            "I want to buy these shoes",
            "How do I proceed to checkout?",
            "Can I talk to someone?",
        ]

        urgency = await notification_service.determine_urgency(
            handoff_reason=HandoffReason.KEYWORD,
            recent_messages=recent_messages,
        )
        assert urgency == UrgencyLevel.HIGH
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_urgency_high_with_checkout_case_insensitive(
        self, notification_service, monkeypatch
    ):
        """Test HIGH urgency with case-insensitive 'checkout' detection."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        recent_messages = [
            "I'm stuck at CHECKOUT",
            "Please help",
        ]

        urgency = await notification_service.determine_urgency(
            handoff_reason=HandoffReason.KEYWORD,
            recent_messages=recent_messages,
        )
        assert urgency == UrgencyLevel.HIGH
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_urgency_high_overrides_medium_reason(self, notification_service, monkeypatch):
        """Test HIGH urgency overrides MEDIUM reason when checkout mentioned."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        recent_messages = ["I can't complete the checkout"]

        urgency = await notification_service.determine_urgency(
            handoff_reason=HandoffReason.LOW_CONFIDENCE,
            recent_messages=recent_messages,
        )
        assert urgency == UrgencyLevel.HIGH
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_urgency_high_only_last_three_messages(self, notification_service, monkeypatch):
        """Test only last 3 messages are checked for checkout context."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        recent_messages = [
            "I want to checkout",
            "Message 2",
            "Message 3",
            "Message 4",
            "Message 5 without keyword",
        ]

        urgency = await notification_service.determine_urgency(
            handoff_reason=HandoffReason.KEYWORD,
            recent_messages=recent_messages,
        )
        assert urgency == UrgencyLevel.LOW
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_urgency_string_reason_keyword(self, notification_service, monkeypatch):
        """Test string reason 'keyword' returns LOW urgency."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        urgency = await notification_service.determine_urgency(
            handoff_reason="keyword",
            recent_messages=None,
        )
        assert urgency == UrgencyLevel.LOW
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_urgency_string_reason_low_confidence(self, notification_service, monkeypatch):
        """Test string reason 'low_confidence' returns MEDIUM urgency."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        urgency = await notification_service.determine_urgency(
            handoff_reason="low_confidence",
            recent_messages=None,
        )
        assert urgency == UrgencyLevel.MEDIUM
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_urgency_none_reason_returns_low(self, notification_service, monkeypatch):
        """Test None reason returns LOW urgency (default)."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        urgency = await notification_service.determine_urgency(
            handoff_reason=None,
            recent_messages=None,
        )
        assert urgency == UrgencyLevel.LOW
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_urgency_empty_recent_messages(self, notification_service, monkeypatch):
        """Test empty recent messages list works correctly."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        urgency = await notification_service.determine_urgency(
            handoff_reason=HandoffReason.LOW_CONFIDENCE,
            recent_messages=[],
        )
        assert urgency == UrgencyLevel.MEDIUM
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_is_testing_returns_low(self, mock_db):
        """Test IS_TESTING=true returns LOW urgency."""
        settings.cache_clear()
        os.environ["IS_TESTING"] = "true"
        settings.cache_clear()

        service = HandoffNotificationService(db=mock_db, redis=None)
        urgency = await service.determine_urgency(
            handoff_reason=HandoffReason.LOW_CONFIDENCE,
            recent_messages=["I need help with checkout"],
        )
        assert urgency == UrgencyLevel.LOW

        os.environ["IS_TESTING"] = "false"
        settings.cache_clear()


class TestFormatNotificationContent:
    """Tests for notification content formatting."""

    def test_format_content_basic(self, notification_service):
        """Test basic notification content formatting."""
        content = notification_service.format_notification_content(
            customer_name="John Doe",
            customer_id="psid_123",
            conversation_preview=["Hello", "I need help", "Thank you"],
            wait_time_seconds=125,
            handoff_reason="keyword",
            urgency=UrgencyLevel.LOW,
        )

        assert content["customer_name"] == "John Doe"
        assert content["customer_id"] == "psid_123"
        assert len(content["conversation_preview"]) == 3
        assert content["wait_time_seconds"] == 125
        assert content["handoff_reason"] == "keyword"
        assert content["urgency"] == "low"
        assert content["urgency_emoji"] == "🟢"

    def test_format_content_high_urgency(self, notification_service):
        """Test HIGH urgency uses correct emoji."""
        content = notification_service.format_notification_content(
            customer_name="Jane",
            customer_id="psid_456",
            conversation_preview=["Help with checkout"],
            wait_time_seconds=30,
            handoff_reason="low_confidence",
            urgency=UrgencyLevel.HIGH,
        )

        assert content["urgency"] == "high"
        assert content["urgency_emoji"] == "🔴"
        assert content["urgency_label"] == "HIGH"

    def test_format_content_medium_urgency(self, notification_service):
        """Test MEDIUM urgency uses correct emoji."""
        content = notification_service.format_notification_content(
            customer_name="Bob",
            customer_id="psid_789",
            conversation_preview=["Question"],
            wait_time_seconds=60,
            handoff_reason="clarification_loop",
            urgency=UrgencyLevel.MEDIUM,
        )

        assert content["urgency"] == "medium"
        assert content["urgency_emoji"] == "🟡"

    def test_format_content_no_customer_name(self, notification_service):
        """Test fallback to customer_id when no name."""
        content = notification_service.format_notification_content(
            customer_name=None,
            customer_id="psid_999",
            conversation_preview=["Hi"],
            wait_time_seconds=10,
            handoff_reason="keyword",
            urgency=UrgencyLevel.LOW,
        )

        assert content["customer_name"] == "psid_999"

    def test_format_content_no_name_or_id(self, notification_service):
        """Test fallback to 'Unknown Customer' when no name or ID."""
        content = notification_service.format_notification_content(
            customer_name=None,
            customer_id=None,
            conversation_preview=["Hi"],
            wait_time_seconds=10,
            handoff_reason="keyword",
            urgency=UrgencyLevel.LOW,
        )

        assert content["customer_name"] == "Unknown Customer"

    def test_format_content_wait_time_display(self, notification_service):
        """Test wait time display formatting."""
        content = notification_service.format_notification_content(
            customer_name="Test",
            customer_id="test_id",
            conversation_preview=["Hi"],
            wait_time_seconds=90,
            handoff_reason="keyword",
            urgency=UrgencyLevel.LOW,
        )

        assert content["wait_time_display"] == "1m 30s"

    def test_format_content_wait_time_under_minute(self, notification_service):
        """Test wait time display for under 1 minute."""
        content = notification_service.format_notification_content(
            customer_name="Test",
            customer_id="test_id",
            conversation_preview=["Hi"],
            wait_time_seconds=45,
            handoff_reason="keyword",
            urgency=UrgencyLevel.LOW,
        )

        assert content["wait_time_display"] == "45s"

    def test_format_content_truncates_long_messages(self, notification_service):
        """Test long messages are truncated in preview."""
        long_msg = "x" * 150
        content = notification_service.format_notification_content(
            customer_name="Test",
            customer_id="test_id",
            conversation_preview=[long_msg],
            wait_time_seconds=10,
            handoff_reason="keyword",
            urgency=UrgencyLevel.LOW,
        )

        assert "..." in content["preview_text"]

    def test_format_content_limits_to_three_messages(self, notification_service):
        """Test only last 3 messages are included in preview."""
        content = notification_service.format_notification_content(
            customer_name="Test",
            customer_id="test_id",
            conversation_preview=["msg1", "msg2", "msg3", "msg4", "msg5"],
            wait_time_seconds=10,
            handoff_reason="keyword",
            urgency=UrgencyLevel.LOW,
        )

        assert len(content["conversation_preview"]) == 3
        assert content["conversation_preview"] == ["msg3", "msg4", "msg5"]


class TestSendNotifications:
    """Tests for multi-channel notification dispatch."""

    @pytest.mark.asyncio
    async def test_send_notifications_dashboard_success(self, notification_service, monkeypatch):
        """Test dashboard notification succeeds."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        content = notification_service.format_notification_content(
            customer_name="Test",
            customer_id="test_id",
            conversation_preview=["Help"],
            wait_time_seconds=30,
            handoff_reason="keyword",
            urgency=UrgencyLevel.LOW,
        )

        result = await notification_service.send_notifications(
            merchant_id=1,
            conversation_id=100,
            urgency=UrgencyLevel.LOW,
            notification_content=content,
            email_provider=None,
        )

        assert result["dashboard"] is True
        assert result["email"] is False
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_send_notifications_with_email(
        self, notification_service, mock_redis, monkeypatch
    ):
        """Test both dashboard and email notifications sent."""
        settings.cache_clear()
        monkeypatch.setenv("IS_TESTING", "false")
        settings.cache_clear()

        mock_email_provider = AsyncMock()
        mock_email_provider.send.return_value = True

        content = notification_service.format_notification_content(
            customer_name="Test",
            customer_id="test_id",
            conversation_preview=["Help"],
            wait_time_seconds=30,
            handoff_reason="keyword",
            urgency=UrgencyLevel.MEDIUM,
        )

        result = await notification_service.send_notifications(
            merchant_id=1,
            conversation_id=100,
            urgency=UrgencyLevel.MEDIUM,
            notification_content=content,
            email_provider=mock_email_provider,
        )

        assert result["dashboard"] is True
        assert result["email"] is True
        mock_email_provider.send.assert_called_once()
        settings.cache_clear()

    @pytest.mark.asyncio
    async def test_send_notifications_is_testing(self, mock_db):
        """Test IS_TESTING returns success without sending."""
        settings.cache_clear()
        os.environ["IS_TESTING"] = "true"
        settings.cache_clear()

        service = HandoffNotificationService(db=mock_db, redis=None)

        result = await service.send_notifications(
            merchant_id=1,
            conversation_id=100,
            urgency=UrgencyLevel.LOW,
            notification_content={},
            email_provider=None,
        )

        assert result["dashboard"] is True
        assert result["email"] is True

        os.environ["IS_TESTING"] = "false"
        settings.cache_clear()


class TestEmailRateLimiting:
    """Tests for email rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_can_send_email_initial(self, notification_service):
        """Test can send email when not rate limited."""
        can_send = await notification_service._can_send_email(
            merchant_id=1,
            urgency=UrgencyLevel.LOW,
        )
        assert can_send is True

    @pytest.mark.asyncio
    async def test_cannot_send_email_when_rate_limited(self, notification_service, mock_redis):
        """Test cannot send email when rate limited."""
        redis_key = HANDOFF_EMAIL_RATE_KEY.format(merchant_id=1, urgency="low")
        mock_redis.data[redis_key] = "2026-02-14T10:00:00"

        can_send = await notification_service._can_send_email(
            merchant_id=1,
            urgency=UrgencyLevel.LOW,
        )
        assert can_send is False

    @pytest.mark.asyncio
    async def test_different_urgency_not_rate_limited(self, notification_service, mock_redis):
        """Test different urgency level is not rate limited."""
        redis_key = HANDOFF_EMAIL_RATE_KEY.format(merchant_id=1, urgency="low")
        mock_redis.data[redis_key] = "2026-02-14T10:00:00"

        can_send_high = await notification_service._can_send_email(
            merchant_id=1,
            urgency=UrgencyLevel.HIGH,
        )
        assert can_send_high is True

        can_send_medium = await notification_service._can_send_email(
            merchant_id=1,
            urgency=UrgencyLevel.MEDIUM,
        )
        assert can_send_medium is True

    @pytest.mark.asyncio
    async def test_mark_email_sent(self, notification_service, mock_redis):
        """Test marking email as sent sets rate limit key."""
        await notification_service._mark_email_sent(
            merchant_id=1,
            urgency=UrgencyLevel.LOW,
        )

        redis_key = HANDOFF_EMAIL_RATE_KEY.format(merchant_id=1, urgency="low")
        assert redis_key in mock_redis.data
        assert mock_redis.expirations.get(redis_key) == EMAIL_RATE_TTL

    @pytest.mark.asyncio
    async def test_can_send_without_redis(self, mock_db):
        """Test can send email when Redis is not available."""
        service = HandoffNotificationService(db=mock_db, redis=None)

        can_send = await service._can_send_email(
            merchant_id=1,
            urgency=UrgencyLevel.LOW,
        )
        assert can_send is True

    @pytest.mark.asyncio
    async def test_mark_email_sent_without_redis(self, mock_db):
        """Test mark email sent is safe without Redis."""
        service = HandoffNotificationService(db=mock_db, redis=None)

        await service._mark_email_sent(
            merchant_id=1,
            urgency=UrgencyLevel.LOW,
        )


class TestBuildEmailMessage:
    """Tests for email message building."""

    def test_build_email_message_includes_all_content(self, notification_service):
        """Test email message includes all required content."""
        content = {
            "urgency_emoji": "🔴",
            "urgency_label": "HIGH",
            "customer_name": "John Doe",
            "wait_time_display": "2m 30s",
            "handoff_reason": "checkout_blocked",
            "preview_text": "  - I need help\n  - With checkout",
        }

        message = notification_service._build_email_message(content)

        assert "🔴" in message
        assert "HIGH" in message
        assert "John Doe" in message
        assert "2m 30s" in message
        assert "checkout_blocked" in message
        assert "I need help" in message

    def test_build_email_message_customer_needs_help(self, notification_service):
        """Test email message has correct subject line."""
        content = {
            "urgency_emoji": "🟡",
            "urgency_label": "MEDIUM",
            "customer_name": "Test",
            "wait_time_display": "30s",
            "handoff_reason": "low_confidence",
            "preview_text": "",
        }

        message = notification_service._build_email_message(content)

        assert "Customer Needs Help" in message
        assert "MEDIUM Priority" in message


class TestUrgencyEmoji:
    """Tests for urgency emoji mapping."""

    def test_high_emoji_is_red_circle(self):
        """Test HIGH urgency has red circle emoji."""
        assert URGENCY_EMOJI[UrgencyLevel.HIGH] == "🔴"

    def test_medium_emoji_is_yellow_circle(self):
        """Test MEDIUM urgency has yellow circle emoji."""
        assert URGENCY_EMOJI[UrgencyLevel.MEDIUM] == "🟡"

    def test_low_emoji_is_green_circle(self):
        """Test LOW urgency has green circle emoji."""
        assert URGENCY_EMOJI[UrgencyLevel.LOW] == "🟢"


class TestConstants:
    """Tests for module constants."""

    def test_checkout_keyword_constant(self):
        """Test checkout keyword is correctly defined."""
        assert CHECKOUT_KEYWORD == "checkout"

    def test_email_rate_ttl_is_24_hours(self):
        """Test email rate limit TTL is 24 hours in seconds."""
        assert EMAIL_RATE_TTL == 86400
