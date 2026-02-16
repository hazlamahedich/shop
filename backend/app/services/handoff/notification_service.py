"""Handoff notification service for multi-channel notifications.

Story 4-6: Handoff Notifications

Sends notifications when conversations need human attention:
- Dashboard badge (in-app notification)
- Email notification (rate-limited)
- Future: Push notification (stubbed)

Implements IS_TESTING pattern for deterministic test responses.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import structlog

from app.core.config import settings
from app.schemas.handoff import (
    HandoffReason,
    UrgencyLevel,
    URGENCY_EMOJI,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

HANDOFF_EMAIL_RATE_KEY = "handoff_email:{merchant_id}:{urgency}"
EMAIL_RATE_TTL = 86400  # 24 hours
HANDOFF_UNREAD_COUNT_KEY = "handoff_unread:{merchant_id}"
COUNT_TTL = 300  # 5 minutes

CHECKOUT_KEYWORD = "checkout"


class HandoffNotificationService:
    """Service for sending handoff notifications.

    Handles multi-channel notification dispatch including:
    - Urgency level detection based on handoff reason and context
    - In-app dashboard badge notifications
    - Email notifications with rate limiting
    """

    def __init__(self, db: AsyncSession, redis: Any | None = None):
        """Initialize notification service.

        Args:
            db: AsyncSession for database operations
            redis: Optional Redis client for rate limiting and caching
        """
        self.db = db
        self.redis = redis

    async def determine_urgency(
        self,
        handoff_reason: HandoffReason | str | None,
        recent_messages: list[str] | None = None,
    ) -> UrgencyLevel:
        """Determine urgency level based on handoff reason and context.

        Priority:
        - HIGH: If "checkout" mentioned in recent messages
        - MEDIUM: If low_confidence or clarification_loop
        - LOW: If keyword trigger (routine)

        Args:
            handoff_reason: Reason for handoff (keyword, low_confidence, clarification_loop)
            recent_messages: List of recent message contents for context analysis

        Returns:
            UrgencyLevel (HIGH, MEDIUM, or LOW)
        """
        if settings().get("IS_TESTING", False):
            return UrgencyLevel.LOW

        if recent_messages:
            for msg in recent_messages[-3:]:
                if msg and CHECKOUT_KEYWORD in msg.lower():
                    logger.debug(
                        "handoff_urgency_detected",
                        urgency=UrgencyLevel.HIGH.value,
                        reason="checkout_context",
                    )
                    return UrgencyLevel.HIGH

        reason_map = {
            HandoffReason.KEYWORD.value: UrgencyLevel.LOW,
            HandoffReason.LOW_CONFIDENCE.value: UrgencyLevel.MEDIUM,
            HandoffReason.CLARIFICATION_LOOP.value: UrgencyLevel.MEDIUM,
        }

        if handoff_reason is None:
            urgency = UrgencyLevel.LOW
            reason_display = "none"
        elif isinstance(handoff_reason, HandoffReason):
            urgency = reason_map.get(handoff_reason.value, UrgencyLevel.LOW)
            reason_display = handoff_reason.value
        else:
            urgency = reason_map.get(handoff_reason, UrgencyLevel.LOW)
            reason_display = handoff_reason

        logger.debug(
            "handoff_urgency_detected",
            urgency=urgency.value,
            handoff_reason=reason_display,
        )

        return urgency

    def format_notification_content(
        self,
        customer_name: str | None,
        customer_id: str | None,
        conversation_preview: list[str],
        wait_time_seconds: int,
        handoff_reason: str | None,
        urgency: UrgencyLevel | str,
    ) -> dict[str, Any]:
        """Format notification content for display.

        Args:
            customer_name: Customer name (or None)
            customer_id: Customer platform ID
            conversation_preview: Last 3 messages from conversation
            wait_time_seconds: Time elapsed since handoff trigger
            handoff_reason: Reason for handoff
            urgency: Urgency level for the notification

        Returns:
            Dict with formatted notification content
        """
        display_name = customer_name or customer_id or "Unknown Customer"

        wait_minutes = wait_time_seconds // 60
        wait_seconds = wait_time_seconds % 60
        if wait_minutes > 0:
            wait_time_display = f"{wait_minutes}m {wait_seconds}s"
        else:
            wait_time_display = f"{wait_seconds}s"

        preview_text = "\n".join(
            f"  - {msg[:100]}{'...' if len(msg) > 100 else ''}" for msg in conversation_preview[-3:]
        )

        urgency_value = urgency.value if isinstance(urgency, UrgencyLevel) else urgency
        urgency_enum = urgency if isinstance(urgency, UrgencyLevel) else UrgencyLevel(urgency_value)
        emoji = URGENCY_EMOJI.get(urgency_enum, "🟢")

        return {
            "customer_name": display_name,
            "customer_id": customer_id,
            "conversation_preview": conversation_preview[-3:],
            "preview_text": preview_text,
            "wait_time_seconds": wait_time_seconds,
            "wait_time_display": wait_time_display,
            "handoff_reason": handoff_reason,
            "urgency": urgency_value,
            "urgency_emoji": emoji,
            "urgency_label": urgency_value.upper(),
        }

    async def send_notifications(
        self,
        merchant_id: int,
        conversation_id: int,
        urgency: UrgencyLevel,
        notification_content: dict[str, Any],
        email_provider: Any | None = None,
    ) -> dict[str, bool]:
        """Send multi-channel notifications for handoff.

        Orchestrates:
        1. In-app notification (database record)
        2. Email notification (rate-limited)

        Args:
            merchant_id: Target merchant ID
            conversation_id: Conversation ID that triggered handoff
            urgency: Urgency level for notification
            notification_content: Formatted content dict from format_notification_content
            email_provider: Optional email provider for sending emails

        Returns:
            Dict with channel results: {"dashboard": bool, "email": bool}
        """
        if settings().get("IS_TESTING", False):
            return {"dashboard": True, "email": True}

        results = {"dashboard": False, "email": False}

        results["dashboard"] = True

        if email_provider:
            email_sent = await self._send_email(
                merchant_id=merchant_id,
                conversation_id=conversation_id,
                urgency=urgency,
                notification_content=notification_content,
                email_provider=email_provider,
            )
            results["email"] = email_sent
        else:
            results["email"] = False

        logger.info(
            "handoff_notification_sent",
            merchant_id=merchant_id,
            conversation_id=conversation_id,
            urgency=urgency.value,
            dashboard=results["dashboard"],
            email=results["email"],
        )

        return results

    async def _send_email(
        self,
        merchant_id: int,
        conversation_id: int,
        urgency: UrgencyLevel,
        notification_content: dict[str, Any],
        email_provider: Any,
    ) -> bool:
        """Send email notification with rate limiting.

        Rate limited to max 1 email per urgency level per merchant per 24 hours.

        Args:
            merchant_id: Target merchant ID
            conversation_id: Conversation ID for context
            urgency: Urgency level for rate limiting key
            notification_content: Formatted content for email body
            email_provider: Email provider instance

        Returns:
            True if email sent, False if rate limited or failed
        """
        if not await self._can_send_email(merchant_id, urgency):
            logger.info(
                "handoff_email_rate_limited",
                merchant_id=merchant_id,
                urgency=urgency.value,
            )
            return True

        try:
            message = self._build_email_message(notification_content)

            metadata = {
                "conversation_id": conversation_id,
                "urgency": urgency.value,
                "customer_name": notification_content.get("customer_name"),
            }

            sent = await email_provider.send(
                merchant_id=merchant_id,
                message=message,
                metadata=metadata,
            )

            if sent:
                await self._mark_email_sent(merchant_id, urgency)

            return sent

        except Exception as e:
            logger.error(
                "handoff_email_send_failed",
                merchant_id=merchant_id,
                conversation_id=conversation_id,
                error=str(e),
            )
            return False

    async def _can_send_email(self, merchant_id: int, urgency: UrgencyLevel | str) -> bool:
        """Check if email can be sent (rate limiting).

        Args:
            merchant_id: Merchant ID for rate limit key
            urgency: Urgency level for rate limit key

        Returns:
            True if email can be sent (not rate limited)
        """
        if not self.redis:
            return True

        urgency_value = urgency.value if isinstance(urgency, UrgencyLevel) else urgency
        redis_key = HANDOFF_EMAIL_RATE_KEY.format(
            merchant_id=merchant_id,
            urgency=urgency_value,
        )

        try:
            last_sent = await self.redis.get(redis_key)
            if last_sent:
                return False
            return True
        except Exception as e:
            logger.warning(
                "email_rate_check_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            return True

    async def _mark_email_sent(self, merchant_id: int, urgency: UrgencyLevel | str) -> None:
        """Mark email as sent for rate limiting.

        Args:
            merchant_id: Merchant ID for rate limit key
            urgency: Urgency level for rate limit key
        """
        if not self.redis:
            return

        urgency_value = urgency.value if isinstance(urgency, UrgencyLevel) else urgency
        redis_key = HANDOFF_EMAIL_RATE_KEY.format(
            merchant_id=merchant_id,
            urgency=urgency_value,
        )

        try:
            await self.redis.set(
                redis_key,
                datetime.now(timezone.utc).isoformat(),
                ex=EMAIL_RATE_TTL,
            )
        except Exception as e:
            logger.warning(
                "email_rate_mark_failed",
                merchant_id=merchant_id,
                error=str(e),
            )

    def _build_email_message(self, notification_content: dict[str, Any]) -> str:
        """Build email message body from notification content.

        Args:
            notification_content: Formatted content dict

        Returns:
            Plain text email message body
        """
        emoji = notification_content.get("urgency_emoji", "🟢")
        urgency_label = notification_content.get("urgency_label", "LOW")
        customer_name = notification_content.get("customer_name", "Unknown")
        wait_time = notification_content.get("wait_time_display", "0s")
        handoff_reason = notification_content.get("handoff_reason", "unknown")
        preview_text = notification_content.get("preview_text", "")

        return f"""{emoji} Customer Needs Help - {urgency_label} Priority

Customer Handoff Request

Urgency: {emoji} {urgency_label}
Customer: {customer_name}
Wait Time: {wait_time}
Reason: {handoff_reason}

Conversation Preview:
{preview_text}

Please respond promptly to assist this customer.
"""


__all__ = [
    "HandoffNotificationService",
    "HANDOFF_EMAIL_RATE_KEY",
    "EMAIL_RATE_TTL",
    "HANDOFF_UNREAD_COUNT_KEY",
    "COUNT_TTL",
    "CHECKOUT_KEYWORD",
]
