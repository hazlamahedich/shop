"""Background job to send pending GDPR/CCPA confirmation emails.

Story 6-6: GDPR Deletion Processing - Task 4.5

Periodically checks for DeletionAuditLog entries that require a confirmation
email but haven't been sent one yet.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.deletion_audit_log import DeletionAuditLog, DeletionRequestType
from app.services.email.email_service import EmailService

logger = structlog.get_logger(__name__)


async def send_pending_gdpr_emails(db: AsyncSession | None = None) -> dict:
    """Send confirmation emails for pending GDPR/CCPA requests.

    Story 6-6: Task 4.5

    Fetches DeletionAuditLog entries where:
    - confirmation_email_sent == False
    - email_sent_at is null
    - customer_email is not null

    Sends emails using EmailService and updates the database records.

    Args:
        db: Optional database session (created if not provided)

    Returns:
        dict: Processing statistics (sent, failed, total)
    """
    logger.info("processing_pending_gdpr_emails_started", timestamp=datetime.utcnow().isoformat())

    stats = {
        "total_processed": 0,
        "emails_sent": 0,
        "emails_failed": 0,
    }

    async def process_with_session(session: AsyncSession):
        # Find entries that need emails
        stmt = (
            select(DeletionAuditLog)
            .where(DeletionAuditLog.confirmation_email_sent == False)
            .where(DeletionAuditLog.email_sent_at.is_(None))
            .where(DeletionAuditLog.customer_email.is_not(None))
        )

        result = await session.execute(stmt)
        pending_logs = result.scalars().all()

        stats["total_processed"] = len(pending_logs)

        if not pending_logs:
            logger.debug("no_pending_gdpr_emails_found")
            return

        email_service = EmailService()

        for log in pending_logs:
            try:
                # Default values if missing
                deadline = log.processing_deadline or (log.requested_at + timedelta(days=30))
                request_type = log.request_type or DeletionRequestType.GDPR_FORMAL.value

                success = await email_service.send_gdpr_confirmation(
                    to_email=log.customer_email,
                    customer_id=log.customer_id or log.session_id,
                    request_date=log.request_timestamp or log.requested_at,
                    deadline=deadline,
                    request_type=request_type,
                )

                if success:
                    # Update record
                    log.confirmation_email_sent = True
                    log.email_sent_at = datetime.utcnow()
                    log.customer_email = None  # Clear email for data minimization
                    stats["emails_sent"] += 1
                else:
                    stats["emails_failed"] += 1
                    logger.warning("gdpr_email_send_failed", audit_log_id=log.id)

            except Exception as e:
                stats["emails_failed"] += 1
                logger.error(
                    "gdpr_email_processing_error",
                    audit_log_id=log.id,
                    error=str(e),
                )

        # Commit all updates
        await session.commit()

    # Run with provided session or create a new one
    if db:
        await process_with_session(db)
    else:
        async with async_session()() as session:
            await process_with_session(session)

    logger.info("processing_pending_gdpr_emails_completed", **stats)
    return stats


def add_email_job_to_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Add the pending emails job to the APScheduler.

    Args:
        scheduler: The APScheduler instance
    """
    scheduler.add_job(
        lambda: send_pending_gdpr_emails(),
        trigger=IntervalTrigger(minutes=30),  # Check every 30 minutes
        id="send_pending_gdpr_emails",
        name="Process Pending GDPR Emails",
        replace_existing=True,
    )
    logger.info("scheduled_gdpr_email_job", interval="30 minutes")
