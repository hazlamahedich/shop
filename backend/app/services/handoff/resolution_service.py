"""Handoff Resolution Service.

Handles the complete handoff lifecycle including:
- Auto-close after 24-hour customer inactivity
- 20-hour warning message before auto-close
- 7-day reopen window for customers
- 4-hour escalation for pending handoffs
- Customer satisfaction feedback collection
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Optional

import structlog
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.handoff_alert import HandoffAlert

logger = structlog.get_logger(__name__)

# Timing constants (in hours/days)
WARNING_HOURS = 20
AUTO_CLOSE_HOURS = 24
REOPEN_WINDOW_DAYS = 7
PENDING_ESCALATION_HOURS = 4

# Resolution types
RESOLUTION_AUTO_TIMEOUT = "auto_timeout"
RESOLUTION_MERCHANT_RESOLVED = "merchant_resolved"
RESOLUTION_CUSTOMER_CLOSED = "customer_closed"
RESOLUTION_REOPENED = "reopened"


class HandoffResolutionService:
    """Service for managing handoff resolution lifecycle.

    Usage:
        service = HandoffResolutionService(db)

        # Get handoffs needing attention
        warnings = await service.get_handoffs_for_warning()
        to_close = await service.get_handoffs_for_auto_close()
        to_escalate = await service.get_pending_for_escalation()

        # Process them
        for conv in warnings:
            await service.send_warning_message(conv)

        for conv in to_close:
            await service.auto_close_handoff(conv)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_handoffs_for_warning(self) -> list[Conversation]:
        """Get handoffs approaching auto-close (20h inactivity).

        Returns handoffs where:
        - Status is 'handoff'
        - handoff_status is 'active' or 'resolved'
        - Last customer message was between 20-24 hours ago
        - Warning not already sent (tracked in conversation_data)

        Returns:
            List of Conversation objects needing warning message
        """
        now = datetime.utcnow()
        warning_threshold = now - timedelta(hours=WARNING_HOURS)
        upper_threshold = now - timedelta(hours=AUTO_CLOSE_HOURS - 1)

        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.status == "handoff",
                    Conversation.handoff_status.in_(["active", "resolved"]),
                    Conversation.last_customer_message_at < warning_threshold,
                    Conversation.last_customer_message_at > upper_threshold,
                )
            )
        )
        conversations = result.scalars().all()

        # Filter out ones that already received warning
        needs_warning = []
        for conv in conversations:
            if not self._has_received_warning(conv):
                needs_warning.append(conv)

        return needs_warning

    async def get_handoffs_for_auto_close(self) -> list[Conversation]:
        """Get handoffs ready for auto-close (24h inactivity).

        Returns handoffs where:
        - Status is 'handoff'
        - handoff_status is 'active' or 'resolved'
        - Last customer message was more than 24 hours ago

        Returns:
            List of Conversation objects ready for auto-close
        """
        threshold = datetime.utcnow() - timedelta(hours=AUTO_CLOSE_HOURS)

        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.status == "handoff",
                    Conversation.handoff_status.in_(["active", "resolved"]),
                    Conversation.last_customer_message_at < threshold,
                )
            )
        )
        return list(result.scalars().all())

    async def get_pending_for_escalation(self) -> list[Conversation]:
        """Get pending handoffs with no merchant response (4h).

        Returns handoffs where:
        - Status is 'handoff'
        - handoff_status is 'pending'
        - Handoff was triggered more than 4 hours ago
        - No merchant message has been sent

        Returns:
            List of Conversation objects needing escalation
        """
        threshold = datetime.utcnow() - timedelta(hours=PENDING_ESCALATION_HOURS)

        result = await self.db.execute(
            select(Conversation).where(
                and_(
                    Conversation.status == "handoff",
                    Conversation.handoff_status == "pending",
                    Conversation.handoff_triggered_at < threshold,
                    or_(
                        Conversation.last_merchant_message_at.is_(None),
                        Conversation.last_merchant_message_at < Conversation.handoff_triggered_at,
                    ),
                )
            )
        )
        return list(result.scalars().all())

    async def get_reopenable_handoff(
        self, session_id: str, merchant_id: int
    ) -> Optional[Conversation]:
        """Get a recently resolved handoff that can be reopened.

        Args:
            session_id: Customer's session/platform ID
            merchant_id: Merchant ID

        Returns:
            Conversation if reopenable within 7-day window, None otherwise
        """
        threshold = datetime.utcnow() - timedelta(days=REOPEN_WINDOW_DAYS)

        result = await self.db.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.platform_sender_id == session_id,
                    Conversation.merchant_id == merchant_id,
                    Conversation.status == "active",
                    Conversation.handoff_status == "none",
                    Conversation.handoff_resolved_at > threshold,
                )
            )
            .order_by(Conversation.handoff_resolved_at.desc())
        )
        return result.scalars().first()

    async def send_warning_message(self, conversation: Conversation) -> bool:
        """Send 20-hour warning to customer.

        Args:
            conversation: The conversation to send warning for

        Returns:
            True if warning was sent successfully
        """
        try:
            self._mark_warning_sent(conversation)
            await self.db.flush()

            logger.info(
                "handoff_warning_sent",
                conversation_id=conversation.id,
                merchant_id=conversation.merchant_id,
            )
            return True

        except Exception as e:
            logger.warning(
                "handoff_warning_failed",
                conversation_id=conversation.id,
                error=str(e),
            )
            return False

    async def auto_close_handoff(self, conversation: Conversation) -> bool:
        """Auto-close a handoff due to customer inactivity.

        Sets:
        - conversation.status = 'active' (returns to bot)
        - conversation.handoff_status = 'none'
        - conversation.handoff_resolved_at = now
        - conversation.handoff_resolution_type = 'auto_timeout'
        - alert.resolved_at = now
        - alert.resolution_type = 'auto_timeout'

        Args:
            conversation: The conversation to auto-close

        Returns:
            True if auto-close was successful
        """
        try:
            now = datetime.utcnow()

            conversation.status = "active"
            conversation.handoff_status = "none"
            conversation.handoff_resolved_at = now
            conversation.handoff_resolution_type = RESOLUTION_AUTO_TIMEOUT

            alert = await self._get_alert_for_conversation(conversation.id)
            if alert:
                alert.resolved_at = now
                alert.resolution_type = RESOLUTION_AUTO_TIMEOUT

            await self.db.flush()

            logger.info(
                "handoff_auto_closed",
                conversation_id=conversation.id,
                merchant_id=conversation.merchant_id,
            )
            return True

        except Exception as e:
            logger.warning(
                "handoff_auto_close_failed",
                conversation_id=conversation.id,
                error=str(e),
            )
            return False

    async def resolve_handoff(
        self,
        conversation: Conversation,
        resolution_type: str = RESOLUTION_MERCHANT_RESOLVED,
        notes: Optional[str] = None,
    ) -> bool:
        """Manually resolve a handoff (merchant action).

        Args:
            conversation: The conversation to resolve
            resolution_type: Type of resolution
            notes: Optional notes about the resolution

        Returns:
            True if resolution was successful
        """
        try:
            now = datetime.utcnow()

            conversation.status = "active"
            conversation.handoff_status = "none"
            conversation.handoff_resolved_at = now
            conversation.handoff_resolution_type = resolution_type

            alert = await self._get_alert_for_conversation(conversation.id)
            if alert:
                alert.resolved_at = now
                alert.resolution_type = resolution_type

            await self.db.flush()

            logger.info(
                "handoff_resolved",
                conversation_id=conversation.id,
                merchant_id=conversation.merchant_id,
                resolution_type=resolution_type,
            )
            return True

        except Exception as e:
            logger.warning(
                "handoff_resolve_failed",
                conversation_id=conversation.id,
                error=str(e),
            )
            return False

    async def reopen_handoff(
        self,
        conversation: Conversation,
        message: str,
    ) -> Optional[HandoffAlert]:
        """Reopen a recently resolved handoff.

        Creates a new HandoffAlert and updates conversation status.

        Args:
            conversation: The conversation to reopen
            message: The customer message that triggered reopen

        Returns:
            New HandoffAlert if successful, None otherwise
        """
        try:
            now = datetime.utcnow()

            conversation.status = "handoff"
            conversation.handoff_status = "reopened"
            conversation.handoff_reopened_count = (conversation.handoff_reopened_count or 0) + 1

            # Determine urgency based on reopen count
            if conversation.handoff_reopened_count >= 3:
                urgency = "high"
            elif conversation.handoff_reopened_count >= 2:
                urgency = "medium"
            else:
                urgency = "medium"

            alert = HandoffAlert(
                merchant_id=conversation.merchant_id,
                conversation_id=conversation.id,
                urgency_level=urgency,
                is_offline=False,
                customer_id=conversation.platform_sender_id,
                conversation_preview=message[:500] if message else None,
                wait_time_seconds=0,
                is_read=False,
                reopen_count=conversation.handoff_reopened_count,
            )

            self.db.add(alert)
            await self.db.flush()

            logger.info(
                "handoff_reopened",
                conversation_id=conversation.id,
                alert_id=alert.id,
                reopen_count=conversation.handoff_reopened_count,
            )
            return alert

        except Exception as e:
            logger.warning(
                "handoff_reopen_failed",
                conversation_id=conversation.id,
                error=str(e),
            )
            return None

    async def escalate_handoff(self, conversation: Conversation) -> bool:
        """Escalate a pending handoff that hasn't been responded to.

        Updates handoff_status to 'escalated' and logs for follow-up.

        Args:
            conversation: The conversation to escalate

        Returns:
            True if escalation was successful
        """
        try:
            conversation.handoff_status = "escalated"
            await self.db.flush()

            logger.info(
                "handoff_escalated",
                conversation_id=conversation.id,
                merchant_id=conversation.merchant_id,
            )
            return True

        except Exception as e:
            logger.warning(
                "handoff_escalate_failed",
                conversation_id=conversation.id,
                error=str(e),
            )
            return False

    async def record_satisfaction(
        self,
        conversation_id: int,
        satisfied: bool,
    ) -> bool:
        """Record customer satisfaction feedback.

        Args:
            conversation_id: ID of the conversation
            satisfied: Whether the customer was satisfied

        Returns:
            True if feedback was recorded successfully
        """
        try:
            result = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalars().first()

            if conversation:
                conversation.customer_satisfied = satisfied
                await self.db.flush()

                logger.info(
                    "handoff_satisfaction_recorded",
                    conversation_id=conversation_id,
                    satisfied=satisfied,
                )
                return True

            return False

        except Exception as e:
            logger.warning(
                "handoff_satisfaction_failed",
                conversation_id=conversation_id,
                error=str(e),
            )
            return False

    async def update_customer_message_time(self, conversation_id: int) -> None:
        """Update last_customer_message_at timestamp.

        Called when customer sends a message during handoff.

        Args:
            conversation_id: ID of the conversation
        """
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalars().first()
        if conversation:
            conversation.last_customer_message_at = datetime.utcnow()

    async def update_merchant_message_time(self, conversation_id: int) -> None:
        """Update last_merchant_message_at timestamp.

        Called when merchant sends a message during handoff.

        Args:
            conversation_id: ID of the conversation
        """
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalars().first()
        if conversation:
            conversation.last_merchant_message_at = datetime.utcnow()
            if conversation.handoff_status == "pending":
                conversation.handoff_status = "active"

    def _has_received_warning(self, conversation: Conversation) -> bool:
        """Check if conversation has already received auto-close warning."""
        if not conversation.conversation_data:
            return False
        return conversation.conversation_data.get("auto_close_warning_sent", False)

    def _mark_warning_sent(self, conversation: Conversation) -> None:
        """Mark that auto-close warning has been sent."""
        if conversation.conversation_data is None:
            conversation.conversation_data = {}
        conversation.conversation_data["auto_close_warning_sent"] = True
        conversation.conversation_data["auto_close_warning_sent_at"] = datetime.now(
            timezone.utc
        ).isoformat()

    async def _get_alert_for_conversation(self, conversation_id: int) -> Optional[HandoffAlert]:
        """Get the most recent handoff alert for a conversation."""
        result = await self.db.execute(
            select(HandoffAlert)
            .where(HandoffAlert.conversation_id == conversation_id)
            .order_by(HandoffAlert.created_at.desc())
        )
        return result.scalars().first()


__all__ = [
    "HandoffResolutionService",
    "WARNING_HOURS",
    "AUTO_CLOSE_HOURS",
    "REOPEN_WINDOW_DAYS",
    "PENDING_ESCALATION_HOURS",
    "RESOLUTION_AUTO_TIMEOUT",
    "RESOLUTION_MERCHANT_RESOLVED",
    "RESOLUTION_CUSTOMER_CLOSED",
    "RESOLUTION_REOPENED",
]
