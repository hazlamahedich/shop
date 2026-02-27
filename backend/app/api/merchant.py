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


class GreetingTransformRequest(BaseModel):
    """Request schema for transforming greeting to target personality."""

    custom_greeting: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="The custom greeting to transform",
    )
    target_personality: PersonalityType = Field(
        ...,
        description="The target personality tone to apply",
    )
    bot_name: Optional[str] = Field(
        None,
        description="Bot name for context (optional)",
    )
    business_name: Optional[str] = Field(
        None,
        description="Business name for context (optional)",
    )


class GreetingTransformResponse(BaseModel):
    """Response schema for transformed greeting."""

    transformed_greeting: str = Field(
        description="The greeting rewritten in the target personality tone",
    )
    personality: PersonalityType = Field(
        description="The personality tone applied",
    )
    original_greeting: str = Field(
        description="The original greeting provided",
    )


PERSONALITY_TONE_GUIDES = {
    PersonalityType.FRIENDLY: """Write in a casual, warm, conversational tone.
- Use friendly, approachable language
- Use emojis sparingly but naturally (1-2 max)
- Keep it welcoming and personable
- Example: "Hey there! 👋 I'm {bot_name} from {business_name}. How can I help you today?" """,
    PersonalityType.PROFESSIONAL: """Write in a direct, helpful, respectful business tone.
- NO emojis at all
- Use formal, professional language
- Be concise and clear
- Example: "Good day. I am {bot_name} from {business_name}. How may I assist you today?" """,
    PersonalityType.ENTHUSIASTIC: """Write in a high-energy, exciting, positive tone!
- Use expressive emojis naturally (2-3 max)
- Use exclamation marks sparingly but effectively
- Show genuine excitement and energy
- Example: "Hello! 🎉 I'm {bot_name} from {business_name}. How can I help you find exactly what you need!!! ✨"
""",
}


