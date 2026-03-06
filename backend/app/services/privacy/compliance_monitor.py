"""GDPR/CCPA compliance monitoring service.

Story 6-6: GDPR Deletion Processing

Monitors GDPR/CCPA 30-day compliance window and alerts on overdue requests.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deletion_audit_log import DeletionAuditLog

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)


class GDPRComplianceMonitor:
    """Monitor GDPR/CCPA 30-day compliance window.

    Checks for:
    - Overdue requests (past deadline, not completed)
    - Requests approaching deadline (within 5 days)
    - Provides compliance status for dashboard
    """

    async def check_compliance_status(self, db: AsyncSession) -> dict:
        """Check GDPR/CCPA compliance status.

        Returns:
            dict with compliance metrics and request lists
        """
        now = datetime.now(timezone.utc)

        # Find overdue requests (past deadline, not completed)
        overdue = await db.execute(
            select(DeletionAuditLog)
            .where(DeletionAuditLog.processing_deadline < now)
            .where(DeletionAuditLog.completion_date.is_(None))
        )
        overdue_requests = overdue.scalars().all()

        # Find requests approaching deadline (within 5 days)
        approaching_deadline = await db.execute(
            select(DeletionAuditLog)
            .where(DeletionAuditLog.processing_deadline <= now + timedelta(days=5))
            .where(DeletionAuditLog.processing_deadline > now)
            .where(DeletionAuditLog.completion_date.is_(None))
        )
        approaching_requests = approaching_deadline.scalars().all()

        return {
            "overdue_count": len(overdue_requests),
            "approaching_count": len(approaching_requests),
            "overdue_requests": [
                {
                    "id": r.id,
                    "customer_id": r.customer_id,
                    "deadline": r.processing_deadline.isoformat(),
                }
                for r in overdue_requests
            ],
            "approaching_requests": [
                {
                    "id": r.id,
                    "customer_id": r.customer_id,
                    "deadline": r.processing_deadline.isoformat(),
                }
                for r in approaching_requests
            ],
        }
