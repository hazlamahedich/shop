"""Hybrid mode middleware for unified conversation processing.

Story 5-10 Task 19: Hybrid Mode (@bot Mentions)

Manages bot responses in hybrid mode (when human is active).
Bot only responds when explicitly mentioned with @bot.

Hybrid mode is activated when:
- Merchant takes over conversation
- Human handoff is triggered

Bot behavior in hybrid mode:
- Silent for regular messages
- Responds to @bot mentions
- Auto-expires after 2 hours
"""

from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.conversation import Conversation
from app.services.conversation.schemas import ConversationContext, ConversationResponse


logger = structlog.get_logger(__name__)


class HybridModeMiddleware:
    """Middleware for managing bot responses in hybrid mode.

    In hybrid mode, the bot stays silent unless explicitly mentioned.
    This allows human agents to take over conversations while still
    allowing customers to reach the bot with @bot mentions.

    Usage:
        middleware = HybridModeMiddleware()

        # Check if bot should respond
        should_respond, silent_message = await middleware.should_bot_respond(
            db=db,
            context=context,
            message="hello",
        )

        if not should_respond:
            return ConversationResponse(message=silent_message, ...)
    """

    BOT_MENTION_PATTERN = r"@bot\b"
    HYBRID_MODE_DURATION_HOURS = 2
    SILENT_MESSAGE = (
        "A human team member is helping you right now. "
        "If you need me, just mention @bot in your message!"
    )

    def __init__(self) -> None:
        """Initialize hybrid mode middleware."""
        self.logger = structlog.get_logger(__name__)

    async def should_bot_respond(
        self,
        db: AsyncSession,
        context: ConversationContext,
        message: str,
    ) -> tuple[bool, Optional[str]]:
        """Check if bot should respond based on hybrid mode state.

        Args:
            db: Database session
            context: Conversation context with session info
            message: User's message

        Returns:
            Tuple of (should_respond, silent_message_if_not)
            - (True, None) if bot should respond
            - (False, message) if bot should stay silent
        """
        conversation = await self._get_conversation(db, context.session_id)

        if not conversation:
            return True, None

        hybrid_mode = self._get_hybrid_mode_data(conversation)

        if not hybrid_mode.get("enabled"):
            return True, None

        if self._is_hybrid_mode_expired(hybrid_mode):
            self.logger.info(
                "hybrid_mode_expired",
                session_id=context.session_id[:8],
            )
            return True, None

        if self._is_bot_mentioned(message):
            self.logger.info(
                "hybrid_mode_bot_mention",
                session_id=context.session_id[:8],
            )
            return True, None

        self.logger.info(
            "hybrid_mode_silent",
            session_id=context.session_id[:8],
        )
        return False, self.SILENT_MESSAGE

    async def _get_conversation(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> Optional[Conversation]:
        """Get conversation by session ID.

        Args:
            db: Database session
            session_id: Widget session ID or PSID

        Returns:
            Conversation or None
        """
        result = await db.execute(
            select(Conversation).where(Conversation.platform_sender_id == session_id)
        )
        return result.scalars().first()

    def _get_hybrid_mode_data(self, conversation: Conversation) -> dict:
        """Extract hybrid mode data from conversation.

        Args:
            conversation: Conversation model

        Returns:
            Hybrid mode dict or empty dict
        """
        if not conversation.conversation_data:
            return {}

        return conversation.conversation_data.get("hybrid_mode", {})

    def _is_hybrid_mode_expired(self, hybrid_mode: dict) -> bool:
        """Check if hybrid mode has expired.

        Args:
            hybrid_mode: Hybrid mode configuration

        Returns:
            True if expired, False otherwise
        """
        expires_at_str = hybrid_mode.get("expires_at")

        if not expires_at_str:
            return False

        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))

            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            return datetime.now(timezone.utc) > expires_at
        except (ValueError, TypeError):
            self.logger.warning(
                "hybrid_mode_malformed_expiry",
                expires_at=expires_at_str,
            )
            return True

    def _is_bot_mentioned(self, message: str) -> bool:
        """Check if @bot is mentioned in the message.

        Args:
            message: User's message

        Returns:
            True if @bot is mentioned
        """
        return bool(re.search(self.BOT_MENTION_PATTERN, message, re.IGNORECASE))

    async def activate_hybrid_mode(
        self,
        db: AsyncSession,
        context: ConversationContext,
        reason: str = "human_handoff",
    ) -> None:
        """Activate hybrid mode for a conversation.

        Args:
            db: Database session
            context: Conversation context
            reason: Reason for activation
        """
        conversation = await self._get_conversation(db, context.session_id)

        if not conversation:
            return

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.HYBRID_MODE_DURATION_HOURS)

        if not conversation.conversation_data:
            conversation.conversation_data = {}

        conversation.conversation_data["hybrid_mode"] = {
            "enabled": True,
            "activated_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "reason": reason,
        }

        await db.commit()

        self.logger.info(
            "hybrid_mode_activated",
            session_id=context.session_id[:8],
            reason=reason,
            expires_at=expires_at.isoformat(),
        )

    async def deactivate_hybrid_mode(
        self,
        db: AsyncSession,
        context: ConversationContext,
    ) -> None:
        """Deactivate hybrid mode for a conversation.

        Args:
            db: Database session
            context: Conversation context
        """
        conversation = await self._get_conversation(db, context.session_id)

        if not conversation or not conversation.conversation_data:
            return

        conversation.conversation_data["hybrid_mode"] = {
            "enabled": False,
        }

        await db.commit()

        self.logger.info(
            "hybrid_mode_deactivated",
            session_id=context.session_id[:8],
        )

    def get_hybrid_mode_status(
        self,
        conversation: Optional[Conversation],
    ) -> dict:
        """Get current hybrid mode status.

        Args:
            conversation: Conversation model

        Returns:
            Dict with enabled, remaining_seconds, etc.
        """
        if not conversation or not conversation.conversation_data:
            return {
                "enabled": False,
                "remaining_seconds": 0,
            }

        hybrid_mode = conversation.conversation_data.get("hybrid_mode", {})

        if not hybrid_mode.get("enabled"):
            return {
                "enabled": False,
                "remaining_seconds": 0,
            }

        expires_at_str = hybrid_mode.get("expires_at")

        if not expires_at_str:
            return {
                "enabled": True,
                "remaining_seconds": 0,
            }

        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))

            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            remaining = (expires_at - datetime.now(timezone.utc)).total_seconds()

            if remaining <= 0:
                return {
                    "enabled": False,
                    "remaining_seconds": 0,
                }

            return {
                "enabled": True,
                "remaining_seconds": int(remaining),
                "expires_at": expires_at_str,
            }
        except (ValueError, TypeError):
            return {
                "enabled": True,
                "remaining_seconds": 0,
            }
