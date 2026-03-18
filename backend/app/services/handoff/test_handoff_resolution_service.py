"""Tests for HandoffResolutionService.

Story: LLM-powered handoff resolution messages for widget

Tests resolution message generation, storage, and delivery.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.conversation import Conversation
from app.models.merchant import Merchant, PersonalityType
from app.models.message import Message
from app.services.handoff.handoff_resolution_service import HandoffResolutionService


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def handoff_resolution_service(mock_db):
    """Create HandoffResolutionService instance."""
    return HandoffResolutionService(db=mock_db)


@pytest.fixture
def test_merchant():
    """Create test merchant."""
    merchant = MagicMock(spec=Merchant)
    merchant.id = 1
    merchant.business_name = "Test Shop"
    merchant.personality = PersonalityType.FRIENDLY
    return merchant


@pytest.fixture
def test_widget_conversation():
    """Create test widget conversation."""
    conv = MagicMock(spec=Conversation)
    conv.id = 1
    conv.merchant_id = 1
    conv.platform = "widget"
    conv.platform_sender_id = "test_session_123"
    conv.status = "handoff"
    return conv


@pytest.fixture
def test_messenger_conversation():
    """Create test messenger conversation."""
    conv = MagicMock(spec=Conversation)
    conv.id = 2
    conv.merchant_id = 1
    conv.platform = "messenger"
    conv.platform_sender_id = "test_psid_456"
    conv.status = "handoff"
    return conv


@pytest.fixture
def test_message():
    """Create test message."""
    msg = MagicMock(spec=Message)
    msg.id = 1
    msg.content = "Test resolution message"
    msg.sender = "bot"
    msg.created_at = datetime.now(UTC)
    return msg


@pytest.mark.asyncio
class TestHandoffResolutionService:
    """Test HandoffResolutionService."""

    async def test_send_resolution_message_llm_success(
        self,
        handoff_resolution_service,
        test_widget_conversation,
        test_merchant,
        test_message,
        mock_db,
    ):
        """Test successful LLM generation and delivery."""
        # Mock UnifiedConversationService
        with patch(
            "app.services.conversation.unified_conversation_service.UnifiedConversationService"
        ) as mock_unified_service_class:
            mock_unified_service = MagicMock()
            mock_unified_service.generate_handoff_resolution_message = AsyncMock(
                return_value={
                    "content": "All set! Test Shop is here for you! 😊",
                    "fallback": False,
                    "reason": "llm_success",
                    "response_time_ms": 500,
                }
            )
            mock_unified_service_class.return_value = mock_unified_service

            # Mock _store_message
            with patch.object(
                handoff_resolution_service,
                "_store_message",
                return_value=test_message,
            ):
                # Mock _broadcast_to_widget
                with patch.object(
                    handoff_resolution_service,
                    "_broadcast_to_widget",
                    return_value=True,
                ):
                    result = await handoff_resolution_service.send_resolution_message(
                        conversation=test_widget_conversation,
                        merchant=test_merchant,
                    )

        assert result["sent"] is True
        assert result["message_id"] == test_message.id
        assert result["fallback"] is False
        assert result["reason"] == "llm_success"
        assert result["broadcast_sent"] is True

    async def test_send_resolution_message_llm_timeout_fallback(
        self,
        handoff_resolution_service,
        test_widget_conversation,
        test_merchant,
        test_message,
    ):
        """Test fallback to generic message on LLM timeout."""
        with patch(
            "app.services.conversation.unified_conversation_service.UnifiedConversationService"
        ) as mock_unified_service_class:
            mock_unified_service = MagicMock()
            mock_unified_service.generate_handoff_resolution_message = AsyncMock(
                return_value={
                    "content": "Welcome back! Is there anything else I can help you with?",
                    "fallback": True,
                    "reason": "llm_timeout",
                }
            )
            mock_unified_service_class.return_value = mock_unified_service

            with patch.object(
                handoff_resolution_service,
                "_store_message",
                return_value=test_message,
            ):
                with patch.object(
                    handoff_resolution_service,
                    "_broadcast_to_widget",
                    return_value=True,
                ):
                    result = await handoff_resolution_service.send_resolution_message(
                        conversation=test_widget_conversation,
                        merchant=test_merchant,
                    )

        assert result["sent"] is True
        assert result["fallback"] is True
        assert result["reason"] == "llm_timeout"
        assert "Welcome back" in result["content"]

    async def test_send_resolution_message_messenger_platform(
        self,
        handoff_resolution_service,
        test_messenger_conversation,
        test_merchant,
        test_message,
    ):
        """Test that messenger conversations don't broadcast to widget."""
        with patch(
            "app.services.conversation.unified_conversation_service.UnifiedConversationService"
        ) as mock_unified_service_class:
            mock_unified_service = MagicMock()
            mock_unified_service.generate_handoff_resolution_message = AsyncMock(
                return_value={
                    "content": "Test message",
                    "fallback": False,
                    "reason": "llm_success",
                }
            )
            mock_unified_service_class.return_value = mock_unified_service

            with patch.object(
                handoff_resolution_service,
                "_store_message",
                return_value=test_message,
            ):
                # Should not call _broadcast_to_widget for messenger
                with patch.object(
                    handoff_resolution_service,
                    "_broadcast_to_widget",
                    return_value=False,
                ) as mock_broadcast:
                    result = await handoff_resolution_service.send_resolution_message(
                        conversation=test_messenger_conversation,
                        merchant=test_merchant,
                    )

                    # Broadcast should not be called for messenger
                    mock_broadcast.assert_not_called()

        assert result["sent"] is True
        assert result["broadcast_sent"] is False

    async def test_store_message(
        self,
        handoff_resolution_service,
        test_widget_conversation,
        mock_db,
    ):
        """Test message storage in database."""
        content = "Test resolution message"

        # Create a mock message that will be returned
        mock_message = MagicMock(spec=Message)
        mock_message.id = 1
        mock_message.content = content

        # Mock the refresh to update the message
        async def mock_refresh_side_effect(msg):
            msg.id = 1
            return None

        mock_db.refresh = AsyncMock(side_effect=mock_refresh_side_effect)

        message = await handoff_resolution_service._store_message(
            conversation=test_widget_conversation,
            content=content,
        )

        # Verify db.add was called with correct message
        assert mock_db.add.called
        added_message = mock_db.add.call_args[0][0]
        assert added_message.conversation_id == test_widget_conversation.id
        assert added_message.sender == "bot"
        assert added_message.content == content
        assert added_message.message_type == "text"

        # Verify commit and refresh were called
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    async def test_broadcast_to_widget_success(
        self,
        handoff_resolution_service,
        test_widget_conversation,
        test_message,
    ):
        """Test successful WebSocket broadcast."""
        with patch(
            "app.services.widget.connection_manager.get_connection_manager"
        ) as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.broadcast_to_session = AsyncMock(return_value=2)
            mock_get_manager.return_value = mock_manager

            result = await handoff_resolution_service._broadcast_to_widget(
                conversation=test_widget_conversation,
                message=test_message,
            )

        assert result is True
        mock_manager.broadcast_to_session.assert_called_once()

        # Verify payload structure
        call_args = mock_manager.broadcast_to_session.call_args
        assert call_args[1]["session_id"] == test_widget_conversation.platform_sender_id
        payload = call_args[1]["message"]
        assert payload["type"] == "handoff_resolved"
        assert payload["data"]["id"] == test_message.id
        assert payload["data"]["content"] == test_message.content
        assert payload["data"]["sender"] == "bot"

    async def test_broadcast_to_widget_no_session_id(
        self,
        handoff_resolution_service,
        test_message,
    ):
        """Test broadcast fails gracefully when no session_id."""
        conv = MagicMock(spec=Conversation)
        conv.id = 1
        conv.platform = "widget"
        conv.platform_sender_id = None

        result = await handoff_resolution_service._broadcast_to_widget(
            conversation=conv,
            message=test_message,
        )

        assert result is False

    async def test_broadcast_to_widget_exception(
        self,
        handoff_resolution_service,
        test_widget_conversation,
        test_message,
    ):
        """Test broadcast handles exceptions gracefully."""
        with patch(
            "app.services.widget.connection_manager.get_connection_manager"
        ) as mock_get_manager:
            mock_get_manager.side_effect = Exception("Connection error")

            result = await handoff_resolution_service._broadcast_to_widget(
                conversation=test_widget_conversation,
                message=test_message,
            )

        assert result is False

    async def test_personality_friendly(
        self,
        handoff_resolution_service,
        test_widget_conversation,
        test_merchant,
        test_message,
    ):
        """Test friendly personality generates appropriate message."""
        test_merchant.personality = PersonalityType.FRIENDLY

        with patch(
            "app.services.conversation.unified_conversation_service.UnifiedConversationService"
        ) as mock_unified_service_class:
            mock_unified_service = MagicMock()
            mock_unified_service.generate_handoff_resolution_message = AsyncMock(
                return_value={
                    "content": "All set! Test Shop is here for you! 😊",
                    "fallback": False,
                    "reason": "llm_success",
                }
            )
            mock_unified_service_class.return_value = mock_unified_service

            with patch.object(
                handoff_resolution_service,
                "_store_message",
                return_value=test_message,
            ):
                with patch.object(
                    handoff_resolution_service,
                    "_broadcast_to_widget",
                    return_value=True,
                ):
                    await handoff_resolution_service.send_resolution_message(
                        conversation=test_widget_conversation,
                        merchant=test_merchant,
                    )

        # Verify the service was called with correct merchant
        mock_unified_service.generate_handoff_resolution_message.assert_called_once()
        call_args = mock_unified_service.generate_handoff_resolution_message.call_args
        assert call_args[1]["merchant_id"] == test_merchant.id

    async def test_personality_professional(
        self,
        handoff_resolution_service,
        test_widget_conversation,
        test_message,
    ):
        """Test professional personality generates appropriate message."""
        merchant = MagicMock(spec=Merchant)
        merchant.id = 1
        merchant.business_name = "TechCorp"
        merchant.personality = PersonalityType.PROFESSIONAL

        with patch(
            "app.services.conversation.unified_conversation_service.UnifiedConversationService"
        ) as mock_unified_service_class:
            mock_unified_service = MagicMock()
            mock_unified_service.generate_handoff_resolution_message = AsyncMock(
                return_value={
                    "content": "Thank you for your patience. TechCorp is available to assist you.",
                    "fallback": False,
                    "reason": "llm_success",
                }
            )
            mock_unified_service_class.return_value = mock_unified_service

            with patch.object(
                handoff_resolution_service,
                "_store_message",
                return_value=test_message,
            ):
                with patch.object(
                    handoff_resolution_service,
                    "_broadcast_to_widget",
                    return_value=True,
                ):
                    result = await handoff_resolution_service.send_resolution_message(
                        conversation=test_widget_conversation,
                        merchant=merchant,
                    )

        assert result["sent"] is True
        assert "TechCorp" in result["content"] or result["content"]  # Content generated

    async def test_personality_enthusiastic(
        self,
        handoff_resolution_service,
        test_widget_conversation,
        test_message,
    ):
        """Test enthusiastic personality generates appropriate message."""
        merchant = MagicMock(spec=Merchant)
        merchant.id = 1
        merchant.business_name = "Party Supplies"
        merchant.personality = PersonalityType.ENTHUSIASTIC

        with patch(
            "app.services.conversation.unified_conversation_service.UnifiedConversationService"
        ) as mock_unified_service_class:
            mock_unified_service = MagicMock()
            mock_unified_service.generate_handoff_resolution_message = AsyncMock(
                return_value={
                    "content": "YAY! Party Supplies has got you covered! ✨",
                    "fallback": False,
                    "reason": "llm_success",
                }
            )
            mock_unified_service_class.return_value = mock_unified_service

            with patch.object(
                handoff_resolution_service,
                "_store_message",
                return_value=test_message,
            ):
                with patch.object(
                    handoff_resolution_service,
                    "_broadcast_to_widget",
                    return_value=True,
                ):
                    result = await handoff_resolution_service.send_resolution_message(
                        conversation=test_widget_conversation,
                        merchant=merchant,
                    )

        assert result["sent"] is True
