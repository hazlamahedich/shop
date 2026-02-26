"""Data tier classification service for GDPR/CCPA compliance.

Story 6-1: Opt-In Consent Flow

Provides data classification based on retention requirements:
- VOLUNTARY: User preferences, conversation history (deletable)
- OPERATIONAL: Order references, cart contents, consent records (business required)
- ANONYMIZED: Aggregated analytics without PII (indefinite retention)
"""

from __future__ import annotations

from enum import Enum

import structlog


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