@router.post(
    "/greeting/transform",
    response_model=MinimalEnvelope,
)
async def transform_greeting(
    request: Request,
    transform_request: GreetingTransformRequest,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Transform a custom greeting to match a target personality tone.

    Uses LLM to rewrite the greeting while preserving all business details
    (business name, products, location, taglines, etc.) but changing the
    tone to match the target personality.

    Args:
        request: FastAPI request with merchant authentication
        transform_request: The greeting and target personality
        db: Database session

    Returns:
        MinimalEnvelope with transformed greeting

    Raises:
        APIError: If transformation fails
    """
    from app.services.llm.llm_factory import LLMProviderFactory
    from app.services.llm.base_llm_service import LLMMessage

    merchant_id = _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant with ID {merchant_id} not found",
        )

    bot_name = transform_request.bot_name or merchant.bot_name or "Shopping Assistant"
    business_name = transform_request.business_name or merchant.business_name or "our store"
    target_personality = transform_request.target_personality
    original_greeting = transform_request.custom_greeting

    tone_guide = PERSONALITY_TONE_GUIDES[target_personality]

    system_prompt = f"""You are a greeting message editor. Your task is to rewrite greeting messages to match a specific personality tone while preserving ALL business details.

CRITICAL RULES:
1. PRESERVE all business-specific information exactly as written:
   - Business name, products, services
   - Location, taglines, unique selling points
   - Numbers, prices, specific details
   - Any special offers or promotions

2. ONLY change the TONE and STYLE to match the target personality:
{tone_guide}

3. Keep the greeting concise (1-3 sentences max)

4. Do NOT add new information that wasn't in the original

5. Do NOT remove any business details from the original"""

    user_prompt = f"""Original greeting:
"{original_greeting}"

Target personality: {target_personality.value}

Context:
- Bot name: {bot_name}
- Business name: {business_name}

Rewrite this greeting in the {target_personality.value} personality tone, preserving all business details. Return ONLY the rewritten greeting, nothing else."""

    try:
        # Try LLM transformation first
        llm_config = {}
        provider_name = "ollama"

        if hasattr(merchant, "llm_configuration") and merchant.llm_configuration:
            llm_config_obj = merchant.llm_configuration
            provider_name = llm_config_obj.provider or "ollama"
            llm_config = {
                "model": llm_config_obj.ollama_model or llm_config_obj.cloud_model,
            }
            if provider_name == "ollama":
                llm_config["ollama_url"] = llm_config_obj.ollama_url
            elif llm_config_obj.api_key_encrypted:
                from app.core.security import decrypt_access_token

                llm_config["api_key"] = decrypt_access_token(llm_config_obj.api_key_encrypted)

        llm_service = LLMProviderFactory.create_provider(
            provider_name=provider_name,
            config=llm_config,
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        llm_response = await llm_service.chat(
            messages=messages,
            temperature=0.3,
            max_tokens=200,
        )

        transformed_greeting = llm_response.content.strip()

        if transformed_greeting.startswith('"') and transformed_greeting.endswith('"'):
            transformed_greeting = transformed_greeting[1:-1]

        logger.info(
            "greeting_transformed_via_llm",
            merchant_id=merchant_id,
            target_personality=target_personality.value,
            original_length=len(original_greeting),
            transformed_length=len(transformed_greeting),
        )

    except Exception as e:
        # Fallback: Use rule-based transformation without LLM
        logger.warning(
            "greeting_transform_llm_failed_using_rule_based_fallback",
            merchant_id=merchant_id,
            error=str(e),
        )

        # Rule-based transformation: adjust tone based on personality
        import re

        transformed_greeting = original_greeting

        if target_personality == PersonalityType.PROFESSIONAL:
            # Remove emojis for Professional
            emoji_pattern = re.compile(
                "["
                "\U0001f600-\U0001f64f"
                "\U0001f300-\U0001f5ff"
                "\U0001f680-\U0001f6ff"
                "\U0001f1e0-\U0001f1ff"
                "\U00002702-\U000027b0"
                "\U000024c2-\U0001f251"
                "\U0001f926-\U0001f937"
                "\U00010000-\U0010ffff"
                "\u2640-\u2642"
                "\u2600-\u2b55"
                "\u200d"
                "\u23cf"
                "\u23e9"
                "\u231a"
                "\ufe0f"
                "\u3030"
                "]+",
                flags=re.UNICODE,
            )
            transformed_greeting = emoji_pattern.sub("", transformed_greeting)

            # Replace multiple exclamation marks with period
            transformed_greeting = re.sub(r"!{2,}", ".", transformed_greeting)
            transformed_greeting = re.sub(r"!$", ".", transformed_greeting)

            # Replace casual words with professional alternatives
            casual_to_professional = {
                "Hi!": "Good day.",
                "Hi ": "Hello ",
                "Hey!": "Good day.",
                "Hey ": "Hello ",
                "your smart and friendly": "your professional",
                "smart and friendly": "professional",
                "friendly": "professional",
                "number 1": "premier",
                "How can I help you?": "How may I assist you?",
                "How can I help you": "How may I assist you",
                "How can I help?": "How may I assist?",
                "can't wait": "look forward",
                "awesome": "excellent",
                "amazing": "excellent",
            }

            for casual, professional in casual_to_professional.items():
                transformed_greeting = transformed_greeting.replace(casual, professional)

            # Clean up any double spaces
            transformed_greeting = re.sub(r"\s+", " ", transformed_greeting).strip()

        elif target_personality == PersonalityType.ENTHUSIASTIC:
            # Add enthusiasm for Enthusiastic personality
            if not re.search(r"[!]{2,}", transformed_greeting):
                transformed_greeting = transformed_greeting.replace("!", "!")

            # Add emoji at the end if not present
            if not re.search(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]", transformed_greeting):
                transformed_greeting = transformed_greeting.rstrip(".!") + "! 🎉"

            # Replace some words with enthusiastic alternatives
            professional_to_enthusiastic = {
                "professional": "amazing",
                "your professional": "your awesome",
                "premier": "number 1",
                "How may I assist you?": "How can I help you today?!",
                "How may I assist you": "How can I help you",
            }

            for professional, enthusiastic in professional_to_enthusiastic.items():
                transformed_greeting = transformed_greeting.replace(professional, enthusiastic)

        # For FRIENDLY, keep as-is since it's already friendly
        # Just ensure there's one emoji if none present
        elif target_personality == PersonalityType.FRIENDLY:
            if not re.search(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]", transformed_greeting):
                transformed_greeting = transformed_greeting.rstrip(".!") + "! 👋"

    return MinimalEnvelope(
        data=GreetingTransformResponse(
            transformed_greeting=transformed_greeting,
            personality=target_personality,
            original_greeting=original_greeting,
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
