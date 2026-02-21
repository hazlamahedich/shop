"""Tests for HybridModeMiddleware.

Story 5-10 Task 19: Hybrid Mode (@bot Mentions)

Tests hybrid mode bot response logic.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.services.conversation.middleware.hybrid_mode_middleware import (
    HybridModeMiddleware,
)
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
)


@pytest.fixture
def middleware():
    """Create HybridModeMiddleware instance."""
    return HybridModeMiddleware()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def context():
    """Create conversation context."""
    return ConversationContext(
        session_id="test-session-123",
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=[],
        metadata={},
    )


@pytest.fixture
def mock_conversation_disabled():
    """Create mock conversation with hybrid mode disabled."""
    conv = MagicMock(spec=Conversation)
    conv.conversation_data = {}
    return conv


@pytest.fixture
def mock_conversation_enabled():
    """Create mock conversation with hybrid mode enabled."""
    conv = MagicMock(spec=Conversation)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=2)
    conv.conversation_data = {
        "hybrid_mode": {
            "enabled": True,
            "activated_at": now.isoformat(),
            "expires_at": expires.isoformat(),
        }
    }
    return conv


@pytest.fixture
def mock_conversation_expired():
    """Create mock conversation with expired hybrid mode."""
    conv = MagicMock(spec=Conversation)
    expired = datetime.now(timezone.utc) - timedelta(hours=1)
    conv.conversation_data = {
        "hybrid_mode": {
            "enabled": True,
            "activated_at": expired.isoformat(),
            "expires_at": expired.isoformat(),
        }
    }
    return conv


class TestShouldBotRespond:
    """Tests for should_bot_respond method."""

    @pytest.mark.asyncio
    async def test_responds_when_no_conversation(
        self,
        middleware,
        mock_db,
        context,
    ):
        """Bot should respond when no conversation exists."""
        with patch.object(middleware, "_get_conversation", return_value=None):
            should_respond, message = await middleware.should_bot_respond(
                db=mock_db,
                context=context,
                message="hello",
            )

        assert should_respond is True
        assert message is None

    @pytest.mark.asyncio
    async def test_responds_when_hybrid_mode_disabled(
        self,
        middleware,
        mock_db,
        context,
        mock_conversation_disabled,
    ):
        """Bot should respond when hybrid mode is disabled."""
        with patch.object(
            middleware,
            "_get_conversation",
            return_value=mock_conversation_disabled,
        ):
            should_respond, message = await middleware.should_bot_respond(
                db=mock_db,
                context=context,
                message="hello",
            )

        assert should_respond is True
        assert message is None

    @pytest.mark.asyncio
    async def test_silent_when_hybrid_mode_enabled(
        self,
        middleware,
        mock_db,
        context,
        mock_conversation_enabled,
    ):
        """Bot should stay silent when hybrid mode is enabled."""
        with patch.object(
            middleware,
            "_get_conversation",
            return_value=mock_conversation_enabled,
        ):
            should_respond, message = await middleware.should_bot_respond(
                db=mock_db,
                context=context,
                message="hello",
            )

        assert should_respond is False
        assert message is not None
        assert "@bot" in message

    @pytest.mark.asyncio
    async def test_responds_to_bot_mention(
        self,
        middleware,
        mock_db,
        context,
        mock_conversation_enabled,
    ):
        """Bot should respond to @bot mention in hybrid mode."""
        with patch.object(
            middleware,
            "_get_conversation",
            return_value=mock_conversation_enabled,
        ):
            should_respond, message = await middleware.should_bot_respond(
                db=mock_db,
                context=context,
                message="@bot help",
            )

        assert should_respond is True
        assert message is None

    @pytest.mark.asyncio
    async def test_responds_to_case_insensitive_mention(
        self,
        middleware,
        mock_db,
        context,
        mock_conversation_enabled,
    ):
        """@bot mention should work case-insensitively."""
        with patch.object(
            middleware,
            "_get_conversation",
            return_value=mock_conversation_enabled,
        ):
            should_respond, message = await middleware.should_bot_respond(
                db=mock_db,
                context=context,
                message="@BOT HELP",
            )

        assert should_respond is True

    @pytest.mark.asyncio
    async def test_responds_when_hybrid_mode_expired(
        self,
        middleware,
        mock_db,
        context,
        mock_conversation_expired,
    ):
        """Bot should respond when hybrid mode has expired."""
        with patch.object(
            middleware,
            "_get_conversation",
            return_value=mock_conversation_expired,
        ):
            should_respond, message = await middleware.should_bot_respond(
                db=mock_db,
                context=context,
                message="hello",
            )

        assert should_respond is True


class TestBotMentionDetection:
    """Tests for @bot mention detection."""

    def test_detects_lowercase_mention(self, middleware):
        """Should detect @bot in lowercase."""
        assert middleware._is_bot_mentioned("@bot help") is True

    def test_detects_uppercase_mention(self, middleware):
        """Should detect @BOT in uppercase."""
        assert middleware._is_bot_mentioned("@BOT HELP") is True

    def test_detects_mixed_case_mention(self, middleware):
        """Should detect @Bot in mixed case."""
        assert middleware._is_bot_mentioned("@Bot what's up") is True

    def test_detects_mention_mid_message(self, middleware):
        """Should detect @bot in middle of message."""
        assert middleware._is_bot_mentioned("Hey @bot can you help?") is True

    def test_detects_mention_end_message(self, middleware):
        """Should detect @bot at end of message."""
        assert middleware._is_bot_mentioned("Help me @bot") is True

    def test_no_match_without_mention(self, middleware):
        """Should not match without @bot."""
        assert middleware._is_bot_mentioned("hello there") is False
        assert middleware._is_bot_mentioned("bot help") is False

    def test_no_match_partial_word(self, middleware):
        """Should not match partial words like @botany."""
        assert middleware._is_bot_mentioned("@botany plants") is False
        assert middleware._is_bot_mentioned("@bottle water") is False


class TestHybridModeExpiry:
    """Tests for hybrid mode expiry logic."""

    def test_not_expired_when_valid(self, middleware):
        """Should not be expired when within time limit."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)

        hybrid_mode = {
            "enabled": True,
            "expires_at": expires.isoformat(),
        }

        assert middleware._is_hybrid_mode_expired(hybrid_mode) is False

    def test_expired_when_past(self, middleware):
        """Should be expired when past expiry time."""
        expired = datetime.now(timezone.utc) - timedelta(hours=1)

        hybrid_mode = {
            "enabled": True,
            "expires_at": expired.isoformat(),
        }

        assert middleware._is_hybrid_mode_expired(hybrid_mode) is True

    def test_expired_when_no_expiry(self, middleware):
        """Should not be expired when no expiry set."""
        hybrid_mode = {
            "enabled": True,
        }

        assert middleware._is_hybrid_mode_expired(hybrid_mode) is False

    def test_expired_when_malformed_date(self, middleware):
        """Should be expired (fail-safe) when date is malformed."""
        hybrid_mode = {
            "enabled": True,
            "expires_at": "invalid-date",
        }

        assert middleware._is_hybrid_mode_expired(hybrid_mode) is True


