"""Tests for Business Hours API endpoints.

Story 3.10: Business Hours Configuration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class MockMerchant:
    """Mock Merchant model."""

    def __init__(self, id=1, business_hours_config=None):
        self.id = id
        self.business_hours_config = business_hours_config
        self.updated_at = datetime.utcnow()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    return db


@pytest.fixture
def mock_request():
    """Create mock FastAPI request with merchant_id."""
    request = MagicMock()
    request.state.merchant_id = 1
    request.headers = {}
    return request


@pytest.fixture
def business_hours_payload():
    return {
        "timezone": "America/Los_Angeles",
        "hours": [
            {"day": "mon", "isOpen": True, "openTime": "09:00", "closeTime": "17:00"},
            {"day": "tue", "isOpen": True, "openTime": "09:00", "closeTime": "17:00"},
            {"day": "wed", "isOpen": True, "openTime": "09:00", "closeTime": "17:00"},
            {"day": "thu", "isOpen": True, "openTime": "09:00", "closeTime": "17:00"},
            {"day": "fri", "isOpen": True, "openTime": "09:00", "closeTime": "17:00"},
            {"day": "sat", "isOpen": False},
            {"day": "sun", "isOpen": False},
        ],
        "outOfOfficeMessage": "We're currently closed.",
    }


class TestGetBusinessHours:
    """Tests for GET /api/v1/merchant/business-hours endpoint."""

    @pytest.mark.asyncio
    async def test_get_business_hours_no_config(self, mock_request, mock_db):
        from app.api.business_hours import get_business_hours

        merchant = MockMerchant(id=1, business_hours_config=None)

        with (
            patch("app.api.business_hours.get_merchant_id", return_value=1),
            patch("app.api.business_hours.verify_merchant_exists", return_value=merchant),
        ):
            result = await get_business_hours(mock_request, mock_db)

        assert result.data.timezone == "America/Los_Angeles"
        assert result.data.hours == []

    @pytest.mark.asyncio
    async def test_get_business_hours_with_config(self, mock_request, mock_db):
        from app.api.business_hours import get_business_hours

        merchant = MockMerchant(
            id=1,
            business_hours_config={
                "timezone": "America/New_York",
                "hours": [
                    {"day": "mon", "is_open": True, "open_time": "09:00", "close_time": "17:00"}
                ],
                "out_of_office_message": "Closed for the day",
            },
        )

        with (
            patch("app.api.business_hours.get_merchant_id", return_value=1),
            patch("app.api.business_hours.verify_merchant_exists", return_value=merchant),
        ):
            result = await get_business_hours(mock_request, mock_db)

        assert result.data.timezone == "America/New_York"
        assert len(result.data.hours) == 1
        assert result.data.out_of_office_message == "Closed for the day"


class TestUpdateBusinessHours:
    """Tests for PUT /api/v1/merchant/business-hours endpoint."""

    @pytest.mark.asyncio
    async def test_update_business_hours_full(self, mock_request, mock_db, business_hours_payload):
        from app.api.business_hours import update_business_hours
        from app.schemas.business_hours import BusinessHoursRequest

        merchant = MockMerchant(id=1, business_hours_config=None)

        update = BusinessHoursRequest(**business_hours_payload)

        with (
            patch("app.api.business_hours.get_merchant_id", return_value=1),
            patch("app.api.business_hours.verify_merchant_exists", return_value=merchant),
        ):
            result = await update_business_hours(mock_request, update, mock_db)

        assert result.data.timezone == "America/Los_Angeles"
        assert len(result.data.hours) == 7
        assert result.data.out_of_office_message == "We're currently closed."
        assert merchant.business_hours_config is not None

    @pytest.mark.asyncio
    async def test_update_timezone_only(self, mock_request, mock_db):
        from app.api.business_hours import update_business_hours
        from app.schemas.business_hours import BusinessHoursRequest

        merchant = MockMerchant(id=1, business_hours_config=None)
        update = BusinessHoursRequest(timezone="Europe/London", hours=[])

        with (
            patch("app.api.business_hours.get_merchant_id", return_value=1),
            patch("app.api.business_hours.verify_merchant_exists", return_value=merchant),
        ):
            result = await update_business_hours(mock_request, update, mock_db)

        assert result.data.timezone == "Europe/London"


class TestFormattedHours:
    """Tests for formatted hours output."""

    @pytest.mark.asyncio
    async def test_formatted_hours_uniform(self, mock_request, mock_db):
        from app.api.business_hours import update_business_hours
        from app.schemas.business_hours import BusinessHoursRequest, DayHours

        merchant = MockMerchant(id=1, business_hours_config=None)
        update = BusinessHoursRequest(
            timezone="America/Los_Angeles",
            hours=[
                DayHours(day="mon", is_open=True, open_time="09:00", close_time="17:00"),
                DayHours(day="tue", is_open=True, open_time="09:00", close_time="17:00"),
                DayHours(day="wed", is_open=True, open_time="09:00", close_time="17:00"),
                DayHours(day="thu", is_open=True, open_time="09:00", close_time="17:00"),
                DayHours(day="fri", is_open=True, open_time="09:00", close_time="17:00"),
            ],
        )

        with (
            patch("app.api.business_hours.get_merchant_id", return_value=1),
            patch("app.api.business_hours.verify_merchant_exists", return_value=merchant),
        ):
            result = await update_business_hours(mock_request, update, mock_db)

        assert "9:00 AM - 5:00 PM, Mon-Fri" in result.data.formatted_hours

    @pytest.mark.asyncio
    async def test_formatted_hours_varied(self, mock_request, mock_db):
        from app.api.business_hours import update_business_hours
        from app.schemas.business_hours import BusinessHoursRequest, DayHours

        merchant = MockMerchant(id=1, business_hours_config=None)
        update = BusinessHoursRequest(
            timezone="America/Los_Angeles",
            hours=[
                DayHours(day="mon", is_open=True, open_time="09:00", close_time="17:00"),
                DayHours(day="tue", is_open=True, open_time="09:00", close_time="17:00"),
                DayHours(day="wed", is_open=True, open_time="09:00", close_time="17:00"),
                DayHours(day="thu", is_open=True, open_time="09:00", close_time="17:00"),
                DayHours(day="fri", is_open=True, open_time="09:00", close_time="17:00"),
                DayHours(day="sat", is_open=True, open_time="10:00", close_time="14:00"),
            ],
        )

        with (
            patch("app.api.business_hours.get_merchant_id", return_value=1),
            patch("app.api.business_hours.verify_merchant_exists", return_value=merchant),
        ):
            result = await update_business_hours(mock_request, update, mock_db)

        formatted = result.data.formatted_hours
        assert "9:00 AM - 5:00 PM, Mon-Fri" in formatted
        assert "10:00 AM - 2:00 PM, Sat" in formatted
