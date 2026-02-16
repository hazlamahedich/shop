"""
Integration tests for hybrid mode message flow.

Story 4-9: Tests the full message flow with hybrid mode:
- Bot stays silent when hybrid mode is active
- Bot responds to @bot mentions in hybrid mode
- Hybrid mode auto-expiry allows bot to respond

Priority: P0 - Tests critical AC4 behavior end-to-end
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch


@pytest.mark.asyncio
class TestHybridModeMessageFlow:
    """Integration tests for hybrid mode in message processing."""

    @pytest.fixture
    def mock_webhook_payload(self):
        """Create a mock webhook payload."""
        payload = MagicMock()
        payload.sender_id = "test_psid_12345"
        payload.message_text = "Hello, I need help"
        payload.postback_payload = None
        return payload

    @pytest.fixture
    def mock_conversation_with_hybrid_mode(self):
        """Create a mock conversation with hybrid mode enabled."""
        conversation = MagicMock()
        conversation.id = 123
        conversation.merchant_id = 1
        conversation.platform_sender_id = "test_psid_12345"
        conversation.conversation_data = {
            "hybrid_mode": {
                "enabled": True,
                "activated_at": datetime.now(timezone.utc).isoformat(),
                "activated_by": "merchant",
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            }
        }
        return conversation

    @pytest.fixture
    def mock_conversation_without_hybrid_mode(self):
        """Create a mock conversation without hybrid mode."""
        conversation = MagicMock()
        conversation.id = 123
        conversation.merchant_id = 1
        conversation.platform_sender_id = "test_psid_12345"
        conversation.conversation_data = {}
        return conversation

    @pytest.fixture
    def mock_conversation_expired_hybrid_mode(self):
        """Create a mock conversation with expired hybrid mode."""
        conversation = MagicMock()
        conversation.id = 123
        conversation.merchant_id = 1
        conversation.platform_sender_id = "test_psid_12345"
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        conversation.conversation_data = {
            "hybrid_mode": {
                "enabled": True,
                "activated_at": expired_time.isoformat(),
                "expires_at": expired_time.isoformat(),
            }
        }
        return conversation

    def test_should_bot_respond_returns_true_when_hybrid_mode_disabled(self):
        """Bot should respond when hybrid mode is disabled."""
        from app.services.messaging.message_processor import MessageProcessor

        processor = MessageProcessor(merchant_id=1)
        conversation = MagicMock()
        conversation.id = 123
        conversation.conversation_data = {}

        result = processor.should_bot_respond(conversation, "Hello")

        assert result is True

    def test_should_bot_respond_returns_false_when_hybrid_mode_enabled(self):
        """Bot should not respond when hybrid mode is enabled."""
        from app.services.messaging.message_processor import MessageProcessor

        processor = MessageProcessor(merchant_id=1)
        conversation = MagicMock()
        conversation.id = 123
        conversation.conversation_data = {
            "hybrid_mode": {
                "enabled": True,
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            }
        }

        result = processor.should_bot_respond(conversation, "Hello")

        assert result is False

    def test_should_bot_respond_returns_true_for_bot_mention_in_hybrid_mode(self):
        """Bot should respond to @bot mentions even in hybrid mode."""
        from app.services.messaging.message_processor import MessageProcessor

        processor = MessageProcessor(merchant_id=1)
        conversation = MagicMock()
        conversation.id = 123
        conversation.conversation_data = {
            "hybrid_mode": {
                "enabled": True,
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            }
        }

        result = processor.should_bot_respond(conversation, "@bot help")

        assert result is True

    def test_should_bot_respond_returns_true_when_hybrid_mode_expired(self):
        """Bot should respond when hybrid mode has expired."""
        from app.services.messaging.message_processor import MessageProcessor

        processor = MessageProcessor(merchant_id=1)
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        conversation = MagicMock()
        conversation.id = 123
        conversation.conversation_data = {
            "hybrid_mode": {
                "enabled": True,
                "expires_at": expired_time.isoformat(),
            }
        }

        result = processor.should_bot_respond(conversation, "Hello")

        assert result is True

    @pytest.mark.asyncio
    async def test_full_message_flow_bot_silent_in_hybrid_mode(
        self,
        mock_webhook_payload,
        mock_conversation_with_hybrid_mode,
    ):
        """Full flow test: bot stays silent when hybrid mode is active."""
        from app.services.messaging.message_processor import MessageProcessor

        processor = MessageProcessor(merchant_id=1)

        with patch.object(
            processor, "_get_conversation", return_value=mock_conversation_with_hybrid_mode
        ):
            should_respond = processor.should_bot_respond(
                mock_conversation_with_hybrid_mode, mock_webhook_payload.message_text
            )

            assert should_respond is False

    @pytest.mark.asyncio
    async def test_full_message_flow_bot_responds_to_mention_in_hybrid_mode(
        self,
        mock_webhook_payload,
        mock_conversation_with_hybrid_mode,
    ):
        """Full flow test: bot responds to @bot mention in hybrid mode."""
        from app.services.messaging.message_processor import MessageProcessor

        processor = MessageProcessor(merchant_id=1)
        mock_webhook_payload.message_text = "@bot I need help with my order"

        should_respond = processor.should_bot_respond(
            mock_conversation_with_hybrid_mode, mock_webhook_payload.message_text
        )

        assert should_respond is True

    @pytest.mark.asyncio
    async def test_full_message_flow_expired_hybrid_mode_allows_bot_response(
        self,
        mock_webhook_payload,
        mock_conversation_expired_hybrid_mode,
    ):
        """Full flow test: expired hybrid mode allows bot to respond."""
        from app.services.messaging.message_processor import MessageProcessor

        processor = MessageProcessor(merchant_id=1)

        should_respond = processor.should_bot_respond(
            mock_conversation_expired_hybrid_mode, mock_webhook_payload.message_text
        )

        assert should_respond is True
