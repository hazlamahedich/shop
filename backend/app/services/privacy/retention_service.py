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
from sqlalchemy import delete

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
    ) -> int:
        """Delete VOLUNTARY tier data older than retention period.

        Story 6-4: Automated retention enforcement

        Args:
            db: Database session
            days: Retention period in days (default: 30)

        Returns:
            Number of records deleted
        """
        from app.models.conversation import Conversation
        from app.models.message import Message

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        async with db as session:
            # Delete expired conversations
            conv_result = await session.execute(
                delete(Conversation)
                .where(Conversation.data_tier == DataTier.VOLUNTARY)
                .where(Conversation.updated_at < cutoff_date)
                .returning(Conversation.id)
            )
            deleted_conversations = conv_result.scalars().all()

            # Delete orphaned messages
            msg_result = await session.execute(
                delete(Message)
                .where(Message.data_tier == DataTier.VOLUNTARY)
                .where(Message.created_at < cutoff_date)
                .returning(Message.id)
            )
            deleted_messages = msg_result.scalars().all()

            await session.commit()

            total_deleted = len(deleted_conversations) + len(deleted_messages)

            logger.info(
                "retention_policy_executed",
                tier=DataTier.VOLUNTARY.value,
                retention_days=days,
                deleted_conversations=len(deleted_conversations),
                deleted_messages=len(deleted_messages),
                cutoff_date=cutoff_date.isoformat(),
            )

            return total_deleted
