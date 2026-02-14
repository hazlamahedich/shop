"""Tests for Business Hours Service.

Story 3.10: Business Hours Configuration
"""

import pytest
from datetime import datetime, time
from zoneinfo import ZoneInfo

from app.services.business_hours.business_hours_service import (
    is_within_business_hours,
    get_formatted_hours,
    get_next_business_hour,
    BusinessHoursService,
)


class TestIsWithinBusinessHours:
    """Tests for is_within_business_hours function."""

    @pytest.fixture
    def standard_hours(self):
        return {
            "timezone": "America/Los_Angeles",
            "hours": [
                {"day": "mon", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "tue", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "wed", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "thu", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "fri", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "sat", "is_open": False},
                {"day": "sun", "is_open": False},
            ],
        }

    def test_within_hours_monday_morning(self, standard_hours):
        check_time = datetime(2024, 1, 15, 10, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
        assert is_within_business_hours(standard_hours, check_time) is True

    def test_before_hours_monday_early(self, standard_hours):
        check_time = datetime(2024, 1, 15, 6, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
        assert is_within_business_hours(standard_hours, check_time) is False

    def test_after_hours_monday_evening(self, standard_hours):
        check_time = datetime(2024, 1, 15, 18, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
        assert is_within_business_hours(standard_hours, check_time) is False

    def test_closed_sunday(self, standard_hours):
        check_time = datetime(2024, 1, 14, 10, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
        assert is_within_business_hours(standard_hours, check_time) is False

    def test_utc_conversion(self, standard_hours):
        utc_time = datetime(2024, 1, 15, 18, 0, tzinfo=ZoneInfo("UTC"))
        assert is_within_business_hours(standard_hours, utc_time) is True

    def test_no_config_returns_true(self):
        assert is_within_business_hours(None) is True

    def test_empty_hours_returns_true(self):
        assert is_within_business_hours({"timezone": "UTC", "hours": []}) is True

    def test_midnight_crossover_open(self):
        config = {
            "timezone": "America/New_York",
            "hours": [
                {"day": "fri", "is_open": True, "open_time": "18:00", "close_time": "02:00"},
            ],
        }
        friday_8pm = datetime(2024, 1, 12, 20, 0, tzinfo=ZoneInfo("America/New_York"))
        assert is_within_business_hours(config, friday_8pm) is True

    def test_midnight_crossover_past_midnight(self):
        config = {
            "timezone": "America/New_York",
            "hours": [
                {"day": "fri", "is_open": True, "open_time": "18:00", "close_time": "02:00"},
            ],
        }
        saturday_1am = datetime(2024, 1, 13, 1, 0, tzinfo=ZoneInfo("America/New_York"))
        assert is_within_business_hours(config, saturday_1am) is True

    def test_midnight_crossover_closed_after(self):
        config = {
            "timezone": "America/New_York",
            "hours": [
                {"day": "fri", "is_open": True, "open_time": "18:00", "close_time": "02:00"},
            ],
        }
        saturday_3am = datetime(2024, 1, 13, 3, 0, tzinfo=ZoneInfo("America/New_York"))
        assert is_within_business_hours(config, saturday_3am) is False

    def test_exact_open_time(self, standard_hours):
        check_time = datetime(2024, 1, 15, 9, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
        assert is_within_business_hours(standard_hours, check_time) is True

    def test_exact_close_time(self, standard_hours):
        check_time = datetime(2024, 1, 15, 17, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
        assert is_within_business_hours(standard_hours, check_time) is True

    def test_invalid_timezone_fallback(self, standard_hours):
        standard_hours["timezone"] = "Invalid/Timezone"
        check_time = datetime(2024, 1, 15, 10, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
        assert is_within_business_hours(standard_hours, check_time) is True


class TestGetFormattedHours:
    """Tests for get_formatted_hours function."""

    def test_uniform_hours_grouped(self):
        config = {
            "timezone": "America/Los_Angeles",
            "hours": [
                {"day": "mon", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "tue", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "wed", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "thu", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "fri", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
            ],
        }
        result = get_formatted_hours(config)
        assert "9:00 AM - 5:00 PM, Mon-Fri" == result

    def test_varied_hours_separated(self):
        config = {
            "timezone": "America/Los_Angeles",
            "hours": [
                {"day": "mon", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "tue", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "wed", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "thu", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "fri", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "sat", "is_open": True, "open_time": "10:00", "close_time": "14:00"},
            ],
        }
        result = get_formatted_hours(config)
        assert "9:00 AM - 5:00 PM, Mon-Fri" in result
        assert "10:00 AM - 2:00 PM, Sat" in result
        assert ";" in result

    def test_no_open_hours(self):
        config = {
            "timezone": "America/Los_Angeles",
            "hours": [
                {"day": "mon", "is_open": False},
            ],
        }
        assert get_formatted_hours(config) == ""

    def test_no_config(self):
        assert get_formatted_hours(None) == ""

    def test_midnight_formatting(self):
        config = {
            "timezone": "America/New_York",
            "hours": [
                {"day": "fri", "is_open": True, "open_time": "00:00", "close_time": "12:00"},
            ],
        }
        result = get_formatted_hours(config)
        assert "12:00 AM - 12:00 PM, Fri" == result


class TestGetNextBusinessHour:
    """Tests for get_next_business_hour function."""

    @pytest.fixture
    def weekday_hours(self):
        return {
            "timezone": "America/Los_Angeles",
            "hours": [
                {"day": "mon", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "tue", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "wed", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "thu", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
                {"day": "fri", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
            ],
        }

    def test_next_day_when_closed(self, weekday_hours):
        friday_afternoon = datetime(2024, 1, 12, 18, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
        next_hour = get_next_business_hour(weekday_hours, friday_afternoon)
        assert next_hour is not None
        local_next = next_hour.astimezone(ZoneInfo("America/Los_Angeles"))
        assert local_next.weekday() == 0
        assert local_next.hour == 9

    def test_returns_none_if_always_closed(self):
        config = {
            "timezone": "UTC",
            "hours": [
                {"day": "mon", "is_open": False},
                {"day": "tue", "is_open": False},
            ],
        }
        result = get_next_business_hour(config)
        assert result is None

    def test_no_config_returns_now(self):
        result = get_next_business_hour(None)
        assert result is not None

    def test_during_hours_returns_next_day(self, weekday_hours):
        monday_10am = datetime(2024, 1, 15, 10, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
        next_hour = get_next_business_hour(weekday_hours, monday_10am)
        assert next_hour is not None
        local_next = next_hour.astimezone(ZoneInfo("America/Los_Angeles"))
        assert local_next.day > monday_10am.day or local_next.hour == 9


class TestBusinessHoursService:
    """Tests for BusinessHoursService class."""

    def test_service_methods_exist(self):
        service = BusinessHoursService()
        assert hasattr(service, "is_within_business_hours")
        assert hasattr(service, "get_formatted_hours")
        assert hasattr(service, "get_next_business_hour")

    def test_service_delegates_to_functions(self):
        service = BusinessHoursService()
        config = {
            "timezone": "UTC",
            "hours": [{"day": "mon", "is_open": True, "open_time": "09:00", "close_time": "17:00"}],
        }
        check_time = datetime(2024, 1, 15, 10, 0, tzinfo=ZoneInfo("UTC"))

        assert service.is_within_business_hours(config, check_time) == is_within_business_hours(
            config, check_time
        )
        assert service.get_formatted_hours(config) == get_formatted_hours(config)
        assert service.get_next_business_hour(config, check_time) == get_next_business_hour(
            config, check_time
        )
