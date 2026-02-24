"""Business Hours configuration API endpoints.

Story 3.10: Business Hours Configuration

Provides endpoints for:
- Getting business hours configuration
- Updating business hours configuration
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.merchant import Merchant
from app.schemas.business_hours import (
    BusinessHoursRequest,
    BusinessHoursResponse,
    BusinessHoursEnvelope,
)
from app.api.helpers import create_meta, get_merchant_id, verify_merchant_exists
from app.services.business_hours import get_formatted_hours


logger = structlog.get_logger(__name__)

router = APIRouter()

DEFAULT_OUT_OF_OFFICE_MESSAGE = "Our team is offline. We'll respond during business hours."
DEFAULT_BUSINESS_HOURS = {
    "timezone": "America/Los_Angeles",
    "hours": [],
    "out_of_office_message": DEFAULT_OUT_OF_OFFICE_MESSAGE,
}


@router.get(
    "/business-hours",
    response_model=BusinessHoursEnvelope,
)
async def get_business_hours(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> BusinessHoursEnvelope:
    """Get business hours configuration.

    Returns the current merchant's business hours configuration including
    timezone, day-by-day hours, and out-of-office message.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        BusinessHoursEnvelope with business hours configuration

    Raises:
        APIError: If authentication fails or merchant not found
    """
    merchant_id = get_merchant_id(request)
    merchant = await verify_merchant_exists(merchant_id, db)

    config = merchant.business_hours_config or DEFAULT_BUSINESS_HOURS
    formatted_hours = get_formatted_hours(config)
    out_of_office = config.get("out_of_office_message") or DEFAULT_OUT_OF_OFFICE_MESSAGE
    updated_at = merchant.updated_at.isoformat() if merchant.updated_at else None

    return BusinessHoursEnvelope(
        data=BusinessHoursResponse(
            timezone=config.get("timezone", "America/Los_Angeles"),
            hours=config.get("hours", []),
            out_of_office_message=out_of_office,
            formatted_hours=formatted_hours,
            updated_at=updated_at,
        ),
        meta=create_meta(),
    )


@router.put(
    "/business-hours",
    response_model=BusinessHoursEnvelope,
)
async def update_business_hours(
    request: Request,
    update: BusinessHoursRequest,
    db: AsyncSession = Depends(get_db),
) -> BusinessHoursEnvelope:
    """Update business hours configuration.

    Allows merchants to update their business hours, timezone,
    and out-of-office message. All fields are optional.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session
        update: Business hours update data

    Returns:
        BusinessHoursEnvelope with updated business hours configuration

    Raises:
        APIError: If authentication fails or merchant not found
    """
    try:
        merchant_id = get_merchant_id(request)
        merchant = await verify_merchant_exists(merchant_id, db)

        logger.info(
            "updating_business_hours",
            merchant_id=merchant_id,
            timezone=update.timezone,
            hours_count=len(update.hours),
        )

        config_dict = {
            "timezone": update.timezone,
            "hours": [h.model_dump(by_alias=False) for h in update.hours],
            "out_of_office_message": update.out_of_office_message or DEFAULT_OUT_OF_OFFICE_MESSAGE,
        }

        merchant.business_hours_config = config_dict

        try:
            await db.commit()
            await db.refresh(merchant)
        except Exception as e:
            await db.rollback()
            logger.error(
                "update_business_hours_commit_failed",
                merchant_id=merchant_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise APIError(
                ErrorCode.INTERNAL_ERROR,
                f"Failed to update business hours: {str(e)}",
            )

        formatted_hours = get_formatted_hours(config_dict)

        logger.info(
            "business_hours_updated",
            merchant_id=merchant_id,
            timezone=config_dict["timezone"],
        )

        updated_at = merchant.updated_at.isoformat() if merchant.updated_at else None

        return BusinessHoursEnvelope(
            data=BusinessHoursResponse(
                timezone=config_dict["timezone"],
                hours=update.hours,
                out_of_office_message=config_dict["out_of_office_message"],
                formatted_hours=formatted_hours,
                updated_at=updated_at,
            ),
            meta=create_meta(),
        )
    except APIError:
        raise
    except Exception as e:
        logger.error(
            "update_business_hours_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to update business hours: {str(e)}",
        )
