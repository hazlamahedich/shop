"""Unit tests for carrier service (Story 6.2).

Tests carrier detection service with priority-based resolution.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrier_config import CarrierConfig
from app.models.order import Order
from app.services.carrier.carrier_service import CarrierService


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def carrier_service(mock_db):
    """Create a carrier service instance."""
    return CarrierService(mock_db)


@pytest.fixture
def sample_order():
    """Create a sample order for testing."""
    order = MagicMock(spec=Order)
    order.id = 1
    order.order_number = "ORD-123"
    order.merchant_id = 1
    order.tracking_number = "1Z999AA10123456784"
    order.tracking_company = None
    order.tracking_url = None
    return order


class TestCarrierServiceInit:
    """Test CarrierService initialization."""

    def test_init_with_db(self, mock_db):
        """Test initialization with database session."""
        service = CarrierService(mock_db)
        assert service.db == mock_db


class TestGetTrackingUrl:
    """Test get_tracking_url method."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_tracking_number(self, carrier_service, sample_order):
        """Test that None is returned when order has no tracking number."""
        sample_order.tracking_number = None
        result = await carrier_service.get_tracking_url(sample_order)
        assert result is None

    @pytest.mark.asyncio
    async def test_uses_webhook_tracking_url_if_present(self, carrier_service, sample_order):
        """Test that webhook tracking_url is used if present."""
        sample_order.tracking_url = "https://custom.tracking.com/123"
        result = await carrier_service.get_tracking_url(sample_order)
        assert result == "https://custom.tracking.com/123"

    @pytest.mark.asyncio
    async def test_uses_shopify_mapping_when_tracking_company_present(
        self, carrier_service, sample_order, mock_db
    ):
        """Test Shopify carrier mapping is used when tracking_company is present."""
        sample_order.tracking_company = "UPS"
        sample_order.tracking_number = "1Z999AA10123456784"

        # Mock no custom carriers
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await carrier_service.get_tracking_url(sample_order)

        assert result is not None
        assert "ups.com" in result.lower()
        assert "1Z999AA10123456784" in result

    @pytest.mark.asyncio
    async def test_uses_pattern_detection_as_fallback(self, carrier_service, sample_order, mock_db):
        """Test pattern detection is used when no other method works."""
        sample_order.tracking_number = "1Z999AA10123456784"

        # Mock no custom carriers
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await carrier_service.get_tracking_url(sample_order)

        assert result is not None
        assert "ups.com" in result.lower()

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_tracking(self, carrier_service, sample_order, mock_db):
        """Test None is returned for unknown tracking number format."""
        sample_order.tracking_number = "INVALID123"

        # Mock no custom carriers
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await carrier_service.get_tracking_url(sample_order)
        assert result is None


