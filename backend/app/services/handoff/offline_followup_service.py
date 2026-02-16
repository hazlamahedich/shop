"""Offline Follow-Up Service.

Story 4-11: Offline Follow-Up Messages

Sends follow-up messages to shoppers when merchant is offline/unresponsive:
- 12-hour follow-up: "Still working on your request..."
- 24-hour follow-up: "Sorry for the delay..." with backup email

Respects Facebook 24-hour messaging window and business hours.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select, and_

from app.models.message import Message

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.conversation import Conversation
    from app.models.merchant import Merchant
    from app.services.messenger.send_service import MessengerSendService

logger = structlog.get_logger(__name__)

FOLLOWUP_12H_MESSAGE = (
    "Still working on your request. Our team will respond as soon as possible. "
    "In the meantime, is there anything else I can help with?"
)

FOLLOWUP_24H_MESSAGE_WITH_EMAIL = (
    "Sorry for the delay. Our team is experiencing high volume. "
    "You can also reach us at {email} for faster response."
)

FOLLOWUP_24H_MESSAGE_NO_EMAIL = (
    "Sorry for the delay. Our team is experiencing high volume. "
    "We'll respond to your request as soon as possible."
)

FOLLOWUP_12H_THRESHOLD_HOURS = 12
FOLLOWUP_24H_THRESHOLD_HOURS = 24
FACEBOOK_WINDOW_HOURS = 24


class OfflineFollowUpService:
    """Service for sending follow-up messages during handoff.

    Handles automatic follow-up messages when merchant hasn't responded:
    1. 12-hour follow-up: Reassurance message
    2. 24-hour follow-up: Apology with backup contact (if email available)

    Critical constraints:
    - Only sends within Facebook 24-hour messaging window
    - Respects business hours configuration
    - Idempotent: never sends same follow-up twice
    - Validates conversation state before sending

    Usage:
        service = OfflineFollowUpService(db)
        result = await service.process_pending_followups(
            conversations=conversations,
            messenger_service=messenger_service
        )
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize Offline Follow-Up service.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db

    async def get_pending_followups(
        self,
        hours_threshold: float,
    ) -> list[Conversation]:
        """Query conversations with pending handoff that may need follow-up.

        Args:
            hours_threshold: Hours since handoff to consider for follow-up

        Returns:
            List of Conversation objects with pending handoff
        """
        from app.models.conversation import Conversation

        threshold_time = datetime.now(timezone.utc) - __import__("datetime").timedelta(
            hours=hours_threshold
        )

        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.status == "handoff",
                    Conversation.handoff_status.in_(["pending", "active"]),
                    Conversation.handoff_triggered_at <= threshold_time,
                )
            )
        )
        return list(result.scalars().all())

    async def process_pending_followups(
        self,
        conversations: list[Conversation],
        messenger_service: MessengerSendService,
        business_hours_service: Any | None = None,
    ) -> dict[str, Any]:
        """Process pending follow-ups for a list of conversations.

        Checks each conversation for:
        - 12-hour follow-up eligibility
        - 24-hour follow-up eligibility

        Args:
            conversations: List of conversations to check
            messenger_service: Service for sending Facebook messages
            business_hours_service: Optional service for business hours checking

        Returns:
            Dict with counts: {
                "processed": int,
                "12h_sent": int,
                "24h_sent": int,
                "skipped_state_changed": int,
                "skipped_already_sent": int,
                "skipped_24h_window": int,
                "skipped_business_hours": int,
                "errors": int
            }
        """
        results = {
            "processed": 0,
            "12h_sent": 0,
            "24h_sent": 0,
            "skipped_state_changed": 0,
            "skipped_already_sent": 0,
            "skipped_24h_window": 0,
            "skipped_business_hours": 0,
            "errors": 0,
        }

        for conversation in conversations:
            results["processed"] += 1

            try:
                await self._process_conversation_followup(
                    conversation=conversation,
                    messenger_service=messenger_service,
                    business_hours_service=business_hours_service,
                    results=results,
                )
            except Exception as e:
                logger.error(
                    "followup_process_error",
                    conversation_id=conversation.id,
                    error=str(e),
                )
                results["errors"] += 1

        return results

    async def _process_conversation_followup(
        self,
        conversation: Conversation,
        messenger_service: MessengerSendService,
        business_hours_service: Any | None,
        results: dict[str, Any],
    ) -> None:
        """Process follow-up for a single conversation.

        Args:
            conversation: Conversation to process
            messenger_service: Service for sending messages
            business_hours_service: Optional business hours service
            results: Results dict to update with counts
        """
        conversation_data = conversation.conversation_data or {}

        followup_12h_sent_at = conversation_data.get("followup_12h_sent_at")
        followup_24h_sent_at = conversation_data.get("followup_24h_sent_at")

        hours_since_handoff = await self._hours_since_handoff(conversation)

        if followup_24h_sent_at is None and hours_since_handoff >= FOLLOWUP_24H_THRESHOLD_HOURS:
            await self._maybe_send_24h_followup(
                conversation=conversation,
                messenger_service=messenger_service,
                business_hours_service=business_hours_service,
                already_sent_12h=followup_12h_sent_at is not None,
                results=results,
            )
        elif followup_12h_sent_at is None and hours_since_handoff >= FOLLOWUP_12H_THRESHOLD_HOURS:
            await self._maybe_send_12h_followup(
                conversation=conversation,
                messenger_service=messenger_service,
                business_hours_service=business_hours_service,
                results=results,
            )

    async def _maybe_send_12h_followup(
        self,
        conversation: Conversation,
        messenger_service: MessengerSendService,
        business_hours_service: Any | None,
        results: dict[str, Any],
    ) -> None:
        """Check and send 12-hour follow-up if eligible.

        Args:
            conversation: Conversation to send follow-up for
            messenger_service: Service for sending messages
            business_hours_service: Optional business hours service
            results: Results dict to update
        """
        if not await self._is_conversation_still_in_handoff(conversation):
            results["skipped_state_changed"] += 1
            return

        if not await self._is_within_facebook_window(conversation):
            logger.info(
                "followup_blocked_24h_window",
                conversation_id=conversation.id,
                followup_type="12h",
            )
            results["skipped_24h_window"] += 1
            return

        if business_hours_service and not await self._is_within_business_hours(
            conversation, business_hours_service
        ):
            logger.info(
                "followup_skipped_business_hours",
                conversation_id=conversation.id,
                followup_type="12h",
            )
            results["skipped_business_hours"] += 1
            return

        sent = await self._send_followup_message(
            conversation=conversation,
            message=FOLLOWUP_12H_MESSAGE,
            messenger_service=messenger_service,
        )

        if sent:
            await self._track_followup_sent(conversation, "12h", FOLLOWUP_12H_MESSAGE)
            results["12h_sent"] += 1
            logger.info(
                "followup_sent",
                conversation_id=conversation.id,
                followup_type="12h",
                hours_since_handoff=await self._hours_since_handoff(conversation),
            )

    async def _maybe_send_24h_followup(
        self,
        conversation: Conversation,
        messenger_service: MessengerSendService,
        business_hours_service: Any | None,
        already_sent_12h: bool,
        results: dict[str, Any],
    ) -> None:
        """Check and send 24-hour follow-up if eligible.

        Args:
            conversation: Conversation to send follow-up for
            messenger_service: Service for sending messages
            business_hours_service: Optional business hours service
            already_sent_12h: Whether 12h follow-up was already sent
            results: Results dict to update
        """
        if not await self._is_conversation_still_in_handoff(conversation):
            results["skipped_state_changed"] += 1
            return

        if not await self._is_within_facebook_window(conversation):
            logger.info(
                "followup_blocked_24h_window",
                conversation_id=conversation.id,
                followup_type="24h",
            )
            results["skipped_24h_window"] += 1
            return

        if business_hours_service and not await self._is_within_business_hours(
            conversation, business_hours_service
        ):
            logger.info(
                "followup_skipped_business_hours",
                conversation_id=conversation.id,
                followup_type="24h",
            )
            results["skipped_business_hours"] += 1
            return

        merchant = await self._get_merchant(conversation.merchant_id)
        message = self._build_24h_message(merchant)

        sent = await self._send_followup_message(
            conversation=conversation,
            message=message,
            messenger_service=messenger_service,
        )

        if sent:
            await self._track_followup_sent(conversation, "24h", message)
            results["24h_sent"] += 1
            logger.info(
                "followup_sent",
                conversation_id=conversation.id,
                followup_type="24h",
                hours_since_handoff=await self._hours_since_handoff(conversation),
                has_email=merchant.email is not None if merchant else False,
            )

    async def send_12h_followup(
        self,
        conversation: Conversation,
        messenger_service: MessengerSendService,
    ) -> dict[str, Any]:
        """Send 12-hour follow-up message directly.

        Args:
            conversation: Conversation to send follow-up for
            messenger_service: Service for sending messages

        Returns:
            Dict with 'sent' (bool) and 'reason' (str) keys
        """
        conversation_data = conversation.conversation_data or {}
        if conversation_data.get("followup_12h_sent_at"):
            return {"sent": False, "reason": "already_sent"}

        if not await self._is_conversation_still_in_handoff(conversation):
            return {"sent": False, "reason": "state_changed"}

        if not await self._is_within_facebook_window(conversation):
            return {"sent": False, "reason": "outside_24h_window"}

        sent = await self._send_followup_message(
            conversation=conversation,
            message=FOLLOWUP_12H_MESSAGE,
            messenger_service=messenger_service,
        )

        if sent:
            await self._track_followup_sent(conversation, "12h", FOLLOWUP_12H_MESSAGE)
            return {"sent": True, "reason": "success"}

        return {"sent": False, "reason": "send_failed"}

    async def send_24h_followup(
        self,
        conversation: Conversation,
        messenger_service: MessengerSendService,
    ) -> dict[str, Any]:
        """Send 24-hour follow-up message directly.

        Args:
            conversation: Conversation to send follow-up for
            messenger_service: Service for sending messages

        Returns:
            Dict with 'sent' (bool) and 'reason' (str) keys
        """
        conversation_data = conversation.conversation_data or {}
        if conversation_data.get("followup_24h_sent_at"):
            return {"sent": False, "reason": "already_sent"}

        if not await self._is_conversation_still_in_handoff(conversation):
            return {"sent": False, "reason": "state_changed"}

        if not await self._is_within_facebook_window(conversation):
            return {"sent": False, "reason": "outside_24h_window"}

        merchant = await self._get_merchant(conversation.merchant_id)
        message = self._build_24h_message(merchant)

        sent = await self._send_followup_message(
            conversation=conversation,
            message=message,
            messenger_service=messenger_service,
        )

        if sent:
            await self._track_followup_sent(conversation, "24h", message)
            return {"sent": True, "reason": "success"}

        return {"sent": False, "reason": "send_failed"}

    async def _send_followup_message(
        self,
        conversation: Conversation,
        message: str,
        messenger_service: MessengerSendService,
    ) -> bool:
        """Send follow-up message to shopper.

        Note: Message storage is handled by _track_followup_sent for atomic transaction.

        Args:
            conversation: Conversation to send message for
            message: Message text to send
            messenger_service: Service for sending messages

        Returns:
            True if message was sent successfully
        """
        try:
            await messenger_service.send_message(
                recipient_id=conversation.platform_sender_id,
                message_payload={"text": message},
            )

            return True

        except Exception as e:
            logger.error(
                "followup_send_failed",
                conversation_id=conversation.id,
                error=str(e),
            )
            return False

    async def _is_conversation_still_in_handoff(
        self,
        conversation: Conversation,
    ) -> bool:
        """Check if conversation is still in handoff state.

        Args:
            conversation: Conversation to check

        Returns:
            True if still in valid handoff state
        """
        from sqlalchemy import select

        from app.models.conversation import Conversation as ConvModel

        result = await self.db.execute(
            select(ConvModel.status, ConvModel.handoff_status).where(
                ConvModel.id == conversation.id
            )
        )
        row = result.first()

        if not row:
            return False

        status, handoff_status = row
        return status == "handoff" and handoff_status in ["pending", "active"]

    async def _is_within_facebook_window(
        self,
        conversation: Conversation,
    ) -> bool:
        """Check if within Facebook 24-hour messaging window.

        REUSE pattern from ReturnToBotService (Story 4-10).

        Args:
            conversation: Conversation to check

        Returns:
            True if within 24-hour window
        """
        last_shopper_message = await self._get_last_shopper_message(conversation.id)

        if not last_shopper_message:
            return False

        hours_since_last = self._hours_since_message(last_shopper_message)
        return hours_since_last <= FACEBOOK_WINDOW_HOURS

    async def _is_within_business_hours(
        self,
        conversation: Conversation,
        business_hours_service: Any,
    ) -> bool:
        """Check if current time is within business hours.

        Args:
            conversation: Conversation to check
            business_hours_service: Service for business hours checking

        Returns:
            True if within business hours
        """
        merchant = await self._get_merchant(conversation.merchant_id)

        if not merchant or not merchant.business_hours_config:
            return True

        from app.services.business_hours.business_hours_service import (
            is_within_business_hours,
        )

        return is_within_business_hours(merchant.business_hours_config)

    async def _get_last_shopper_message(
        self,
        conversation_id: int,
    ) -> Message | None:
        """Get the last message from shopper in conversation.

        REUSE pattern from ReturnToBotService (Story 4-10).

        Args:
            conversation_id: ID of the conversation

        Returns:
            Last shopper Message or None if not found
        """
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

        REUSE pattern from ReturnToBotService (Story 4-10).

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

    async def _hours_since_handoff(self, conversation: Conversation) -> float:
        """Calculate hours since handoff was triggered.

        Args:
            conversation: Conversation to check

        Returns:
            Hours since handoff, or 0 if not triggered
        """
        if not conversation.handoff_triggered_at:
            return 0.0

        now = datetime.now(timezone.utc)
        triggered_at = conversation.handoff_triggered_at

        if triggered_at.tzinfo is None:
            triggered_at = triggered_at.replace(tzinfo=timezone.utc)

        delta = now - triggered_at
        return delta.total_seconds() / 3600

    async def _get_merchant(self, merchant_id: int) -> Merchant | None:
        """Get merchant by ID.

        Args:
            merchant_id: ID of the merchant

        Returns:
            Merchant or None if not found
        """
        from app.models.merchant import Merchant

        result = await self.db.execute(select(Merchant).where(Merchant.id == merchant_id))
        return result.scalars().first()

    def _build_24h_message(self, merchant: Merchant | None) -> str:
        """Build 24-hour follow-up message with optional email.

        Args:
            merchant: Merchant for email fallback

        Returns:
            Message string with email if available, fallback otherwise
        """
        if merchant and merchant.email:
            return FOLLOWUP_24H_MESSAGE_WITH_EMAIL.format(email=merchant.email)
        return FOLLOWUP_24H_MESSAGE_NO_EMAIL

    async def _track_followup_sent(
        self,
        conversation: Conversation,
        followup_type: str,
        content: str | None = None,
    ) -> Message | None:
        """Track follow-up timestamp and store message in single transaction.

        Args:
            conversation: Conversation to update
            followup_type: "12h" or "24h"
            content: Optional message content to store (if message was sent)

        Returns:
            Created Message instance if content provided, None otherwise
        """
        from app.models.message import Message

        conversation_data = conversation.conversation_data or {}
        conversation_data[f"followup_{followup_type}_sent_at"] = datetime.now(
            timezone.utc
        ).isoformat()
        conversation.conversation_data = conversation_data

        message = None
        if content:
            message = Message(
                conversation_id=conversation.id,
                sender="bot",
                content=content,
                message_type="text",
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(message)

        await self.db.commit()
        await self.db.refresh(conversation)

        if message:
            await self.db.refresh(message)

        logger.debug(
            "followup_tracked",
            conversation_id=conversation.id,
            followup_type=followup_type,
        )

        return message

    async def _store_bot_message(
        self,
        conversation_id: int,
        content: str,
    ) -> Message:
        """Store bot message in database.

        DEPRECATED: Use _track_followup_sent with content parameter instead
        to ensure atomic transaction.

        Args:
            conversation_id: ID of the conversation
            content: Message content

        Returns:
            Created Message instance
        """
        message = Message(
            conversation_id=conversation_id,
            sender="bot",
            content=content,
            message_type="text",
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message


__all__ = [
    "OfflineFollowUpService",
    "FOLLOWUP_12H_MESSAGE",
    "FOLLOWUP_24H_MESSAGE_WITH_EMAIL",
    "FOLLOWUP_24H_MESSAGE_NO_EMAIL",
    "FOLLOWUP_12H_THRESHOLD_HOURS",
    "FOLLOWUP_24H_THRESHOLD_HOURS",
    "FACEBOOK_WINDOW_HOURS",
]
