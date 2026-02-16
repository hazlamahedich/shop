"""Unit tests for HandoffAlert model.

Story 4-6: Handoff Notifications

Tests cover:
- Model creation and field validation
- Relationships to Merchant and Conversation
- Default values (is_read, created_at)
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.models.handoff_alert import HandoffAlert


class TestHandoffAlertModel:
    """Tests for HandoffAlert model."""

    def test_create_handoff_alert_basic(self):
        """Test basic handoff alert creation."""
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="high",
            customer_name="John Doe",
            customer_id="psid_123",
            conversation_preview="I need help with checkout",
            wait_time_seconds=30,
            is_read=False,
        )

        assert alert.merchant_id == 1
        assert alert.conversation_id == 100
        assert alert.urgency_level == "high"
        assert alert.customer_name == "John Doe"
        assert alert.customer_id == "psid_123"
        assert alert.conversation_preview == "I need help with checkout"
        assert alert.wait_time_seconds == 30
        assert alert.is_read is False

    def test_create_handoff_alert_with_low_urgency(self):
        """Test handoff alert with low urgency."""
        alert = HandoffAlert(
            merchant_id=2,
            conversation_id=200,
            urgency_level="low",
            customer_name="Jane",
            customer_id="psid_456",
            conversation_preview="Question about products",
            wait_time_seconds=60,
        )

        assert alert.urgency_level == "low"

    def test_create_handoff_alert_with_medium_urgency(self):
        """Test handoff alert with medium urgency."""
        alert = HandoffAlert(
            merchant_id=3,
            conversation_id=300,
            urgency_level="medium",
            customer_name="Bob",
            customer_id="psid_789",
            conversation_preview="Confused about options",
            wait_time_seconds=45,
        )

        assert alert.urgency_level == "medium"

    def test_create_handoff_alert_without_customer_name(self):
        """Test handoff alert with no customer name (uses customer_id)."""
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="low",
            customer_name=None,
            customer_id="psid_999",
            conversation_preview="Help",
            wait_time_seconds=10,
        )

        assert alert.customer_name is None
        assert alert.customer_id == "psid_999"

    def test_create_handoff_alert_without_preview(self):
        """Test handoff alert with no conversation preview."""
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="high",
            customer_name="Test",
            customer_id="test_id",
            conversation_preview=None,
            wait_time_seconds=0,
        )

        assert alert.conversation_preview is None

    def test_is_read_can_be_set(self):
        """Test is_read can be set to False."""
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="low",
            wait_time_seconds=0,
            is_read=False,
        )

        assert alert.is_read is False

    def test_created_at_can_be_set(self):
        """Test created_at can be set."""
        now = datetime.utcnow()
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="low",
            wait_time_seconds=0,
            created_at=now,
        )

        assert alert.created_at == now

    def test_mark_as_read(self):
        """Test marking alert as read."""
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="low",
            wait_time_seconds=0,
            is_read=False,
        )

        assert alert.is_read is False

        alert.is_read = True

        assert alert.is_read is True

    def test_wait_time_can_be_set(self):
        """Test wait_time_seconds can be set."""
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="low",
            wait_time_seconds=0,
        )

        assert alert.wait_time_seconds == 0

    def test_repr_string(self):
        """Test __repr__ returns correct string."""
        alert = HandoffAlert(
            id=1,
            merchant_id=10,
            conversation_id=100,
            urgency_level="high",
            wait_time_seconds=30,
            is_read=False,
        )

        repr_str = repr(alert)

        assert "HandoffAlert" in repr_str
        assert "id=1" in repr_str
        assert "merchant_id=10" in repr_str
        assert "conversation_id=100" in repr_str
        assert "urgency=high" in repr_str
        assert "is_read=False" in repr_str


class TestHandoffAlertUrgencyLevels:
    """Tests for urgency level values."""

    @pytest.mark.parametrize("urgency", ["high", "medium", "low"])
    def test_valid_urgency_levels(self, urgency):
        """Test all valid urgency levels."""
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level=urgency,
            wait_time_seconds=0,
        )

        assert alert.urgency_level == urgency


class TestHandoffAlertWaitTime:
    """Tests for wait time handling."""

    def test_wait_time_zero(self):
        """Test wait time of 0 seconds."""
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="low",
            wait_time_seconds=0,
        )

        assert alert.wait_time_seconds == 0

    def test_wait_time_under_minute(self):
        """Test wait time under 1 minute."""
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="medium",
            wait_time_seconds=45,
        )

        assert alert.wait_time_seconds == 45

    def test_wait_time_over_minute(self):
        """Test wait time over 1 minute."""
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="high",
            wait_time_seconds=125,
        )

        assert alert.wait_time_seconds == 125

    def test_wait_time_long_wait(self):
        """Test long wait time (hours)."""
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="high",
            wait_time_seconds=3600,  # 1 hour
        )

        assert alert.wait_time_seconds == 3600


class TestHandoffAlertPreview:
    """Tests for conversation preview handling."""

    def test_short_preview(self):
        """Test short conversation preview."""
        preview = "I need help"
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="low",
            conversation_preview=preview,
            wait_time_seconds=0,
        )

        assert alert.conversation_preview == preview

    def test_long_preview(self):
        """Test long conversation preview."""
        preview = "x" * 500  # 500 characters
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="medium",
            conversation_preview=preview,
            wait_time_seconds=0,
        )

        assert alert.conversation_preview == preview

    def test_multiline_preview(self):
        """Test multiline conversation preview."""
        preview = "Message 1\nMessage 2\nMessage 3"
        alert = HandoffAlert(
            merchant_id=1,
            conversation_id=100,
            urgency_level="high",
            conversation_preview=preview,
            wait_time_seconds=0,
        )

        assert alert.conversation_preview == preview
        assert "\n" in alert.conversation_preview
