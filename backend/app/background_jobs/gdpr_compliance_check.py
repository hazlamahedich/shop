"""Background jobs for GDPR/CCPA compliance monitoring.

Story 6-6: GDPR Deletion Processing - Task 5.2

Monitors GDPR/CCPA 30-day compliance window and alerts on overdue requests.
Runs daily at 9 AM UTC to check compliance status.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Optional

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import async_session
from app.services.privacy.compliance_monitor import GDPRComplianceMonitor

logger = structlog.get_logger(__name__)

# Reference to main scheduler (imported from data_retention)
_main_scheduler: Optional[AsyncIOScheduler] = None


async def run_gdpr_compliance_check() -> dict:
    """Run daily GDPR compliance check job.

    Story 6-6: Task 5.2

    Checks for:
    - Overdue requests (past deadline, not completed)
    - Requests approaching deadline (within 5 days)

    Returns:
        Dictionary with compliance status and alert info
    """
    logger.info("gdpr_compliance_check_started", timestamp=datetime.now(timezone.utc).isoformat())

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "compliant": True,
        "overdue_count": 0,
        "approaching_count": 0,
        "alerts": [],
    }

    try:
        async with async_session() as db:
            monitor = GDPRComplianceMonitor()
            status = await monitor.check_compliance_status(db)

            results["overdue_count"] = status["overdue_count"]
            results["approaching_count"] = status["approaching_count"]

            # Alert on overdue requests (compliance violation)
            if status["overdue_count"] > 0:
                results["compliant"] = False
                results["alerts"].append(
                    {
                        "level": "error",
                        "type": "gdpr_overdue",
                        "count": status["overdue_count"],
                        "requests": status["overdue_requests"],
                        "message": f"{status['overdue_count']} GDPR request(s) are past their 30-day deadline",
                    }
                )

                logger.error(
                    "gdpr_compliance_overdue",
                    overdue_count=status["overdue_count"],
                    requests=status["overdue_requests"],
                )

            # Warning on approaching deadline
            if status["approaching_count"] > 0:
                results["alerts"].append(
                    {
                        "level": "warning",
                        "type": "gdpr_approaching",
                        "count": status["approaching_count"],
                        "requests": status["approaching_requests"],
                        "message": f"{status['approaching_count']} GDPR request(s) approaching deadline within 5 days",
                    }
                )

                logger.warning(
                    "gdpr_compliance_approaching",
                    approaching_count=status["approaching_count"],
                    requests=status["approaching_requests"],
                )

            # Log success
            if status["overdue_count"] == 0:
                logger.info(
                    "gdpr_compliance_ok",
                    approaching_count=status["approaching_count"],
                )

    except Exception as e:
        results["error"] = str(e)
        results["compliant"] = False
        logger.error(
            "gdpr_compliance_check_failed",
            error=str(e),
            error_type=type(e).__name__,
        )

    logger.info("gdpr_compliance_check_completed", **results)
    return results


def add_gdpr_job_to_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Add GDPR compliance check job to existing scheduler.

    Story 6-6: Task 5.2

    Should be called during application startup alongside other background jobs.
    Integrates with the main data_retention scheduler.

    Args:
        scheduler: Existing APScheduler instance
    """
    global _main_scheduler
    _main_scheduler = scheduler

    # Schedule daily GDPR compliance check at 9 AM UTC
    scheduler.add_job(
        run_gdpr_compliance_check,
        trigger=CronTrigger(hour=9, minute=0, timezone="UTC"),
        id="gdpr_compliance_check",
        name="Daily GDPR/CCPA compliance check",
        replace_existing=True,
        max_instances=1,  # Prevent concurrent execution
    )

    logger.info(
        "gdpr_compliance_job_added",
        job_id="gdpr_compliance_check",
        schedule="0 9 * * * (daily at 9 AM UTC)",
    )
