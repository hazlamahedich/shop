"""Tests for OfflineFollowUpService.

Story 4-11: Offline Follow-Up Messages

Tests follow-up message sending with:
- 12h and 24h follow-up triggers
- Facebook 24-hour window enforcement
- Business hours integration
- Idempotency (no duplicate follow-ups)
- Email fallback for 24h message
- Conversation state validation
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.handoff.offline_followup_service import (
    OfflineFollowUpService,
    FOLLOWUP_12H_MESSAGE,
    FOLLOWUP_24H_MESSAGE_WITH_EMAIL,
    FOLLOWUP_24H_MESSAGE_NO_EMAIL,
    FOLLOWUP_12H_THRESHOLD_HOURS,
    FOLLOWUP_24H_THRESHOLD_HOURS,
    FACEBOOK_WINDOW_HOURS,
)
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.merchant import Merchant


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_messenger_service():
    """Create mock messenger service."""
    service = AsyncMock()
    service.send_message = AsyncMock(return_value={"message_id": "mid.test123"})
    service.close = AsyncMock()
    return service


@pytest.fixture
def followup_service(mock_db):
    """Create OfflineFollowUpService instance."""
    return OfflineFollowUpService(db=mock_db)


@pytest.fixture
def test_merchant_with_email():
    """Create test merchant with email."""
    merchant = MagicMock(spec=Merchant)
    merchant.id = 1
    merchant.email = "support@test.com"
    merchant.business_hours_config = None
    return merchant


@pytest.fixture
def test_merchant_no_email():
    """Create test merchant without email."""
    merchant = MagicMock(spec=Merchant)
    merchant.id = 2
    merchant.email = None
    merchant.business_hours_config = None
    return merchant


@pytest.fixture
def test_conversation_pending_handoff():
    """Create test conversation in pending handoff state."""
    conv = MagicMock(spec=Conversation)
    conv.id = 1
    conv.merchant_id = 1
    conv.platform_sender_id = "test_psid_123"
    conv.status = "handoff"
    conv.handoff_status = "pending"
    conv.handoff_triggered_at = datetime.now(timezone.utc) - timedelta(hours=13)
    conv.conversation_data = {}
    return conv


@pytest.fixture
def test_conversation_with_12h_sent():
    """Create test conversation with 12h follow-up already sent."""
    conv = MagicMock(spec=Conversation)
    conv.id = 2
    conv.merchant_id = 1
    conv.platform_sender_id = "test_psid_456"
    conv.status = "handoff"
    conv.handoff_status = "pending"
    conv.handoff_triggered_at = datetime.now(timezone.utc) - timedelta(hours=25)
    conv.conversation_data = {
        "followup_12h_sent_at": (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
    }
    return conv


@pytest.fixture
def test_conversation_both_sent():
    """Create test conversation with both follow-ups already sent."""
    conv = MagicMock(spec=Conversation)
    conv.id = 3
    conv.merchant_id = 1
    conv.platform_sender_id = "test_psid_789"
    conv.status = "handoff"
    conv.handoff_status = "pending"
    conv.handoff_triggered_at = datetime.now(timezone.utc) - timedelta(hours=30)
    conv.conversation_data = {
        "followup_12h_sent_at": (datetime.now(timezone.utc) - timedelta(hours=18)).isoformat(),
        "followup_24h_sent_at": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
    }
    return conv


@pytest.fixture
def recent_shopper_message():
    """Create recent shopper message (within 24h)."""
    msg = MagicMock(spec=Message)
    msg.id = 1
    msg.sender = "customer"
    msg.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
    return msg


@pytest.fixture
def old_shopper_message():
    """Create old shopper message (outside 24h)."""
    msg = MagicMock(spec=Message)
    msg.id = 2
    msg.sender = "customer"
    msg.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
    return msg


@pytest.mark.asyncio
class TestOfflineFollowUpService:
    """Test OfflineFollowUpService."""

    async def test_12h_followup_sent_when_threshold_reached(
        self,
        followup_service,
        test_conversation_pending_handoff,
        mock_messenger_service,
        mock_db,
        recent_shopper_message,
        test_merchant_with_email,
    ):
        """AC1: 12h follow-up sent when threshold reached."""
        with patch.object(
            followup_service,
            "_is_conversation_still_in_handoff",
            return_value=True,
        ):
            with patch.object(
                followup_service,
                "_is_within_facebook_window",
                return_value=True,
            ):
                result = await followup_service.send_12h_followup(
                    test_conversation_pending_handoff, mock_messenger_service
                )

        assert result["sent"] is True
        assert result["reason"] == "success"
        mock_messenger_service.send_message.assert_called_once()

    async def test_24h_followup_sent_when_threshold_reached(
        self,
        followup_service,
        test_conversation_with_12h_sent,
        mock_messenger_service,
        mock_db,
        recent_shopper_message,
        test_merchant_with_email,
    ):
        """AC2: 24h follow-up sent when threshold reached."""
        with patch.object(
            followup_service,
            "_is_conversation_still_in_handoff",
            return_value=True,
        ):
            with patch.object(
                followup_service,
                "_is_within_facebook_window",
                return_value=True,
            ):
                with patch.object(
                    followup_service,
                    "_get_merchant",
                    return_value=test_merchant_with_email,
                ):
                    result = await followup_service.send_24h_followup(
                        test_conversation_with_12h_sent, mock_messenger_service
                    )

        assert result["sent"] is True
        assert result["reason"] == "success"

    async def test_no_duplicate_12h_followups(
        self,
        followup_service,
        test_conversation_with_12h_sent,
        mock_messenger_service,
    ):
        """AC4: No duplicate 12h follow-ups (idempotency)."""
        result = await followup_service.send_12h_followup(
            test_conversation_with_12h_sent, mock_messenger_service
        )

        assert result["sent"] is False
        assert result["reason"] == "already_sent"
        mock_messenger_service.send_message.assert_not_called()

    async def test_no_duplicate_24h_followups(
        self,
        followup_service,
        test_conversation_both_sent,
        mock_messenger_service,
    ):
        """AC4: No duplicate 24h follow-ups (idempotency)."""
        result = await followup_service.send_24h_followup(
            test_conversation_both_sent, mock_messenger_service
        )

        assert result["sent"] is False
        assert result["reason"] == "already_sent"
        mock_messenger_service.send_message.assert_not_called()

    async def test_followup_skipped_if_outside_facebook_24h_window(
        self,
        followup_service,
        test_conversation_pending_handoff,
        mock_messenger_service,
        mock_db,
        old_shopper_message,
    ):
        """CRITICAL: Follow-up skipped if outside Facebook 24h window."""
        with patch.object(
            followup_service,
            "_is_conversation_still_in_handoff",
            return_value=True,
        ):
            with patch.object(
                followup_service,
                "_is_within_facebook_window",
                return_value=False,
            ):
                result = await followup_service.send_12h_followup(
                    test_conversation_pending_handoff, mock_messenger_service
                )

        assert result["sent"] is False
        assert result["reason"] == "outside_24h_window"
        mock_messenger_service.send_message.assert_not_called()

    async def test_business_hours_integration_delay_if_outside_hours(
        self,
        followup_service,
        test_conversation_pending_handoff,
        mock_messenger_service,
        mock_db,
        recent_shopper_message,
    ):
        """AC3: Business hours integration - delay if outside hours."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = recent_shopper_message
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_bhs = MagicMock()
        mock_bhs.is_within_business_hours = MagicMock(return_value=False)

        results = {
            "processed": 0,
            "12h_sent": 0,
            "24h_sent": 0,
            "skipped_state_changed": 0,
            "skipped_already_sent": 0,
            "skipped_24h_window": 0,
            "skipped_business_hours": 0,
            "errors": 0,
        }

        with patch.object(
            followup_service,
            "_is_within_business_hours",
            return_value=False,
        ):
            with patch.object(
                followup_service,
                "_is_conversation_still_in_handoff",
                return_value=True,
            ):
                with patch.object(
                    followup_service,
                    "_is_within_facebook_window",
                    return_value=True,
                ):
                    await followup_service._maybe_send_12h_followup(
                        conversation=test_conversation_pending_handoff,
                        messenger_service=mock_messenger_service,
                        business_hours_service=mock_bhs,
                        results=results,
                    )

        assert results["skipped_business_hours"] == 1
        assert results["12h_sent"] == 0

    async def test_email_inclusion_in_24h_followup_message(
        self,
        followup_service,
        test_merchant_with_email,
    ):
        """24h follow-up includes email when available."""
        message = followup_service._build_24h_message(test_merchant_with_email)

        assert "support@test.com" in message
        assert FOLLOWUP_24H_MESSAGE_WITH_EMAIL.format(email="support@test.com") == message

    async def test_24h_followup_without_email_fallback(
        self,
        followup_service,
        test_merchant_no_email,
    ):
        """24h follow-up WITHOUT email (fallback message)."""
        message = followup_service._build_24h_message(test_merchant_no_email)

        assert "@" not in message
        assert message == FOLLOWUP_24H_MESSAGE_NO_EMAIL

    async def test_followup_skipped_if_conversation_status_changed(
        self,
        followup_service,
        test_conversation_pending_handoff,
        mock_messenger_service,
        mock_db,
    ):
        """Follow-up skipped if conversation status changed (not handoff)."""
        mock_result = MagicMock()
        mock_result.first.return_value = ("active", "none")
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await followup_service.send_12h_followup(
            test_conversation_pending_handoff, mock_messenger_service
        )

        assert result["sent"] is False
        assert result["reason"] == "state_changed"

    async def test_followup_skipped_if_handoff_status_changed(
        self,
        followup_service,
        test_conversation_pending_handoff,
        mock_messenger_service,
        mock_db,
    ):
        """Follow-up skipped if handoff_status changed (not pending/active)."""
        mock_result = MagicMock()
        mock_result.first.return_value = ("handoff", "resolved")
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await followup_service.send_12h_followup(
            test_conversation_pending_handoff, mock_messenger_service
        )

        assert result["sent"] is False
        assert result["reason"] == "state_changed"

    async def test_get_pending_followups_queries_correctly(
        self,
        followup_service,
        mock_db,
    ):
        """Test get_pending_followups queries with correct filters."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        conversations = await followup_service.get_pending_followups(hours_threshold=12)

        assert isinstance(conversations, list)
        mock_db.execute.assert_called_once()

    async def test_process_pending_followups_batch_processing(
        self,
        followup_service,
        test_conversation_pending_handoff,
        mock_messenger_service,
        mock_db,
        recent_shopper_message,
    ):
        """Test batch processing of multiple conversations."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = recent_shopper_message
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch.object(
            followup_service,
            "_is_conversation_still_in_handoff",
            return_value=True,
        ):
            with patch.object(
                followup_service,
                "_is_within_facebook_window",
                return_value=True,
            ):
                with patch.object(
                    followup_service,
                    "_is_within_business_hours",
                    return_value=True,
                ):
                    results = await followup_service.process_pending_followups(
                        conversations=[test_conversation_pending_handoff],
                        messenger_service=mock_messenger_service,
                    )

        assert "processed" in results
        assert results["processed"] == 1

    async def test_track_followup_sent_stores_timestamp(
        self,
        followup_service,
        test_conversation_pending_handoff,
        mock_db,
    ):
        """AC5: Follow-up timestamps tracked in conversation_data."""
        await followup_service._track_followup_sent(test_conversation_pending_handoff, "12h")

        assert "followup_12h_sent_at" in test_conversation_pending_handoff.conversation_data
        mock_db.commit.assert_called_once()

    async def test_hours_since_handoff_calculation(
        self,
        followup_service,
        test_conversation_pending_handoff,
    ):
        """Test hours since handoff calculation is accurate."""
        hours = await followup_service._hours_since_handoff(test_conversation_pending_handoff)

        assert isinstance(hours, float)
        assert 12 < hours < 14

    async def test_hours_since_handoff_returns_zero_if_not_triggered(
        self,
        followup_service,
    ):
        """Test hours since handoff returns 0 if handoff not triggered."""
        conv = MagicMock(spec=Conversation)
        conv.handoff_triggered_at = None

        hours = await followup_service._hours_since_handoff(conv)

        assert hours == 0.0

    async def test_is_within_facebook_window_with_recent_message(
        self,
        followup_service,
        test_conversation_pending_handoff,
        mock_db,
        recent_shopper_message,
    ):
        """Test Facebook window check with recent message."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = recent_shopper_message
        mock_db.execute = AsyncMock(return_value=mock_result)

        is_within = await followup_service._is_within_facebook_window(
            test_conversation_pending_handoff
        )

        assert is_within is True

    async def test_is_within_facebook_window_with_old_message(
        self,
        followup_service,
        test_conversation_pending_handoff,
        mock_db,
        old_shopper_message,
    ):
        """Test Facebook window check with old message."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = old_shopper_message
        mock_db.execute = AsyncMock(return_value=mock_result)

        is_within = await followup_service._is_within_facebook_window(
            test_conversation_pending_handoff
        )

        assert is_within is False

    async def test_is_within_facebook_window_no_messages(
        self,
        followup_service,
        test_conversation_pending_handoff,
        mock_db,
    ):
        """Test Facebook window check with no messages."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        is_within = await followup_service._is_within_facebook_window(
            test_conversation_pending_handoff
        )

        assert is_within is False


class TestOfflineFollowUpServiceConstants:
    """Test constants and message templates (non-async)."""

    def test_message_templates_defined(self):
        """Test message templates are properly defined."""
        assert "Still working on your request" in FOLLOWUP_12H_MESSAGE
        assert "Sorry for the delay" in FOLLOWUP_24H_MESSAGE_WITH_EMAIL
        assert "Sorry for the delay" in FOLLOWUP_24H_MESSAGE_NO_EMAIL
        assert "{email}" in FOLLOWUP_24H_MESSAGE_WITH_EMAIL
        assert "{email}" not in FOLLOWUP_24H_MESSAGE_NO_EMAIL

    def test_threshold_constants(self):
        """Test threshold constants are correct."""
        assert FOLLOWUP_12H_THRESHOLD_HOURS == 12
        assert FOLLOWUP_24H_THRESHOLD_HOURS == 24
        assert FACEBOOK_WINDOW_HOURS == 24
