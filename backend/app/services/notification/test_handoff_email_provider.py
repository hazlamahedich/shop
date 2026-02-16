"""Unit tests for HandoffEmailProvider.

Story 4-6: Handoff Notifications

Tests cover:
- Rate limiting per urgency level
- Email template selection
- Fallback template generation
- Metadata handling
"""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock aiosmtplib before importing the provider
mock_aiosmtplib = MagicMock()
mock_aiosmtplib.send = AsyncMock(return_value=None)
sys.modules["aiosmtplib"] = mock_aiosmtplib

from app.services.notification.handoff_email_provider import (
    HandoffEmailProvider,
    NotificationError,
    HANDOFF_EMAIL_RATE_KEY,
    EMAIL_RATE_TTL,
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
def mock_redis():
    """Provide mock Redis client."""
    return MockRedis()


@pytest.fixture
def email_provider(mock_redis):
    """Provide email provider with mocked Redis."""
    return HandoffEmailProvider(redis_client=mock_redis)


@pytest.fixture
def email_provider_no_redis():
    """Provide email provider without Redis."""
    return HandoffEmailProvider(redis_client=None)


class TestCanSendEmail:
    """Tests for email rate limiting check."""

    @pytest.mark.asyncio
    async def test_can_send_initial(self, email_provider):
        """Test can send email when not rate limited."""
        can_send = await email_provider._can_send_email(
            merchant_id=1,
            urgency="low",
        )
        assert can_send is True

    @pytest.mark.asyncio
    async def test_cannot_send_when_rate_limited(self, email_provider, mock_redis):
        """Test cannot send email when rate limited."""
        redis_key = HANDOFF_EMAIL_RATE_KEY.format(merchant_id=1, urgency="high")
        mock_redis.data[redis_key] = "2026-02-14T10:00:00"

        can_send = await email_provider._can_send_email(
            merchant_id=1,
            urgency="high",
        )
        assert can_send is False

    @pytest.mark.asyncio
    async def test_different_urgency_not_rate_limited(self, email_provider, mock_redis):
        """Test different urgency level is not rate limited."""
        redis_key = HANDOFF_EMAIL_RATE_KEY.format(merchant_id=1, urgency="low")
        mock_redis.data[redis_key] = "2026-02-14T10:00:00"

        can_send_high = await email_provider._can_send_email(
            merchant_id=1,
            urgency="high",
        )
        assert can_send_high is True

        can_send_medium = await email_provider._can_send_email(
            merchant_id=1,
            urgency="medium",
        )
        assert can_send_medium is True

    @pytest.mark.asyncio
    async def test_can_send_without_redis(self, email_provider_no_redis):
        """Test can send email when Redis is not available."""
        can_send = await email_provider_no_redis._can_send_email(
            merchant_id=1,
            urgency="high",
        )
        assert can_send is True


class TestMarkEmailSent:
    """Tests for marking email as sent."""

    @pytest.mark.asyncio
    async def test_mark_email_sent(self, email_provider, mock_redis):
        """Test marking email as sent sets rate limit key."""
        await email_provider._mark_email_sent(
            merchant_id=1,
            urgency="medium",
        )

        redis_key = HANDOFF_EMAIL_RATE_KEY.format(merchant_id=1, urgency="medium")
        assert redis_key in mock_redis.data
        assert mock_redis.expirations.get(redis_key) == EMAIL_RATE_TTL

    @pytest.mark.asyncio
    async def test_mark_email_sent_without_redis(self, email_provider_no_redis):
        """Test mark email sent is safe without Redis."""
        await email_provider_no_redis._mark_email_sent(
            merchant_id=1,
            urgency="low",
        )


class TestGetTemplateContent:
    """Tests for email template content generation."""

    def test_get_template_high_urgency(self, email_provider):
        """Test HIGH urgency template has correct styling."""
        subject, html = email_provider._get_template_content(
            urgency="high",
            customer_name="John Doe",
            wait_time="2m 30s",
            handoff_reason="checkout_blocked",
            conversation_preview="I need help",
            dashboard_url="http://example.com/convo/1",
        )

        assert "HIGH" in subject
        assert "🔴" in subject
        assert "John Doe" in html
        assert "2m 30s" in html
        assert "#DC2626" in html or "#FEE2E2" in html

    def test_get_template_medium_urgency(self, email_provider):
        """Test MEDIUM urgency template has correct styling."""
        subject, html = email_provider._get_template_content(
            urgency="medium",
            customer_name="Jane",
            wait_time="1m",
            handoff_reason="low_confidence",
            conversation_preview="Help me",
            dashboard_url="http://example.com/convo/2",
        )

        assert "MEDIUM" in subject
        assert "🟡" in subject
        assert "#D97706" in html or "#FEF3C7" in html

    def test_get_template_low_urgency(self, email_provider):
        """Test LOW urgency template has correct styling."""
        subject, html = email_provider._get_template_content(
            urgency="low",
            customer_name="Bob",
            wait_time="30s",
            handoff_reason="keyword",
            conversation_preview="Question",
            dashboard_url="http://example.com/convo/3",
        )

        assert "LOW" in subject
        assert "🟢" in subject
        assert "#059669" in html or "#D1FAE5" in html

    def test_template_replaces_placeholders(self, email_provider):
        """Test template placeholders are replaced."""
        subject, html = email_provider._get_template_content(
            urgency="low",
            customer_name="Test Customer",
            wait_time="5m",
            handoff_reason="test_reason",
            conversation_preview="Test preview content",
            dashboard_url="http://test.url/convo",
        )

        assert "Test Customer" in html
        assert "5m" in html
        assert "test_reason" in html
        assert "Test preview content" in html
        assert "http://test.url/convo" in html


class TestGetFallbackTemplate:
    """Tests for fallback template generation."""

    def test_fallback_high_urgency(self, email_provider):
        """Test fallback template for HIGH urgency."""
        config = {
            "emoji": "🔴",
            "label": "HIGH",
            "color": "#DC2626",
            "bg_color": "#FEE2E2",
        }

        html = email_provider._get_fallback_template(
            config=config,
            customer_name="Test",
            wait_time="1m",
            handoff_reason="test",
            conversation_preview="Preview",
            dashboard_url="http://test.com",
        )

        assert "🔴" in html
        assert "Test" in html
        assert "1m" in html
        assert "test" in html
        assert "Preview" in html
        assert "http://test.com" in html

    def test_fallback_includes_cta_button(self, email_provider):
        """Test fallback template includes CTA button."""
        config = {
            "emoji": "🟢",
            "label": "LOW",
            "color": "#059669",
            "bg_color": "#D1FAE5",
        }

        html = email_provider._get_fallback_template(
            config=config,
            customer_name="Test",
            wait_time="30s",
            handoff_reason="keyword",
            conversation_preview="Help",
            dashboard_url="http://dashboard.com/convo/1",
        )

        assert "View Conversation" in html


class TestSend:
    """Tests for send method."""

    @pytest.mark.asyncio
    async def test_send_returns_false_without_email(self, email_provider):
        """Test send returns False when email is missing."""
        result = await email_provider.send(
            merchant_id=1,
            message="Test message",
            metadata={"urgency": "low"},
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_returns_true_when_rate_limited(self, email_provider, mock_redis):
        """Test send returns True when rate limited (not an error)."""
        redis_key = HANDOFF_EMAIL_RATE_KEY.format(merchant_id=1, urgency="low")
        mock_redis.data[redis_key] = "2026-02-14T10:00:00"

        result = await email_provider.send(
            merchant_id=1,
            message="Test",
            metadata={"email": "test@example.com", "urgency": "low"},
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_send_raises_on_smtp_error(self, email_provider):
        """Test send raises NotificationError on SMTP failure."""
        with patch("app.services.notification.handoff_email_provider.aiosmtplib") as mock_smtp:
            mock_smtp.send = AsyncMock(side_effect=Exception("SMTP error"))

            with pytest.raises(NotificationError) as exc_info:
                await email_provider.send(
                    merchant_id=1,
                    message="Test",
                    metadata={
                        "email": "test@example.com",
                        "urgency": "high",
                        "customer_name": "Test",
                        "wait_time": "1m",
                        "handoff_reason": "test",
                        "conversation_preview": "Preview",
                        "dashboard_url": "http://test.com",
                    },
                )

            assert "Failed to send handoff email" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_send_success_marks_rate_limit(self, email_provider, mock_redis):
        """Test successful send marks rate limit."""
        with patch("app.services.notification.handoff_email_provider.aiosmtplib") as mock_smtp:
            mock_smtp.send = AsyncMock(return_value=None)

            result = await email_provider.send(
                merchant_id=1,
                message="Test",
                metadata={
                    "email": "test@example.com",
                    "urgency": "medium",
                    "customer_name": "Test",
                    "wait_time": "30s",
                    "handoff_reason": "test",
                    "conversation_preview": "Preview",
                    "dashboard_url": "http://test.com",
                },
            )

            assert result is True
            redis_key = HANDOFF_EMAIL_RATE_KEY.format(merchant_id=1, urgency="medium")
            assert redis_key in mock_redis.data


class TestSendBatch:
    """Tests for send_batch method."""

    @pytest.mark.asyncio
    async def test_send_batch_returns_count(self, email_provider):
        """Test send_batch returns success count."""
        with patch("app.services.notification.handoff_email_provider.aiosmtplib") as mock_smtp:
            mock_smtp.send = AsyncMock(return_value=None)

            notifications = [
                {
                    "merchant_id": 1,
                    "message": "Test 1",
                    "metadata": {"email": "test1@example.com", "urgency": "low"},
                },
                {
                    "merchant_id": 2,
                    "message": "Test 2",
                    "metadata": {"email": "test2@example.com", "urgency": "medium"},
                },
            ]

            count = await email_provider.send_batch(notifications)

            assert count == 2

    @pytest.mark.asyncio
    async def test_send_batch_continues_on_error(self, email_provider):
        """Test send_batch continues when one fails."""
        call_count = 0

        async def mock_send(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("SMTP error")
            return None

        with patch("app.services.notification.handoff_email_provider.aiosmtplib") as mock_smtp:
            mock_smtp.send = mock_send

            notifications = [
                {
                    "merchant_id": 1,
                    "message": "Test 1",
                    "metadata": {
                        "email": "test1@example.com",
                        "urgency": "low",
                        "customer_name": "Test 1",
                    },
                },
                {
                    "merchant_id": 2,
                    "message": "Test 2",
                    "metadata": {
                        "email": "test2@example.com",
                        "urgency": "medium",
                        "customer_name": "Test 2",
                    },
                },
            ]

            count = await email_provider.send_batch(notifications)

            assert count == 1


class TestConstants:
    """Tests for module constants."""

    def test_rate_key_format(self):
        """Test rate limit key format."""
        key = HANDOFF_EMAIL_RATE_KEY.format(merchant_id=123, urgency="high")
        assert key == "handoff_email:123:high"

    def test_rate_ttl_is_24_hours(self):
        """Test rate limit TTL is 24 hours in seconds."""
        assert EMAIL_RATE_TTL == 86400
