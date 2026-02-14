"""Tests for Business Hours Pydantic schemas.

Story 3.10: Business Hours Configuration
"""

import pytest
from pydantic import ValidationError

from app.schemas.business_hours import (
    DayHours,
    BusinessHoursRequest,
    BusinessHoursResponse,
    DAYS_OF_WEEK,
)


class TestDayHours:
    """Tests for DayHours schema."""

    def test_valid_day_hours(self):
        valid = DayHours(day="mon", is_open=True, open_time="09:00", close_time="17:00")
        assert valid.day == "mon"
        assert valid.is_open is True
        assert valid.open_time == "09:00"
        assert valid.close_time == "17:00"

    def test_closed_day_no_times_required(self):
        closed = DayHours(day="sun", is_open=False)
        assert closed.day == "sun"
        assert closed.is_open is False
        assert closed.open_time is None
        assert closed.close_time is None

    def test_open_day_requires_open_time(self):
        with pytest.raises(ValidationError) as exc_info:
            DayHours(day="mon", is_open=True, close_time="17:00")
        assert "open_time is required" in str(exc_info.value)

    def test_open_day_requires_close_time(self):
        with pytest.raises(ValidationError) as exc_info:
            DayHours(day="mon", is_open=True, open_time="09:00")
        assert "close_time is required" in str(exc_info.value)

    def test_invalid_day_name(self):
        with pytest.raises(ValidationError):
            DayHours(day="xyz", is_open=True, open_time="09:00", close_time="17:00")

    def test_invalid_time_format(self):
        with pytest.raises(ValidationError):
            DayHours(day="mon", is_open=True, open_time="9am", close_time="17:00")

    def test_invalid_time_value(self):
        with pytest.raises(ValidationError):
            DayHours(day="mon", is_open=True, open_time="25:00", close_time="17:00")

    def test_midnight_crossover_allowed(self):
        overnight = DayHours(day="fri", is_open=True, open_time="18:00", close_time="02:00")
        assert overnight.open_time == "18:00"
        assert overnight.close_time == "02:00"


class TestBusinessHoursRequest:
    """Tests for BusinessHoursRequest schema."""

    def test_valid_request(self):
        request = BusinessHoursRequest(
            timezone="America/Los_Angeles",
            hours=[
                DayHours(day="mon", is_open=True, open_time="09:00", close_time="17:00"),
                DayHours(day="tue", is_open=True, open_time="09:00", close_time="17:00"),
            ],
            out_of_office_message="We're closed!",
        )
        assert request.timezone == "America/Los_Angeles"
        assert len(request.hours) == 2
        assert request.out_of_office_message == "We're closed!"

    def test_default_timezone(self):
        request = BusinessHoursRequest()
        assert request.timezone == "America/Los_Angeles"

    def test_invalid_timezone(self):
        with pytest.raises(ValidationError) as exc_info:
            BusinessHoursRequest(timezone="Invalid/Timezone")
        assert "Invalid timezone" in str(exc_info.value)

    def test_valid_utc_timezone(self):
        request = BusinessHoursRequest(timezone="UTC")
        assert request.timezone == "UTC"

    def test_message_max_length(self):
        long_message = "x" * 500
        request = BusinessHoursRequest(out_of_office_message=long_message)
        assert len(request.out_of_office_message) == 500

    def test_message_too_long(self):
        with pytest.raises(ValidationError):
            BusinessHoursRequest(out_of_office_message="x" * 501)

    def test_message_whitespace_stripped(self):
        request = BusinessHoursRequest(out_of_office_message="  Hello  ")
        assert request.out_of_office_message == "Hello"

    def test_empty_message_becomes_none(self):
        request = BusinessHoursRequest(out_of_office_message="   ")
        assert request.out_of_office_message is None

    def test_max_hours_length(self):
        hours = [DayHours(day=d, is_open=False) for d in DAYS_OF_WEEK]
        request = BusinessHoursRequest(hours=hours)
        assert len(request.hours) == 7

    def test_too_many_hours(self):
        hours = [DayHours(day=d, is_open=False) for d in DAYS_OF_WEEK]
        hours.append(DayHours(day="mon", is_open=False))
        with pytest.raises(ValidationError):
            BusinessHoursRequest(hours=hours)


class TestBusinessHoursResponse:
    """Tests for BusinessHoursResponse schema."""

    def test_valid_response(self):
        response = BusinessHoursResponse(
            timezone="America/New_York",
            hours=[DayHours(day="mon", is_open=True, open_time="09:00", close_time="17:00")],
            out_of_office_message="We're closed",
            formatted_hours="9 AM - 5 PM, Mon",
        )
        assert response.timezone == "America/New_York"
        assert len(response.hours) == 1
        assert response.formatted_hours == "9 AM - 5 PM, Mon"

    def test_default_out_of_office_message(self):
        response = BusinessHoursResponse(timezone="UTC", hours=[])
        assert (
            response.out_of_office_message
            == "Our team is offline. We'll respond during business hours."
        )
