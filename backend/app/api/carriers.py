"""Carrier configuration API endpoints (Story 6.3).

Provides CRUD operations for merchant's custom carrier configurations
and carrier detection from tracking numbers.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.carrier_config import CarrierConfig
from app.models.merchant import Merchant
from app.schemas.carrier import (
    CarrierConfigCreate,
    CarrierConfigResponse,
    CarrierConfigUpdate,
    CarrierDetectionRequest,
    CarrierDetectionResult,
    SupportedCarrier,
)
from app.services.carrier.carrier_service import CarrierService
from app.services.carrier.carrier_patterns import get_sorted_patterns

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/carriers", tags=["carriers"])


@router.get(
    "/supported",
    response_model=List[SupportedCarrier],
    summary="List all supported carriers",
)
async def get_supported_carriers() -> List[SupportedCarrier]:
    """Get list of all supported carriers with their patterns.

    Returns:
        List of supported carriers organized by region.
    """
    patterns = get_sorted_patterns()
    return [
        SupportedCarrier(
            name=p.name,
            region=p.region.value,
            pattern=p.pattern,
            tracking_url_template=p.url_template,
        )
        for p in patterns
    ]


@router.get(
    "/shopify",
    response_model=List[dict],
    summary="List Shopify-supported carriers",
)
async def get_shopify_carriers() -> List[dict]:
    """Get list of carriers supported by Shopify.

    Returns:
        List of Shopify carrier names and URL templates.
    """
    from app.services.carrier.shopify_carriers import SHOPIFY_CARRIER_URLS

    return [
        {"name": name, "url_template": url_template}
        for name, url_template in SHOPIFY_CARRIER_URLS.items()
    ]


@router.post(
    "/detect",
    response_model=CarrierDetectionResult,
    summary="Detect carrier from tracking number",
)
async def detect_carrier(
    request: CarrierDetectionRequest,
    db: AsyncSession = Depends(get_db),
) -> CarrierDetectionResult:
    """Detect carrier from tracking number.

    Priority order:
    1. Merchant's custom carrier config (if merchant_id provided)
    2. Shopify carrier mapping (if tracking_company provided)
    3. Pattern detection (290+ carriers)

    Args:
        request: Detection request with tracking number and optional context.
        db: Database session.

    Returns:
        Detection result with carrier name and tracking URL.
    """
    service = CarrierService(db)
    result = await service.detect_carrier(
        tracking_number=request.tracking_number,
        merchant_id=request.merchant_id,
        tracking_company=request.tracking_company,
    )

    detection_method = "none"
    if result["carrier_name"]:
        if request.merchant_id:
            detection_method = "custom"
        elif request.tracking_company:
            detection_method = "shopify"
        else:
            detection_method = "pattern"

    return CarrierDetectionResult(
        carrier_name=result["carrier_name"],
        tracking_url=result["tracking_url"],
        detection_method=detection_method,
    )


@router.get(
    "/merchants/{merchant_id}/carriers",
    response_model=List[CarrierConfigResponse],
    summary="List merchant's custom carriers",
)
async def list_merchant_carriers(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> List[CarrierConfigResponse]:
    """List all custom carrier configurations for a merchant.

    Args:
        merchant_id: Merchant ID.
        db: Database session.

    Returns:
        List of custom carrier configurations.

    Raises:
        HTTPException: 404 if merchant not found.
    """
    merchant = await db.get(Merchant, merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {merchant_id} not found",
        )

    result = await db.execute(
        select(CarrierConfig)
        .where(CarrierConfig.merchant_id == merchant_id)
        .order_by(CarrierConfig.priority.desc())
    )
    carriers = result.scalars().all()

    return [
        CarrierConfigResponse(
            id=c.id,
            merchant_id=c.merchant_id,
            carrier_name=c.carrier_name,
            tracking_url_template=c.tracking_url_template,
            tracking_number_pattern=c.tracking_number_pattern,
            is_active=c.is_active,
            priority=c.priority,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in carriers
    ]


@router.post(
    "/merchants/{merchant_id}/carriers",
    response_model=CarrierConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add custom carrier",
)
async def create_merchant_carrier(
    merchant_id: int,
    carrier_data: CarrierConfigCreate,
    db: AsyncSession = Depends(get_db),
) -> CarrierConfigResponse:
    """Create a new custom carrier configuration.

    Args:
        merchant_id: Merchant ID.
        carrier_data: Carrier configuration data.
        db: Database session.

    Returns:
        Created carrier configuration.

    Raises:
        HTTPException: 404 if merchant not found, 400 if validation fails.
    """
    try:
        merchant = await db.get(Merchant, merchant_id)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Merchant {merchant_id} not found",
            )

        carrier = CarrierConfig(
            merchant_id=merchant_id,
            carrier_name=carrier_data.carrier_name,
            tracking_url_template=carrier_data.tracking_url_template,
            tracking_number_pattern=carrier_data.tracking_number_pattern,
            is_active=carrier_data.is_active if carrier_data.is_active is not None else True,
            priority=carrier_data.priority if carrier_data.priority is not None else 50,
        )

        db.add(carrier)
        await db.commit()
        await db.refresh(carrier)

        return CarrierConfigResponse(
            id=carrier.id,
            merchant_id=carrier.merchant_id,
            carrier_name=carrier.carrier_name,
            tracking_url_template=carrier.tracking_url_template,
            tracking_number_pattern=carrier.tracking_number_pattern,
            is_active=carrier.is_active,
            priority=carrier.priority,
            created_at=carrier.created_at,
            updated_at=carrier.updated_at,
        )
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Integrity error creating carrier for merchant {merchant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Carrier configuration violates database constraints",
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error creating carrier for merchant {merchant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create carrier configuration",
        )


@router.get(
    "/merchants/{merchant_id}/carriers/{carrier_id}",
    response_model=CarrierConfigResponse,
    summary="Get custom carrier",
)
async def get_merchant_carrier(
    merchant_id: int,
    carrier_id: int,
    db: AsyncSession = Depends(get_db),
) -> CarrierConfigResponse:
    """Get a specific custom carrier configuration.

    Args:
        merchant_id: Merchant ID.
        carrier_id: Carrier configuration ID.
        db: Database session.

    Returns:
        Carrier configuration.

    Raises:
        HTTPException: 404 if carrier not found.
    """
    carrier = await db.get(CarrierConfig, carrier_id)

    if not carrier or carrier.merchant_id != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Carrier {carrier_id} not found for merchant {merchant_id}",
        )

    return CarrierConfigResponse(
        id=carrier.id,
        merchant_id=carrier.merchant_id,
        carrier_name=carrier.carrier_name,
        tracking_url_template=carrier.tracking_url_template,
        tracking_number_pattern=carrier.tracking_number_pattern,
        is_active=carrier.is_active,
        priority=carrier.priority,
        created_at=carrier.created_at,
        updated_at=carrier.updated_at,
    )


@router.put(
    "/merchants/{merchant_id}/carriers/{carrier_id}",
    response_model=CarrierConfigResponse,
    summary="Update custom carrier",
)
async def update_merchant_carrier(
    merchant_id: int,
    carrier_id: int,
    carrier_data: CarrierConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> CarrierConfigResponse:
    """Update a custom carrier configuration.

    Args:
        merchant_id: Merchant ID.
        carrier_id: Carrier configuration ID.
        carrier_data: Updated carrier data.
        db: Database session.

    Returns:
        Updated carrier configuration.

    Raises:
        HTTPException: 404 if carrier not found, 400 if validation fails.
    """
    try:
        carrier = await db.get(CarrierConfig, carrier_id)

        if not carrier or carrier.merchant_id != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Carrier {carrier_id} not found for merchant {merchant_id}",
            )

        update_data = carrier_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(carrier, field, value)

        carrier.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(carrier)

        return CarrierConfigResponse(
            id=carrier.id,
            merchant_id=carrier.merchant_id,
            carrier_name=carrier.carrier_name,
            tracking_url_template=carrier.tracking_url_template,
            tracking_number_pattern=carrier.tracking_number_pattern,
            is_active=carrier.is_active,
            priority=carrier.priority,
            created_at=carrier.created_at,
            updated_at=carrier.updated_at,
        )
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Integrity error updating carrier {carrier_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Carrier update violates database constraints",
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error updating carrier {carrier_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update carrier configuration",
        )


@router.delete(
    "/merchants/{merchant_id}/carriers/{carrier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete custom carrier",
)
async def delete_merchant_carrier(
    merchant_id: int,
    carrier_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a custom carrier configuration.

    Args:
        merchant_id: Merchant ID.
        carrier_id: Carrier configuration ID.
        db: Database session.

    Raises:
        HTTPException: 404 if carrier not found, 500 if database error.
    """
    try:
        carrier = await db.get(CarrierConfig, carrier_id)

        if not carrier or carrier.merchant_id != merchant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Carrier {carrier_id} not found for merchant {merchant_id}",
            )

        await db.delete(carrier)
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error deleting carrier {carrier_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete carrier configuration",
        )
