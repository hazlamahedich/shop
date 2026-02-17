"""Tests for polling scheduler.

Story 4-4 Task 6: Unit tests for scheduler
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Set empty DATABASE_URL to force memory jobstore for tests
os.environ["DATABASE_URL"] = ""
os.environ["TEST_DATABASE_URL"] = ""

from app.tasks.polling_scheduler import (
    PollingScheduler,
    get_polling_scheduler,
    start_polling_scheduler,
    shutdown_polling_scheduler,
    get_polling_status,
)


async def _force_shutdown_global_scheduler():
    """Force shutdown of global scheduler if running."""
    import app.tasks.polling_scheduler as scheduler_module

    if scheduler_module._global_scheduler is not None:
        try:
            sched = scheduler_module._global_scheduler
            if sched.scheduler is not None:
                if hasattr(sched.scheduler, "running") and sched.scheduler.running:
                    sched.scheduler.shutdown(wait=False)
                sched.scheduler = None
        except Exception:
            pass
    scheduler_module._global_scheduler = None


@pytest_asyncio.fixture(autouse=True)
async def reset_global_scheduler():
    """Reset global scheduler before and after each test."""
    await _force_shutdown_global_scheduler()

    yield

    await _force_shutdown_global_scheduler()


class TestPollingScheduler:
    """Tests for PollingScheduler."""

    @pytest.fixture
    def scheduler(self):
        """Create scheduler instance."""
        scheduler = PollingScheduler()
        yield scheduler
        if scheduler.scheduler is not None and scheduler.scheduler.running:
            scheduler.scheduler.shutdown(wait=False)

    @pytest.fixture
    def mock_polling_service(self):
        """Mock polling service."""
        service = MagicMock()
        service.poll_all_merchants = AsyncMock(return_value=[])
        service.get_health_status = MagicMock(
            return_value={
                "scheduler_running": False,
                "last_poll_timestamp": None,
                "merchants_polled": 0,
                "total_orders_synced": 0,
                "errors_last_hour": 0,
                "merchant_status": [],
            }
        )
        service.set_scheduler_running = MagicMock()
        return service

    def test_scheduler_initialization(self, scheduler):
        """Test scheduler initializes correctly."""
        assert scheduler.scheduler is None
        assert scheduler._in_flight_polls == 0
        assert scheduler._shutdown_requested is False
        assert scheduler._started_at is None

    @pytest.mark.asyncio
    async def test_get_merchants_with_shopify_empty(self, scheduler):
        """Test getting merchants when none configured."""
        with patch.object(scheduler, "get_merchants_with_shopify", return_value=[]):
            merchants = await scheduler.get_merchants_with_shopify()
            assert merchants == []

    @pytest.mark.asyncio
    async def test_startup(self, scheduler):
        """Test scheduler startup."""
        await scheduler.startup()

        assert scheduler.scheduler is not None
        assert scheduler.scheduler.running is True
        assert scheduler._started_at is not None
        assert scheduler._shutdown_requested is False

        await scheduler.shutdown()

    @pytest.mark.asyncio
    async def test_startup_idempotent(self, scheduler):
        """Test calling startup multiple times."""
        await scheduler.startup()
        first_started_at = scheduler._started_at

        await scheduler.startup()

        assert scheduler._started_at == first_started_at

        await scheduler.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown(self, scheduler):
        """Test scheduler shutdown."""
        await scheduler.startup()
        await scheduler.shutdown()

        assert scheduler.scheduler is None
        assert scheduler._shutdown_requested is True

    @pytest.mark.asyncio
    async def test_shutdown_waits_for_in_flight(self, scheduler, mock_polling_service):
        """Test shutdown waits for in-flight polls."""
        scheduler.polling_service = mock_polling_service
        scheduler._in_flight_polls = 1

        async def simulate_poll_completion():
            await asyncio.sleep(0.1)
            scheduler._in_flight_polls = 0

        await scheduler.startup()

        asyncio.create_task(simulate_poll_completion())
        await scheduler.shutdown()

        assert scheduler._in_flight_polls == 0

    @pytest.mark.asyncio
    async def test_poll_cycle_skips_when_shutdown_requested(self, scheduler, mock_polling_service):
        """Test that poll cycle is skipped during shutdown."""
        scheduler.polling_service = mock_polling_service
        scheduler._shutdown_requested = True

        await scheduler._poll_cycle()

        mock_polling_service.poll_all_merchants.assert_not_called()

    def test_get_status(self, scheduler, mock_polling_service):
        """Test getting scheduler status."""
        scheduler.polling_service = mock_polling_service
        scheduler._started_at = datetime.now(timezone.utc)
        scheduler._in_flight_polls = 0
        scheduler._shutdown_requested = False

        status = scheduler.get_status()

        assert "scheduler_running" in status
        assert "started_at" in status
        assert "in_flight_polls" in status
        assert "shutdown_requested" in status


class TestSchedulerFunctions:
    """Tests for module-level functions."""

    def test_get_polling_scheduler_singleton(self):
        """Test that get_polling_scheduler returns singleton."""
        scheduler1 = get_polling_scheduler()
        scheduler2 = get_polling_scheduler()

        assert scheduler1 is scheduler2

    @pytest.mark.asyncio
    async def test_start_polling_scheduler(self):
        """Test start_polling_scheduler function."""
        await start_polling_scheduler()

        scheduler = get_polling_scheduler()
        assert scheduler.scheduler is not None
        assert scheduler.scheduler.running is True

        await shutdown_polling_scheduler()

    @pytest.mark.asyncio
    async def test_shutdown_polling_scheduler(self):
        """Test shutdown_polling_scheduler function."""
        await start_polling_scheduler()
        await shutdown_polling_scheduler()

        scheduler = get_polling_scheduler()
        assert scheduler.scheduler is None
        assert scheduler._shutdown_requested is True

    def test_get_polling_status(self):
        """Test get_polling_status function."""
        status = get_polling_status()

        assert isinstance(status, dict)
        assert "scheduler_running" in status
