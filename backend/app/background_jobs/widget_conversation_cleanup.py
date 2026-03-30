"""Background job for widget conversation cleanup.

Schedules periodic cleanup of stale widget conversations.

Story 5-2: Widget Session Management - Conversation Lifecycle
"""

from __future__ import annotations

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.services.widget.widget_conversation_cleanup_service import (
    WidgetConversationCleanupService,
)

logger = structlog.get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def cleanup_stale_conversations() -> dict:
    """Cleanup task wrapper - close stale widget conversations.

    Story 5-2 AC3: Runs every 10 minutes.

    This closes conversations where:
    - Redis session has expired (TTL)
    - Conversation is older than 2 hours

    Returns:
        Dictionary with cleanup statistics
    """
    service = WidgetConversationCleanupService()
    return await service.cleanup_stale_conversations()


async def start_widget_conversation_cleanup_scheduler() -> None:
    """Start widget conversation cleanup scheduler.

    Called from main.py startup event.
    Runs cleanup every 10 minutes to close stale conversations.
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("widget_conversation_cleanup_scheduler_already_running")
        return

    _scheduler = AsyncIOScheduler()

    _scheduler.add_job(
        cleanup_stale_conversations,
        trigger=IntervalTrigger(minutes=10),
        id="widget_conversation_cleanup",
        name="Widget Conversation Cleanup",
        replace_existing=True,
    )

    _scheduler.start()

    logger.info(
        "widget_conversation_cleanup_scheduler_started",
        interval_minutes=10,
    )


async def shutdown_widget_conversation_cleanup_scheduler() -> None:
    """Shutdown widget conversation cleanup scheduler gracefully.

    Called from main.py shutdown event.
    """
    global _scheduler

    if _scheduler is None:
        return

    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("widget_conversation_cleanup_scheduler_shutdown")

    _scheduler = None


def get_conversation_cleanup_scheduler_status() -> dict:
    """Get current status of widget conversation cleanup scheduler.

    Returns:
        Dictionary with scheduler status
    """
    global _scheduler

    status = {
        "running": False,
        "job_count": 0,
        "jobs": [],
    }

    if _scheduler is not None and _scheduler.running:
        status["running"] = True
        status["job_count"] = len(_scheduler.get_jobs())

        for job in _scheduler.get_jobs():
            status["jobs"].append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                }
            )

    return status
