"""Integration tests for Offline Follow-Up Flow.

Story 4-11: Offline Follow-Up Messages

Tests the complete flow:
- Handoff → 12h wait → follow-up sent → 24h wait → follow-up sent
- Conversation state updated after each follow-up
- Multiple conversations processed in batch
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.handoff.offline_followup_service import (
    OfflineFollowUpService,
    FOLLOWUP_12H_MESSAGE,
    FOLLOWUP_24H_MESSAGE_WITH_EMAIL,
    FOLLOWUP_24H_MESSAGE_NO_EMAIL,
)
from app.models.conversation import Conversation
from app.models.merchant import Merchant
from app.models.message import Message


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


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
def test_merchant():
    """Create test merchant."""
    merchant = MagicMock(spec=Merchant)
    merchant.id = 1
    merchant.email = "test@merchant.com"
    merchant.business_hours_config = None
    return merchant


@pytest.fixture
def recent_shopper_message():
    """Create recent shopper message (within 24h)."""
    msg = MagicMock(spec=Message)
    msg.id = 1
    msg.sender = "customer"
    msg.created_at = datetime.now(timezone.utc) - timedelta(hours=1)
    return msg


@pytest.mark.asyncio
class TestOfflineFollowUpFlow:
    """Integration tests for offline follow-up flow."""

    async def test_full_flow_handoff_to_both_followups(
        self,
        followup_service,
        mock_db,
        mock_messenger_service,
        test_merchant,
        recent_shopper_message,
    ):
        """Full flow: handoff → 12h wait → follow-up sent → 24h wait → follow-up sent."""
        conv = MagicMock(spec=Conversation)
        conv.id = 1
        conv.merchant_id = 1
        conv.platform_sender_id = "test_psid"
        conv.status = "handoff"
        conv.handoff_status = "pending"
        conv.handoff_triggered_at = datetime.now(timezone.utc) - timedelta(hours=25)
        conv.conversation_data = {}

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
                    return_value=test_merchant,
                ):
                    result_12h = await followup_service.send_12h_followup(
                        conv, mock_messenger_service
                    )
                    assert result_12h["sent"] is True
                    assert "followup_12h_sent_at" in conv.conversation_data

                    result_24h = await followup_service.send_24h_followup(
                        conv, mock_messenger_service
                    )
                    assert result_24h["sent"] is True
                    assert "followup_24h_sent_at" in conv.conversation_data

    async def test_conversation_state_updated_after_each_followup(
        self,
        followup_service,
        mock_db,
        mock_messenger_service,
        test_merchant,
        recent_shopper_message,
    ):
        """Conversation state updated after each follow-up."""
        conv = MagicMock(spec=Conversation)
        conv.id = 2
        conv.merchant_id = 1
        conv.platform_sender_id = "test_psid_2"
        conv.status = "handoff"
        conv.handoff_status = "pending"
        conv.handoff_triggered_at = datetime.now(timezone.utc) - timedelta(hours=13)
        conv.conversation_data = {}

        def mock_execute(query):
            result = MagicMock()
            result.scalars.return_value.first.return_value = recent_shopper_message
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        with patch.object(
            followup_service,
            "_is_conversation_still_in_handoff",
            return_value=True,
        ):
            with patch.object(
                followup_service,
                "_get_merchant",
                return_value=test_merchant,
            ):
                result = await followup_service.send_12h_followup(conv, mock_messenger_service)

        assert result["sent"] is True
        assert "followup_12h_sent_at" in conv.conversation_data

        timestamp = conv.conversation_data["followup_12h_sent_at"]
        assert timestamp is not None
        datetime.fromisoformat(timestamp)

    async def test_multiple_conversations_processed_in_batch(
        self,
        followup_service,
        mock_db,
        mock_messenger_service,
        test_merchant,
        recent_shopper_message,
    ):
        """Multiple conversations processed in batch."""
        conversations = []
        for i in range(3):
            conv = MagicMock(spec=Conversation)
            conv.id = i + 1
            conv.merchant_id = 1
            conv.platform_sender_id = f"test_psid_{i}"
            conv.status = "handoff"
            conv.handoff_status = "pending"
            conv.handoff_triggered_at = datetime.now(timezone.utc) - timedelta(hours=13)
            conv.conversation_data = {}
            conversations.append(conv)

        def mock_execute(query):
            result = MagicMock()
            result.scalars.return_value.first.return_value = recent_shopper_message
            result.first.return_value = ("handoff", "pending")
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        results = await followup_service.process_pending_followups(
            conversations=conversations,
            messenger_service=mock_messenger_service,
        )

        assert results["processed"] == 3
        assert results["12h_sent"] >= 0
        assert results["errors"] == 0

    async def test_24h_followup_includes_merchant_email(
        self,
        followup_service,
        mock_db,
        mock_messenger_service,
        test_merchant,
        recent_shopper_message,
    ):
        """24h follow-up includes merchant email when available."""
        conv = MagicMock(spec=Conversation)
        conv.id = 10
        conv.merchant_id = 1
        conv.platform_sender_id = "test_psid_email"
        conv.status = "handoff"
        conv.handoff_status = "pending"
        conv.handoff_triggered_at = datetime.now(timezone.utc) - timedelta(hours=25)
        conv.conversation_data = {}

        def mock_execute(query):
            result = MagicMock()
            result.scalars.return_value.first.return_value = recent_shopper_message
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        with patch.object(
            followup_service,
            "_is_conversation_still_in_handoff",
            return_value=True,
        ):
            with patch.object(
                followup_service,
                "_get_merchant",
                return_value=test_merchant,
            ):
                result = await followup_service.send_24h_followup(conv, mock_messenger_service)

        assert result["sent"] is True

        sent_payload = mock_messenger_service.send_message.call_args[1]["message_payload"]
        assert "test@merchant.com" in sent_payload["text"]

    async def test_24h_followup_without_merchant_email(
        self,
        followup_service,
        mock_db,
        mock_messenger_service,
        recent_shopper_message,
    ):
        """24h follow-up uses fallback message when no merchant email."""
        merchant_no_email = MagicMock(spec=Merchant)
        merchant_no_email.id = 2
        merchant_no_email.email = None
        merchant_no_email.business_hours_config = None

        conv = MagicMock(spec=Conversation)
        conv.id = 11
        conv.merchant_id = 2
        conv.platform_sender_id = "test_psid_noemail"
        conv.status = "handoff"
        conv.handoff_status = "pending"
        conv.handoff_triggered_at = datetime.now(timezone.utc) - timedelta(hours=25)
        conv.conversation_data = {}

        def mock_execute(query):
            result = MagicMock()
            result.scalars.return_value.first.return_value = recent_shopper_message
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        with patch.object(
            followup_service,
            "_is_conversation_still_in_handoff",
            return_value=True,
        ):
            with patch.object(
                followup_service,
                "_get_merchant",
                return_value=merchant_no_email,
            ):
                result = await followup_service.send_24h_followup(conv, mock_messenger_service)

        assert result["sent"] is True

        sent_payload = mock_messenger_service.send_message.call_args[1]["message_payload"]
        assert "@" not in sent_payload["text"]
        assert "We'll respond to your request" in sent_payload["text"]

    async def test_facebook_window_blocks_all_followups(
        self,
        followup_service,
        mock_db,
        mock_messenger_service,
        test_merchant,
    ):
        """Facebook 24h window blocks all follow-ups when expired."""
        conv = MagicMock(spec=Conversation)
        conv.id = 20
        conv.merchant_id = 1
        conv.platform_sender_id = "test_psid_old"
        conv.status = "handoff"
        conv.handoff_status = "pending"
        conv.handoff_triggered_at = datetime.now(timezone.utc) - timedelta(hours=25)
        conv.conversation_data = {}

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
                result_12h = await followup_service.send_12h_followup(conv, mock_messenger_service)
                assert result_12h["sent"] is False
                assert result_12h["reason"] == "outside_24h_window"

                result_24h = await followup_service.send_24h_followup(conv, mock_messenger_service)
                assert result_24h["sent"] is False
                assert result_24h["reason"] == "outside_24h_window"

    async def test_conversation_resolved_mid_flow_skips_remaining(
        self,
        followup_service,
        mock_db,
        mock_messenger_service,
        recent_shopper_message,
    ):
        """Conversation resolved mid-flow skips remaining follow-ups."""
        conv = MagicMock(spec=Conversation)
        conv.id = 30
        conv.merchant_id = 1
        conv.platform_sender_id = "test_psid_resolved"
        conv.status = "handoff"
        conv.handoff_status = "pending"
        conv.handoff_triggered_at = datetime.now(timezone.utc) - timedelta(hours=25)
        conv.conversation_data = {}

        call_count = 0

        def mock_execute(query):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.scalars.return_value.first.return_value = recent_shopper_message
            result.first.return_value = ("active", "none")
            return result

        mock_db.execute = AsyncMock(side_effect=mock_execute)

        result_24h = await followup_service.send_24h_followup(conv, mock_messenger_service)

        assert result_24h["sent"] is False
        assert result_24h["reason"] == "state_changed"
