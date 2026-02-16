"""Business Hours Handoff Service.

Story 4-12: Business Hours Handling

Provides business hours context for handoff messages:
- Check if handoff is triggered outside business hours
- Format expected response time based on next business hour
- Prepare handoff message context with business hours info

REUSES patterns from Story 3-10 (BusinessHoursService).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import structlog

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.services.business_hours.business_hours_service import (
    get_formatted_hours,
    get_next_business_hour,
    is_within_business_hours,
)

logger = structlog.get_logger(__name__)

STANDARD_HANDOFF_MESSAGE = (
    "I'm having trouble understanding. Sorry! Let me get someone who can help. "
    "I've flagged this - our team will respond within 12 hours."
)

OFFLINE_HANDOFF_PREFIX = "I'm having trouble understanding. Sorry! Our team is currently offline."


@dataclass
class HandoffMessageContext:
    """Context for handoff message generation."""

    is_offline: bool
    business_hours_str: str
    expected_response_time: str
    next_business_hour: Optional[datetime]
    hours_until_response: Optional[float]


class BusinessHoursHandoffService:
    """Service for business hours-aware handoff messages.

    Provides context for handoff messages when shoppers request human help:
    - Detects if merchant is offline (outside business hours)
    - Calculates expected response time until next business hour
    - Formats business hours string for display

    Usage:
        service = BusinessHoursHandoffService()
        context = await service.get_handoff_message_context(merchant.business_hours_config)
        if context.is_offline:
            message = f"Our team is offline. We'll respond in {context.expected_response_time}"
    """

    def __init__(self) -> None:
        """Initialize business hours handoff service."""
        pass

    def get_handoff_message_context(
        self,
        business_hours_config: Optional[dict[str, Any]],
        check_time: Optional[datetime] = None,
    ) -> HandoffMessageContext:
        """Get context for handoff message based on business hours.

        Args:
            business_hours_config: Business hours configuration from merchant
            check_time: Time to check (defaults to now)

        Returns:
            HandoffMessageContext with offline status and response time info

        Raises:
            APIError: If business hours check fails (ErrorCode.BUSINESS_HOURS_CHECK_FAILED)
        """
        check_time = check_time or datetime.now(timezone.utc)

        if not business_hours_config or not business_hours_config.get("hours"):
            return HandoffMessageContext(
                is_offline=False,
                business_hours_str="",
                expected_response_time="within 12 hours",
                next_business_hour=None,
                hours_until_response=None,
            )

        try:
            is_within = is_within_business_hours(business_hours_config, check_time)
        except Exception as e:
            logger.warning(
                "business_hours_check_failed_using_fallback",
                error=str(e),
                config=business_hours_config,
            )
            return HandoffMessageContext(
                is_offline=False,
                business_hours_str="",
                expected_response_time="within 12 hours",
                next_business_hour=None,
                hours_until_response=None,
            )

        if is_within:
            return HandoffMessageContext(
                is_offline=False,
                business_hours_str="",
                expected_response_time="within 12 hours",
                next_business_hour=None,
                hours_until_response=None,
            )

        formatted_hours = get_formatted_hours(business_hours_config)
        next_hour = get_next_business_hour(business_hours_config, check_time)

        if not next_hour:
            return HandoffMessageContext(
                is_offline=True,
                business_hours_str=formatted_hours,
                expected_response_time="at the next available time",
                next_business_hour=None,
                hours_until_response=None,
            )

        hours_until = self._calculate_hours_until(check_time, next_hour)
        response_time_str = self.format_expected_response_time(check_time, next_hour)

        logger.info(
            "handoff_offline_detected",
            business_hours=formatted_hours,
            next_business_hour=next_hour.isoformat(),
            hours_until_response=hours_until,
        )

        return HandoffMessageContext(
            is_offline=True,
            business_hours_str=formatted_hours,
            expected_response_time=response_time_str,
            next_business_hour=next_hour,
            hours_until_response=hours_until,
        )

    def format_expected_response_time(
        self,
        from_time: datetime,
        next_business_hour: datetime,
    ) -> str:
        """Format expected response time for display.

        Formats human-readable response time:
        - "< 1 hour" if within 1 hour
        - "about X hours" if within same day
        - "tomorrow at 9 AM" if next business day
        - "on Monday at 9 AM" if weekend

        Args:
            from_time: Current time
            next_business_hour: Next business hour start time

        Returns:
            Human-readable response time string
        """
        hours_until = self._calculate_hours_until(from_time, next_business_hour)

        if hours_until < 1:
            return "less than 1 hour"

        if hours_until < 6:
            return f"about {int(round(hours_until))} hours"

        local_next = next_business_hour.astimezone()
        local_from = from_time.astimezone()

        is_same_day = local_next.date() == local_from.date()
        is_tomorrow = (local_next.date() - local_from.date()).days == 1

        time_str = self._format_time_12h(local_next)
        day_name = local_next.strftime("%A")

        if is_same_day:
            return f"later today at {time_str}"
        elif is_tomorrow:
            return f"tomorrow at {time_str}"
        else:
            return f"on {day_name} at {time_str}"

    def is_offline_handoff(
        self,
        business_hours_config: Optional[dict[str, Any]],
        check_time: Optional[datetime] = None,
    ) -> bool:
        """Check if handoff is triggered outside business hours.

        Args:
            business_hours_config: Business hours configuration from merchant
            check_time: Time to check (defaults to now)

        Returns:
            True if outside business hours, False otherwise
        """
        return not is_within_business_hours(business_hours_config, check_time)

    def build_handoff_message(
        self,
        business_hours_config: Optional[dict[str, Any]],
        check_time: Optional[datetime] = None,
    ) -> str:
        """Build complete handoff message with business hours context.

        Args:
            business_hours_config: Business hours configuration from merchant
            check_time: Time to check (defaults to now)

        Returns:
            Complete handoff message string
        """
        context = self.get_handoff_message_context(business_hours_config, check_time)

        if not context.is_offline:
            return STANDARD_HANDOFF_MESSAGE

        parts = [OFFLINE_HANDOFF_PREFIX]

        if context.business_hours_str:
            parts.append(f"We'll respond during business hours ({context.business_hours_str}).")

        parts.append(f"Expected response: {context.expected_response_time}.")

        return " ".join(parts)

    def _calculate_hours_until(
        self,
        from_time: datetime,
        target_time: datetime,
    ) -> float:
        """Calculate hours until target time.

        Args:
            from_time: Starting time
            target_time: Target time

        Returns:
            Hours until target (0 if already passed)
        """
        if from_time.tzinfo is None:
            from_time = from_time.replace(tzinfo=timezone.utc)
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)

        delta = target_time - from_time
        hours = delta.total_seconds() / 3600
        return max(0, hours)

    def _format_time_12h(self, dt: datetime) -> str:
        """Format datetime as 12-hour time string.

        Args:
            dt: Datetime to format

        Returns:
            Time string like "9 AM" or "2:30 PM"
        """
        hour = dt.hour
        minute = dt.minute

        if hour == 0:
            hour_str = "12"
            period = "AM"
        elif hour < 12:
            hour_str = str(hour)
            period = "AM"
        elif hour == 12:
            hour_str = "12"
            period = "PM"
        else:
            hour_str = str(hour - 12)
            period = "PM"

        if minute == 0:
            return f"{hour_str} {period}"
        return f"{hour_str}:{minute:02d} {period}"


__all__ = [
    "BusinessHoursHandoffService",
    "HandoffMessageContext",
    "STANDARD_HANDOFF_MESSAGE",
    "OFFLINE_HANDOFF_PREFIX",
]
