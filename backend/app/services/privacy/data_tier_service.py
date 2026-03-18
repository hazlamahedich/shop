"""Data tier classification service for GDPR/CCPA compliance.

Story 6-1: Opt-In Consent Flow
Story 6-4: Data Tier Separation

Provides data classification based on retention requirements:
- VOLUNTARY: User preferences, conversation history (deletable)
- OPERATIONAL: Order references, cart contents, consent records (business required)
- ANONYMIZED: Aggregated analytics without PII (indefinite retention)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import delete, func, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import DeclarativeBase


logger = structlog.get_logger(__name__)


class DataTier(str, Enum):
    """Data classification tiers for GDPR/CCPA compliance."""

    VOLUNTARY = "voluntary"
    OPERATIONAL = "operational"
    ANONYMIZED = "anonymized"


class DataTierService:
    """Service for classifying data into compliance tiers.

    Data Tier Classification:
    - VOLUNTARY: User preferences, conversation history - 30 day retention, deletable
    - OPERATIONAL: Order references, active cart, consent records - business required
    - ANONYMIZED: Aggregated analytics, cost tracking - indefinite, no PII
    """

    VOLUNTARY_DATA_TYPES = {
        "conversation_history",
        "product_preferences",
        "voluntary_memory",
        "chat_messages",
        "user_preferences",
        "search_history",
        "browsing_history",
    }

    OPERATIONAL_DATA_TYPES = {
        "order_references",
        "cart_contents",
        "consent_records",
        "payment_references",
        "shipping_info",
        "customer_id",
        "session_id",
    }

    ANONYMIZED_DATA_TYPES = {
        "aggregated_analytics",
        "cost_tracking",
        "performance_metrics",
        "usage_statistics",
    }

    @classmethod
    def classify_data_tier(cls, data_type: str) -> DataTier:
        data_type_lower = data_type.lower()

        if data_type_lower in cls.VOLUNTARY_DATA_TYPES:
            return DataTier.VOLUNTARY

        if data_type_lower in cls.OPERATIONAL_DATA_TYPES:
            return DataTier.OPERATIONAL

        if data_type_lower in cls.ANONYMIZED_DATA_TYPES:
            return DataTier.ANONYMIZED

        logger.warning(
            "unknown_data_type",
            data_type=data_type,
            default_tier=DataTier.OPERATIONAL.value,
        )
        return DataTier.OPERATIONAL

    @classmethod
    def can_delete_data(cls, data_type: str) -> bool:
        """Check if data type can be deleted by user.

        Args:
            data_type: Type of data to check

        Returns:
            True if data can be deleted (VOLUNTARY tier)
        """
        tier = cls.classify_data_tier(data_type)
        return tier == DataTier.VOLUNTARY

    @classmethod
    def get_retention_days(cls, data_type: str) -> int:
        """Get retention period in days for data type.

        Args:
            data_type: Type of data to check

        Returns:
            Number of days to retain data (0 = indefinite)
        """
        tier = cls.classify_data_tier(data_type)

        if tier == DataTier.VOLUNTARY:
            return 30
        elif tier == DataTier.OPERATIONAL:
            return 365
        else:
            return 0

    @classmethod
    def get_tier_description(cls, tier: DataTier) -> str:
        """Get human-readable description of data tier.

        Args:
            tier: DataTier enum value

        Returns:
            Description string
        """
        descriptions = {
            DataTier.VOLUNTARY: "User preferences and conversation history - deletable via 'forget my preferences'",
            DataTier.OPERATIONAL: "Order references and business data - retained for order support",
            DataTier.ANONYMIZED: "Aggregated analytics without personal data - indefinite retention",
        }
        return descriptions.get(tier, "Unknown data tier")

    @classmethod
    def get_all_voluntary_data_types(cls) -> set[str]:
        """Get all data types in VOLUNTARY tier.

        Returns:
            Set of voluntary data type names
        """
        return cls.VOLUNTARY_DATA_TYPES.copy()

    @classmethod
    def get_all_operational_data_types(cls) -> set[str]:
        """Get all data types in OPERATIONAL tier.

        Returns:
            Set of operational data type names
        """
        return cls.OPERATIONAL_DATA_TYPES.copy()

    @classmethod
    def get_all_anonymized_data_types(cls) -> set[str]:
        """Get all data types in ANONYMIZED tier.

        Returns:
            Set of anonymized data type names
        """
        return cls.ANONYMIZED_DATA_TYPES.copy()

    # ==============================================================================
    # Story 6-4: Data Tier Extensions
    # ==============================================================================

    @classmethod
    def categorize_data(cls, data_type: str) -> DataTier:
        """Alias for classify_data_tier() for consistency.

        Args:
            data_type: Type of data to classify

        Returns:
            DataTier enum value
        """
        return cls.classify_data_tier(data_type)

    @classmethod
    async def get_tier_summary(cls, db: AsyncSession, merchant_id: int) -> dict:
        """Get tier distribution summary for a merchant.

        Args:
            db: Database session
            merchant_id: Merchant ID to get summary for

        Returns:
            Dictionary with tier counts and total
        """
        from app.models.conversation import Conversation

        async with db as session:
            result = await session.execute(
                select(Conversation.data_tier, func.count(Conversation.id).label("count"))
                .where(Conversation.merchant_id == merchant_id)
                .group_by(Conversation.data_tier)
            )

            tier_counts = {row[0]: row[1] for row in result.fetchall()}

            return {
                "voluntary": tier_counts.get(DataTier.VOLUNTARY, 0),
                "operational": tier_counts.get(DataTier.OPERATIONAL, 0),
                "anonymized": tier_counts.get(DataTier.ANONYMIZED, 0),
                "total": sum(tier_counts.values()),
            }

    @classmethod
    async def update_tier(
        cls,
        db: AsyncSession,
        model_class: type[DeclarativeBase],
        record_id: int,
        new_tier: DataTier,
    ) -> None:
        """Update data tier for a specific record.

        Args:
            db: Database session
            model_class: SQLAlchemy model class
            record_id: ID of the record to update
            new_tier: New data tier value

        Raises:
            ValueError: If tier downgrade is attempted (operational → voluntary)
        """
        async with db as session:
            result = await session.execute(select(model_class).where(model_class.id == record_id))
            record = result.scalar_one_or_none()

            if not record:
                raise ValueError(f"Record {record_id} not found")

            current_tier = record.data_tier

            # Prevent tier downgrade (data protection)
            if current_tier == DataTier.OPERATIONAL and new_tier == DataTier.VOLUNTARY:
                raise ValueError(
                    "Tier downgrade not allowed: operational data cannot become voluntary"
                )

            record.data_tier = new_tier
            await session.commit()

            logger.info(
                "data_tier_updated",
                record_id=record_id,
                model=model_class.__name__,
                old_tier=current_tier.value,
                new_tier=new_tier.value,
            )

    @classmethod
    async def apply_retention_policy(
        cls,
        db: AsyncSession,
        tier: DataTier,
        days: int | None = None,
    ) -> int:
        """Apply retention policy for a specific tier.

        Args:
            db: Database session
            tier: Data tier to apply retention policy to
            days: Optional custom retention period (defaults based on tier)

        Returns:
            Number of records deleted

        Note:
            - VOLUNTARY: Default 30-day retention
            - OPERATIONAL: No deletion (indefinite retention)
            - ANONYMIZED: No deletion (indefinite retention)
        """
        if tier == DataTier.OPERATIONAL:
            logger.info(
                "retention_skipped_operational", reason="Operational data has indefinite retention"
            )
            return 0

        if tier == DataTier.ANONYMIZED:
            logger.info(
                "retention_skipped_anonymized", reason="Anonymized data has indefinite retention"
            )
            return 0

        # VOLUNTARY tier: Apply retention policy
        retention_days = days if days is not None else 30
        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)

        from app.models.conversation import Conversation
        from app.models.message import Message

        deleted_count = 0

        async with db as session:
            # Delete old conversations
            result = await session.execute(
                delete(Conversation)
                .where(Conversation.data_tier == tier)
                .where(Conversation.created_at < cutoff_date)
                .returning(Conversation.id)
            )
            conv_ids = [row[0] for row in result.fetchall()]
            deleted_count += len(conv_ids)

            # Delete old messages (orphaned by conversation cascade)
            result = await session.execute(
                delete(Message)
                .where(Message.data_tier == tier)
                .where(Message.created_at < cutoff_date)
                .returning(Message.id)
            )
            msg_ids = [row[0] for row in result.fetchall()]
            deleted_count += len(msg_ids)

            await session.commit()

            logger.info(
                "retention_policy_applied",
                tier=tier.value,
                retention_days=retention_days,
                deleted_count=deleted_count,
                cutoff_date=cutoff_date.isoformat(),
            )

        return deleted_count
