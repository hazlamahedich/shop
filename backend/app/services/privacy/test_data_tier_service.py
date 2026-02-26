"""Tests for DataTierService.

Story 6-1: Opt-In Consent Flow

Tests for data tier classification service.
"""

from __future__ import annotations

import pytest

from app.services.privacy.data_tier_service import DataTierService, DataTier


class TestClassifyDataTier:
    """Tests for classify_data_tier method."""

    def test_conversation_history_is_voluntary(self) -> None:
        """Test conversation history is classified as VOLUNTARY."""
        tier = DataTierService.classify_data_tier("conversation_history")
        assert tier == DataTier.VOLUNTARY

    def test_product_preferences_is_voluntary(self) -> None:
        """Test product preferences is classified as VOLUNTARY."""
        tier = DataTierService.classify_data_tier("product_preferences")
        assert tier == DataTier.VOLUNTARY

    def test_voluntary_memory_is_voluntary(self) -> None:
        """Test voluntary memory is classified as VOLUNTARY."""
        tier = DataTierService.classify_data_tier("voluntary_memory")
        assert tier == DataTier.VOLUNTARY

    def test_chat_messages_is_voluntary(self) -> None:
        """Test chat messages is classified as VOLUNTARY."""
        tier = DataTierService.classify_data_tier("chat_messages")
        assert tier == DataTier.VOLUNTARY

    def test_order_references_is_operational(self) -> None:
        """Test order references is classified as OPERATIONAL."""
        tier = DataTierService.classify_data_tier("order_references")
        assert tier == DataTier.OPERATIONAL

    def test_cart_contents_is_operational(self) -> None:
        """Test cart contents is classified as OPERATIONAL."""
        tier = DataTierService.classify_data_tier("cart_contents")
        assert tier == DataTier.OPERATIONAL

    def test_consent_records_is_operational(self) -> None:
        """Test consent records is classified as OPERATIONAL."""
        tier = DataTierService.classify_data_tier("consent_records")
        assert tier == DataTier.OPERATIONAL

    def test_session_id_is_operational(self) -> None:
        """Test session ID is classified as OPERATIONAL."""
        tier = DataTierService.classify_data_tier("session_id")
        assert tier == DataTier.OPERATIONAL

    def test_aggregated_analytics_is_anonymized(self) -> None:
        """Test aggregated analytics is classified as ANONYMIZED."""
        tier = DataTierService.classify_data_tier("aggregated_analytics")
        assert tier == DataTier.ANONYMIZED

    def test_cost_tracking_is_anonymized(self) -> None:
        """Test cost tracking is classified as ANONYMIZED."""
        tier = DataTierService.classify_data_tier("cost_tracking")
        assert tier == DataTier.ANONYMIZED

    def test_unknown_type_defaults_to_operational(self) -> None:
        """Test unknown data type defaults to OPERATIONAL (conservative)."""
        tier = DataTierService.classify_data_tier("unknown_data_type")
        assert tier == DataTier.OPERATIONAL

    def test_case_insensitive_classification(self) -> None:
        """Test classification is case insensitive."""
        assert DataTierService.classify_data_tier("CONVERSATION_HISTORY") == DataTier.VOLUNTARY
        assert DataTierService.classify_data_tier("Order_References") == DataTier.OPERATIONAL


class TestCanDeleteData:
    """Tests for can_delete_data method."""

    def test_can_delete_voluntary_data(self) -> None:
        """Test voluntary data can be deleted."""
        assert DataTierService.can_delete_data("conversation_history") is True
        assert DataTierService.can_delete_data("product_preferences") is True

    def test_cannot_delete_operational_data(self) -> None:
        """Test operational data cannot be deleted."""
        assert DataTierService.can_delete_data("order_references") is False
        assert DataTierService.can_delete_data("consent_records") is False

    def test_cannot_delete_anonymized_data(self) -> None:
        """Test anonymized data cannot be deleted."""
        assert DataTierService.can_delete_data("aggregated_analytics") is False


class TestGetRetentionDays:
    """Tests for get_retention_days method."""

    def test_voluntary_retention_is_30_days(self) -> None:
        """Test voluntary data has 30-day retention."""
        days = DataTierService.get_retention_days("conversation_history")
        assert days == 30

    def test_operational_retention_is_365_days(self) -> None:
        """Test operational data has 365-day retention."""
        days = DataTierService.get_retention_days("order_references")
        assert days == 365

    def test_anonymized_retention_is_indefinite(self) -> None:
        """Test anonymized data has indefinite retention (0 days)."""
        days = DataTierService.get_retention_days("aggregated_analytics")
        assert days == 0


class TestGetTierDescription:
    """Tests for get_tier_description method."""

    def test_voluntary_description(self) -> None:
        """Test voluntary tier description."""
        desc = DataTierService.get_tier_description(DataTier.VOLUNTARY)
        assert "preferences" in desc.lower()
        assert "deletable" in desc.lower()

    def test_operational_description(self) -> None:
        """Test operational tier description."""
        desc = DataTierService.get_tier_description(DataTier.OPERATIONAL)
        assert "order" in desc.lower()
        assert "business" in desc.lower()

    def test_anonymized_description(self) -> None:
        """Test anonymized tier description."""
        desc = DataTierService.get_tier_description(DataTier.ANONYMIZED)
        assert "analytics" in desc.lower()
        assert "personal" in desc.lower()


class TestGetAllDataTypes:
    """Tests for get_all_*_data_types methods."""

    def test_get_all_voluntary_data_types(self) -> None:
        """Test getting all voluntary data types."""
        types = DataTierService.get_all_voluntary_data_types()

        assert "conversation_history" in types
        assert "product_preferences" in types
        assert len(types) >= 5

    def test_get_all_operational_data_types(self) -> None:
        """Test getting all operational data types."""
        types = DataTierService.get_all_operational_data_types()

        assert "order_references" in types
        assert "consent_records" in types
        assert len(types) >= 5

    def test_get_all_anonymized_data_types(self) -> None:
        """Test getting all anonymized data types."""
        types = DataTierService.get_all_anonymized_data_types()

        assert "aggregated_analytics" in types
        assert "cost_tracking" in types
        assert len(types) >= 3

    def test_no_overlap_between_tiers(self) -> None:
        """Test no data type appears in multiple tiers."""
        voluntary = DataTierService.get_all_voluntary_data_types()
        operational = DataTierService.get_all_operational_data_types()
        anonymized = DataTierService.get_all_anonymized_data_types()

        assert voluntary.isdisjoint(operational)
        assert voluntary.isdisjoint(anonymized)
        assert operational.isdisjoint(anonymized)


class TestDataTierEnum:
    """Tests for DataTier enum."""

    def test_enum_values(self) -> None:
        """Test DataTier enum has expected values."""
        assert DataTier.VOLUNTARY.value == "voluntary"
        assert DataTier.OPERATIONAL.value == "operational"
        assert DataTier.ANONYMIZED.value == "anonymized"

    def test_enum_is_string(self) -> None:
        """Test DataTier enum inherits from str."""
        assert isinstance(DataTier.VOLUNTARY, str)
        assert isinstance(DataTier.OPERATIONAL, str)
        assert isinstance(DataTier.ANONYMIZED, str)
