"""Carrier configuration API endpoints (Story 6.3).

Provides CRUD operations for merchant's custom carrier configurations
and carrier detection from tracking numbers.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.carrier_config import CarrierConfig
from app.models.merchant import Merchant
from app.schemas.base import MetaData, MinimalEnvelope
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


def _create_meta() -> MetaData:
    """Create metadata for API response envelope.

    Returns:
        MetaData object with request_id and timestamp
    """
    return MetaData(
        request_id=str(uuid4()),
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@router.get(
    "/supported",
    response_model=MinimalEnvelope,
    summary="List all supported carriers",
)
async def get_supported_carriers() -> MinimalEnvelope:
    """Get list of all supported carriers with their patterns.

    Returns:
        MinimalEnvelope containing list of supported carriers organized by region.
    """
    patterns = get_sorted_patterns()
    carriers = [
        SupportedCarrier(
            name=p.name,
            region=p.region.value,
            pattern=p.pattern,
            tracking_url_template=p.url_template,
        )
        for p in patterns
    ]
    return MinimalEnvelope(data=carriers, meta=_create_meta())


@router.get(
    "/shopify",
    response_model=MinimalEnvelope,
    summary="List Shopify-supported carriers",
)
async def get_shopify_carriers() -> MinimalEnvelope:
    """Get list of carriers supported by Shopify.

    Returns:
        MinimalEnvelope containing list of Shopify carrier names and URL templates.
    """
    from app.services.carrier.shopify_carriers import SHOPIFY_CARRIER_URLS

    carriers = [
        {"name": name, "url_template": url_template}
        for name, url_template in SHOPIFY_CARRIER_URLS.items()
    ]
    return MinimalEnvelope(data=carriers, meta=_create_meta())


@router.post(
    "/detect",
    response_model=MinimalEnvelope,
    summary="Detect carrier from tracking number",
)
async def detect_carrier(
    request: CarrierDetectionRequest,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Detect carrier from tracking number.

    Priority order:
    1. Merchant's custom carrier config (if merchant_id provided)
    2. Shopify carrier mapping (if tracking_company provided)
    3. Pattern detection (290+ carriers)

    Args:
        request: Detection request with tracking number and optional context.
        db: Database session.

    Returns:
        MinimalEnvelope containing detection result with carrier name and tracking URL.
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

    detection_result = CarrierDetectionResult(
        carrier_name=result["carrier_name"],
        tracking_url=result["tracking_url"],
        detection_method=detection_method,
    )
    return MinimalEnvelope(data=detection_result, meta=_create_meta())


@router.get(
    "/merchants/{merchant_id}/carriers",
    response_model=MinimalEnvelope,
    summary="List merchant's custom carriers",
)
async def list_merchant_carriers(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """List all custom carrier configurations for a merchant.

    Args:
        merchant_id: Merchant ID.
        db: Database session.

    Returns:
        MinimalEnvelope containing list of custom carrier configurations.

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

    carrier_configs = [
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
    return MinimalEnvelope(data=carrier_configs, meta=_create_meta())


@router.post(
    "/merchants/{merchant_id}/carriers",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_201_CREATED,
    summary="Add custom carrier",
)
async def create_merchant_carrier(
    merchant_id: int,
    carrier_data: CarrierConfigCreate,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Create a new custom carrier configuration.

    Args:
        merchant_id: Merchant ID.
        carrier_data: Carrier configuration data.
        db: Database session.

    Returns:
        MinimalEnvelope containing created carrier configuration.

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

        carrier_response = CarrierConfigResponse(
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
        return MinimalEnvelope(data=carrier_response, meta=_create_meta())
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
    response_model=MinimalEnvelope,
    summary="Get custom carrier",
)
async def get_merchant_carrier(
    merchant_id: int,
    carrier_id: int,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Get a specific custom carrier configuration.

    Args:
        merchant_id: Merchant ID.
        carrier_id: Carrier configuration ID.
        db: Database session.

    Returns:
        MinimalEnvelope containing carrier configuration.

    Raises:
        HTTPException: 404 if carrier not found.
    """
    carrier = await db.get(CarrierConfig, carrier_id)

    if not carrier or carrier.merchant_id != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Carrier {carrier_id} not found for merchant {merchant_id}",
        )

    carrier_response = CarrierConfigResponse(
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
    return MinimalEnvelope(data=carrier_response, meta=_create_meta())


@router.put(
    "/merchants/{merchant_id}/carriers/{carrier_id}",
    response_model=MinimalEnvelope,
    summary="Update custom carrier",
)
async def update_merchant_carrier(
    merchant_id: int,
    carrier_id: int,
    carrier_data: CarrierConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Update a custom carrier configuration.

    Args:
        merchant_id: Merchant ID.
        carrier_id: Carrier configuration ID.
        carrier_data: Updated carrier data.
        db: Database session.

    Returns:
        MinimalEnvelope containing updated carrier configuration.

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

        carrier_response = CarrierConfigResponse(
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
        return MinimalEnvelope(data=carrier_response, meta=_create_meta())
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
