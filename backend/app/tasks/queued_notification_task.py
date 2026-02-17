"""Scheduled task for processing queued offline handoff notifications.

Story 4-12: Business Hours Handling

Runs periodically to check for queued notifications that should be
delivered when business hours open.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select, and_

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.models.conversation import Conversation

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TASK_INTERVAL_MINUTES = 30


async def process_queued_notifications(
    db: AsyncSession,
    redis: Any | None = None,
) -> dict[str, Any]:
    """Process queued offline handoff notifications.

    Checks for conversations with queued notifications that are now
    within business hours and sends the notifications.

    Args:
        db: AsyncSession for database operations
        redis: Optional Redis client for rate limiting

    Returns:
        Dict with processing results
    """
    if settings().get("IS_TESTING", False):
        logger.info("queued_notification_task_skipped_testing")
        return {"processed": 0, "skipped": "testing_mode"}

    logger.info(
        "queued_notification_task_started",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    results = {
        "processed": 0,
        "notifications_sent": 0,
        "no_queued": 0,
        "still_offline": 0,
        "errors": 0,
    }

    try:
        from app.services.business_hours.business_hours_service import (
            is_within_business_hours,
        )
        from app.services.handoff.notification_service import HandoffNotificationService
        from app.models.merchant import Merchant

        result = await db.execute(
            select(Conversation).where(
                and_(
                    Conversation.status == "handoff",
                    Conversation.handoff_status.in_(["pending", "active"]),
                )
            )
        )
        conversations = list(result.scalars().all())

        for conversation in conversations:
            conversation_data = conversation.conversation_data or {}

            if not conversation_data.get("offline_handoff_notification_queued"):
                results["no_queued"] += 1
                continue

            merchant_result = await db.execute(
                select(Merchant).where(Merchant.id == conversation.merchant_id)
            )
            merchant = merchant_result.scalars().first()

            if not merchant or not merchant.business_hours_config:
                results["processed"] += 1
                continue

            try:
                is_within = is_within_business_hours(merchant.business_hours_config)
            except Exception as e:
                logger.error(
                    "business_hours_check_failed_in_queue",
                    conversation_id=conversation.id,
                    error=str(e),
                )
                results["errors"] += 1
                continue

            if not is_within:
                results["still_offline"] += 1
                continue

            try:
                notification_service = HandoffNotificationService(db=db, redis=redis)

                urgency_value = conversation_data.get(
                    "offline_handoff_notification_urgency", "medium"
                )
                from app.schemas.handoff import UrgencyLevel

                urgency = (
                    UrgencyLevel(urgency_value) if isinstance(urgency_value, str) else urgency_value
                )

                notification_content = notification_service.format_notification_content(
                    customer_name=None,
                    customer_id=conversation.platform_sender_id,
                    conversation_preview=["Queued notification delivery"],
                    wait_time_seconds=0,
                    handoff_reason=conversation.handoff_reason,
                    urgency=urgency,
                )

                await notification_service.send_notifications(
                    merchant_id=conversation.merchant_id,
                    conversation_id=conversation.id,
                    urgency=urgency,
                    notification_content=notification_content,
                )

                conversation_data.pop("offline_handoff_notification_queued", None)
                conversation_data.pop("offline_handoff_notification_scheduled_for", None)
                conversation_data.pop("offline_handoff_notification_urgency", None)
                conversation.conversation_data = conversation_data

                results["notifications_sent"] += 1
                results["processed"] += 1

                logger.info(
                    "queued_notification_sent",
                    conversation_id=conversation.id,
                    merchant_id=conversation.merchant_id,
                    urgency=urgency.value if hasattr(urgency, "value") else urgency,
                )

            except Exception as e:
                logger.error(
                    "queued_notification_send_failed",
                    conversation_id=conversation.id,
                    error=str(e),
                    error_code=ErrorCode.NOTIFICATION_QUEUE_ERROR,
                )
                results["errors"] += 1

        await db.commit()

        logger.info(
            "queued_notification_task_completed",
            **results,
        )

        return results

    except Exception as e:
        logger.error(
            "queued_notification_task_error",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return {"error": str(e), "processed": 0}


def schedule_queued_notification_task(scheduler: Any) -> None:
    """Schedule the queued notification task with APScheduler.

    Args:
        scheduler: APScheduler AsyncIOScheduler instance
    """
    from app.core.database import async_session

    async def job() -> dict[str, Any]:
        async with async_session() as db:
            return await process_queued_notifications(db)

    scheduler.add_job(
        job,
        "interval",
        minutes=TASK_INTERVAL_MINUTES,
        id="queued_notification_task",
        name="Process Queued Offline Notifications",
        replace_existing=True,
    )

    logger.info(
        "queued_notification_task_scheduled",
        interval_minutes=TASK_INTERVAL_MINUTES,
    )


__all__ = [
    "process_queued_notifications",
    "schedule_queued_notification_task",
    "TASK_INTERVAL_MINUTES",
]
