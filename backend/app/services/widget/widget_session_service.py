"""Widget session service for managing anonymous widget sessions.

Provides session lifecycle management with Redis-based storage,
TTL-based expiry, and activity tracking.

Story 5.1: Backend Widget API
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from uuid import uuid4

import redis.asyncio as redis
import structlog

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.schemas.widget import WidgetSessionData


logger = structlog.get_logger(__name__)


class WidgetSessionService:
    """Service for managing widget session lifecycle.

    Session Management:
    - Store sessions in Redis with TTL-based expiry
    - Track session activity for expiry refresh
    - Support anonymous sessions (no auth required)
    - Isolate sessions per merchant

    Redis Keys:
    - widget:session:{session_id} - Session data (1 hour TTL)
    - widget:messages:{session_id} - Message history (1 hour TTL, max 10)
    """

    SESSION_TTL_SECONDS = 3600
    KEY_PREFIX = "widget:session"
    MESSAGES_KEY_PREFIX = "widget:messages"
    MAX_MESSAGE_HISTORY = 10

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
    ) -> None:
        """Initialize session service.

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
        return f"{self.KEY_PREFIX}:{session_id}"

    def _get_messages_key(self, session_id: str) -> str:
        """Generate Redis key for message history.

        Args:
            session_id: Widget session identifier

        Returns:
            Redis key string
        """
        return f"{self.MESSAGES_KEY_PREFIX}:{session_id}"

    async def create_session(
        self,
        merchant_id: int,
        visitor_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> WidgetSessionData:
        """Create a new anonymous widget session.

        Args:
            merchant_id: The merchant ID for this session
            visitor_ip: Optional visitor IP for analytics
            user_agent: Optional user agent for analytics

        Returns:
            WidgetSessionData with session details
        """
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.SESSION_TTL_SECONDS)

        session = WidgetSessionData(
            session_id=str(uuid4()),
            merchant_id=merchant_id,
            created_at=now,
            last_activity_at=now,
            expires_at=expires_at,
            visitor_ip=visitor_ip,
            user_agent=user_agent,
        )

        key = self._get_session_key(session.session_id)
        await self.redis.setex(
            key,
            self.SESSION_TTL_SECONDS,
            session.model_dump_json(),
        )

        self.logger.info(
            "widget_session_created",
            session_id=session.session_id,
            merchant_id=merchant_id,
        )

        return session

    async def get_session(self, session_id: str) -> Optional[WidgetSessionData]:
        """Get an existing session by ID.

        Args:
            session_id: Widget session identifier

        Returns:
            WidgetSessionData if found and valid, None otherwise
        """
        key = self._get_session_key(session_id)
        data = await self.redis.get(key)

        if not data:
            return None

        try:
            session_dict = json.loads(data)
            return WidgetSessionData(**session_dict)
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(
                "widget_session_parse_error",
                session_id=session_id,
                error=str(e),
            )
            return None

    async def refresh_session(self, session_id: str) -> bool:
        """Refresh session expiry and activity timestamp.

        Args:
            session_id: Widget session identifier

        Returns:
            True if session was refreshed, False if not found
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.SESSION_TTL_SECONDS)

        session.last_activity_at = now
        session.expires_at = expires_at

        key = self._get_session_key(session_id)
        await self.redis.setex(
            key,
            self.SESSION_TTL_SECONDS,
            session.model_dump_json(),
        )

        # Also refresh message history TTL
        messages_key = self._get_messages_key(session_id)
        await self.redis.expire(messages_key, self.SESSION_TTL_SECONDS)

        self.logger.debug(
            "widget_session_refreshed",
            session_id=session_id,
        )

        return True

    async def end_session(self, session_id: str) -> bool:
        """Terminate a session and clear its data.

        Args:
            session_id: Widget session identifier

        Returns:
            True if session was terminated, False if not found
        """
        key = self._get_session_key(session_id)
        messages_key = self._get_messages_key(session_id)

        # Delete both session and message history
        deleted = await self.redis.delete(key, messages_key)

        if deleted > 0:
            self.logger.info(
                "widget_session_ended",
                session_id=session_id,
            )
            return True

        return False

    async def is_session_valid(self, session_id: str) -> bool:
        """Check if a session exists and is valid.

        Args:
            session_id: Widget session identifier

        Returns:
            True if session is valid, False otherwise
        """
        key = self._get_session_key(session_id)
        exists = await self.redis.exists(key)
        return exists > 0

    async def get_session_or_error(self, session_id: str) -> WidgetSessionData:
        """Get session or raise appropriate error.

        Args:
            session_id: Widget session identifier

        Returns:
            WidgetSessionData if found and valid

        Raises:
            APIError: If session not found (WIDGET_SESSION_NOT_FOUND)
            APIError: If session expired (WIDGET_SESSION_EXPIRED)
        """
        session = await self.get_session(session_id)

        if not session:
            raise APIError(
                ErrorCode.WIDGET_SESSION_NOT_FOUND,
                f"Widget session {session_id} not found",
            )

        if session.expires_at < datetime.now(timezone.utc):
            # Session has expired, clean it up
            await self.end_session(session_id)
            raise APIError(
                ErrorCode.WIDGET_SESSION_EXPIRED,
                f"Widget session {session_id} has expired",
            )

        return session

    async def add_message_to_history(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Add a message to session history.

        Args:
            session_id: Widget session identifier
            role: Message role ('user' or 'bot')
            content: Message content
        """
        messages_key = self._get_messages_key(session_id)

        message = json.dumps(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Add to list (RPUSH adds to end)
        await self.redis.rpush(messages_key, message)

        # Trim to max history size (keep last N messages)
        await self.redis.ltrim(
            messages_key,
            -self.MAX_MESSAGE_HISTORY,
            -1,
        )

        # Set/refresh TTL
        await self.redis.expire(messages_key, self.SESSION_TTL_SECONDS)

    async def get_message_history(
        self,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """Get message history for a session.

        Args:
            session_id: Widget session identifier

        Returns:
            List of message dictionaries
        """
        messages_key = self._get_messages_key(session_id)
        messages = await self.redis.lrange(messages_key, 0, -1)

        result = []
        for msg_json in messages:
            try:
                result.append(json.loads(msg_json))
            except (json.JSONDecodeError, ValueError):
                continue

        return result
