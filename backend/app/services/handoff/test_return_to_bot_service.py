"""Tests for ReturnToBotService.

Story 4-10: Return to Bot

Tests welcome message sending with 24-hour window enforcement.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.handoff.return_to_bot_service import (
    ReturnToBotService,
    WELCOME_BACK_MESSAGE,
)
from app.models.message import Message
from app.models.conversation import Conversation


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_facebook_service():
    """Create mock Facebook messenger service."""
    service = AsyncMock()
    service.send_message = AsyncMock(return_value={"message_id": "mid.test123"})
    return service


@pytest.fixture
def return_to_bot_service(mock_db):
    """Create ReturnToBotService instance."""
    return ReturnToBotService(db=mock_db)


@pytest.fixture
def test_conversation():
    """Create test conversation."""
    conv = MagicMock(spec=Conversation)
    conv.id = 1
    conv.platform_sender_id = "test_psid_123"
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
class TestReturnToBotService:
    """Test ReturnToBotService."""

    async def test_send_welcome_message_within_24h_window(
        self,
        return_to_bot_service,
        test_conversation,
        mock_facebook_service,
        mock_db,
        recent_shopper_message,
    ):
        """Test welcome message sent when within 24h window."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = recent_shopper_message
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await return_to_bot_service.send_welcome_message(
            test_conversation, mock_facebook_service
        )

        assert result["sent"] is True
        assert result["reason"] == "success"
        mock_facebook_service.send_message.assert_called_once_with(
            test_conversation.platform_sender_id,
            {"text": WELCOME_BACK_MESSAGE},
        )

    async def test_send_welcome_message_outside_24h_window(
        self,
        return_to_bot_service,
        test_conversation,
        mock_facebook_service,
        mock_db,
        old_shopper_message,
    ):
        """Test welcome message NOT sent when outside 24h window."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = old_shopper_message
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await return_to_bot_service.send_welcome_message(
            test_conversation, mock_facebook_service
        )

        assert result["sent"] is False
        assert result["reason"] == "outside_24h_window"
        mock_facebook_service.send_message.assert_not_called()

    async def test_send_welcome_message_no_shopper_messages(
        self,
        return_to_bot_service,
        test_conversation,
        mock_facebook_service,
        mock_db,
    ):
        """Test welcome message NOT sent when no shopper messages exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await return_to_bot_service.send_welcome_message(
            test_conversation, mock_facebook_service
        )

        assert result["sent"] is False
        assert result["reason"] == "no_shopper_message"
        mock_facebook_service.send_message.assert_not_called()

    async def test_send_welcome_message_handles_facebook_error(
        self,
        return_to_bot_service,
        test_conversation,
        mock_facebook_service,
        mock_db,
        recent_shopper_message,
    ):
        """Test welcome message handles Facebook API errors gracefully."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = recent_shopper_message
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_facebook_service.send_message.side_effect = Exception("API Error")

        result = await return_to_bot_service.send_welcome_message(
            test_conversation, mock_facebook_service
        )

        assert result["sent"] is False
        assert "send_error" in result["reason"]

    async def test_message_stored_in_database(
        self,
        return_to_bot_service,
        test_conversation,
        mock_facebook_service,
        mock_db,
        recent_shopper_message,
    ):
        """Test that welcome message is stored in database."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = recent_shopper_message
        mock_db.execute = AsyncMock(return_value=mock_result)

        await return_to_bot_service.send_welcome_message(test_conversation, mock_facebook_service)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

        added_message = mock_db.add.call_args[0][0]
        assert added_message.sender == "bot"
        assert added_message.content == WELCOME_BACK_MESSAGE
        assert added_message.message_type == "text"

    def test_welcome_message_content(self):
        """Test welcome message content matches expected format."""
        expected = "Welcome back! Is there anything else I can help you with?"
        assert WELCOME_BACK_MESSAGE == expected

    async def test_hours_since_message_calculation(
        self,
        return_to_bot_service,
        recent_shopper_message,
    ):
        """Test hours since message calculation is accurate."""
        hours = return_to_bot_service._hours_since_message(recent_shopper_message)

        assert isinstance(hours, float)
        assert 0 < hours < 2

    async def test_hours_since_message_with_timezone_naive(
        self,
        return_to_bot_service,
    ):
        """Test hours calculation handles timezone-naive timestamps."""
        msg = MagicMock(spec=Message)
        msg.created_at = datetime.utcnow() - timedelta(hours=5)

        hours = return_to_bot_service._hours_since_message(msg)

        assert 4.9 < hours < 5.1
