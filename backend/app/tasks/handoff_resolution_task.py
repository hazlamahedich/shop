"""Scheduled task for handoff resolution lifecycle.

Runs every 30 minutes to:
- Send 20-hour warnings to customers
- Auto-close 24-hour inactive handoffs
- Escalate 4-hour pending handoffs with no merchant response

Story: Handoff Resolution Flow Enhancement
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.handoff.resolution_service import HandoffResolutionService

logger = structlog.get_logger(__name__)

TASK_INTERVAL_MINUTES = 30


async def process_handoff_resolutions(db: AsyncSession) -> dict[str, Any]:
    """Process handoff resolution lifecycle.

    Main entry point for the scheduled task. Performs:
    1. Send 20-hour warnings to customers approaching auto-close
    2. Auto-close handoffs with 24h customer inactivity
    3. Escalate pending handoffs with 4h no merchant response

    Args:
        db: AsyncSession for database operations

    Returns:
        Dict with processing results
    """
    if settings().get("IS_TESTING", False):
        logger.info("resolution_task_skipped_testing")
        return {"processed": 0, "skipped": "testing_mode"}

    logger.info(
        "handoff_resolution_task_started",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    results = {
        "warnings_sent": 0,
        "auto_closed": 0,
        "escalated": 0,
        "errors": 0,
    }

    try:
        service = HandoffResolutionService(db)

        # 1. Send 20-hour warnings
        warnings = await service.get_handoffs_for_warning()
        logger.info("handoff_warnings_found", count=len(warnings))

        for conv in warnings:
            try:
                success = await service.send_warning_message(conv)
                if success:
                    results["warnings_sent"] += 1
            except Exception as e:
                logger.warning(
                    "warning_send_failed",
                    conversation_id=conv.id,
                    error=str(e),
                )
                results["errors"] += 1

        # 2. Auto-close 24-hour inactive handoffs
        to_close = await service.get_handoffs_for_auto_close()
        logger.info("handoffs_to_close_found", count=len(to_close))

        for conv in to_close:
            try:
                success = await service.auto_close_handoff(conv)
                if success:
                    results["auto_closed"] += 1
            except Exception as e:
                logger.warning(
                    "auto_close_failed",
                    conversation_id=conv.id,
                    error=str(e),
                )
                results["errors"] += 1

        # 3. Escalate 4-hour pending handoffs
        to_escalate = await service.get_pending_for_escalation()
        logger.info("handoffs_to_escalate_found", count=len(to_escalate))

        for conv in to_escalate:
            try:
                success = await service.escalate_handoff(conv)
                if success:
                    results["escalated"] += 1
            except Exception as e:
                logger.warning(
                    "escalation_failed",
                    conversation_id=conv.id,
                    error=str(e),
                )
                results["errors"] += 1

        await db.commit()

    except Exception as e:
        logger.error(
            "handoff_resolution_task_error",
            error=str(e),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        results["errors"] += 1

    logger.info(
        "handoff_resolution_task_completed",
        **results,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    return results


def schedule_handoff_resolution_task(scheduler: Any) -> None:
    """Schedule the handoff resolution task with APScheduler.

    Args:
        scheduler: APScheduler AsyncIOScheduler instance
    """
    from app.core.database import async_session

    async def job() -> dict[str, Any]:
        async with async_session() as db:
            return await process_handoff_resolutions(db)

    scheduler.add_job(
        job,
        "interval",
        minutes=TASK_INTERVAL_MINUTES,
        id="handoff_resolution_task",
        name="Handoff Resolution Lifecycle",
        replace_existing=True,
    )

    logger.info(
        "handoff_resolution_task_scheduled",
        interval_minutes=TASK_INTERVAL_MINUTES,
    )


__all__ = [
    "process_handoff_resolutions",
    "schedule_handoff_resolution_task",
    "TASK_INTERVAL_MINUTES",
]
