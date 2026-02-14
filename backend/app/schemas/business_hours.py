"""Pydantic schemas for Business Hours configuration.

Story 3.10: Business Hours Configuration

Provides request/response schemas for business hours CRUD operations.
"""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator
from zoneinfo import available_timezones

from app.schemas.base import BaseSchema, MinimalEnvelope, MetaData


DAYS_OF_WEEK = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
TIME_PATTERN = r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"


class DayHours(BaseSchema):
    """Hours for a single day of the week.

    Story 3.10 AC 1: Day-by-day hours configuration.

    Attributes:
        day: Day of week (mon, tue, wed, thu, fri, sat, sun)
        is_open: Whether business is open on this day
        open_time: Opening time in HH:MM 24h format (required if is_open)
        close_time: Closing time in HH:MM 24h format (required if is_open)
    """

    day: str = Field(..., pattern=f"^({'|'.join(DAYS_OF_WEEK)})$")
    is_open: bool = Field(default=True)
    open_time: Optional[str] = Field(
        default=None,
        pattern=TIME_PATTERN,
        description="Opening time in HH:MM 24h format",
    )
    close_time: Optional[str] = Field(
        default=None,
        pattern=TIME_PATTERN,
        description="Closing time in HH:MM 24h format",
    )

    @model_validator(mode="after")
    def validate_times_when_open(self) -> "DayHours":
        if self.is_open:
            if not self.open_time:
                raise ValueError(f"open_time is required when {self.day} is open")
            if not self.close_time:
                raise ValueError(f"close_time is required when {self.day} is open")
        return self


class BusinessHoursRequest(BaseSchema):
    """Request schema for business hours configuration.

    Story 3.10 AC 1, 2, 3: Business hours configuration fields.

    Attributes:
        timezone: IANA timezone identifier (e.g., America/Los_Angeles)
        hours: List of day hours configurations
        out_of_office_message: Custom message shown outside business hours
    """

    timezone: str = Field(
        default="America/Los_Angeles",
        description="IANA timezone identifier",
    )
    hours: List[DayHours] = Field(
        default_factory=list,
        max_length=7,
        description="Hours for each day of the week",
    )
    out_of_office_message: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Custom message when business is closed",
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        valid_timezones = available_timezones()
        if v not in valid_timezones:
            raise ValueError(f"Invalid timezone: {v}")
        return v

    @field_validator("out_of_office_message")
    @classmethod
    def strip_message_whitespace(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


class BusinessHoursResponse(BaseSchema):
    """Response schema for business hours configuration.

    Story 3.10 AC 1, 2, 3: Business hours response with formatted display.

    Attributes:
        timezone: IANA timezone identifier
        hours: List of day hours configurations
        out_of_office_message: Custom offline message (or default)
        formatted_hours: Human-readable hours string (e.g., "9 AM - 5 PM, Mon-Fri")
        updated_at: ISO-8601 timestamp of last update
    """

    timezone: str = Field(description="IANA timezone identifier")
    hours: List[DayHours] = Field(default_factory=list)
    out_of_office_message: Optional[str] = Field(
        default="Our team is offline. We'll respond during business hours.",
        description="Message shown when business is closed",
    )
    formatted_hours: str = Field(
        default="",
        description="Human-readable hours string",
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="ISO-8601 timestamp of last update",
    )


class BusinessHoursEnvelope(MinimalEnvelope):
    """Minimal envelope for business hours responses.

    Story 3.10 AC 4: Use MinimalEnvelope response format.

    Attributes:
        data: Business hours response
        meta: Response metadata
    """

    data: BusinessHoursResponse


__all__ = [
    "DayHours",
    "BusinessHoursRequest",
    "BusinessHoursResponse",
    "BusinessHoursEnvelope",
    "DAYS_OF_WEEK",
]
