"""Business Info configuration API endpoints.

Story 1.11: Business Info & FAQ Configuration

Provides endpoints for:
- Getting business information
- Updating business information
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.merchant import Merchant
from app.schemas.business_info import (
    BusinessInfoRequest,
    BusinessInfoResponse,
    BusinessInfoEnvelope,
)
from app.schemas.base import MetaData


logger = structlog.get_logger(__name__)

router = APIRouter()


def _create_meta() -> MetaData:
    """Create metadata for API response.

    Returns:
        MetaData object with request_id and timestamp
    """
    return MetaData(
        request_id=str(uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


def _get_merchant_id(request: Request) -> int:
    """Get merchant ID from request state with fallback for testing.

    Args:
        request: FastAPI request

    Returns:
        Merchant ID

    Raises:
        APIError: If authentication fails
    """
    merchant_id = getattr(request.state, "merchant_id", None)
    if not merchant_id:
        # Check X-Merchant-Id header in DEBUG mode for easier testing
        if settings()["DEBUG"]:
            merchant_id_header = request.headers.get("X-Merchant-Id")
            if merchant_id_header:
                merchant_id = int(merchant_id_header)
            else:
                merchant_id = 1  # Default for dev/test
        else:
            raise APIError(
                ErrorCode.AUTH_FAILED,
                "Authentication required",
            )
    return merchant_id


@router.get(
    "/business-info",
    response_model=BusinessInfoEnvelope,
)
async def get_business_info(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> BusinessInfoEnvelope:
    """
    Get business information.

    Returns the current merchant's business information including
    business name, description, and hours.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        BusinessInfoEnvelope with business information

    Raises:
        APIError: If authentication fails or merchant not found
    """
    merchant_id = _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant with ID {merchant_id} not found",
        )

    return BusinessInfoEnvelope(
        data=BusinessInfoResponse(
            business_name=merchant.business_name,
            business_description=merchant.business_description,
            business_hours=merchant.business_hours,
        ),
        meta=_create_meta(),
    )


@router.put(
    "/business-info",
    response_model=BusinessInfoEnvelope,
)
async def update_business_info(
    request: Request,
    update: BusinessInfoRequest,
    db: AsyncSession = Depends(get_db),
) -> BusinessInfoEnvelope:
    """
    Update business information.

    Allows merchants to update their business name, description, and hours.
    All fields are optional - only provided fields will be updated.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session
        update: Business info update data

    Returns:
        BusinessInfoEnvelope with updated business information

    Raises:
        APIError: If authentication fails or merchant not found
    """
    try:
        merchant_id = _get_merchant_id(request)

        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalars().first()

        if not merchant:
            raise APIError(
                ErrorCode.MERCHANT_NOT_FOUND,
                f"Merchant with ID {merchant_id} not found",
            )

        logger.info(
            "updating_business_info",
            merchant_id=merchant_id,
            has_business_name=update.business_name is not None,
            has_business_description=update.business_description is not None,
            has_business_hours=update.business_hours is not None,
        )

        # Update fields that were provided (None means clear the field)
        # We use model_fields_set to track which fields were explicitly provided
        provided_fields = update.model_fields_set
        if "business_name" in provided_fields:
            merchant.business_name = update.business_name
        if "business_description" in provided_fields:
            merchant.business_description = update.business_description
        if "business_hours" in provided_fields:
            merchant.business_hours = update.business_hours

        # Commit changes
        try:
            await db.commit()
            await db.refresh(merchant)
        except Exception as e:
            await db.rollback()
            raise APIError(
                ErrorCode.INTERNAL_ERROR,
                f"Failed to update business info: {str(e)}",
            )

        logger.info(
            "business_info_updated",
            merchant_id=merchant_id,
            business_name=merchant.business_name,
        )

        return BusinessInfoEnvelope(
            data=BusinessInfoResponse(
                business_name=merchant.business_name,
                business_description=merchant.business_description,
                business_hours=merchant.business_hours,
            ),
            meta=_create_meta(),
        )
    except APIError:
        raise
    except Exception as e:
        logger.error("update_business_info_failed", error=str(e))
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to update business info: {str(e)}",
        )
