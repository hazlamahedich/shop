"""Unit tests for BusinessHoursHandoffService.

Story 4-12: Business Hours Handling

Tests cover:
- Handoff message context generation
- Expected response time formatting
- Offline handoff detection
- Business hours integration
- Queue idempotency
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.handoff.business_hours_handoff_service import (
    BusinessHoursHandoffService,
    HandoffMessageContext,
    STANDARD_HANDOFF_MESSAGE,
    OFFLINE_HANDOFF_PREFIX,
)


@pytest.fixture
def service() -> BusinessHoursHandoffService:
    """Create a BusinessHoursHandoffService instance."""
    return BusinessHoursHandoffService()


@pytest.fixture
def business_hours_config() -> dict:
    """Standard business hours config (9 AM - 5 PM, Mon-Fri)."""
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


@pytest.fixture
def no_config() -> dict:
    """No business hours configured."""
    return {}


@pytest.fixture
def always_open_config() -> dict:
    """Always open (24/7) business hours."""
    return {
        "timezone": "America/Los_Angeles",
        "hours": [
            {"day": "mon", "is_open": True, "open_time": "00:00", "close_time": "23:59"},
            {"day": "tue", "is_open": True, "open_time": "00:00", "close_time": "23:59"},
            {"day": "wed", "is_open": True, "open_time": "00:00", "close_time": "23:59"},
            {"day": "thu", "is_open": True, "open_time": "00:00", "close_time": "23:59"},
            {"day": "fri", "is_open": True, "open_time": "00:00", "close_time": "23:59"},
            {"day": "sat", "is_open": True, "open_time": "00:00", "close_time": "23:59"},
            {"day": "sun", "is_open": True, "open_time": "00:00", "close_time": "23:59"},
        ],
    }


class TestGetHandoffMessageContext:
    """Tests for get_handoff_message_context method."""

    def test_no_config_returns_online(
        self, service: BusinessHoursHandoffService, no_config: dict
    ) -> None:
        """No business hours config should return online context."""
        context = service.get_handoff_message_context(no_config)
        assert context.is_offline is False
        assert context.business_hours_str == ""
        assert context.expected_response_time == "within 12 hours"

    def test_none_config_returns_online(self, service: BusinessHoursHandoffService) -> None:
        """None config should return online context."""
        context = service.get_handoff_message_context(None)
        assert context.is_offline is False

    def test_within_business_hours_returns_online(
        self, service: BusinessHoursHandoffService, business_hours_config: dict
    ) -> None:
        """Within business hours should return online context."""
        wednesday_10am = datetime(2026, 2, 18, 18, 0, 0, tzinfo=timezone.utc)
        context = service.get_handoff_message_context(business_hours_config, wednesday_10am)
        assert context.is_offline is False

    def test_outside_business_hours_returns_offline(
        self, service: BusinessHoursHandoffService, business_hours_config: dict
    ) -> None:
        """Outside business hours should return offline context."""
        saturday_10am = datetime(2026, 2, 21, 18, 0, 0, tzinfo=timezone.utc)
        context = service.get_handoff_message_context(business_hours_config, saturday_10am)
        assert context.is_offline is True
        assert "9" in context.business_hours_str and "AM" in context.business_hours_str
        assert "5" in context.business_hours_str and "PM" in context.business_hours_str

    def test_always_open_never_offline(
        self, service: BusinessHoursHandoffService, always_open_config: dict
    ) -> None:
        """Always open config should never be offline."""
        any_time = datetime(2026, 2, 21, 10, 0, 0, tzinfo=timezone.utc)
        context = service.get_handoff_message_context(always_open_config, any_time)
        assert context.is_offline is False


class TestFormatExpectedResponseTime:
    """Tests for format_expected_response_time method."""

    def test_less_than_one_hour(self, service: BusinessHoursHandoffService) -> None:
        """Response time < 1 hour should return 'less than 1 hour'."""
        from_time = datetime(2026, 2, 18, 16, 30, 0, tzinfo=timezone.utc)
        next_hour = datetime(2026, 2, 18, 17, 0, 0, tzinfo=timezone.utc)
        result = service.format_expected_response_time(from_time, next_hour)
        assert result == "less than 1 hour"

    def test_about_x_hours(self, service: BusinessHoursHandoffService) -> None:
        """Response time 1-6 hours should return 'about X hours'."""
        from_time = datetime(2026, 2, 18, 14, 0, 0, tzinfo=timezone.utc)
        next_hour = datetime(2026, 2, 18, 17, 0, 0, tzinfo=timezone.utc)
        result = service.format_expected_response_time(from_time, next_hour)
        assert result == "about 3 hours"

    def test_tomorrow_at_time(self, service: BusinessHoursHandoffService) -> None:
        """Response time next day should include 'tomorrow'."""
        from_time = datetime(2026, 2, 18, 20, 0, 0, tzinfo=timezone.utc)
        next_hour = datetime(2026, 2, 19, 17, 0, 0, tzinfo=timezone.utc)
        result = service.format_expected_response_time(from_time, next_hour)
        assert "tomorrow" in result.lower()

    def test_day_name_for_weekend(self, service: BusinessHoursHandoffService) -> None:
        """Response time > 1 day should include day name."""
        from_time = datetime(2026, 2, 21, 10, 0, 0, tzinfo=timezone.utc)
        next_hour = datetime(2026, 2, 23, 17, 0, 0, tzinfo=timezone.utc)
        result = service.format_expected_response_time(from_time, next_hour)
        assert "on" in result.lower() and "at" in result.lower()


class TestIsOfflineHandoff:
    """Tests for is_offline_handoff method."""

    def test_no_config_not_offline(self, service: BusinessHoursHandoffService) -> None:
        """No config should not be offline."""
        assert service.is_offline_handoff(None) is False

    def test_within_hours_not_offline(
        self, service: BusinessHoursHandoffService, business_hours_config: dict
    ) -> None:
        """Within business hours should not be offline."""
        wednesday_10am = datetime(2026, 2, 18, 18, 0, 0, tzinfo=timezone.utc)
        assert service.is_offline_handoff(business_hours_config, wednesday_10am) is False

    def test_outside_hours_is_offline(
        self, service: BusinessHoursHandoffService, business_hours_config: dict
    ) -> None:
        """Outside business hours should be offline."""
        saturday_10am = datetime(2026, 2, 21, 18, 0, 0, tzinfo=timezone.utc)
        assert service.is_offline_handoff(business_hours_config, saturday_10am) is True


class TestBuildHandoffMessage:
    """Tests for build_handoff_message method."""

    def test_online_returns_standard_message(
        self, service: BusinessHoursHandoffService, business_hours_config: dict
    ) -> None:
        """Within business hours should return standard handoff message."""
        wednesday_10am = datetime(2026, 2, 18, 18, 0, 0, tzinfo=timezone.utc)
        message = service.build_handoff_message(business_hours_config, wednesday_10am)
        assert message == STANDARD_HANDOFF_MESSAGE

    def test_offline_includes_business_hours(
        self, service: BusinessHoursHandoffService, business_hours_config: dict
    ) -> None:
        """Offline should include business hours in message."""
        saturday_10am = datetime(2026, 2, 21, 18, 0, 0, tzinfo=timezone.utc)
        message = service.build_handoff_message(business_hours_config, saturday_10am)
        assert OFFLINE_HANDOFF_PREFIX in message
        assert "business hours" in message.lower()
        assert "Expected response:" in message

    def test_no_config_returns_standard_message(self, service: BusinessHoursHandoffService) -> None:
        """No config should return standard message."""
        message = service.build_handoff_message(None)
        assert message == STANDARD_HANDOFF_MESSAGE


class TestTimezoneHandling:
    """Tests for cross-timezone scenarios."""

    def test_different_timezone_handling(self, service: BusinessHoursHandoffService) -> None:
        """Should handle different timezone configurations."""
        est_config = {
            "timezone": "America/New_York",
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
        utc_2pm = datetime(2026, 2, 18, 14, 0, 0, tzinfo=timezone.utc)
        context = service.get_handoff_message_context(est_config, utc_2pm)
        assert context.is_offline is False

    def test_midnight_crossover_handling(self, service: BusinessHoursHandoffService) -> None:
        """Should handle business hours that span midnight."""
        crossover_config = {
            "timezone": "America/Los_Angeles",
            "hours": [
                {"day": "fri", "is_open": True, "open_time": "22:00", "close_time": "02:00"},
                {"day": "sat", "is_open": False},
                {"day": "sun", "is_open": False},
            ],
        }
        friday_11pm_pst_in_utc = datetime(2026, 2, 21, 7, 0, 0, tzinfo=timezone.utc)
        context = service.get_handoff_message_context(crossover_config, friday_11pm_pst_in_utc)
        assert context.is_offline is False


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_hours_list(self, service: BusinessHoursHandoffService) -> None:
        """Empty hours list should return online."""
        config = {"timezone": "America/Los_Angeles", "hours": []}
        context = service.get_handoff_message_context(config)
        assert context.is_offline is False

    def test_all_days_closed(self, service: BusinessHoursHandoffService) -> None:
        """All days closed should return offline with no next business hour."""
        closed_config = {
            "timezone": "America/Los_Angeles",
            "hours": [
                {"day": "mon", "is_open": False},
                {"day": "tue", "is_open": False},
                {"day": "wed", "is_open": False},
                {"day": "thu", "is_open": False},
                {"day": "fri", "is_open": False},
                {"day": "sat", "is_open": False},
                {"day": "sun", "is_open": False},
            ],
        }
        context = service.get_handoff_message_context(closed_config)
        assert context.is_offline is True
        assert context.next_business_hour is None

    def test_format_time_with_minutes(self, service: BusinessHoursHandoffService) -> None:
        """Should format times with minutes correctly."""
        from_time = datetime(2026, 2, 18, 10, 0, 0, tzinfo=timezone.utc)
        next_hour = datetime(2026, 2, 19, 17, 30, 0, tzinfo=timezone.utc)
        result = service.format_expected_response_time(from_time, next_hour)
        assert "on" in result.lower() or "tomorrow" in result.lower()


class TestQueueIdempotency:
    """Tests for queue state handling (preparation for AC3)."""

    def test_context_data_structure(
        self, service: BusinessHoursHandoffService, business_hours_config: dict
    ) -> None:
        """Should return proper context for queue state management."""
        saturday_10am = datetime(2026, 2, 21, 18, 0, 0, tzinfo=timezone.utc)
        context = service.get_handoff_message_context(business_hours_config, saturday_10am)

        assert context.is_offline is True
        assert context.next_business_hour is not None
        assert context.hours_until_response is not None
        assert context.hours_until_response > 0


class TestBusinessHoursCheckErrorHandling:
    """Tests for error handling in business hours check."""

    def test_malformed_config_returns_online_gracefully(
        self, service: BusinessHoursHandoffService
    ) -> None:
        """Malformed config should return online context gracefully."""
        malformed_config = {"timezone": "Invalid/Timezone", "hours": "not a list"}
        context = service.get_handoff_message_context(malformed_config)
        assert context.is_offline is False

    def test_missing_timezone_in_config(self, service: BusinessHoursHandoffService) -> None:
        """Config without timezone should be handled."""
        config_no_tz = {
            "hours": [
                {"day": "mon", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
            ]
        }
        context = service.get_handoff_message_context(config_no_tz)
        assert context is not None


class TestResponseTimeEdgeCases:
    """Tests for response time calculation edge cases."""

    def test_exactly_one_hour(self, service: BusinessHoursHandoffService) -> None:
        """Response time exactly 1 hour should return 'about 1 hours'."""
        from_time = datetime(2026, 2, 18, 16, 0, 0, tzinfo=timezone.utc)
        next_hour = datetime(2026, 2, 18, 17, 0, 0, tzinfo=timezone.utc)
        result = service.format_expected_response_time(from_time, next_hour)
        assert "about 1 hour" in result

    def test_exactly_six_hours(self, service: BusinessHoursHandoffService) -> None:
        """Response time exactly 6 hours should show day-appropriate message."""
        from_time = datetime(2026, 2, 18, 11, 0, 0, tzinfo=timezone.utc)
        next_hour = datetime(2026, 2, 18, 17, 0, 0, tzinfo=timezone.utc)
        result = service.format_expected_response_time(from_time, next_hour)
        assert "today" in result.lower() or "tomorrow" in result.lower()

    def test_format_time_noon(self, service: BusinessHoursHandoffService) -> None:
        """Should format noon correctly as '12 PM'."""
        noon = datetime(2026, 2, 18, 12, 0, 0, tzinfo=timezone.utc)
        result = service._format_time_12h(noon)
        assert result == "12 PM"

    def test_format_time_midnight(self, service: BusinessHoursHandoffService) -> None:
        """Should format midnight correctly as '12 AM'."""
        midnight = datetime(2026, 2, 18, 0, 0, 0, tzinfo=timezone.utc)
        result = service._format_time_12h(midnight)
        assert result == "12 AM"
