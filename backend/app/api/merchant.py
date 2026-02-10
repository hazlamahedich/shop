"""Merchant settings API endpoints.

Provides endpoints for:
- Updating merchant configuration (budget cap, etc.)
- Getting merchant settings
- Bot personality configuration
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import APIError, ErrorCode, ValidationError
from app.models.merchant import Merchant, PersonalityType
from app.schemas.base import MinimalEnvelope, MetaData


logger = structlog.get_logger(__name__)

router = APIRouter()


class BudgetCapUpdate(BaseModel):
    """Request schema for updating budget cap."""

    budget_cap: float = Field(
        ...,
        ge=0,
        description="Monthly budget cap in USD",
        examples=[50.0, 100.0, 500.0],
    )


class MerchantSettingsResponse(BaseModel):
    """Response schema for merchant settings."""

    budget_cap: Optional[float] = Field(
        None,
        description="Monthly budget cap in USD",
    )
    config: dict = Field(
        default_factory=dict,
        description="Full merchant configuration",
    )


class PersonalityConfigurationUpdate(BaseModel):
    """Request schema for updating personality configuration."""

    personality: Optional[PersonalityType] = Field(
        None,
        description="Bot personality type",
    )
    custom_greeting: Optional[str] = Field(
        None,
        max_length=500,
        description="Custom greeting message (optional, up to 500 characters)",
    )


class PersonalityConfigurationResponse(BaseModel):
    """Response schema for personality configuration."""

    personality: PersonalityType = Field(
        description="Bot personality type",
    )
    custom_greeting: Optional[str] = Field(
        None,
        description="Custom greeting message",
    )


# Helper Functions


def _create_meta() -> MetaData:
    """Create metadata for API response.

    Returns:
        MetaData object with request_id and timestamp
    """
    return MetaData(
        request_id=str(uuid4()),
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@router.get(
    "/personality",
    response_model=MinimalEnvelope,
)
async def get_personality_configuration(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """
    Get bot personality configuration.

    Returns the current merchant's bot personality and custom greeting.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        MinimalEnvelope with personality configuration

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

    return MinimalEnvelope(
        data=PersonalityConfigurationResponse(
            personality=merchant.personality,
            custom_greeting=merchant.custom_greeting,
        ),
        meta=_create_meta(),
    )


@router.patch(
    "/personality",
    response_model=MinimalEnvelope,
)
async def update_personality_configuration(
    request: Request,
    update: PersonalityConfigurationUpdate,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """
    Update bot personality configuration.

    Allows merchants to update their bot's personality type and custom greeting.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session
        update: Personality configuration update data

    Returns:
        MinimalEnvelope with updated personality configuration

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
            "updating_personality_configuration",
            merchant_id=merchant_id,
            personality=update.personality.value if update.personality else None,
            has_custom_greeting=update.custom_greeting is not None,
        )

        # Update personality if provided
        if update.personality:
            merchant.personality = update.personality

        # Update custom greeting - treat empty/whitespace strings as None
        # But preserve trailing spaces for non-empty greetings
        if update.custom_greeting is not None:
            # Check if greeting is empty or whitespace-only
            if update.custom_greeting.strip():
                # Non-empty greeting - preserve original value including trailing spaces
                merchant.custom_greeting = update.custom_greeting
            else:
                # Whitespace-only - treat as None
                merchant.custom_greeting = None

        # Commit changes
        try:
            await db.commit()
            await db.refresh(merchant)
        except Exception as e:
            await db.rollback()
            raise APIError(ErrorCode.INTERNAL_ERROR, f"Failed to update personality configuration: {str(e)}")

        logger.info(
            "personality_configuration_updated",
            merchant_id=merchant_id,
            personality=merchant.personality.value,
            custom_greeting=merchant.custom_greeting,
        )

        return MinimalEnvelope(
            data=PersonalityConfigurationResponse(
                personality=merchant.personality,
                custom_greeting=merchant.custom_greeting,
            ),
            meta=_create_meta(),
        )
    except APIError:
        raise
    except Exception as e:
        logger.error("update_personality_configuration_failed", error=str(e))
        raise APIError(ErrorCode.INTERNAL_ERROR, f"Failed to update personality configuration: {str(e)}")


@router.patch(
    "/settings",
    response_model=MerchantSettingsResponse,
)
async def update_merchant_settings(
    request: Request,
    update: BudgetCapUpdate,
    db: AsyncSession = Depends(get_db),
) -> MerchantSettingsResponse:
    """
    Update merchant settings.

    Allows merchants to update their configuration, including budget cap
    for cost tracking. The budget_cap is stored in the config JSONB column.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session
        update: Budget cap update data

    Returns:
        Updated merchant settings

    Raises:
        APIError: If authentication fails or merchant not found
    """
    # 1. Verify Authentication
    try:
        merchant_id = _get_merchant_id(request)
        budget_cap = update.budget_cap

        # 2. Get merchant record
        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalars().first()

        if not merchant:
            raise APIError(
                ErrorCode.MERCHANT_NOT_FOUND,
                f"Merchant with ID {merchant_id} not found",
            )

        # 3. Update config with new budget cap
        logger.info("updating_budget_cap", merchant_id=merchant_id, budget_cap=budget_cap)

        current_config = merchant.config or {}
        # Ensure it's a dict we can modify
        new_config = dict(current_config)
        new_config["budget_cap"] = float(budget_cap)

        # Re-assign to ensure SQLAlchemy tracks change
        merchant.config = new_config

        # 4. Commit changes
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            raise APIError(ErrorCode.INTERNAL_ERROR, f"Failed to update merchant: {str(e)}")

        logger.info(
            "merchant_settings_updated",
            merchant_id=merchant_id,
            budget_cap=budget_cap,
        )

        # 5. Return updated settings
        return MerchantSettingsResponse(
            budget_cap=merchant.config.get("budget_cap"),
            config=merchant.config or {},
        )
    except Exception as e:
        logger.error("update_merchant_settings_failed", error=str(e))
        raise


@router.get(
    "/settings",
    response_model=MerchantSettingsResponse,
)
async def get_merchant_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MerchantSettingsResponse:
    """
    Get merchant settings.

    Returns the current merchant configuration including budget cap.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        Current merchant settings

    Raises:
        APIError: If authentication fails or merchant not found
    """
    # 1. Verify Authentication
    merchant_id = _get_merchant_id(request)

    # 2. Get merchant record
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant with ID {merchant_id} not found",
        )

    # 3. Return settings
    return MerchantSettingsResponse(
        budget_cap=merchant.config.get("budget_cap") if merchant.config else None,
        config=merchant.config or {},
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
