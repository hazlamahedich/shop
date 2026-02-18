"""Background job for widget session cleanup.

Schedules periodic cleanup of orphaned widget sessions.

Story 5-2: Widget Session Management
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Optional

import structlog

from app.services.widget.widget_cleanup_service import WidgetCleanupService


logger = structlog.get_logger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None


async def cleanup_expired_sessions() -> dict:
    """Cleanup task wrapper - scan Redis for orphaned sessions past TTL.

    Story 5-2 AC3: Runs every 5 minutes.

    Returns:
        Dictionary with cleanup statistics
    """
    service = WidgetCleanupService()
    return await service.cleanup_expired_sessions()


async def start_widget_cleanup_scheduler() -> None:
    """Start widget session cleanup scheduler.

    Called from main.py startup event.
    Runs cleanup every 5 minutes as backup to Redis TTL.
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("widget_cleanup_scheduler_already_running")
        return

    _scheduler = AsyncIOScheduler()

    _scheduler.add_job(
        cleanup_expired_sessions,
        trigger=IntervalTrigger(minutes=5),
        id="widget_cleanup",
        name="Widget Session Cleanup",
        replace_existing=True,
    )

    _scheduler.start()

    logger.info(
        "widget_cleanup_scheduler_started",
        interval_minutes=5,
    )


async def shutdown_widget_cleanup_scheduler() -> None:
    """Shutdown widget cleanup scheduler gracefully.

    Called from main.py shutdown event.
    """
    global _scheduler

    if _scheduler is None:
        return

    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("widget_cleanup_scheduler_shutdown")

    _scheduler = None


def get_scheduler_status() -> dict:
    """Get current status of widget cleanup scheduler.

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
