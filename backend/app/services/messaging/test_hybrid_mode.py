"""
Unit tests for hybrid mode functionality in MessageProcessor.

Story 4-9: Tests should_bot_respond logic including:
- Hybrid mode enabled/disabled
- @bot mentions in hybrid mode
- Auto-expiry of hybrid mode
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock


class TestShouldBotRespond:
    """Test the should_bot_respond helper method."""

    @pytest.fixture
    def message_processor(self):
        """Create a MessageProcessor instance for testing."""
        from app.services.messaging.message_processor import MessageProcessor

        return MessageProcessor(merchant_id=1)

    @pytest.fixture
    def mock_conversation(self):
        """Create a mock conversation with configurable conversation_data."""
        conversation = MagicMock()
        conversation.id = 123
        conversation.conversation_data = {}
        return conversation

    def test_returns_true_when_hybrid_mode_disabled(self, message_processor, mock_conversation):
        """Bot should respond when hybrid mode is disabled."""
        mock_conversation.conversation_data = {}

        result = message_processor.should_bot_respond(mock_conversation, "hello")

        assert result is True

    def test_returns_false_when_hybrid_mode_enabled(self, message_processor, mock_conversation):
        """Bot should not respond when hybrid mode is enabled (unless @bot mention)."""
        mock_conversation.conversation_data = {
            "hybrid_mode": {
                "enabled": True,
                "activated_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            }
        }

        result = message_processor.should_bot_respond(mock_conversation, "hello")

        assert result is False

    def test_returns_true_for_bot_mention_in_hybrid_mode(
        self, message_processor, mock_conversation
    ):
        """Bot should respond to @bot mentions even in hybrid mode."""
        mock_conversation.conversation_data = {
            "hybrid_mode": {
                "enabled": True,
                "activated_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            }
        }

        result = message_processor.should_bot_respond(mock_conversation, "@bot help")

        assert result is True

    def test_returns_true_for_bot_mention_case_insensitive(
        self, message_processor, mock_conversation
    ):
        """Bot mention should work case-insensitively."""
        mock_conversation.conversation_data = {
            "hybrid_mode": {
                "enabled": True,
                "activated_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            }
        }

        assert message_processor.should_bot_respond(mock_conversation, "@BOT HELP") is True
        assert message_processor.should_bot_respond(mock_conversation, "@Bot what's up") is True

    def test_returns_true_when_hybrid_mode_expired(self, message_processor, mock_conversation):
        """Bot should respond when hybrid mode has expired (2 hours passed)."""
        expired_time = datetime.now(timezone.utc) - timedelta(hours=3)
        mock_conversation.conversation_data = {
            "hybrid_mode": {
                "enabled": True,
                "activated_at": expired_time.isoformat(),
                "expires_at": expired_time.isoformat(),
            }
        }

        result = message_processor.should_bot_respond(mock_conversation, "hello")

        assert result is True

    def test_returns_true_when_no_conversation(self, message_processor):
        """Bot should respond when there's no conversation object."""
        result = message_processor.should_bot_respond(None, "hello")

        assert result is True

    def test_returns_true_when_conversation_data_is_none(
        self, message_processor, mock_conversation
    ):
        """Bot should respond when conversation_data is None."""
        mock_conversation.conversation_data = None

        result = message_processor.should_bot_respond(mock_conversation, "hello")

        assert result is True

    def test_handles_malformed_expires_at(self, message_processor, mock_conversation):
        """Bot should respond (fail-safe) if expires_at is malformed.

        When we can't parse the expiry time, fail-safe behavior means
        the bot SHOULD respond rather than staying silent indefinitely.
        This prevents the bot from being permanently stuck in hybrid mode
        due to data corruption.
        """
        mock_conversation.conversation_data = {
            "hybrid_mode": {
                "enabled": True,
                "expires_at": "invalid-date",
            }
        }

        result = message_processor.should_bot_respond(mock_conversation, "hello")

        assert result is True  # Fail-safe: respond on malformed expiry
