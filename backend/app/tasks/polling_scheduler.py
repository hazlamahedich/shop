"""Polling scheduler for Shopify order polling.

Story 4-4 Task 9: Scheduler lifecycle management

Features:
- APScheduler with 5-minute polling interval
- SQLAlchemy job store for persistence across restarts
- Graceful startup and shutdown
- Distributed locking for multi-instance safety
- Health tracking and status endpoints
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime

import structlog
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.core.database import async_session
from app.models.shopify_integration import ShopifyIntegration
from app.services.shopify.order_polling_service import (
    OrderPollingService,
    PollingStatus,
)

logger = structlog.get_logger(__name__)


class PollingScheduler:
    """Scheduler for Shopify order polling.

    Manages the lifecycle of the polling service including:
    - Starting the 5-minute polling cycle
    - Graceful shutdown with in-flight poll completion
    - Health status tracking
    """

    POLLING_INTERVAL_MINUTES = 5
    SHUTDOWN_TIMEOUT_SECONDS = 30

    def __init__(self) -> None:
        """Initialize polling scheduler."""
        self.scheduler: AsyncIOScheduler | None = None
        self.polling_service = OrderPollingService()
        self._in_flight_polls: int = 0
        self._shutdown_requested: bool = False
        self._started_at: datetime | None = None

    async def get_merchants_with_shopify(self) -> list[int]:
        """Get list of merchant IDs with verified Shopify integrations.

        Returns:
            List of merchant IDs to poll
        """
        try:
            async with async_session() as db:
                result = await db.execute(
                    select(ShopifyIntegration.merchant_id)
                    .where(ShopifyIntegration.admin_api_verified.is_(True))
                    .distinct()
                )
                merchant_ids = [row[0] for row in result.fetchall()]

                if not merchant_ids:
                    logger.info(
                        "polling_no_merchants_configured",
                        error_code=7053,
                    )

                return merchant_ids
        except Exception as e:
            logger.error(
                "polling_merchant_lookup_failed",
                error=str(e),
                error_code=7054,
            )
            return []

    async def _poll_cycle(self) -> None:
        """Execute a single polling cycle for all merchants."""
        if self._shutdown_requested:
            logger.info("polling_cycle_skipped_shutdown_requested")
            return

        self._in_flight_polls += 1
        start_time = datetime.now(UTC)

        try:
            merchant_ids = await self.get_merchants_with_shopify()

            if not merchant_ids:
                return

            async with async_session() as db:
                results = await self.polling_service.poll_all_merchants(
                    merchant_ids=merchant_ids,
                    db=db,
                    delay_between_merchants=0.1,
                )

            success_count = sum(1 for r in results if r.status == PollingStatus.SUCCESS)
            duration_ms = (datetime.now(UTC) - start_time).total_seconds() * 1000

            logger.info(
                "polling_scheduler_cycle_complete",
                merchants_count=len(merchant_ids),
                success_count=success_count,
                duration_ms=round(duration_ms, 2),
            )

        except Exception as e:
            logger.error(
                "polling_scheduler_cycle_error",
                error=str(e),
                error_code=7054,
            )
        finally:
            self._in_flight_polls -= 1

    async def startup(self) -> None:
        """Start the polling scheduler.

        Called from application startup.
        """
        if self.scheduler is not None and self.scheduler.running:
            logger.warning("polling_scheduler_already_running")
            return

        database_url = os.getenv("DATABASE_URL", os.getenv("TEST_DATABASE_URL", ""))

        jobstores = {}
        job_store_type = "memory"

        if database_url:
            try:
                jobstores = {"default": SQLAlchemyJobStore(url=database_url)}
                job_store_type = "sqlalchemy"
            except Exception as e:
                logger.warning(
                    "polling_scheduler_jobstore_fallback",
                    error=str(e),
                    fallback="memory",
                )

        self.scheduler = AsyncIOScheduler(jobstores=jobstores)

        self.scheduler.add_job(
            self._poll_cycle,
            trigger=IntervalTrigger(minutes=self.POLLING_INTERVAL_MINUTES),
            id="shopify_order_polling",
            name="Shopify Order Polling",
            replace_existing=True,
        )

        self.scheduler.start()
        self._started_at = datetime.now(UTC)
        self.polling_service.set_scheduler_running(True)
        self._shutdown_requested = False

        logger.info(
            "polling_scheduler_started",
            interval_minutes=self.POLLING_INTERVAL_MINUTES,
            started_at=self._started_at.isoformat(),
            job_store=job_store_type,
        )

    async def shutdown(self) -> None:
        """Shutdown the polling scheduler gracefully.

        - Stops accepting new polling cycles
        - Waits for in-flight polls to complete (max 30 seconds)
        - Releases all distributed locks
        """
        if self.scheduler is None:
            return

        self._shutdown_requested = True
        self.polling_service.set_scheduler_running(False)

        logger.info(
            "polling_scheduler_shutdown_initiated",
            in_flight_polls=self._in_flight_polls,
            wait_timeout_seconds=self.SHUTDOWN_TIMEOUT_SECONDS,
        )

        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

        wait_start = datetime.now(UTC)
        while self._in_flight_polls > 0:
            elapsed = (datetime.now(UTC) - wait_start).total_seconds()
            if elapsed >= self.SHUTDOWN_TIMEOUT_SECONDS:
                logger.warning(
                    "polling_scheduler_shutdown_timeout",
                    remaining_in_flight=self._in_flight_polls,
                )
                break

            await asyncio.sleep(0.5)

        logger.info(
            "polling_scheduler_shutdown_complete",
            in_flight_polls=self._in_flight_polls,
        )

        self.scheduler = None

    def get_status(self) -> dict:
        """Get scheduler status.

        Returns:
            Dict with scheduler status information
        """
        health = self.polling_service.get_health_status()
        health["started_at"] = self._started_at.isoformat() if self._started_at else None
        health["in_flight_polls"] = self._in_flight_polls
        health["shutdown_requested"] = self._shutdown_requested

        if self.scheduler is not None and self.scheduler.running:
            jobs = self.scheduler.get_jobs()
            if jobs:
                job = jobs[0]
                health["next_run_time"] = (
                    job.next_run_time.isoformat() if job.next_run_time else None
                )

        return health


_global_scheduler: PollingScheduler | None = None


def get_polling_scheduler() -> PollingScheduler:
    """Get the global polling scheduler instance.

    Returns:
        PollingScheduler singleton
    """
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = PollingScheduler()
    return _global_scheduler


async def start_polling_scheduler() -> None:
    """Start the polling scheduler.

    Called from application lifespan startup.
    """
    scheduler = get_polling_scheduler()
    await scheduler.startup()


async def shutdown_polling_scheduler() -> None:
    """Shutdown the polling scheduler.

    Called from application lifespan shutdown.
    """
    scheduler = get_polling_scheduler()
    await scheduler.shutdown()


def get_polling_status() -> dict:
    """Get polling scheduler status.

    Returns:
        Dict with scheduler status
    """
    scheduler = get_polling_scheduler()
    return scheduler.get_status()
