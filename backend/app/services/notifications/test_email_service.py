"""Test email notification service.

Story 3-8: Budget Alert Notifications

Tests for email sending at:
- Warning (80%): "Budget Alert: 80% of your ${budget} budget used"
- Critical (95%): "Urgent: 95% of budget used - Action required"
- Hard Stop (100%): "Bot Paused: Budget limit reached"
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.notifications.email_service import (
    EmailNotificationProvider,
    NotificationError,
)


class MockRedis:
    """Mock Redis client for testing."""

    def __init__(self):
        self.data = {}

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self.data[key] = value
        return True

    async def delete(self, key: str) -> bool:
        if key in self.data:
            del self.data[key]
        return True


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    return MockRedis()


@pytest.fixture
def email_provider(mock_redis):
    """Create email provider with mock Redis."""
    return EmailNotificationProvider(redis_client=mock_redis)


class TestEmailRateLimiting:
    """Test email rate limiting functionality."""

    async def test_can_send_email_when_not_rate_limited(
        self,
        email_provider,
        mock_redis,
    ) -> None:
        """Test email can be sent when not rate limited."""
        can_send = await email_provider._can_send_email(1, "warning")
        assert can_send is True

    async def test_cannot_send_email_when_rate_limited(
        self,
        email_provider,
        mock_redis,
    ) -> None:
        """Test email blocked when rate limited."""
        await email_provider._mark_email_sent(1, "warning")

        can_send = await email_provider._can_send_email(1, "warning")
        assert can_send is False

    async def test_different_alert_levels_not_rate_limited(
        self,
        email_provider,
        mock_redis,
    ) -> None:
        """Test different alert levels have separate rate limits."""
        await email_provider._mark_email_sent(1, "warning")

        can_send_warning = await email_provider._can_send_email(1, "warning")
        can_send_critical = await email_provider._can_send_email(1, "critical")
        can_send_hard_stop = await email_provider._can_send_email(1, "hard_stop")

        assert can_send_warning is False
        assert can_send_critical is True
        assert can_send_hard_stop is True

    async def test_rate_limit_without_redis(self) -> None:
        """Test rate limiting returns True when no Redis."""
        provider = EmailNotificationProvider(redis_client=None)

        can_send = await provider._can_send_email(1, "warning")
        assert can_send is True


class TestTemplateContent:
    """Test email template content generation."""

    def test_warning_template_content(
        self,
        email_provider,
    ) -> None:
        """Test warning template has correct content."""
        subject, html = email_provider._get_template_content(
            "warning",
            80,
            Decimal("100.00"),
            Decimal("20.00"),
        )

        assert "80%" in subject
        assert "$100.00" in subject
        assert "80%" in html
        assert "$100.00" in html
        assert "$20.00" in html

    def test_critical_template_content(
        self,
        email_provider,
    ) -> None:
        """Test critical template has correct content."""
        subject, html = email_provider._get_template_content(
            "critical",
            95,
            Decimal("100.00"),
            Decimal("5.00"),
        )

        assert "95%" in subject
        assert "Urgent" in subject or "Action required" in subject
        assert "95%" in html

    def test_hard_stop_template_content(
        self,
        email_provider,
    ) -> None:
        """Test hard stop template has correct content."""
        subject, html = email_provider._get_template_content(
            "hard_stop",
            100,
            Decimal("100.00"),
            Decimal("0.00"),
        )

        assert "Paused" in subject or "limit reached" in subject
        assert "100%" in html

    def test_fallback_template_used(
        self,
        email_provider,
    ) -> None:
        """Test fallback template when file not found."""
        subject, html = email_provider._get_template_content(
            "unknown_level",
            80,
            Decimal("100.00"),
            Decimal("20.00"),
        )

        assert "80%" in html
        assert "$100.00" in html


class TestSendEmail:
    """Test email sending functionality."""

    async def test_send_email_missing_email(
        self,
        email_provider,
    ) -> None:
        """Test send returns False when email missing."""
        result = await email_provider.send(
            merchant_id=1,
            message="Test message",
            metadata={"alert_level": "warning"},
        )

        assert result is False

    async def test_send_email_rate_limited(
        self,
        email_provider,
        mock_redis,
    ) -> None:
        """Test send returns True when rate limited (already sent)."""
        await email_provider._mark_email_sent(1, "warning")

        result = await email_provider.send(
            merchant_id=1,
            message="Test",
            metadata={
                "email": "test@example.com",
                "alert_level": "warning",
            },
        )

        assert result is True

    @patch("app.services.notifications.email_service.aiosmtplib.send")
    async def test_send_email_success(
        self,
        mock_send,
        email_provider,
    ) -> None:
        """Test successful email send."""
        mock_send.return_value = None

        result = await email_provider.send(
            merchant_id=1,
            message="Test message",
            metadata={
                "email": "test@example.com",
                "alert_level": "warning",
                "percentage": 80,
                "budget_cap": 100.00,
                "remaining_budget": 20.00,
            },
        )

        assert result is True
        mock_send.assert_called_once()

    @patch("app.services.notifications.email_service.aiosmtplib.send")
    async def test_send_email_marks_rate_limit(
        self,
        mock_send,
        email_provider,
        mock_redis,
    ) -> None:
        """Test successful send marks rate limit."""
        mock_send.return_value = None

        await email_provider.send(
            merchant_id=1,
            message="Test",
            metadata={
                "email": "test@example.com",
                "alert_level": "warning",
            },
        )

        is_limited = await email_provider._can_send_email(1, "warning")
        assert is_limited is False

    @patch("app.services.notifications.email_service.aiosmtplib.send")
    async def test_send_email_failure_raises(
        self,
        mock_send,
        email_provider,
    ) -> None:
        """Test send failure raises NotificationError."""
        mock_send.side_effect = Exception("SMTP error")

        with pytest.raises(NotificationError) as exc_info:
            await email_provider.send(
                merchant_id=1,
                message="Test",
                metadata={
                    "email": "test@example.com",
                    "alert_level": "warning",
                },
            )

        assert "Failed to send email" in str(exc_info.value)


class TestSendBatch:
    """Test batch email sending."""

    @patch("app.services.notifications.email_service.aiosmtplib.send")
    async def test_send_batch_success(
        self,
        mock_send,
        email_provider,
    ) -> None:
        """Test batch send returns correct count."""
        mock_send.return_value = None

        notifications = [
            {
                "merchant_id": 1,
                "message": "Alert 1",
                "metadata": {"email": "test1@example.com", "alert_level": "warning"},
            },
            {
                "merchant_id": 2,
                "message": "Alert 2",
                "metadata": {"email": "test2@example.com", "alert_level": "warning"},
            },
        ]

        count = await email_provider.send_batch(notifications)

        assert count == 2

    @patch("app.services.notifications.email_service.aiosmtplib.send")
    async def test_send_batch_partial_failure(
        self,
        mock_send,
        email_provider,
    ) -> None:
        """Test batch send handles partial failures."""
        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("SMTP error")

        mock_send.side_effect = side_effect

        notifications = [
            {
                "merchant_id": 1,
                "message": "Alert 1",
                "metadata": {"email": "test1@example.com", "alert_level": "warning"},
            },
            {
                "merchant_id": 2,
                "message": "Alert 2",
                "metadata": {"email": "test2@example.com", "alert_level": "warning"},
            },
        ]

        count = await email_provider.send_batch(notifications)

        assert count == 1
