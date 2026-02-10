"""Business Info configuration API endpoints.

Story 1.11: Business Info & FAQ Configuration

Provides endpoints for:
- Getting business information
- Updating business information
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.merchant import Merchant
from app.schemas.business_info import (
    BusinessInfoRequest,
    BusinessInfoResponse,
    BusinessInfoEnvelope,
)
from app.api.helpers import create_meta, get_merchant_id, verify_merchant_exists


logger = structlog.get_logger(__name__)

router = APIRouter()


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
    merchant_id = get_merchant_id(request)

    merchant = await verify_merchant_exists(merchant_id, db)

    return BusinessInfoEnvelope(
        data=BusinessInfoResponse(
            business_name=merchant.business_name,
            business_description=merchant.business_description,
            business_hours=merchant.business_hours,
        ),
        meta=create_meta(),
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
        merchant_id = get_merchant_id(request)

        merchant = await verify_merchant_exists(merchant_id, db)

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

        # Commit changes with improved error context
        try:
            await db.commit()
            await db.refresh(merchant)
        except Exception as e:
            await db.rollback()
            logger.error(
                "update_business_info_commit_failed",
                merchant_id=merchant_id,
                error=str(e),
                error_type=type(e).__name__,
            )
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
            meta=create_meta(),
        )
    except APIError:
        raise
    except Exception as e:
        logger.error(
            "update_business_info_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to update business info: {str(e)}",
        )
