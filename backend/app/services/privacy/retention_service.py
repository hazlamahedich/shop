"""Retention policy service for GDPR/CCPA compliance.

Story 6-4: Data Tier Separation
Story 6-5: 30-Day Retention Enforcement

Implements automated retention policies for different data tiers:
- VOLUNTARY: Delete after 30 days of inactivity
- OPERATIONAL: Keep indefinitely (business requirement)
- ANONYMIZED: Keep indefinitely for analytics (no PII)

Retention policies ensure GDPR/CCPA compliance by automatically deleting
data that the retention period has expired.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import delete, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.services.privacy.data_tier_service import DataTier


logger = structlog.get_logger(__name__)


class RetentionPolicy:
    """Service for managing data retention based on tier classification.

    Retention Policies:
    - VOLUNTARY: 30-day retention (GDPR/CCPA requirement)
    - OPERATIONAL: Indefinite retention (business requirement)
    - ANONYMIZED: Indefinite retention (no PII)
    """

    @staticmethod
    def get_retention_days(tier: DataTier) -> int:
        """Get retention period in days for a data tier.

        Args:
            tier: DataTier enum value

        Returns:
            Number of days to retain data (0 = indefinite)
        """
        retention_policies = {
            DataTier.VOLUNTARY: 30,
            DataTier.OPERATIONAL: 0,
            DataTier.ANONYMIZED: 0,
        }

        return retention_policies.get(tier, 0)

    @staticmethod
    async def delete_expired_voluntary_data(
        db: "AsyncSession",
        days: int = 30,
        batch_size: int = 1000,
        timeout_seconds: int = 300,
    ) -> int:
        """Delete VOLUNTARY tier data older than retention period.

        Story 6-4: Automated retention enforcement
        Story 6-5: Enhanced with audit logging and batch processing (AC5)

        Performance: Processes in batches to handle 10K+ conversations
        within 5-minute timeout requirement.

        Args:
            db: Database session
            days: Retention period in days (default: 30)
            batch_size: Number of records to process per batch (default: 1000)
            timeout_seconds: Maximum execution time in seconds (default: 300)

        Returns:
            Number of records deleted
        """
        from app.models.conversation import Conversation
        from app.models.deletion_audit_log import DeletionAuditLog, DeletionTrigger
        import asyncio

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        total_deleted = 0
        start_time = datetime.utcnow()

        async with db as session:
            # Process in batches to avoid timeout
            while True:
                # Check timeout
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                if elapsed >= timeout_seconds:
                    logger.warning(
                        "retention_policy_timeout_reached",
                        elapsed_seconds=elapsed,
                        total_deleted=total_deleted,
                        timeout_seconds=timeout_seconds,
                    )
                    break

                # Fetch batch of expired conversations
                conv_result = await session.execute(
                    select(Conversation.id, Conversation.merchant_id)
                    .where(Conversation.data_tier == DataTier.VOLUNTARY)
                    .where(Conversation.updated_at < cutoff_date)
                    .limit(batch_size)
                )
                batch = conv_result.fetchall()

                if not batch:
                    break

                # Delete batch
                conv_ids = [conv_id for conv_id, _ in batch]
                await session.execute(delete(Conversation).where(Conversation.id.in_(conv_ids)))
                await session.commit()

                # Create audit logs for batch
                for conv_id, merchant_id in batch:
                    audit_log = DeletionAuditLog(
                        session_id=f"retention-auto-{conv_id}",
                        merchant_id=merchant_id,
                        retention_period_days=days,
                        deletion_trigger=DeletionTrigger.AUTO,
                        conversations_deleted=1,
                        messages_deleted=0,
                        redis_keys_cleared=0,
                    )
                    audit_log.mark_completed(
                        conversations=1,
                        messages=0,
                        redis_keys=0,
                    )
                    session.add(audit_log)

                await session.commit()
                total_deleted += len(batch)

                logger.info(
                    "retention_policy_batch_processed",
                    batch_size=len(batch),
                    total_deleted=total_deleted,
                    elapsed_seconds=(datetime.utcnow() - start_time).total_seconds(),
                )

            logger.info(
                "retention_policy_executed",
                tier=DataTier.VOLUNTARY.value,
                retention_days=days,
                deleted_conversations=total_deleted,
                cutoff_date=cutoff_date.isoformat(),
                audit_logs_created=total_deleted,
                elapsed_seconds=(datetime.utcnow() - start_time).total_seconds(),
            )

            return total_deleted
