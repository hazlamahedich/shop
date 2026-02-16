"""Scheduled task for processing offline follow-up messages.

Story 4-11: Offline Follow-Up Messages

Runs periodically to check for conversations with pending handoffs
and sends follow-up messages when thresholds are reached.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import structlog

from app.core.config import settings
from app.services.handoff.offline_followup_service import (
    OfflineFollowUpService,
    FOLLOWUP_24H_THRESHOLD_HOURS,
)
from app.services.messenger.send_service import MessengerSendService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

TASK_INTERVAL_MINUTES = 30


async def process_handoff_followups(
    db: AsyncSession,
    redis: Any | None = None,
) -> dict[str, Any]:
    """Process pending handoff follow-ups.

    Main entry point for the scheduled task. Queries conversations
    with pending handoffs and sends appropriate follow-up messages.

    Args:
        db: AsyncSession for database operations
        redis: Optional Redis client for caching

    Returns:
        Dict with processing results
    """
    if settings().get("IS_TESTING", False):
        logger.info("followup_task_skipped_testing")
        return {"processed": 0, "skipped": "testing_mode"}

    logger.info(
        "followup_task_started",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    try:
        followup_service = OfflineFollowUpService(db)
        messenger_service = MessengerSendService()

        business_hours_service = None
        try:
            from app.services.business_hours.business_hours_service import (
                BusinessHoursService,
            )

            business_hours_service = BusinessHoursService()
        except ImportError:
            logger.debug("business_hours_service_not_available")

        conversations = await followup_service.get_pending_followups(
            hours_threshold=FOLLOWUP_24H_THRESHOLD_HOURS,
        )

        logger.info(
            "followup_task_conversations_found",
            count=len(conversations),
        )

        results = await followup_service.process_pending_followups(
            conversations=conversations,
            messenger_service=messenger_service,
            business_hours_service=business_hours_service,
        )

        await messenger_service.close()

        logger.info(
            "followup_task_completed",
            **results,
        )

        return results

    except Exception as e:
        logger.error(
            "followup_task_error",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return {"error": str(e), "processed": 0}


def schedule_handoff_followup_task(scheduler: Any) -> None:
    """Schedule the handoff follow-up task with APScheduler.

    Args:
        scheduler: APScheduler AsyncIOScheduler instance
    """
    from app.core.database import async_session

    async def job() -> dict[str, Any]:
        async with async_session() as db:
            return await process_handoff_followups(db)

    scheduler.add_job(
        job,
        "interval",
        minutes=TASK_INTERVAL_MINUTES,
        id="handoff_followup_task",
        name="Process Handoff Follow-Ups",
        replace_existing=True,
    )

    logger.info(
        "followup_task_scheduled",
        interval_minutes=TASK_INTERVAL_MINUTES,
    )


__all__ = [
    "process_handoff_followups",
    "schedule_handoff_followup_task",
    "TASK_INTERVAL_MINUTES",
]
