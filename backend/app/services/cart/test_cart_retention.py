"""Tests for cart retention service.

Tests Story 2-7: Persistent Cart Sessions
- 30-day extended retention for opted-in shoppers
- Background job cleanup for expired extended carts
- Voluntary data only (operational data preserved)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis

from app.services.cart.cart_retention import CartRetentionService, run_cart_retention_cleanup


class TestCartRetentionService:
    """Tests for CartRetentionService."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return MagicMock(spec=redis.Redis)

    @pytest.fixture
    def retention_service(self, mock_redis):
        """Create cart retention service with mocked Redis."""
        return CartRetentionService(redis_client=mock_redis)

    @pytest.mark.asyncio
    async def test_enable_extended_retention(self, retention_service, mock_redis):
        """Test enabling extended retention for a cart."""
        psid = "test_psid_123"

        await retention_service.enable_extended_retention(psid)

        # Verify setex was called with 30-day TTL
        assert mock_redis.setex.called
        call_args = mock_redis.setex.call_args[0]
        assert "cart_extended_timestamp:" in call_args[0]
        assert call_args[1] == 30 * 24 * 60 * 60  # 30 days in seconds

        # Verify timestamp data was stored
        timestamp_data = json.loads(call_args[2])
        assert timestamp_data["psid"] == psid
        assert "extended_at" in timestamp_data
        assert timestamp_data["retention_days"] == 30

    @pytest.mark.asyncio
    async def test_is_extended_retention_true(self, retention_service, mock_redis):
        """Test is_extended_retention returns True when enabled."""
        psid = "test_psid_123"
        mock_redis.exists.return_value = 1

        result = await retention_service.is_extended_retention(psid)

        assert result is True
        mock_redis.exists.assert_called_once_with(f"cart_extended_timestamp:{psid}")

    @pytest.mark.asyncio
    async def test_is_extended_retention_false(self, retention_service, mock_redis):
        """Test is_extended_retention returns False when not enabled."""
        psid = "test_psid_123"
        mock_redis.exists.return_value = 0

        result = await retention_service.is_extended_retention(psid)

        assert result is False

    @pytest.mark.asyncio
    async def test_get_cart_age_days(self, retention_service, mock_redis):
        """Test getting cart age in days."""
        psid = "test_psid_123"
        created_at = datetime.now(timezone.utc) - timedelta(days=15)

        timestamp_data = json.dumps({
            "psid": psid,
            "extended_at": created_at.isoformat(),
            "retention_days": 30
        })

        mock_redis.get.return_value = timestamp_data

        age = await retention_service.get_cart_age_days(psid)

        assert age == 15

    @pytest.mark.asyncio
    async def test_get_cart_age_days_no_retention(self, retention_service, mock_redis):
        """Test get_cart_age_days returns None when retention not enabled."""
        psid = "test_psid_123"
        mock_redis.get.return_value = None

        age = await retention_service.get_cart_age_days(psid)

        assert age is None

    @pytest.mark.asyncio
    async def test_disable_extended_retention(self, retention_service, mock_redis):
        """Test disabling extended retention."""
        psid = "test_psid_123"

        await retention_service.disable_extended_retention(psid)

        mock_redis.delete.assert_called_once_with(f"cart_extended_timestamp:{psid}")

    @pytest.mark.asyncio
    async def test_cleanup_expired_extended_carts(self, retention_service, mock_redis):
        """Test cleanup of expired extended carts."""
        # Setup mock data
        old_cart_time = datetime.now(timezone.utc) - timedelta(days=35)
        recent_cart_time = datetime.now(timezone.utc) - timedelta(days=15)

        old_timestamp = json.dumps({
            "psid": "old_psid",
            "extended_at": old_cart_time.isoformat(),
            "retention_days": 30
        })

        recent_timestamp = json.dumps({
            "psid": "recent_psid",
            "extended_at": recent_cart_time.isoformat(),
            "retention_days": 30
        })

        # Mock Redis scan to return our test keys
        def mock_scan(cursor=0, match=None, count=None):
            if cursor == "0":
                # First call: return keys and new cursor (0 means done)
                return 0, [
                    f"cart_extended_timestamp:old_psid",
                    f"cart_extended_timestamp:recent_psid"
                ]
            return 0, []

        def mock_get(key):
            if "old_psid" in key:
                return old_timestamp
            elif "recent_psid" in key:
                return recent_timestamp
            return None

        mock_redis.scan.side_effect = mock_scan
        mock_redis.get.side_effect = mock_get
        mock_redis.delete.return_value = 1

        # Run cleanup
        result = await retention_service.cleanup_expired_extended_carts(max_age_days=30)

        # Verify results
        assert result["scanned"] == 2
        assert result["removed"] == 1
        assert result["max_age_days"] == 30

        # Verify delete was called for old cart only
        assert mock_redis.delete.call_count == 1

    @pytest.mark.asyncio
    async def test_cleanup_handles_invalid_timestamp(self, retention_service, mock_redis):
        """Test cleanup handles invalid timestamp data gracefully."""
        # Mock Redis scan to return a key with invalid data
        def mock_scan(cursor=0, match=None, count=None):
            if cursor == "0":
                return 0, ["cart_extended_timestamp:invalid_psid"]
            return 0, []

        mock_redis.scan.side_effect = mock_scan
        mock_redis.get.return_value = "invalid json"
        mock_redis.delete.return_value = 1

        # Run cleanup - should not raise
        result = await retention_service.cleanup_expired_extended_carts()

        # Should remove invalid entry
        assert result["removed"] == 1

    @pytest.mark.asyncio
    async def test_cleanup_error_handling(self, retention_service, mock_redis):
        """Test cleanup handles errors gracefully."""
        # Mock Redis scan to raise error
        mock_redis.scan.side_effect = Exception("Redis connection error")

        # Run cleanup - should raise
        with pytest.raises(Exception, match="Redis connection error"):
            await retention_service.cleanup_expired_extended_carts()

    @pytest.mark.asyncio
    async def test_cleanup_with_pagination(self, retention_service, mock_redis):
        """Test cleanup handles paginated scan results."""
        # Setup mock data for pagination
        def mock_scan(cursor=0, match=None, count=None):
            # Return 100 keys, then paginate
            if cursor == "0":
                keys = [f"cart_extended_timestamp:psid_{i}" for i in range(100)]
                return "1", keys
            elif cursor == "1":
                return 0, []  # Final page
            return 0, []

        def mock_get(key):
            # Return recent timestamp (should not be deleted)
            return json.dumps({
                "psid": key.split(":")[-1],
                "extended_at": datetime.now(timezone.utc).isoformat(),
                "retention_days": 30
            })

        mock_redis.scan.side_effect = mock_scan
        mock_redis.get.side_effect = mock_get

        # Run cleanup
        result = await retention_service.cleanup_expired_extended_carts()

        # Verify all keys were scanned
        assert result["scanned"] == 100
        assert result["removed"] == 0  # All are recent

    @pytest.mark.asyncio
    async def test_run_cart_retention_cleanup_wrapper(self):
        """Test the wrapper function for background job compatibility."""
        with patch("app.services.cart.cart_retention.CartRetentionService") as mock_class:
            mock_service = MagicMock()
            mock_service.cleanup_expired_extended_carts = AsyncMock(return_value={
                "scanned": 10,
                "removed": 2
            })
            mock_class.return_value = mock_service

            result = await run_cart_retention_cleanup()

            assert result["scanned"] == 10
            assert result["removed"] == 2

    @pytest.mark.asyncio
    async def test_enable_extended_retention_return_value(self, retention_service, mock_redis):
        """Test enable_extended_retention returns correct metadata."""
        psid = "test_psid_123"

        result = await retention_service.enable_extended_retention(psid)

        assert result["psid"] == psid
        assert result["extended_retention"] is True
        assert result["retention_days"] == 30
        assert "expires_at" in result

    @pytest.mark.asyncio
    async def test_get_cart_age_days_parse_error(self, retention_service, mock_redis):
        """Test get_cart_age_days handles parse errors."""
        psid = "test_psid_123"
        mock_redis.get.return_value = "not valid json"

        age = await retention_service.get_cart_age_days(psid)

        # Should return None on parse error
        assert age is None
