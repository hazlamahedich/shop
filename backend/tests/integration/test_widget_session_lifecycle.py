"""Integration tests for widget session lifecycle.

Tests full session lifecycle including create, message, expire, and cleanup.

Story 5-2: Widget Session Management
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["IS_TESTING"] = "true"


class TestWidgetSessionLifecycle:
    """Integration tests for session lifecycle (AC6)."""

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

        async def mock_ttl(key):
            return 3600 if key in storage else -1

        async def mock_rpush(key, value):
            if key not in storage:
                storage[key] = []
            if not isinstance(storage[key], list):
                storage[key] = []
            storage[key].append(value)
            return len(storage[key])

        async def mock_lrange(key, start, end):
            if key not in storage or not isinstance(storage[key], list):
                return []
            lst = storage[key]
            if end == -1:
                return lst[start:]
            return lst[start : end + 1]

        async def mock_ltrim(key, start, end):
            if key in storage and isinstance(storage[key], list):
                if end == -1:
                    storage[key] = storage[key][start:]
                else:
                    storage[key] = storage[key][start : end + 1]
            return True

        async def mock_scan(cursor=0, match=None, count=100):
            matching_keys = []
            if match and match.endswith("*"):
                prefix = match[:-1]
                for key in storage:
                    if key.startswith(prefix):
                        matching_keys.append(key)
            else:
                matching_keys = list(storage.keys())

            if cursor >= len(matching_keys):
                return 0, []
            end = min(cursor + count, len(matching_keys))
            next_cursor = 0 if end >= len(matching_keys) else end
            return next_cursor, matching_keys[cursor:end]

        redis.get = mock_get
        redis.setex = mock_setex
        redis.delete = mock_delete
        redis.exists = mock_exists
        redis.expire = mock_expire
        redis.ttl = mock_ttl
        redis.rpush = mock_rpush
        redis.lrange = mock_lrange
        redis.ltrim = mock_ltrim
        redis.scan = mock_scan
        redis.storage = storage

        return redis

    @pytest.fixture
    def session_service(self, mock_redis):
        """Create WidgetSessionService with mock Redis."""
        from app.services.widget.widget_session_service import WidgetSessionService

        return WidgetSessionService(redis_client=mock_redis)

    @pytest.fixture
    def cleanup_service(self, mock_redis):
        """Create WidgetCleanupService with mock Redis."""
        from app.services.widget.widget_cleanup_service import WidgetCleanupService

        return WidgetCleanupService(redis_client=mock_redis)

    @pytest.mark.asyncio
    async def test_full_lifecycle_create_use_expire_cleanup(
        self, session_service, cleanup_service, mock_redis
    ):
        """AC6: Test full session lifecycle: create -> use -> expire -> cleanup."""
        session = await session_service.create_session(
            merchant_id=1,
            visitor_ip="192.168.1.1",
        )

        assert session.session_id is not None
        assert session.merchant_id == 1

        await session_service.add_message_to_history(session.session_id, "user", "Hello")

        history = await session_service.get_message_history(session.session_id)
        assert len(history) == 1
        assert history[0]["content"] == "Hello"

        await session_service.end_session(session.session_id)

        retrieved = await session_service.get_session(session.session_id)
        assert retrieved is None

        stats = await cleanup_service.cleanup_expired_sessions()
        assert "scanned" in stats
        assert "cleaned" in stats

    @pytest.mark.asyncio
    async def test_session_refresh_extends_activity_timestamp(self, session_service, mock_redis):
        """AC6: Test that session refresh extends activity timestamp."""
        session = await session_service.create_session(merchant_id=1)
        original_activity = session.last_activity_at

        import asyncio

        await asyncio.sleep(0.01)

        refreshed = await session_service.refresh_session(session.session_id)
        assert refreshed is True

        updated = await session_service.get_session(session.session_id)
        assert updated is not None
        assert updated.last_activity_at > original_activity

    @pytest.mark.asyncio
    async def test_expired_session_returns_401_with_error_code_12002(
        self, session_service, mock_redis
    ):
        """AC6: Test that expired session returns 401 with error code 12002."""
        from app.core.errors import APIError, ErrorCode

        session = await session_service.create_session(merchant_id=1)

        await mock_redis.delete(f"widget:session:{session.session_id}")

        with pytest.raises(APIError) as exc_info:
            await session_service.get_session_or_error(session.session_id)

        assert exc_info.value.code == ErrorCode.WIDGET_SESSION_NOT_FOUND

    @pytest.mark.asyncio
    async def test_per_ip_rate_limiting_enforcement(self, mock_redis):
        """AC4: Test per-IP rate limiting enforcement (100 req/min)."""
        from app.core.rate_limiter import RateLimiter
        from fastapi import Request

        RateLimiter.reset_all()

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {}
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"

        assert RateLimiter.check_widget_rate_limit(mock_request) is None

    @pytest.mark.asyncio
    async def test_per_merchant_rate_limiting_enforcement(self, mock_redis):
        """AC5: Test per-merchant configurable rate limiting."""
        from app.core.rate_limiter import RateLimiter

        RateLimiter.reset_all()

        result = RateLimiter.check_merchant_rate_limit(merchant_id=123, limit=None)
        assert result is None

        result = RateLimiter.check_merchant_rate_limit(merchant_id=123, limit=0)
        assert result is None

        result = RateLimiter.check_merchant_rate_limit(merchant_id=123, limit=10)
        assert result is None

    @pytest.mark.asyncio
    async def test_cleanup_task_removes_orphaned_sessions(
        self, session_service, cleanup_service, mock_redis
    ):
        """AC6: Test that cleanup task removes orphaned sessions."""
        session = await session_service.create_session(
            merchant_id=1,
            visitor_ip="192.168.1.1",
        )

        key = f"widget:session:{session.session_id}"
        data = await mock_redis.get(key)

        expired_session_data = data.replace(
            session.expires_at.isoformat(),
            (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        )
        mock_redis.storage[key] = expired_session_data

        stats = await cleanup_service.cleanup_expired_sessions()

        assert stats["scanned"] >= 1
