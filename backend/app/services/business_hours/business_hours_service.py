"""Business Hours service for checking business hours status.

Story 3.10: Business Hours Configuration

Provides functions for:
- Checking if current time is within business hours
- Formatting business hours for display
- Getting next business hour for response time estimation
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import structlog


logger = structlog.get_logger(__name__)

DAY_ORDER = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
DAY_NAMES = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun",
}


class BusinessHoursService:
    """Service for business hours operations.

    Story 3.10 AC 5: Integration with human handoff flow.
    """

    @staticmethod
    def is_within_business_hours(
        hours_config: Optional[dict],
        check_time: Optional[datetime] = None,
    ) -> bool:
        """Check if given time falls within configured business hours.

        Args:
            hours_config: Business hours configuration from merchant
            check_time: Time to check (defaults to now)

        Returns:
            True if within business hours, False otherwise

        Note:
            If no config or hours configured, returns True (assumes always open).
        """
        return is_within_business_hours(hours_config, check_time)

    @staticmethod
    def get_formatted_hours(hours_config: Optional[dict]) -> str:
        """Get formatted hours string for display.

        Args:
            hours_config: Business hours configuration from merchant

        Returns:
            Formatted string like "9 AM - 5 PM, Mon-Fri"
        """
        return get_formatted_hours(hours_config)

    @staticmethod
    def get_next_business_hour(
        hours_config: Optional[dict],
        from_time: Optional[datetime] = None,
    ) -> Optional[datetime]:
        """Get next business hour start time.

        Args:
            hours_config: Business hours configuration from merchant
            from_time: Starting point (defaults to now)

        Returns:
            Next business hour start time, or None if always closed
        """
        return get_next_business_hour(hours_config, from_time)


def is_within_business_hours(
    hours_config: Optional[dict],
    check_time: Optional[datetime] = None,
) -> bool:
    """Check if given time falls within configured business hours.

    Args:
        hours_config: Business hours configuration dict with:
            - timezone: IANA timezone string
            - hours: List of day configurations
        check_time: Time to check (defaults to now in UTC)

    Returns:
        True if within business hours, False otherwise

    Note:
        - If no config, returns True (assumes always available)
        - Handles midnight crossover (close_time < open_time)
    """
    if not hours_config or not hours_config.get("hours"):
        return True

    check_time = check_time or datetime.now(ZoneInfo("UTC"))

    timezone_str = hours_config.get("timezone", "America/Los_Angeles")
    try:
        tz = ZoneInfo(timezone_str)
    except Exception:
        tz = ZoneInfo("America/Los_Angeles")

    local_time = check_time.astimezone(tz)
    local_day = local_time.strftime("%a").lower()[:3]
    local_time_of_day = local_time.time()

    hours_list = hours_config.get("hours", [])

    def check_day_hours(day_name: str, time_of_day: time) -> bool:
        day_config = next(
            (h for h in hours_list if h.get("day", "").lower()[:3] == day_name),
            None,
        )
        if not day_config or not day_config.get("is_open", False):
            return False

        open_time_str = day_config.get("open_time")
        close_time_str = day_config.get("close_time")

        if not open_time_str or not close_time_str:
            return False

        try:
            open_time = _parse_time(open_time_str)
            close_time = _parse_time(close_time_str)
        except (ValueError, TypeError):
            return False

        if close_time < open_time:
            if time_of_day >= open_time:
                return True
            return time_of_day <= close_time

        return open_time <= time_of_day <= close_time

    current_day_open = check_day_hours(local_day, local_time_of_day)
    if current_day_open:
        return True

    day_list = list(DAY_ORDER.keys())
    current_idx = day_list.index(local_day) if local_day in day_list else 0
    prev_day = day_list[(current_idx - 1) % 7]

    prev_config = next(
        (h for h in hours_list if h.get("day", "").lower()[:3] == prev_day),
        None,
    )
    if prev_config and prev_config.get("is_open"):
        open_time_str = prev_config.get("open_time")
        close_time_str = prev_config.get("close_time")
        if open_time_str and close_time_str:
            try:
                open_time = _parse_time(open_time_str)
                close_time = _parse_time(close_time_str)
                if close_time < open_time and local_time_of_day <= close_time:
                    return True
            except (ValueError, TypeError):
                pass

    return False


def get_formatted_hours(hours_config: Optional[dict]) -> str:
    """Format business hours into human-readable string.

    Args:
        hours_config: Business hours configuration dict

    Returns:
        Formatted hours string like:
        - "9 AM - 5 PM, Mon-Fri" (uniform hours)
        - "9 AM - 5 PM, Mon-Fri; 10 AM - 2 PM, Sat" (varied hours)
    """
    if not hours_config or not hours_config.get("hours"):
        return ""

    hours_list = hours_config.get("hours", [])
    if not hours_list:
        return ""

    open_days = [
        h for h in hours_list if h.get("is_open") and h.get("open_time") and h.get("close_time")
    ]
    if not open_days:
        return ""

    def format_time(time_str: str) -> str:
        h, m = time_str.split(":")
        hour = int(h)
        minute = int(m)
        if hour == 0:
            return f"12:{minute:02d} AM"
        elif hour < 12:
            return f"{hour}:{minute:02d} AM"
        elif hour == 12:
            return f"12:{minute:02d} PM"
        else:
            return f"{hour - 12}:{minute:02d} PM"

    open_days.sort(key=lambda x: DAY_ORDER.get(x["day"][:3].lower(), 7))

    hours_groups: list[tuple[str, list[str]]] = []
    for day in open_days:
        time_range = f"{format_time(day['open_time'])} - {format_time(day['close_time'])}"
        day_key = day["day"][:3].lower()
        day_name: str = DAY_NAMES.get(DAY_ORDER.get(day_key, 0)) or day_key.capitalize()

        if hours_groups and hours_groups[-1][0] == time_range:
            hours_groups[-1][1].append(day_name)
        else:
            hours_groups.append((time_range, [day_name]))

    parts = []
    for time_range, days in hours_groups:
        if len(days) == 1:
            parts.append(f"{time_range}, {days[0]}")
        elif len(days) == 2:
            parts.append(f"{time_range}, {days[0]} & {days[1]}")
        else:
            parts.append(f"{time_range}, {days[0]}-{days[-1]}")

    return "; ".join(parts)


def get_next_business_hour(
    hours_config: Optional[dict],
    from_time: Optional[datetime] = None,
) -> Optional[datetime]:
    """Get next business hour start time.

    Args:
        hours_config: Business hours configuration dict
        from_time: Starting point (defaults to now in UTC)

    Returns:
        Next business hour start time in UTC, or None if always closed

    Note:
        Searches up to 14 days ahead for the next business hour.
    """
    if not hours_config or not hours_config.get("hours"):
        return from_time or datetime.now(ZoneInfo("UTC"))

    from_time = from_time or datetime.now(ZoneInfo("UTC"))

    timezone_str = hours_config.get("timezone", "America/Los_Angeles")
    try:
        tz = ZoneInfo(timezone_str)
    except Exception:
        tz = ZoneInfo("America/Los_Angeles")

    local_from = from_time.astimezone(tz)
    hours_list = hours_config.get("hours", [])

    if not hours_list:
        return from_time

    for days_ahead in range(15):
        check_date = local_from + timedelta(days=days_ahead)
        day_name = check_date.strftime("%a").lower()[:3]

        day_config = next(
            (h for h in hours_list if h.get("day", "").lower()[:3] == day_name),
            None,
        )

        if not day_config or not day_config.get("is_open"):
            continue

        open_time_str = day_config.get("open_time")
        if not open_time_str:
            continue

        try:
            open_time = _parse_time(open_time_str)
        except (ValueError, TypeError):
            continue

        candidate = datetime.combine(
            check_date.date(),
            open_time,
            tzinfo=tz,
        )

        if days_ahead == 0 and candidate <= local_from:
            continue

        return candidate.astimezone(ZoneInfo("UTC"))

    return None


def _parse_time(time_str: str) -> time:
    """Parse HH:MM time string.

    Args:
        time_str: Time in HH:MM 24h format

    Returns:
        time object

    Raises:
        ValueError: If time string is invalid
    """
    parts = time_str.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {time_str}")

    hour = int(parts[0])
    minute = int(parts[1])

    return time(hour, minute)
