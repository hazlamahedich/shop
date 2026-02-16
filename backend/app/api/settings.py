"""Settings API endpoints.

Story 4-12: Business Hours Handling

Provides endpoints for:
- Getting business hours settings in API test format
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.merchant import Merchant
from app.schemas.base import MinimalEnvelope, MetaData

router = APIRouter()


class DaySchedule(BaseModel):
    """Schedule for a single day."""

    is_open: bool = False
    open_time: str | None = None
    close_time: str | None = None


class BusinessHoursSettingsData(BaseModel):
    """Business hours settings data."""

    enabled: bool = False
    timezone: str = "America/Los_Angeles"
    schedule: dict[str, DaySchedule] = Field(default_factory=dict)


class BusinessHoursSettingsEnvelope(MinimalEnvelope):
    """Envelope for business hours settings response."""

    data: BusinessHoursSettingsData


def _get_merchant_id(request: Request) -> int:
    """Extract merchant ID from request state or headers."""
    merchant_id = getattr(request.state, "merchant_id", None)
    if not merchant_id:
        if settings()["DEBUG"]:
            merchant_id_header = request.headers.get("X-Merchant-Id")
            if merchant_id_header:
                return int(merchant_id_header)
            return 1
        raise APIError(
            ErrorCode.AUTH_FAILED,
            "Authentication required",
        )
    return merchant_id


@router.get(
    "/business-hours",
    response_model=BusinessHoursSettingsEnvelope,
)
async def get_business_hours_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> BusinessHoursSettingsEnvelope:
    """Get business hours settings.

    Story 4-12: Business Hours Handling
    AC1: Business Hours in Handoff Message

    Returns business hours configuration in the format expected by
    the API tests with day-by-day schedule.

    Args:
        request: FastAPI request
        db: Database session

    Returns:
        BusinessHoursSettingsEnvelope with schedule
    """
    from uuid import uuid4
    from datetime import datetime, timezone

    merchant_id = _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            "Merchant not found",
        )

    config = merchant.business_hours_config or {}
    hours_list = config.get("hours", [])

    days_map = {
        "mon": "monday",
        "tue": "tuesday",
        "wed": "wednesday",
        "thu": "thursday",
        "fri": "friday",
        "sat": "saturday",
        "sun": "sunday",
    }

    schedule: dict[str, DaySchedule] = {}
    for day_abbr in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
        schedule[days_map[day_abbr]] = DaySchedule(is_open=False)

    for day_hours in hours_list:
        day_abbr = day_hours.get("day", "").lower()[:3]
        if day_abbr in days_map:
            schedule[days_map[day_abbr]] = DaySchedule(
                is_open=day_hours.get("is_open", False),
                open_time=day_hours.get("open_time"),
                close_time=day_hours.get("close_time"),
            )

    enabled = bool(hours_list)

    return BusinessHoursSettingsEnvelope(
        data=BusinessHoursSettingsData(
            enabled=enabled,
            timezone=config.get("timezone", "America/Los_Angeles"),
            schedule=schedule,
        ),
        meta=MetaData(
            request_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )
