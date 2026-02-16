"""Return to Bot Service.

Story 4-10: Return to Bot

Handles sending welcome back message to shoppers when merchant returns control to bot.
Respects Facebook 24-hour messaging window.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import structlog

from app.models.message import Message

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.conversation import Conversation

logger = structlog.get_logger(__name__)

WELCOME_BACK_MESSAGE = "Welcome back! Is there anything else I can help you with?"


class ReturnToBotService:
    """Service for handling return-to-bot flow.

    When a merchant returns control to the bot:
    1. Check if within 24-hour messaging window
    2. Send welcome back message to shopper (if allowed)
    3. Store message in database

    Usage:
        service = ReturnToBotService(db)
        result = await service.send_welcome_message(conversation, facebook_service)
    """

    TWENTY_FOUR_HOURS_SECONDS = 24 * 60 * 60

    def __init__(self, db: AsyncSession) -> None:
        """Initialize Return to Bot service.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db

    async def send_welcome_message(
        self,
        conversation: Conversation,
        facebook_service: Any,
    ) -> dict[str, Any]:
        """Send welcome back message to shopper.

        Args:
            conversation: Conversation ORM model
            facebook_service: MessengerSendService instance for sending messages

        Returns:
            Dict with 'sent' (bool) and 'reason' (str) keys
        """
        last_shopper_message = await self._get_last_shopper_message(conversation.id)

        if not last_shopper_message:
            logger.info(
                "welcome_message_blocked_no_shopper_message",
                conversation_id=conversation.id,
            )
            return {"sent": False, "reason": "no_shopper_message"}

        hours_since_last = self._hours_since_message(last_shopper_message)

        if hours_since_last > 24:
            logger.info(
                "welcome_message_blocked_24h_window",
                conversation_id=conversation.id,
                hours_since_last=round(hours_since_last, 2),
            )
            return {"sent": False, "reason": "outside_24h_window"}

        try:
            await facebook_service.send_message(
                conversation.platform_sender_id,
                {"text": WELCOME_BACK_MESSAGE},
            )

            await self._store_welcome_message(conversation.id)

            logger.info(
                "welcome_message_sent",
                conversation_id=conversation.id,
                message_length=len(WELCOME_BACK_MESSAGE),
            )

            return {"sent": True, "reason": "success"}

        except Exception as e:
            logger.error(
                "welcome_message_send_failed",
                conversation_id=conversation.id,
                error=str(e),
            )
            return {"sent": False, "reason": f"send_error: {str(e)}"}

    async def _get_last_shopper_message(self, conversation_id: int) -> Message | None:
        """Get the last message from shopper in conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Last shopper Message or None if not found
        """
        from sqlalchemy import select

        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.sender == "customer")
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    def _hours_since_message(self, message: Message) -> float:
        """Calculate hours since a message was created.

        Args:
            message: Message to check

        Returns:
            Hours since message creation
        """
        now = datetime.now(timezone.utc)
        if message.created_at.tzinfo is None:
            message_time = message.created_at.replace(tzinfo=timezone.utc)
        else:
            message_time = message.created_at

        delta = now - message_time
        return delta.total_seconds() / 3600

    async def _store_welcome_message(self, conversation_id: int) -> Message:
        """Store welcome back message in database.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Created Message instance
        """
        message = Message(
            conversation_id=conversation_id,
            sender="bot",
            content=WELCOME_BACK_MESSAGE,
            message_type="text",
            created_at=datetime.utcnow(),
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message


__all__ = ["ReturnToBotService", "WELCOME_BACK_MESSAGE"]
