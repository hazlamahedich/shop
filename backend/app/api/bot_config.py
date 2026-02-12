"""Bot configuration API endpoints.

Story 1.12: Bot Naming
Story 1.14: Smart Greeting Templates

Provides endpoints for:
- Getting bot configuration (including bot name)
- Updating bot configuration (bot name)
- Getting/Updating greeting configuration
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.merchant import Merchant
from app.schemas.bot_config import (
    BotNameUpdate,
    BotConfigResponse,
    BotConfigEnvelope,
)
from app.schemas.greeting import (
    GreetingConfigUpdate,
    GreetingConfigResponse,
    GreetingEnvelope,
)
from app.api.helpers import create_meta, get_merchant_id, verify_merchant_exists
from app.services.personality.greeting_service import (
    get_default_greeting,
    substitute_greeting_variables,
)


logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get(
    "/bot-config",
    response_model=BotConfigEnvelope,
)
async def get_bot_config(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> BotConfigEnvelope:
    """
    Get bot configuration.

    Returns current merchant's bot configuration including
    bot name, personality type, and custom greeting.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        BotConfigEnvelope with bot configuration

    Raises:
        APIError: If authentication fails or merchant not found
    """
    merchant_id = get_merchant_id(request)

    merchant = await verify_merchant_exists(merchant_id, db)

    return BotConfigEnvelope(
        data=BotConfigResponse(
            bot_name=merchant.bot_name,
            personality=merchant.personality.value if merchant.personality else None,
            custom_greeting=merchant.custom_greeting,
        ),
        meta=create_meta(),
    )


@router.get(
    "/greeting-config",
    response_model=GreetingEnvelope,
)
async def get_greeting_config(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> GreetingEnvelope:
    """
    Get greeting configuration.

    Returns current merchant's greeting configuration including
    greeting template, custom greeting flag, personality type,
    default template for personality, and available variables.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        GreetingEnvelope with greeting configuration

    Raises:
        APIError: If authentication fails or merchant not found
    """
    merchant_id = get_merchant_id(request)

    merchant = await verify_merchant_exists(merchant_id, db)

    personality = merchant.personality if merchant else None
    default_template = get_default_greeting(personality) if personality else None

    return GreetingEnvelope(
        data=GreetingConfigResponse(
            greeting_template=merchant.custom_greeting,
            use_custom_greeting=merchant.use_custom_greeting,
            personality=personality.value if personality else None,
            default_template=default_template,
            available_variables=["bot_name", "business_name", "business_hours"],
        ),
        meta=create_meta(),
    )


@router.put(
    "/greeting-config",
    response_model=GreetingEnvelope,
)
async def update_greeting_config(
    request: Request,
    update: GreetingConfigUpdate,
    db: AsyncSession = Depends(get_db),
) -> GreetingEnvelope:
    """
    Update greeting configuration.

    Allows merchants to update their greeting template and
    enable/disable custom greeting.

    NOTE: CSRF protection is provided by CSRFMiddleware (see main.py:164).
    All PUT requests automatically require valid CSRF tokens unless path
    is in BYPASS_PATHS. The /api/v1/merchant/greeting-config path
    is NOT in bypass list, so it is protected by default.

    NOTE: Authentication in DEBUG mode uses X-Merchant-Id header for
    convenience. In production, proper JWT authentication should be used.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session
        update: Greeting configuration update data

    Returns:
        GreetingEnvelope with updated greeting configuration

    Raises:
        APIError: If authentication fails or merchant not found, or validation fails
    """
    merchant_id = get_merchant_id(request)

    merchant = await verify_merchant_exists(merchant_id, db)

    logger.info(
        "updating_greeting_config",
        merchant_id=merchant_id,
        has_template=update.greeting_template is not None,
        use_custom=update.use_custom_greeting,
    )

    # Validate greeting template if provided
    if update.greeting_template is not None:
        template = update.greeting_template.strip()
        # Check if empty after stripping
        if not template:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                "Greeting template cannot be empty",
            )
        # Check max length
        if len(template) > 500:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                "Greeting template must be less than 500 characters",
            )

    provided_fields = update.model_fields_set
    if "greeting_template" in provided_fields:
        merchant.custom_greeting = update.greeting_template
    if "use_custom_greeting" in provided_fields:
        merchant.use_custom_greeting = update.use_custom_greeting

    # Commit changes with error handling
    try:
        await db.commit()
        await db.refresh(merchant)
    except Exception as e:
        await db.rollback()
        logger.error(
            "update_greeting_config_failed",
            merchant_id=merchant_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to update greeting configuration: {str(e)}",
        )

    logger.info(
        "greeting_config_updated",
        merchant_id=merchant_id,
        use_custom_greeting=merchant.use_custom_greeting,
    )

    personality = merchant.personality if merchant else None
    default_template = get_default_greeting(personality) if personality else None

    return GreetingEnvelope(
        data=GreetingConfigResponse(
            greeting_template=merchant.custom_greeting,
            use_custom_greeting=merchant.use_custom_greeting,
            personality=personality.value if personality else None,
            default_template=default_template,
            available_variables=["bot_name", "business_name", "business_hours"],
        ),
        meta=create_meta(),
    )


@router.put(
    "/bot-config",
    response_model=BotConfigEnvelope,
)
async def update_bot_config(
    request: Request,
    update: BotNameUpdate,
    db: AsyncSession = Depends(get_db),
) -> BotConfigEnvelope:
    """
    Update bot configuration.

    Allows merchants to update their bot name.
    The bot_name field is optional - empty string clears bot name.

    NOTE: CSRF protection is provided by CSRFMiddleware (see main.py:164).
    All PUT requests automatically require valid CSRF tokens unless path
    is in BYPASS_PATHS. The /api/v1/merchant/bot-config path is NOT in
    bypass list, so it is protected by default.

    NOTE: Authentication in DEBUG mode uses X-Merchant-Id header for
    convenience. In production, proper JWT authentication should be used.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session
        update: Bot name update data

    Returns:
        BotConfigEnvelope with updated bot configuration

    Raises:
        APIError: If authentication fails or merchant not found
    """
    merchant_id = get_merchant_id(request)

    merchant = await verify_merchant_exists(merchant_id, db)

    logger.info(
        "updating_bot_config",
        merchant_id=merchant_id,
        has_bot_name=update.bot_name is not None,
    )

    # Update bot_name if provided (None means clear the field)
    # We use model_fields_set to track which fields were explicitly provided
    provided_fields = update.model_fields_set
    if "bot_name" in provided_fields:
        merchant.bot_name = update.bot_name

    # Commit changes with error handling
    try:
        await db.commit()
        await db.refresh(merchant)
    except Exception as e:
        await db.rollback()
        logger.error(
            "update_bot_config_failed",
            merchant_id=merchant_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to update bot configuration: {str(e)}",
        )

    logger.info(
        "bot_config_updated",
        merchant_id=merchant_id,
        bot_name=merchant.bot_name,
    )

    return BotConfigEnvelope(
        data=BotConfigResponse(
            bot_name=merchant.bot_name,
            personality=merchant.personality.value if merchant.personality else None,
            custom_greeting=merchant.custom_greeting,
        ),
        meta=create_meta(),
    )
