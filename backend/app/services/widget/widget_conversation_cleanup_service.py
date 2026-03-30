"""Widget conversation cleanup service for closing stale conversations.

Closes widget conversations when their Redis sessions expire or become stale.

Story 5-2: Widget Session Management - Conversation Lifecycle
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import redis.asyncio as redis
import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import async_session
from app.models.conversation import Conversation

logger = structlog.get_logger(__name__)


class WidgetConversationCleanupService:
    """Service for cleaning up stale widget conversations.

    Cleanup Strategy:
    - Find widget conversations with status='active'
    - Check if corresponding Redis session exists
    - Close conversations with expired/missing sessions
    - Also close conversations older than 2 hours (safety net)

    This ensures conversations are properly closed even when:
    - Redis TTL expires naturally
    - WebSocket disconnects unexpectedly
    - Browser closes without proper shutdown
    - Network interruptions occur
    """

    SESSION_KEY_PREFIX = "widget:session"
    STALE_THRESHOLD_HOURS = 2

    def __init__(
        self,
        redis_client: redis.Redis | None = None,
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

    def _get_session_key(self, session_id: str) -> str:
        """Generate Redis key for session data.

        Args:
            session_id: Widget session identifier

        Returns:
            Redis key string
        """
        return f"{self.SESSION_KEY_PREFIX}:{session_id}"

    async def cleanup_stale_conversations(self) -> dict:
        """Find and close stale widget conversations.

        Story 5-2 AC3: Background cleanup task for orphaned conversations.

        A conversation is considered stale if:
        1. Status is 'active'
        2. Platform is 'widget'
        3. Redis session is expired/missing OR conversation is older than 2 hours

        Returns:
            Dictionary with cleanup statistics:
            - scanned: Number of conversations checked
            - stale: Number of stale conversations found
            - closed: Number of conversations successfully closed
            - errors: Number of cleanup errors
        """
        now = datetime.now(UTC)
        stats = {
            "scanned": 0,
            "stale": 0,
            "closed": 0,
            "errors": 0,
            "started_at": now.isoformat(),
            "finished_at": None,
        }

        self.logger.info("widget_conversation_cleanup_started")

        try:
            session_factory = async_session()
            async with session_factory() as db:
                # Get all active widget conversations
                result = await db.execute(
                    select(Conversation)
                    .where(Conversation.status == "active")
                    .where(Conversation.platform == "widget")
                    .order_by(Conversation.created_at.desc())
                )
                conversations = result.scalars().all()

                stats["scanned"] = len(conversations)

                if not conversations:
                    self.logger.info("widget_conversation_cleanup_no_active")
                    return stats

                stale_threshold = now - timedelta(hours=self.STALE_THRESHOLD_HOURS)

                for conv in conversations:
                    try:
                        session_id = conv.platform_sender_id
                        is_stale = False
                        reason = ""

                        # Check if conversation is too old
                        conv_created_at = conv.created_at.replace(tzinfo=UTC) if conv.created_at.tzinfo is None else conv.created_at
                        if conv_created_at < stale_threshold:
                            is_stale = True
                            reason = f"older than {self.STALE_THRESHOLD_HOURS} hours"
                        else:
                            # Check if Redis session still exists
                            session_key = self._get_session_key(session_id)
                            session_data = await self.redis.get(session_key)

                            if not session_data:
                                is_stale = True
                                reason = "Redis session expired"
                            else:
                                # Check if session is expired
                                try:
                                    session_dict = json.loads(session_data)
                                    expires_at_str = session_dict.get("expires_at")

                                    if expires_at_str:
                                        expires_at = datetime.fromisoformat(
                                            expires_at_str.replace("Z", "+00:00")
                                        )

                                        if expires_at < now:
                                            is_stale = True
                                            reason = "Session past expiration"
                                except (json.JSONDecodeError, ValueError) as e:
                                    # If we can't parse, consider it stale
                                    is_stale = True
                                    reason = f"Invalid session data: {str(e)}"

                        if is_stale:
                            stats["stale"] += 1

                            # Close the conversation
                            conv.status = "closed"
                            conv.handoff_status = "resolved"

                            conv_created_at = conv.created_at.replace(tzinfo=UTC) if conv.created_at.tzinfo is None else conv.created_at
                            self.logger.info(
                                "widget_conversation_closed",
                                conversation_id=conv.id,
                                session_id=session_id,
                                reason=reason,
                                age_hours=(now - conv_created_at).total_seconds() / 3600,
                            )

                            stats["closed"] += 1

                    except Exception as e:
                        stats["errors"] += 1
                        self.logger.warning(
                            "widget_conversation_cleanup_error",
                            conversation_id=conv.id,
                            error=str(e),
                            error_type=type(e).__name__,
                        )

                # Commit all changes
                if stats["closed"] > 0:
                    await db.commit()
                    self.logger.info(
                        "widget_conversation_cleanup_committed",
                        closed_count=stats["closed"],
                    )

        except Exception as e:
            stats["errors"] += 1
            self.logger.error(
                "widget_conversation_cleanup_failed",
                error=str(e),
                error_type=type(e).__name__,
            )

        stats["finished_at"] = datetime.now(UTC).isoformat()

        self.logger.info(
            "widget_conversation_cleanup_completed",
            scanned=stats["scanned"],
            stale=stats["stale"],
            closed=stats["closed"],
            errors=stats["errors"],
        )

        return stats
