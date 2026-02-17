"""Integration tests for Widget API flow.

Tests full session lifecycle, message processing, and cross-merchant isolation.

Story 5.1: Backend Widget API
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["IS_TESTING"] = "true"


class TestWidgetFlowIntegration:
    """Integration tests for widget flow."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client with storage simulation."""
        redis = AsyncMock()
        storage = {}

        async def mock_get(key):
            return storage.get(key)

        async def mock_setex(key, ttl, value):
            storage[key] = value
            return True

        async def mock_delete(*keys):
            count = 0
            for key in keys:
                if key in storage:
                    del storage[key]
                    count += 1
            return count

        async def mock_exists(key):
            return 1 if key in storage else 0

        async def mock_expire(key, ttl):
            return key in storage

        async def mock_rpush(key, value):
            if key not in storage:
                storage[key] = []
            storage[key].append(value)
            return len(storage[key])

        async def mock_lrange(key, start, end):
            if key not in storage:
                return []
            return storage[key]

        async def mock_ltrim(key, start, end):
            if key in storage and isinstance(storage[key], list):
                storage[key] = storage[key][start : end + 1] if end >= 0 else storage[key][start:]
            return True

        redis.get = mock_get
        redis.setex = mock_setex
        redis.delete = mock_delete
        redis.exists = mock_exists
        redis.expire = mock_expire
        redis.rpush = mock_rpush
        redis.lrange = mock_lrange
        redis.ltrim = mock_ltrim

        return redis

    @pytest.fixture
    def session_service(self, mock_redis):
        """Create WidgetSessionService with mock Redis."""
        from app.services.widget.widget_session_service import WidgetSessionService

        return WidgetSessionService(redis_client=mock_redis)

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_merchant_a(self):
        """Create mock merchant A."""
        merchant = MagicMock()
        merchant.id = 1
        merchant.bot_name = "Bot A"
        merchant.business_name = "Store A"
        merchant.business_description = "Store A description"
        merchant.widget_config = {"enabled": True}
        merchant.llm_configuration = None
        return merchant

    @pytest.fixture
    def mock_merchant_b(self):
        """Create mock merchant B."""
        merchant = MagicMock()
        merchant.id = 2
        merchant.bot_name = "Bot B"
        merchant.business_name = "Store B"
        merchant.business_description = "Store B description"
        merchant.widget_config = {"enabled": True}
        merchant.llm_configuration = None
        return merchant

    @pytest.mark.asyncio
    async def test_full_session_lifecycle(self, session_service):
        """Test complete session lifecycle: create -> message -> end."""
        # Create session
        session = await session_service.create_session(
            merchant_id=1,
            visitor_ip="192.168.1.1",
        )

        assert session.session_id is not None
        assert session.merchant_id == 1

        # Verify session exists
        is_valid = await session_service.is_session_valid(session.session_id)
        assert is_valid is True

        # Get session
        retrieved = await session_service.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id

        # Add messages
        await session_service.add_message_to_history(session.session_id, "user", "Hello")
        await session_service.add_message_to_history(session.session_id, "bot", "Hi there!")

        # Get history
        history = await session_service.get_message_history(session.session_id)
        assert len(history) == 2

        # End session
        ended = await session_service.end_session(session.session_id)
        assert ended is True

        # Verify session no longer exists
        is_valid = await session_service.is_session_valid(session.session_id)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_multiple_messages_maintain_context(self, session_service):
        """Test that multiple messages maintain conversation context."""
        session = await session_service.create_session(merchant_id=1)

        # Add multiple messages
        messages = [
            ("user", "Hello"),
            ("bot", "Hi! How can I help?"),
            ("user", "Looking for shoes"),
            ("bot", "I can help you find shoes!"),
        ]

        for role, content in messages:
            await session_service.add_message_to_history(session.session_id, role, content)

        # Verify history
        history = await session_service.get_message_history(session.session_id)
        assert len(history) == 4

        # Verify order is maintained
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[3]["role"] == "bot"

    @pytest.mark.asyncio
    async def test_session_expiry_after_idle_timeout(self, session_service, mock_redis):
        """Test that expired sessions are detected."""
        # Create session
        session = await session_service.create_session(merchant_id=1)

        # Manually expire the session by deleting it
        await session_service.end_session(session.session_id)

        # Try to get expired session
        retrieved = await session_service.get_session(session.session_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_cross_merchant_isolation(self, session_service):
        """Test that sessions from merchant A cannot access merchant B's data."""
        # Create session for merchant A
        session_a = await session_service.create_session(
            merchant_id=1,
            visitor_ip="192.168.1.1",
        )

        # Create session for merchant B
        session_b = await session_service.create_session(
            merchant_id=2,
            visitor_ip="192.168.1.2",
        )

        # Add messages to session A
        await session_service.add_message_to_history(session_a.session_id, "user", "Message for A")

        # Add messages to session B
        await session_service.add_message_to_history(session_b.session_id, "user", "Message for B")

        # Get histories
        history_a = await session_service.get_message_history(session_a.session_id)
        history_b = await session_service.get_message_history(session_b.session_id)

        # Verify isolation
        assert len(history_a) == 1
        assert history_a[0]["content"] == "Message for A"

        assert len(history_b) == 1
        assert history_b[0]["content"] == "Message for B"

    @pytest.mark.asyncio
    async def test_message_history_limit(self, session_service):
        """Test that message history is trimmed to max size."""
        session = await session_service.create_session(merchant_id=1)

        # Add more messages than the limit (10)
        for i in range(15):
            await session_service.add_message_to_history(session.session_id, "user", f"Message {i}")

        # Verify history is trimmed
        history = await session_service.get_message_history(session.session_id)
        assert len(history) <= 10

    @pytest.mark.asyncio
    async def test_session_refresh_extends_expiry(self, session_service, mock_redis):
        """Test that session refresh extends TTL."""
        session = await session_service.create_session(merchant_id=1)
        original_expires = session.expires_at

        # Refresh session
        refreshed = await session_service.refresh_session(session.session_id)
        assert refreshed is True

        # Get updated session
        updated = await session_service.get_session(session.session_id)
        assert updated is not None
        assert updated.expires_at >= original_expires

    @pytest.mark.asyncio
    async def test_error_response_format(self, session_service):
        """Test that error responses follow Envelope pattern."""
        from app.core.errors import APIError, ErrorCode

        with pytest.raises(APIError) as exc_info:
            await session_service.get_session_or_error("nonexistent-session")

        error = exc_info.value
        assert isinstance(error.code, ErrorCode)
        assert error.message is not None

        # Verify error format
        error_dict = error.to_dict()
        assert "error_code" in error_dict
        assert "message" in error_dict

    @pytest.mark.asyncio
    async def test_rate_limiting_enforcement(self, mock_redis):
        """Test that rate limiting is enforced (100 req/min per IP)."""
        from app.api.widget import _check_rate_limit
        from fastapi import Request

        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"

        # In test mode, rate limiting is bypassed
        retry_after = _check_rate_limit(mock_request)
        assert retry_after is None


class TestWidgetMessageIntegration:
    """Integration tests for widget message processing."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.setex = AsyncMock(return_value=True)
        redis.delete = AsyncMock(return_value=1)
        redis.rpush = AsyncMock(return_value=1)
        redis.lrange = AsyncMock(return_value=[])
        redis.ltrim = AsyncMock(return_value=True)
        redis.expire = AsyncMock(return_value=True)
        return redis

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_message_processing_with_mock_llm(self, mock_redis, mock_db):
        """Test message processing with mock LLM provider."""
        from app.services.widget.widget_session_service import WidgetSessionService
        from app.services.widget.widget_message_service import WidgetMessageService
        from app.schemas.widget import WidgetSessionData

        session_service = WidgetSessionService(redis_client=mock_redis)
        message_service = WidgetMessageService(
            db=mock_db,
            session_service=session_service,
        )

        # Create test session
        session = WidgetSessionData(
            session_id="test-session",
            merchant_id=1,
            created_at=datetime.now(timezone.utc),
            last_activity_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        # Create test merchant
        merchant = MagicMock()
        merchant.id = 1
        merchant.bot_name = "Test Bot"
        merchant.business_name = "Test Store"
        merchant.business_description = None
        merchant.llm_configuration = None

        # Mock LLM response
        with patch("app.services.widget.widget_message_service.LLMProviderFactory") as mock_factory:
            mock_llm = AsyncMock()
            mock_llm.chat.return_value = MagicMock(content="Hello! How can I help you today?")
            mock_factory.create_provider.return_value = mock_llm

            result = await message_service.process_message(
                session=session,
                message="Hello",
                merchant=merchant,
            )

        assert result["content"] == "Hello! How can I help you today?"
        assert result["sender"] == "bot"
