"""Background jobs for data retention enforcement.

Schedules and manages automated cleanup tasks for NFR-S11 compliance.
Runs daily at midnight UTC to clean up expired data.

Story 2-7: Persistent Cart Sessions
- Includes 30-day cart retention cleanup for opted-in shoppers
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Optional

import structlog

from app.core.database import async_session
from app.services.data_retention import DataRetentionService
from app.services.cart.cart_retention import run_cart_retention_cleanup
from app.tasks.handoff_followup_task import process_handoff_followups
from app.tasks.queued_notification_task import process_queued_notifications

logger = structlog.get_logger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None

# Retention service instance
retention_service = DataRetentionService()


async def run_retention_cleanup() -> dict:
    """Run daily data retention cleanup job.

    Executes all retention cleanup tasks:
    - Voluntary conversation data cleanup (30-day retention)
    - Session data cleanup (24-hour retention)
    - Cart retention cleanup (30-day extended retention) - Story 2-7

    Returns:
        Dictionary with cleanup results from all retention tasks
    """
    logger.info("data_retention_job_started", timestamp=datetime.utcnow().isoformat())

    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "voluntary_data": {},
        "sessions": {},
        "cart_retention": {},  # Story 2-7: Cart retention cleanup
    }

    async with async_session() as db:
        try:
            # Clean up voluntary data
            voluntary_result = await retention_service.cleanup_voluntary_data(db)
            results["voluntary_data"] = voluntary_result

            # Clean up expired sessions
            session_result = await retention_service.cleanup_expired_sessions(db)
            results["sessions"] = session_result

            logger.info("data_retention_job_completed", **results)
        except Exception as e:
            logger.error("data_retention_job_failed", error=str(e), error_type=type(e).__name__)
            results["error"] = str(e)
            raise

    # Story 2-7: Clean up extended cart retention (independent of DB)
    try:
        cart_result = await run_cart_retention_cleanup()
        results["cart_retention"] = cart_result
    except Exception as e:
        logger.error("cart_retention_job_failed", error=str(e), error_type=type(e).__name__)
        results["cart_retention"] = {"error": str(e)}

    return results


async def _run_handoff_followup() -> dict:
    """Run handoff follow-up task wrapper.

    Story 4-11: Processes pending handoff follow-ups every 30 minutes.

    Returns:
        Dictionary with follow-up processing results
    """
    async with async_session() as db:
        return await process_handoff_followups(db)


async def _run_queued_notifications() -> dict:
    """Run queued notification task wrapper.

    Story 4-12: Processes queued offline handoff notifications every 30 minutes.

    Returns:
        Dictionary with notification processing results
    """
    async with async_session() as db:
        return await process_queued_notifications(db)


def start_scheduler() -> None:
    """Start the data retention scheduler.

    Initializes the APScheduler and adds the daily cleanup job.
    Should be called during application startup.
    """
    global scheduler

    if scheduler is not None and scheduler.running:
        logger.warning("data_retention_scheduler_already_running")
        return

    scheduler = AsyncIOScheduler()

    # Schedule daily cleanup at midnight UTC
    scheduler.add_job(
        run_retention_cleanup,
        trigger=CronTrigger(hour=0, minute=0, timezone="UTC"),
        id="data_retention_cleanup",
        name="Daily data retention cleanup",
        replace_existing=True,
    )

    # Story 4-11: Schedule handoff follow-up task every 30 minutes
    scheduler.add_job(
        lambda: _run_handoff_followup(),
        trigger=IntervalTrigger(minutes=30),
        id="handoff_followup_task",
        name="Process Handoff Follow-Ups",
        replace_existing=True,
    )

    # Story 4-12: Schedule queued notification task every 30 minutes
    scheduler.add_job(
        lambda: _run_queued_notifications(),
        trigger=IntervalTrigger(minutes=30),
        id="queued_notification_task",
        name="Process Queued Notifications",
        replace_existing=True,
    )

    scheduler.start()

    logger.info(
        "data_retention_scheduler_started",
        job_id="data_retention_cleanup",
        schedule="0 0 * * * (daily at midnight UTC)",
    )


def shutdown_scheduler() -> None:
    """Shutdown the data retention scheduler.

    Should be called during application shutdown.
    """
    global scheduler

    if scheduler is None:
        return

    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("data_retention_scheduler_shutdown")

    scheduler = None


def get_scheduler_status() -> dict:
    """Get the current status of the data retention scheduler.

    Returns:
        Dictionary with scheduler status information
    """
    global scheduler

    status = {
        "running": False,
        "job_count": 0,
        "jobs": [],
    }

    if scheduler is not None and scheduler.running:
        status["running"] = True
        status["job_count"] = len(scheduler.get_jobs())

        for job in scheduler.get_jobs():
            status["jobs"].append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                }
            )

    return status
