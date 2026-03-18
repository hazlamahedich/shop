"""Background jobs for data retention enforcement.

Schedules and manages automated cleanup tasks for NFR-S11 compliance.
Runs daily at midnight UTC to clean up expired data.

Story 2-7: Persistent Cart Sessions
- Includes 30-day cart retention cleanup for opted-in shoppers
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.background_jobs.gdpr_compliance_check import add_gdpr_job_to_scheduler
from app.background_jobs.gdpr_email_sender import add_email_job_to_scheduler
from app.core.database import async_session
from app.services.cart.cart_retention import run_cart_retention_cleanup
from app.services.data_retention import (
    DataRetentionService,
)  # DEPRECATED: Story 6-5 - Use RetentionPolicy instead
from app.services.privacy.retention_service import RetentionPolicy
from app.tasks.handoff_followup_task import process_handoff_followups
from app.tasks.handoff_resolution_task import process_handoff_resolutions
from app.tasks.queued_notification_task import process_queued_notifications

logger = structlog.get_logger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None

# Retention service instance (DEPRECATED: Story 6-5 - Retained for session cleanup)
retention_service = DataRetentionService()


async def run_retention_cleanup() -> dict:
    """Run daily data retention cleanup job.

    Story 6-5: Enhanced with retry logic (AC6)

    Executes all retention cleanup tasks with automatic retry on failure:
    - Voluntary conversation data cleanup (30-day retention) - Uses RetentionPolicy
    - Session data cleanup (24-hour retention)
    - Cart retention cleanup (30-day extended retention)

    Returns:
        Dictionary with cleanup results from all retention tasks
    """
    logger.info("data_retention_job_started", timestamp=datetime.utcnow().isoformat())

    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "voluntary_data": {},
        "sessions": {},
        "cart_retention": {},
        "retries": 0,
    }

    # Story 6-5: Retry logic (AC6)
    max_retries = 3
    retry_delay_seconds = 10

    async with async_session() as db:
        # Retry loop for voluntary data cleanup
        for attempt in range(max_retries):
            try:
                deleted_count = await RetentionPolicy.delete_expired_voluntary_data(db, days=30)
                results["voluntary_data"] = {
                    "conversations_deleted": deleted_count,
                    "retention_days": 30,
                    "success": True,
                }
                break
            except Exception as e:
                logger.error(
                    "voluntary_data_cleanup_failed",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                    error_type=type(e).__name__,
                )

                if attempt < max_retries - 1:
                    results["retries"] += 1
                    logger.info(
                        "retrying_voluntary_data_cleanup", delay_seconds=retry_delay_seconds
                    )
                    await asyncio.sleep(retry_delay_seconds)
                else:
                    results["voluntary_data"] = {
                        "error": str(e),
                        "success": False,
                        "attempts": attempt + 1,
                    }
                    logger.error("voluntary_data_cleanup_failed_permanently")

        # Retry loop for session cleanup
        for attempt in range(max_retries):
            try:
                session_result = await retention_service.cleanup_expired_sessions(db)
                results["sessions"] = session_result
                break
            except Exception as e:
                logger.error(
                    "session_cleanup_failed",
                    attempt=attempt + 1,
                    error=str(e),
                )

                if attempt < max_retries - 1:
                    results["retries"] += 1
                    await asyncio.sleep(retry_delay_seconds)
                else:
                    results["sessions"] = {"error": str(e), "success": False}

        logger.info("data_retention_job_completed", **results)

    # Story 2-7: Cart retention cleanup (independent of DB)
    for attempt in range(max_retries):
        try:
            cart_result = await run_cart_retention_cleanup()
            results["cart_retention"] = cart_result
            break
        except Exception as e:
            logger.error(
                "cart_retention_job_failed",
                attempt=attempt + 1,
                error=str(e),
                error_type=type(e).__name__,
            )

            if attempt < max_retries - 1:
                results["retries"] += 1
                await asyncio.sleep(retry_delay_seconds)
            else:
                results["cart_retention"] = {"error": str(e), "success": False}

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


async def _run_handoff_resolution() -> dict:
    """Run handoff resolution task wrapper.

    Story: Handoff Resolution Flow
    Processes auto-close warnings, auto-closes, and escalations every 30 minutes.

    Returns:
        Dictionary with resolution processing results
    """
    async with async_session() as db:
        return await process_handoff_resolutions(db)


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
        max_instances=1,  # Story 6-5: Prevent concurrent execution
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

    # Handoff Resolution: Schedule resolution task every 30 minutes
    scheduler.add_job(
        lambda: _run_handoff_resolution(),
        trigger=IntervalTrigger(minutes=30),
        id="handoff_resolution_task",
        name="Handoff Resolution Lifecycle",
        replace_existing=True,
    )

    # Story 6-6: Schedule GDPR compliance check daily at 9 AM UTC
    add_gdpr_job_to_scheduler(scheduler)

    # Story 6-6: Schedule GDPR confirmation emails processing
    add_email_job_to_scheduler(scheduler)

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
