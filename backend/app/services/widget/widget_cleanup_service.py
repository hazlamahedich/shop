"""Widget cleanup service for managing orphaned sessions.

Provides background cleanup for widget sessions that may have been
missed by Redis TTL-based expiry (defense-in-depth).

Story 5-2: Widget Session Management
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as redis
import structlog

from app.core.config import settings


logger = structlog.get_logger(__name__)


class WidgetCleanupService:
    """Service for cleaning up orphaned widget sessions.

    Cleanup Strategy:
    - Scan Redis for widget:session:* keys
    - Check if expires_at is in the past
    - Delete expired session data and message history
    - Log cleanup statistics

    This is a backup to Redis TTL-based expiry, handling:
    - Redis restarts without persistence
    - TTL tracking failures
    - Edge cases where sessions aren't cleaned up
    """

    SESSION_KEY_PREFIX = "widget:session"
    MESSAGES_KEY_PREFIX = "widget:messages"

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
    ) -> None:
        """Initialize cleanup service.

        Args:
            redis_client: Optional Redis client instance
        """
        if redis_client is None:
            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            self.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            self.redis = redis_client

        self.logger = structlog.get_logger(__name__)

    async def cleanup_expired_sessions(self) -> dict:
        """Scan and clean up expired widget sessions.

        Story 5-2 AC3: Background cleanup task for orphaned sessions.

        Returns:
            Dictionary with cleanup statistics:
            - scanned: Number of session keys scanned
            - expired: Number of expired sessions found
            - cleaned: Number of sessions successfully cleaned
            - errors: Number of cleanup errors
        """
        now = datetime.now(timezone.utc)
        stats = {
            "scanned": 0,
            "expired": 0,
            "cleaned": 0,
            "errors": 0,
            "started_at": now.isoformat(),
            "finished_at": None,
        }

        self.logger.info("widget_cleanup_started")

        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor,
                    match=f"{self.SESSION_KEY_PREFIX}:*",
                    count=100,
                )

                for key in keys:
                    stats["scanned"] += 1

                    try:
                        data = await self.redis.get(key)
                        if not data:
                            continue

                        session_dict = json.loads(data)
                        expires_at_str = session_dict.get("expires_at")

                        if not expires_at_str:
                            continue

                        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))

                        if expires_at < now:
                            stats["expired"] += 1
                            session_id = session_dict.get("session_id", "unknown")

                            messages_key = f"{self.MESSAGES_KEY_PREFIX}:{session_id}"
                            deleted = await self.redis.delete(key, messages_key)

                            if deleted > 0:
                                stats["cleaned"] += 1
                                self.logger.debug(
                                    "widget_session_cleaned",
                                    session_id=session_id,
                                )

                    except (json.JSONDecodeError, ValueError, KeyError) as e:
                        stats["errors"] += 1
                        self.logger.warning(
                            "widget_cleanup_parse_error",
                            key=key,
                            error=str(e),
                        )

                if cursor == 0:
                    break

        except Exception as e:
            stats["errors"] += 1
            self.logger.error(
                "widget_cleanup_failed",
                error=str(e),
                error_type=type(e).__name__,
            )

        stats["finished_at"] = datetime.now(timezone.utc).isoformat()

        self.logger.info(
            "widget_cleanup_completed",
            scanned=stats["scanned"],
            expired=stats["expired"],
            cleaned=stats["cleaned"],
            errors=stats["errors"],
        )

        return stats
