"""Unit tests for WidgetSessionService.

Tests session lifecycle management including creation, retrieval,
refresh, expiry, and cleanup.

Story 5.1: Backend Widget API
"""

from __future__ import annotations

import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.errors import APIError, ErrorCode
from app.schemas.widget import WidgetSessionData
from app.services.widget.widget_session_service import WidgetSessionService


class TestWidgetSessionService:
    """Tests for WidgetSessionService."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock(return_value=True)
        redis.delete = AsyncMock(return_value=1)
        redis.exists = AsyncMock(return_value=0)
        redis.expire = AsyncMock(return_value=True)
        redis.rpush = AsyncMock(return_value=1)
        redis.lrange = AsyncMock(return_value=[])
        redis.ltrim = AsyncMock(return_value=True)
        return redis

    @pytest.fixture
    def session_service(self, mock_redis):
        """Create WidgetSessionService with mock Redis."""
        return WidgetSessionService(redis_client=mock_redis)

    @pytest.mark.asyncio
    async def test_create_session_returns_valid_session(self, session_service, mock_redis):
        """Test that create_session returns valid session data."""
        session = await session_service.create_session(
            merchant_id=1,
            visitor_ip="192.168.1.1",
            user_agent="TestAgent/1.0",
        )

        assert session.session_id is not None
        assert session.merchant_id == 1
        assert session.visitor_ip == "192.168.1.1"
        assert session.user_agent == "TestAgent/1.0"
        assert session.created_at is not None
        assert session.expires_at > session.created_at

        # Verify Redis was called
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_stores_in_redis(self, session_service, mock_redis):
        """Test that session is stored in Redis with correct key pattern."""
        session = await session_service.create_session(merchant_id=1)

        # Check setex was called with correct key prefix
        call_args = mock_redis.setex.call_args
        key = call_args[0][0]
        assert key.startswith("widget:session:")

    @pytest.mark.asyncio
    async def test_get_session_returns_session_when_exists(self, session_service, mock_redis):
        """Test that get_session returns session data when it exists."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)

        stored_session = WidgetSessionData(
            session_id="test-session-id",
            merchant_id=1,
            created_at=now,
            last_activity_at=now,
            expires_at=expires,
        )
        mock_redis.get.return_value = stored_session.model_dump_json()

        result = await session_service.get_session("test-session-id")

        assert result is not None
        assert result.session_id == "test-session-id"
        assert result.merchant_id == 1

    @pytest.mark.asyncio
    async def test_get_session_returns_none_when_not_found(self, session_service, mock_redis):
        """Test that get_session returns None when session doesn't exist."""
        mock_redis.get.return_value = None

        result = await session_service.get_session("nonexistent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_session_returns_none_on_invalid_json(self, session_service, mock_redis):
        """Test that get_session handles invalid JSON gracefully."""
        mock_redis.get.return_value = "invalid json"

        result = await session_service.get_session("test-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_refresh_session_updates_timestamp(self, session_service, mock_redis):
        """Test that refresh_session updates last_activity_at."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)

        stored_session = WidgetSessionData(
            session_id="test-session-id",
            merchant_id=1,
            created_at=now - timedelta(minutes=30),
            last_activity_at=now - timedelta(minutes=30),
            expires_at=expires,
        )
        mock_redis.get.return_value = stored_session.model_dump_json()

        result = await session_service.refresh_session("test-session-id")

        assert result is True
        mock_redis.setex.assert_called()
        mock_redis.expire.assert_called()

    @pytest.mark.asyncio
    async def test_refresh_session_returns_false_when_not_found(self, session_service, mock_redis):
        """Test that refresh_session returns False for nonexistent session."""
        mock_redis.get.return_value = None

        result = await session_service.refresh_session("nonexistent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_end_session_deletes_from_redis(self, session_service, mock_redis):
        """Test that end_session deletes session and messages."""
        mock_redis.delete.return_value = 2  # Both keys deleted

        result = await session_service.end_session("test-session-id")

        assert result is True
        mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_session_returns_false_when_not_found(self, session_service, mock_redis):
        """Test that end_session returns False for nonexistent session."""
        mock_redis.delete.return_value = 0

        result = await session_service.end_session("nonexistent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_is_session_valid_returns_true_when_exists(self, session_service, mock_redis):
        """Test that is_session_valid returns True for existing session."""
        mock_redis.exists.return_value = 1

        result = await session_service.is_session_valid("test-session-id")

        assert result is True

    @pytest.mark.asyncio
    async def test_is_session_valid_returns_false_when_not_exists(
        self, session_service, mock_redis
    ):
        """Test that is_session_valid returns False for nonexistent session."""
        mock_redis.exists.return_value = 0

        result = await session_service.is_session_valid("nonexistent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_session_or_error_raises_not_found(self, session_service, mock_redis):
        """Test that get_session_or_error raises WIDGET_SESSION_NOT_FOUND."""
        mock_redis.get.return_value = None

        with pytest.raises(APIError) as exc_info:
            await session_service.get_session_or_error("nonexistent-id")

        assert exc_info.value.code == ErrorCode.WIDGET_SESSION_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_session_or_error_raises_expired(self, session_service, mock_redis):
        """Test that get_session_or_error raises WIDGET_SESSION_EXPIRED for expired session."""
        now = datetime.now(timezone.utc)
        expired_at = now - timedelta(hours=1)  # Expired 1 hour ago

        stored_session = WidgetSessionData(
            session_id="test-session-id",
            merchant_id=1,
            created_at=now - timedelta(hours=2),
            last_activity_at=now - timedelta(hours=2),
            expires_at=expired_at,
        )
        mock_redis.get.return_value = stored_session.model_dump_json()

        with pytest.raises(APIError) as exc_info:
            await session_service.get_session_or_error("test-session-id")

        assert exc_info.value.code == ErrorCode.WIDGET_SESSION_EXPIRED

    @pytest.mark.asyncio
    async def test_get_session_or_error_returns_valid_session(self, session_service, mock_redis):
        """Test that get_session_or_error returns valid session."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)

        stored_session = WidgetSessionData(
            session_id="test-session-id",
            merchant_id=1,
            created_at=now,
            last_activity_at=now,
            expires_at=expires,
        )
        mock_redis.get.return_value = stored_session.model_dump_json()

        result = await session_service.get_session_or_error("test-session-id")

        assert result.session_id == "test-session-id"

    @pytest.mark.asyncio
    async def test_add_message_to_history(self, session_service, mock_redis):
        """Test that add_message_to_history stores message."""
        await session_service.add_message_to_history(
            session_id="test-session-id",
            role="user",
            content="Hello!",
        )

        mock_redis.rpush.assert_called_once()
        mock_redis.ltrim.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_message_history_returns_messages(self, session_service, mock_redis):
        """Test that get_message_history returns stored messages."""
        messages = [
            json.dumps({"role": "user", "content": "Hello!", "timestamp": "2026-01-01T00:00:00Z"}),
            json.dumps(
                {"role": "bot", "content": "Hi there!", "timestamp": "2026-01-01T00:00:01Z"}
            ),
        ]
        mock_redis.lrange.return_value = messages

        result = await session_service.get_message_history("test-session-id")

        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "bot"

    @pytest.mark.asyncio
    async def test_get_message_history_handles_invalid_json(self, session_service, mock_redis):
        """Test that get_message_history handles invalid JSON gracefully."""
        messages = [
            json.dumps({"role": "user", "content": "Hello!", "timestamp": "2026-01-01T00:00:00Z"}),
            "invalid json",
        ]
        mock_redis.lrange.return_value = messages

        result = await session_service.get_message_history("test-session-id")

        assert len(result) == 1  # Only valid message returned