class TestActivateHybridMode:
    """Tests for activating hybrid mode."""

    @pytest.mark.asyncio
    async def test_activates_hybrid_mode(
        self,
        middleware,
        mock_db,
        context,
    ):
        """Should activate hybrid mode."""
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.conversation_data = {}

        with patch.object(
            middleware,
            "_get_conversation",
            return_value=mock_conversation,
        ):
            await middleware.activate_hybrid_mode(
                db=mock_db,
                context=context,
                reason="human_handoff",
            )

        hybrid_mode = mock_conversation.conversation_data.get("hybrid_mode")
        assert hybrid_mode is not None
        assert hybrid_mode["enabled"] is True
        assert "expires_at" in hybrid_mode
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_conversation_does_nothing(
        self,
        middleware,
        mock_db,
        context,
    ):
        """Should do nothing if no conversation exists."""
        with patch.object(middleware, "_get_conversation", return_value=None):
            await middleware.activate_hybrid_mode(
                db=mock_db,
                context=context,
            )

        mock_db.commit.assert_not_called()


class TestDeactivateHybridMode:
    """Tests for deactivating hybrid mode."""

    @pytest.mark.asyncio
    async def test_deactivates_hybrid_mode(
        self,
        middleware,
        mock_db,
        context,
    ):
        """Should deactivate hybrid mode."""
        mock_conversation = MagicMock(spec=Conversation)
        mock_conversation.conversation_data = {"hybrid_mode": {"enabled": True}}

        with patch.object(
            middleware,
            "_get_conversation",
            return_value=mock_conversation,
        ):
            await middleware.deactivate_hybrid_mode(
                db=mock_db,
                context=context,
            )

        hybrid_mode = mock_conversation.conversation_data.get("hybrid_mode")
        assert hybrid_mode["enabled"] is False
        mock_db.commit.assert_called_once()


class TestGetHybridModeStatus:
    """Tests for getting hybrid mode status."""

    def test_status_when_disabled(self, middleware, mock_conversation_disabled):
        """Should return disabled status."""
        result = middleware.get_hybrid_mode_status(mock_conversation_disabled)

        assert result["enabled"] is False
        assert result["remaining_seconds"] == 0

    def test_status_when_enabled(self, middleware, mock_conversation_enabled):
        """Should return enabled status with remaining time."""
        result = middleware.get_hybrid_mode_status(mock_conversation_enabled)

        assert result["enabled"] is True
        assert result["remaining_seconds"] > 0
        assert "expires_at" in result

    def test_status_when_no_conversation(self, middleware):
        """Should return disabled status when no conversation."""
        result = middleware.get_hybrid_mode_status(None)

        assert result["enabled"] is False

    def test_status_when_expired(self, middleware, mock_conversation_expired):
        """Should return disabled status when expired."""
        result = middleware.get_hybrid_mode_status(mock_conversation_expired)

        assert result["enabled"] is False