class TestGetCustomCarrierUrl:
    """Test _get_custom_carrier_url method."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_tracking_number(self, carrier_service, sample_order):
        """Test None is returned when order has no tracking number."""
        sample_order.tracking_number = None
        result = await carrier_service._get_custom_carrier_url(sample_order)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_custom_carriers(
        self, carrier_service, sample_order, mock_db
    ):
        """Test None is returned when merchant has no custom carriers."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await carrier_service._get_custom_carrier_url(sample_order)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_url_when_pattern_matches(self, carrier_service, sample_order, mock_db):
        """Test URL is returned when custom carrier pattern matches."""
        # Create custom carrier
        custom_carrier = CarrierConfig(
            id=1,
            merchant_id=1,
            carrier_name="LBC Express",
            tracking_url_template="https://track.lbcexpress.com/{tracking_number}",
            tracking_number_pattern=r"^LBC\d{12}$",
            is_active=True,
            priority=100,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        sample_order.tracking_number = "LBC123456789012"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [custom_carrier]
        mock_db.execute.return_value = mock_result

        result = await carrier_service._get_custom_carrier_url(sample_order)

        assert result is not None
        assert "lbcexpress.com" in result
        assert "LBC123456789012" in result

    @pytest.mark.asyncio
    async def test_skips_inactive_carriers(self, carrier_service, sample_order, mock_db):
        """Test that inactive carriers are skipped."""
        # Create inactive custom carrier
        custom_carrier = CarrierConfig(
            id=1,
            merchant_id=1,
            carrier_name="LBC Express",
            tracking_url_template="https://track.lbcexpress.com/{tracking_number}",
            tracking_number_pattern=r"^LBC\d{12}$",
            is_active=False,  # Inactive
            priority=100,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        sample_order.tracking_number = "LBC123456789012"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # Only active carriers
        mock_db.execute.return_value = mock_result

        result = await carrier_service._get_custom_carrier_url(sample_order)
        assert result is None

    @pytest.mark.asyncio
    async def test_handles_invalid_regex_pattern(
        self, carrier_service, sample_order, mock_db, caplog
    ):
        """Test that invalid regex patterns are handled gracefully."""
        # Create custom carrier with invalid regex
        custom_carrier = CarrierConfig(
            id=1,
            merchant_id=1,
            carrier_name="Bad Carrier",
            tracking_url_template="https://track.bad.com/{tracking_number}",
            tracking_number_pattern=r"[invalid(regex",  # Invalid regex
            is_active=True,
            priority=100,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        sample_order.tracking_number = "ABC123"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [custom_carrier]
        mock_db.execute.return_value = mock_result

        # Should not raise exception, should return None
        result = await carrier_service._get_custom_carrier_url(sample_order)
        assert result is None
        assert "Invalid regex pattern" in caplog.text

    @pytest.mark.asyncio
    async def test_uses_priority_order(self, carrier_service, sample_order, mock_db):
        """Test that carriers are checked in priority order."""
        # Create two custom carriers with different priorities
        carrier1 = CarrierConfig(
            id=1,
            merchant_id=1,
            carrier_name="Low Priority",
            tracking_url_template="https://low.com/{tracking_number}",
            tracking_number_pattern=r"^TEST\d+$",
            is_active=True,
            priority=50,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        carrier2 = CarrierConfig(
            id=2,
            merchant_id=1,
            carrier_name="High Priority",
            tracking_url_template="https://high.com/{tracking_number}",
            tracking_number_pattern=r"^TEST\d+$",
            is_active=True,
            priority=100,  # Higher priority
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        sample_order.tracking_number = "TEST123"

        # Return in priority order (high first)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [carrier2, carrier1]
        mock_db.execute.return_value = mock_result

        result = await carrier_service._get_custom_carrier_url(sample_order)

        # Should use high priority carrier
        assert result is not None
        assert "high.com" in result


class TestDetectCarrier:
    """Test detect_carrier method."""

    @pytest.mark.asyncio
    async def test_returns_empty_dict_for_no_tracking_number(self, carrier_service):
        """Test empty result when no tracking number."""
        result = await carrier_service.detect_carrier(None)
        assert result == {"carrier_name": None, "tracking_url": None}

    @pytest.mark.asyncio
    async def test_detects_from_custom_carrier(self, carrier_service, mock_db):
        """Test detection from custom carrier."""
        custom_carrier = CarrierConfig(
            id=1,
            merchant_id=1,
            carrier_name="LBC Express",
            tracking_url_template="https://track.lbcexpress.com/{tracking_number}",
            tracking_number_pattern=r"^LBC\d{12}$",
            is_active=True,
            priority=100,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [custom_carrier]
        mock_db.execute.return_value = mock_result

        result = await carrier_service.detect_carrier(
            tracking_number="LBC123456789012",
            merchant_id=1,
        )

        assert result["carrier_name"] == "LBC Express"
        assert "lbcexpress.com" in result["tracking_url"]

    @pytest.mark.asyncio
    async def test_detects_from_shopify_mapping(self, carrier_service):
        """Test detection from Shopify carrier mapping."""
        result = await carrier_service.detect_carrier(
            tracking_number="1Z999AA10123456784",
            tracking_company="UPS",
        )

        assert result["carrier_name"] == "UPS"
        assert "ups.com" in result["tracking_url"]

    @pytest.mark.asyncio
    async def test_detects_from_pattern(self, carrier_service, mock_db):
        """Test detection from pattern matching."""
        # Mock no custom carriers
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await carrier_service.detect_carrier(
            tracking_number="1Z999AA10123456784",
        )

        assert result["carrier_name"] == "UPS"
        assert "ups.com" in result["tracking_url"]

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown(self, carrier_service, mock_db):
        """Test None returned for unknown tracking number."""
        # Mock no custom carriers
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await carrier_service.detect_carrier(
            tracking_number="INVALID123",
        )

        assert result["carrier_name"] is None
        assert result["tracking_url"] is None


class TestGetSupportedCarriers:
    """Test get_supported_carriers static method."""

    def test_returns_list_of_carriers(self):
        """Test that a list of carriers is returned."""
        carriers = CarrierService.get_supported_carriers()
        assert isinstance(carriers, list)
        assert len(carriers) > 0

    def test_carriers_have_required_fields(self):
        """Test that each carrier has required fields."""
        carriers = CarrierService.get_supported_carriers()

        for carrier in carriers:
            assert "name" in carrier
            assert "region" in carrier
            assert "priority" in carrier
            assert "url_template" in carrier

    def test_includes_major_carriers(self):
        """Test that major carriers are included."""
        carriers = CarrierService.get_supported_carriers()
        carrier_names = [c["name"] for c in carriers]

        assert "UPS" in carrier_names
        assert "USPS" in carrier_names
        assert "FedEx" in carrier_names
        assert any("DHL" in name for name in carrier_names)


class TestGetCarriersByRegion:
    """Test get_carriers_by_region static method."""

    def test_filters_by_region(self):
        """Test that carriers are filtered by region."""
        carriers = CarrierService.get_carriers_by_region("us")

        for carrier in carriers:
            assert carrier["region"] == "us"

    def test_returns_empty_for_unknown_region(self):
        """Test empty list for unknown region."""
        carriers = CarrierService.get_carriers_by_region("unknown")
        assert carriers == []

    def test_is_case_insensitive(self):
        """Test that region filtering is case insensitive."""
        carriers_upper = CarrierService.get_carriers_by_region("US")
        carriers_lower = CarrierService.get_carriers_by_region("us")

        assert len(carriers_upper) == len(carriers_lower)
