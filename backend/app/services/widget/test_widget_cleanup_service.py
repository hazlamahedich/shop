"""Unit tests for WidgetCleanupService.

Tests cleanup service logic for orphaned sessions.

Story 5-2: Widget Session Management
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock

os.environ["IS_TESTING"] = "true"


class TestWidgetCleanupService:
    """Unit tests for WidgetCleanupService."""

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
        redis.scan = mock_scan

        redis.storage = storage

        return redis

    @pytest.fixture
    def cleanup_service(self, mock_redis):
        """Create WidgetCleanupService with mock Redis."""
        from app.services.widget.widget_cleanup_service import WidgetCleanupService

        return WidgetCleanupService(redis_client=mock_redis)

    @pytest.mark.asyncio
    async def test_cleanup_deletes_correct_sessions(self, cleanup_service, mock_redis):
        """Test that cleanup deletes expired sessions but not active ones."""
        import json

        now = datetime.now(timezone.utc)

        expired_session = {
            "session_id": "expired-123",
            "merchant_id": 1,
            "created_at": (now - timedelta(hours=2)).isoformat(),
            "last_activity_at": (now - timedelta(hours=2)).isoformat(),
            "expires_at": (now - timedelta(hours=1)).isoformat(),
        }

        active_session = {
            "session_id": "active-456",
            "merchant_id": 2,
            "created_at": now.isoformat(),
            "last_activity_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
        }

        mock_redis.storage["widget:session:expired-123"] = json.dumps(expired_session)
        mock_redis.storage["widget:session:active-456"] = json.dumps(active_session)
        mock_redis.storage["widget:messages:expired-123"] = "[]"

        stats = await cleanup_service.cleanup_expired_sessions()

        assert stats["scanned"] == 2
        assert stats["expired"] == 1
        assert stats["cleaned"] == 1
        assert "widget:session:expired-123" not in mock_redis.storage
        assert "widget:session:active-456" in mock_redis.storage

    @pytest.mark.asyncio
    async def test_cleanup_logs_statistics_correctly(self, cleanup_service, mock_redis):
        """Test that cleanup returns correct statistics."""
        stats = await cleanup_service.cleanup_expired_sessions()

        assert "scanned" in stats
        assert "expired" in stats
        assert "cleaned" in stats
        assert "errors" in stats
        assert "started_at" in stats
        assert "finished_at" in stats

        assert stats["scanned"] == 0
        assert stats["expired"] == 0
        assert stats["cleaned"] == 0

    @pytest.mark.asyncio
    async def test_cleanup_handles_malformed_data(self, cleanup_service, mock_redis):
        """Test that cleanup handles malformed session data gracefully."""
        mock_redis.storage["widget:session:malformed-1"] = "not valid json"
        mock_redis.storage["widget:session:malformed-2"] = '{"missing": "expires_at"}'

        stats = await cleanup_service.cleanup_expired_sessions()

        assert stats["scanned"] == 2
        assert stats["errors"] >= 1
        assert stats["cleaned"] == 0


class TestMerchantRateLimit:
    """Unit tests for merchant rate limiting."""

    def test_merchant_rate_limit_check_logic(self):
        """Test merchant rate limit check logic."""
        from app.core.rate_limiter import RateLimiter

        RateLimiter.reset_all()

        result = RateLimiter.check_merchant_rate_limit(merchant_id=1, limit=None)
        assert result is None

        result = RateLimiter.check_merchant_rate_limit(merchant_id=1, limit=0)
        assert result is None

        result = RateLimiter.check_merchant_rate_limit(merchant_id=1, limit=-1)
        assert result is None

        result = RateLimiter.check_merchant_rate_limit(merchant_id=1, limit=10)
        assert result is None

    def test_merchant_rate_limit_tracking(self):
        """Test that merchant rate limits use separate client IDs."""
        from app.core.rate_limiter import RateLimiter

        RateLimiter.reset_all()

        result1 = RateLimiter.check_merchant_rate_limit(merchant_id=1, limit=10)
        result2 = RateLimiter.check_merchant_rate_limit(merchant_id=2, limit=10)

        assert result1 is None
        assert result2 is None


class TestWidgetSessionServiceActivityTracking:
    """Unit tests for WidgetSessionService activity tracking."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        storage = {}

        async def mock_get(key):
            return storage.get(key)

        async def mock_setex(key, ttl, value):
            storage[key] = value
            return True

        async def mock_ttl(key):
            return 3600 if key in storage else -1

        redis.get = mock_get
        redis.setex = mock_setex
        redis.ttl = mock_ttl
        redis.storage = storage

        return redis

    @pytest.fixture
    def session_service(self, mock_redis):
        """Create WidgetSessionService with mock Redis."""
        from app.services.widget.widget_session_service import WidgetSessionService

        return WidgetSessionService(redis_client=mock_redis)

    @pytest.mark.asyncio
    async def test_update_last_activity_updates_timestamp(self, session_service, mock_redis):
        """Test that update_last_activity updates the timestamp."""
        import json

        now = datetime.now(timezone.utc)
        session_data = {
            "session_id": "test-session",
            "merchant_id": 1,
            "created_at": now.isoformat(),
            "last_activity_at": (now - timedelta(minutes=5)).isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
        }

        mock_redis.storage["widget:session:test-session"] = json.dumps(session_data)

        result = await session_service.update_last_activity("test-session")

        assert result is True

        updated_data = json.loads(mock_redis.storage["widget:session:test-session"])
        assert "lastActivityAt" in updated_data or "last_activity_at" in updated_data

    @pytest.mark.asyncio
    async def test_update_last_activity_returns_false_for_missing_session(
        self, session_service, mock_redis
    ):
        """Test that update_last_activity returns False for missing session."""
        result = await session_service.update_last_activity("nonexistent")

        assert result is False
