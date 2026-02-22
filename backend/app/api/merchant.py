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

    budget_cap: Optional[float] = Field(
        None,
        ge=0,
        description="Monthly budget cap in USD. Set to null for no limit.",
        examples=[50.0, 100.0, 500.0, None],
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
                merchant.use_custom_greeting = True  # Auto-enable custom greeting when provided
            else:
                # Whitespace-only - treat as None
                merchant.custom_greeting = None
                merchant.use_custom_greeting = False  # Disable when clearing greeting

        # Commit changes
        try:
            await db.commit()
            await db.refresh(merchant)
        except Exception as e:
            await db.rollback()
            raise APIError(
                ErrorCode.INTERNAL_ERROR, f"Failed to update personality configuration: {str(e)}"
            )

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
        raise APIError(
            ErrorCode.INTERNAL_ERROR, f"Failed to update personality configuration: {str(e)}"
        )


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

        if budget_cap is None:
            # None means no limit - remove budget_cap from config
            new_config.pop("budget_cap", None)
        else:
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


@router.get(
    "/budget-alerts",
    response_model=MinimalEnvelope,
)
async def get_budget_alerts(
    request: Request,
    db: AsyncSession = Depends(get_db),
    unread_only: bool = False,
) -> MinimalEnvelope:
    """Get budget alerts for the merchant.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session
        unread_only: Only return unread alerts

    Returns:
        MinimalEnvelope with list of alerts and unread count
    """
    from app.services.cost_tracking.budget_alert_service import BudgetAlertService
    from app.schemas.budget_alert import BudgetAlertResponse, BudgetAlertListResponse

    merchant_id = _get_merchant_id(request)

    budget_service = BudgetAlertService(db)
    alerts = await budget_service.get_alerts(merchant_id, unread_only=unread_only)

    unread_count = sum(1 for a in alerts if not a.is_read)

    return MinimalEnvelope(
        data=BudgetAlertListResponse(
            alerts=[BudgetAlertResponse.model_validate(a) for a in alerts],
            unread_count=unread_count,
        ),
        meta=_create_meta(),
    )


@router.post(
    "/budget-alerts/{alert_id}/read",
    response_model=MinimalEnvelope,
)
async def mark_budget_alert_read(
    request: Request,
    alert_id: int,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Mark a budget alert as read.

    Args:
        request: FastAPI request with merchant authentication
        alert_id: Alert ID to mark as read
        db: Database session

    Returns:
        MinimalEnvelope with success status
    """
    from app.services.cost_tracking.budget_alert_service import BudgetAlertService

    merchant_id = _get_merchant_id(request)

    budget_service = BudgetAlertService(db)
    success = await budget_service.mark_alert_read(alert_id, merchant_id)

    if not success:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Alert {alert_id} not found for this merchant",
        )

    await db.commit()

    return MinimalEnvelope(
        data={"success": True, "alert_id": alert_id},
        meta=_create_meta(),
    )


@router.get(
    "/bot-status",
    response_model=MinimalEnvelope,
)
async def get_bot_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Get bot status (paused/active) and budget info.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        MinimalEnvelope with bot status and budget information
    """
    from decimal import Decimal
    from app.services.cost_tracking.budget_alert_service import BudgetAlertService
    from app.services.cost_tracking.cost_tracking_service import CostTrackingService
    from app.schemas.budget_alert import BotStatusResponse

    merchant_id = _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant with ID {merchant_id} not found",
        )

    budget_service = BudgetAlertService(db)
    cost_service = CostTrackingService()

    is_paused, pause_reason = await budget_service.get_bot_paused_state(merchant_id)

    budget_cap = None
    if merchant.config:
        budget_cap = merchant.config.get("budget_cap")

    monthly_spend = None
    budget_percentage = None

    if budget_cap is not None:
        monthly_spend = await cost_service.get_monthly_spend(db, merchant_id)
        if budget_cap > 0:
            budget_percentage = (monthly_spend / budget_cap) * 100

    return MinimalEnvelope(
        data=BotStatusResponse(
            is_paused=is_paused,
            pause_reason=pause_reason,
            budget_percentage=round(budget_percentage, 2) if budget_percentage else None,
            budget_cap=budget_cap,
            monthly_spend=monthly_spend,
        ),
        meta=_create_meta(),
    )


@router.post(
    "/bot/resume",
    response_model=MinimalEnvelope,
)
async def resume_bot(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Manually resume bot if budget allows.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        MinimalEnvelope with resume status
    """
    from app.services.cost_tracking.budget_alert_service import BudgetAlertService
    from app.schemas.budget_alert import ResumeBotResponse

    merchant_id = _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant with ID {merchant_id} not found",
        )

    budget_service = BudgetAlertService(db)

    budget_cap = None
    if merchant.config:
        budget_cap = merchant.config.get("budget_cap")

    if budget_cap is not None and budget_cap == 0:
        return MinimalEnvelope(
            data=ResumeBotResponse(
                success=False,
                message="Cannot resume bot with $0 budget. Please increase budget first.",
                new_budget=None,
            ),
            meta=_create_meta(),
        )

    success, message = await budget_service.resume_bot(merchant_id)

    if success:
        await db.commit()

    return MinimalEnvelope(
        data=ResumeBotResponse(
            success=success,
            message=message,
            new_budget=budget_cap,
        ),
        meta=_create_meta(),
    )


class AlertConfigUpdate(BaseModel):
    """Request schema for updating alert configuration."""

    warning_threshold: int | None = Field(
        None,
        ge=50,
        le=95,
        description="Warning threshold percentage (50-95%)",
    )
    critical_threshold: int | None = Field(
        None,
        ge=80,
        le=99,
        description="Critical threshold percentage (80-99%)",
    )
    enabled: bool | None = Field(
        None,
        description="Whether alerts are enabled",
    )


class AlertConfigResponse(BaseModel):
    """Response schema for alert configuration."""

    warning_threshold: int = Field(description="Warning threshold percentage")
    critical_threshold: int = Field(description="Critical threshold percentage")
    enabled: bool = Field(description="Whether alerts are enabled")


class SnoozeResponse(BaseModel):
    """Response schema for snooze operation."""

    success: bool = Field(description="Whether snooze was set")
    snoozed_until: datetime | None = Field(
        default=None,
        description="When snooze expires (24h from now)",
    )


class AlertStatusResponse(BaseModel):
    """Response schema for alert status."""

    alert_level: str = Field(description="Current alert level: ok/warning/critical/exceeded")
    budget_percentage: float | None = Field(description="Current budget usage percentage")
    is_snoozed: bool = Field(description="Whether warnings are snoozed")
    is_bot_paused: bool = Field(description="Whether bot is paused")


@router.get(
    "/alert-config",
    response_model=MinimalEnvelope,
)
async def get_alert_config(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Get alert configuration (thresholds, enabled status).

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        MinimalEnvelope with alert configuration
    """
    from app.services.cost_tracking.budget_alert_service import BudgetAlertService

    merchant_id = _get_merchant_id(request)
    budget_service = BudgetAlertService(db)

    config = await budget_service.get_alert_config(merchant_id)

    return MinimalEnvelope(
        data=AlertConfigResponse(
            warning_threshold=config["warning_threshold"],
            critical_threshold=config["critical_threshold"],
            enabled=config["enabled"],
        ),
        meta=_create_meta(),
    )


@router.put(
    "/alert-config",
    response_model=MinimalEnvelope,
)
async def update_alert_config(
    request: Request,
    update: AlertConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Update alert configuration.

    Args:
        request: FastAPI request with merchant authentication
        update: Alert configuration update
        db: Database session

    Returns:
        MinimalEnvelope with updated configuration
    """
    from app.services.cost_tracking.budget_alert_service import BudgetAlertService

    merchant_id = _get_merchant_id(request)
    budget_service = BudgetAlertService(db)

    success = await budget_service.update_alert_config(
        merchant_id=merchant_id,
        warning_threshold=update.warning_threshold,
        critical_threshold=update.critical_threshold,
        enabled=update.enabled,
    )

    if not success:
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            "Failed to update alert configuration",
        )

    await db.commit()

    config = await budget_service.get_alert_config(merchant_id)

    return MinimalEnvelope(
        data=AlertConfigResponse(
            warning_threshold=config["warning_threshold"],
            critical_threshold=config["critical_threshold"],
            enabled=config["enabled"],
        ),
        meta=_create_meta(),
    )


@router.post(
    "/alert-snooze",
    response_model=MinimalEnvelope,
)
async def snooze_alerts(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Snooze warning alerts for 24 hours.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        MinimalEnvelope with snooze status
    """
    from datetime import timedelta

    from app.services.cost_tracking.budget_alert_service import BudgetAlertService

    merchant_id = _get_merchant_id(request)
    budget_service = BudgetAlertService(db)

    success = await budget_service.snooze(merchant_id)

    snoozed_until = None
    if success:
        snoozed_until = datetime.utcnow() + timedelta(hours=24)

    return MinimalEnvelope(
        data=SnoozeResponse(
            success=success,
            snoozed_until=snoozed_until,
        ),
        meta=_create_meta(),
    )


@router.delete(
    "/alert-snooze",
    response_model=MinimalEnvelope,
)
async def clear_snooze(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Clear snooze state.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        MinimalEnvelope with clear status
    """
    from app.services.cost_tracking.budget_alert_service import BudgetAlertService

    merchant_id = _get_merchant_id(request)
    budget_service = BudgetAlertService(db)

    success = await budget_service.clear_snooze(merchant_id)

    return MinimalEnvelope(
        data={"success": success},
        meta=_create_meta(),
    )


@router.get(
    "/budget-recommendation",
    response_model=MinimalEnvelope,
)
async def get_budget_recommendation(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Get budget recommendation based on cost history.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        MinimalEnvelope with budget recommendation
    """
    from app.services.merchant_settings_service import (
        get_budget_recommendation as calc_budget_recommendation,
    )

    merchant_id = _get_merchant_id(request)

    recommendation = await calc_budget_recommendation(db, merchant_id)

    return MinimalEnvelope(
        data=recommendation.to_dict(),
        meta=_create_meta(),
    )


@router.get(
    "/alert-status",
    response_model=MinimalEnvelope,
)
async def get_alert_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Get current alert status.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        MinimalEnvelope with alert status
    """
    from decimal import Decimal

    from app.services.cost_tracking.budget_alert_service import BudgetAlertService
    from app.services.cost_tracking.cost_tracking_service import CostTrackingService

    merchant_id = _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant with ID {merchant_id} not found",
        )

    budget_service = BudgetAlertService(db)
    cost_service = CostTrackingService()

    budget_cap = None
    if merchant.config:
        budget_cap = merchant.config.get("budget_cap")

    is_snoozed = await budget_service.is_snoozed(merchant_id)
    is_paused, _ = await budget_service.get_bot_paused_state(merchant_id)

    alert_level = "ok"
    budget_percentage = None

    if budget_cap is not None:
        monthly_spend = await cost_service.get_monthly_spend(db, merchant_id)
        if budget_cap > 0:
            budget_percentage = (monthly_spend / budget_cap) * 100
            alert_level = await budget_service.check_budget_threshold(
                merchant_id,
                Decimal(str(monthly_spend)),
                Decimal(str(budget_cap)),
            )

    return MinimalEnvelope(
        data=AlertStatusResponse(
            alert_level=alert_level,
            budget_percentage=round(budget_percentage, 2) if budget_percentage else None,
            is_snoozed=is_snoozed,
            is_bot_paused=is_paused,
        ),
        meta=_create_meta(),
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
