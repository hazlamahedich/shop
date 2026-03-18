"""Widget Analytics GDPR Cleanup Background Job.

Story 9-10: Scheduled job to cleanup old widget analytics events.
Runs weekly on delete events older than 30 days (configurable).
"""

from datetime import datetime, timezone, timedelta
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.services.analytics.widget_analytics_service import WidgetAnalyticsService


async def cleanup_widget_analytics():
    """Clean up widget analytics events older than retention period.

    This job runs weekly to delete events older than 30 days.
    """
    retention_days = 30
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    logger.info("Starting widget analytics cleanup job")

    async with async_session() as db:
        service = WidgetAnalyticsService(db)
        deleted = await service.cleanup_old_events(days=retention_days)
        logger.info("Deleted widget analytics events", count=deleted)

        logger.info("Widget analytics cleanup job completed")


async def schedule_cleanup():
    """Schedule the weekly cleanup job."""
    # Run weekly on Sunday at 2 AM
    schedule.every().sunday.at("02:00").do(cleanup_widget_analytics)


if __name__ == "__main__":
    from ap.background_jobs.scheduler import scheduler

    scheduler.add_job(cleanup_widget_analytics, name="cleanup_widget_analytics_week")
