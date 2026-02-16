"""Handoff flow orchestrator service.

Story 4-6: Handoff Notifications

Orchestrates the complete handoff flow:
1. Detects when handoff is needed (via HandoffDetector)
2. Creates HandoffAlert database record
3. Sends multi-channel notifications (dashboard + email)

This service bridges the gap between detection and notification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import structlog

from app.core.config import settings
from app.models.handoff_alert import HandoffAlert
from app.schemas.handoff import (
    HandoffReason,
    HandoffResult,
    UrgencyLevel,
)
from app.services.handoff.notification_service import HandoffNotificationService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class HandoffFlowService:
    """Orchestrates complete handoff flow from detection to notification.

    This service coordinates:
    - HandoffDetector: Detects when handoff is needed
    - HandoffAlert: Stores alert in database for dashboard
    - HandoffNotificationService: Sends email/dashboard notifications

    Usage:
        flow_service = HandoffFlowService(db, redis)
        result = await flow_service.process_handoff(
            conversation=conversation,
            message=customer_message,
            confidence_score=0.4,
        )
    """

    def __init__(
        self,
        db: AsyncSession,
        redis: Any | None = None,
        detector: Any | None = None,
    ):
        """Initialize handoff flow service.

        Args:
            db: AsyncSession for database operations
            redis: Optional Redis client for rate limiting
            detector: Optional HandoffDetector instance (created if not provided)
        """
        self.db = db
        self.redis = redis
        self._detector = detector
        self._notification_service = HandoffNotificationService(db=db, redis=redis)

    @property
    def detector(self) -> Any:
        """Lazy-load detector to avoid circular imports."""
        if self._detector is None:
            from app.services.handoff.detector import HandoffDetector

            self._detector = HandoffDetector(redis_client=self.redis)
        return self._detector

    async def process_handoff(
        self,
        conversation: Any,
        message: str,
        confidence_score: float | None = None,
        clarification_type: str | None = None,
        email_provider: Any | None = None,
    ) -> HandoffResult:
        """Process potential handoff for a conversation.

        This is the main entry point. It:
        1. Checks if handoff should be triggered
        2. If triggered, creates alert and sends notifications
        3. Returns result indicating what happened

        Args:
            conversation: Conversation ORM model instance
            message: Customer message that triggered the check
            confidence_score: LLM confidence score (0.0-1.0)
            clarification_type: Current clarification type if in flow
            email_provider: Optional email provider for sending emails

        Returns:
            HandoffResult with should_handoff and reason
        """
        result = await self.detector.detect(
            message=message,
            conversation_id=conversation.id,
            confidence_score=confidence_score,
            clarification_type=clarification_type,
        )

        if not result.should_handoff:
            return result

        if settings().get("IS_TESTING", False):
            logger.debug(
                "handoff_skipped_testing_mode",
                conversation_id=conversation.id,
                reason=result.reason.value if result.reason else None,
            )
            return result

        try:
            urgency = await self._notification_service.determine_urgency(
                handoff_reason=result.reason,
                recent_messages=await self._get_recent_messages(conversation),
            )

            notification_content = self._notification_service.format_notification_content(
                customer_name=getattr(conversation, "customer_name", None),
                customer_id=conversation.platform_sender_id,
                conversation_preview=await self._get_conversation_preview(conversation),
                wait_time_seconds=0,
                handoff_reason=result.reason.value if result.reason else None,
                urgency=urgency,
            )

            alert = await self._create_alert(
                conversation=conversation,
                urgency=urgency,
                notification_content=notification_content,
            )

            notification_result = await self._notification_service.send_notifications(
                merchant_id=conversation.merchant_id,
                conversation_id=conversation.id,
                urgency=urgency,
                notification_content=notification_content,
                email_provider=email_provider,
            )

            logger.info(
                "handoff_processed",
                conversation_id=conversation.id,
                merchant_id=conversation.merchant_id,
                urgency=urgency.value,
                reason=result.reason.value if result.reason else None,
                alert_id=alert.id,
                dashboard=notification_result.get("dashboard", False),
                email=notification_result.get("email", False),
            )

        except Exception as e:
            logger.error(
                "handoff_processing_failed",
                conversation_id=conversation.id,
                error=str(e),
            )

        return result

    async def _create_alert(
        self,
        conversation: Any,
        urgency: UrgencyLevel,
        notification_content: dict[str, Any],
    ) -> HandoffAlert:
        """Create HandoffAlert database record.

        Args:
            conversation: Conversation ORM model
            urgency: Determined urgency level
            notification_content: Formatted notification content

        Returns:
            Created HandoffAlert instance
        """
        preview = notification_content.get("conversation_preview", [])
        preview_text = "\n".join(f"- {msg}" for msg in preview) if preview else None

        alert = HandoffAlert(
            merchant_id=conversation.merchant_id,
            conversation_id=conversation.id,
            urgency_level=urgency.value,
            customer_name=notification_content.get("customer_name"),
            customer_id=notification_content.get("customer_id"),
            conversation_preview=preview_text,
            wait_time_seconds=0,
            is_read=False,
        )

        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)

        logger.info(
            "handoff_alert_created",
            alert_id=alert.id,
            conversation_id=conversation.id,
            urgency=urgency.value,
        )

        return alert

    async def _get_recent_messages(self, conversation: Any, limit: int = 3) -> list[str]:
        """Get recent message contents from conversation.

        Args:
            conversation: Conversation ORM model
            limit: Maximum messages to retrieve

        Returns:
            List of message content strings
        """
        messages = []
        if hasattr(conversation, "messages") and conversation.messages:
            for msg in conversation.messages[-limit:]:
                if hasattr(msg, "content") and msg.content:
                    messages.append(msg.content)
        return messages

    async def _get_conversation_preview(self, conversation: Any, limit: int = 3) -> list[str]:
        """Get conversation preview for notification.

        Args:
            conversation: Conversation ORM model
            limit: Maximum messages to include

        Returns:
            List of message content strings for preview
        """
        return await self._get_recent_messages(conversation, limit=limit)


__all__ = [
    "HandoffFlowService",
]
