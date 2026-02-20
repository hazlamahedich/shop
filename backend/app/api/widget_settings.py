"""Widget settings API endpoints for merchant dashboard.

Provides endpoints for merchants to configure their embeddable widget:
- GET: Retrieve current widget configuration
- PATCH: Update widget configuration (partial update)

Story 5.6: Merchant Widget Settings UI
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.merchant import Merchant
from app.schemas.base import MinimalEnvelope, MetaData
from app.schemas.widget import (
    WidgetConfig,
    WidgetConfigResponse,
    WidgetConfigEnvelope,
    WidgetTheme,
)
from app.schemas.widget_settings import (
    WidgetConfigUpdateRequest,
    PartialWidgetTheme,
)


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
        if settings()["DEBUG"]:
            merchant_id_header = request.headers.get("X-Merchant-Id")
            if merchant_id_header:
                merchant_id = int(merchant_id_header)
            else:
                merchant_id = 1
        else:
            raise APIError(
                ErrorCode.AUTH_FAILED,
                "Authentication required",
            )
    return merchant_id


def _parse_widget_config(config: dict[str, Any] | None) -> WidgetConfig:
    """Parse widget config from merchant.config JSONB column.

    Args:
        config: Raw config dict from merchant.config

    Returns:
        WidgetConfig object with defaults applied
    """
    if not config or "widget_config" not in config:
        return WidgetConfig()

    widget_data = config.get("widget_config", {})
    theme_data = widget_data.get("theme", {})

    theme = WidgetTheme(
        primary_color=theme_data.get("primary_color", "#6366f1"),
        background_color=theme_data.get("background_color", "#ffffff"),
        text_color=theme_data.get("text_color", "#1f2937"),
        bot_bubble_color=theme_data.get("bot_bubble_color", "#f3f4f6"),
        user_bubble_color=theme_data.get("user_bubble_color", "#6366f1"),
        position=theme_data.get("position", "bottom-right"),
        border_radius=theme_data.get("border_radius", 16),
        width=theme_data.get("width", 380),
        height=theme_data.get("height", 600),
        font_family=theme_data.get("font_family", "Inter, sans-serif"),
        font_size=theme_data.get("font_size", 14),
    )

    return WidgetConfig(
        enabled=widget_data.get("enabled", True),
        bot_name=widget_data.get("bot_name", "Shopping Assistant"),
        welcome_message=widget_data.get("welcome_message", "Hi! How can I help you today?"),
        theme=theme,
        allowed_domains=widget_data.get("allowed_domains", []),
        rate_limit=widget_data.get("rate_limit"),
    )


def _merge_widget_config(
    current: dict[str, Any],
    update: WidgetConfigUpdateRequest,
) -> dict[str, Any]:
    """Merge partial update into current widget config.

    Args:
        current: Current merchant.config dict
        update: Partial update request

    Returns:
        Updated widget_config dict
    """
    widget_config = current.get("widget_config", {})

    if update.enabled is not None:
        widget_config["enabled"] = update.enabled

    if update.bot_name is not None:
        widget_config["bot_name"] = update.bot_name

    if update.welcome_message is not None:
        widget_config["welcome_message"] = update.welcome_message

    if update.theme is not None:
        theme = widget_config.get("theme", {})
        if update.theme.primary_color is not None:
            theme["primary_color"] = update.theme.primary_color
        if update.theme.position is not None:
            theme["position"] = update.theme.position
        widget_config["theme"] = theme

    return widget_config


@router.get(
    "/widget-config",
    response_model=WidgetConfigEnvelope,
)
async def get_widget_config(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> WidgetConfigEnvelope:
    """Get current widget configuration for the merchant.

    Returns the widget configuration stored in merchant.config JSONB column.
    If no config exists, returns default values.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        WidgetConfigEnvelope with current widget configuration

    Raises:
        APIError: If authentication fails or merchant not found
    """
    merchant_id = _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.WIDGET_SETTINGS_NOT_FOUND,
            f"Merchant with ID {merchant_id} not found",
        )

    widget_config = _parse_widget_config(merchant.config)

    logger.info(
        "widget_config_retrieved",
        merchant_id=merchant_id,
        enabled=widget_config.enabled,
    )

    return WidgetConfigEnvelope(
        data=WidgetConfigResponse(
            bot_name=widget_config.bot_name,
            welcome_message=widget_config.welcome_message,
            theme=widget_config.theme,
            enabled=widget_config.enabled,
        ),
        meta=_create_meta(),
    )


@router.patch(
    "/widget-config",
    response_model=WidgetConfigEnvelope,
)
async def update_widget_config(
    request: Request,
    update: WidgetConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> WidgetConfigEnvelope:
    """Update widget configuration (partial update).

    Allows merchants to update widget settings including:
    - enabled: Toggle widget on/off
    - bot_name: Display name for the bot
    - welcome_message: Initial greeting message
    - theme: Partial theme updates (primary_color, position)

    All fields are optional - only provided fields are updated.

    Args:
        request: FastAPI request with merchant authentication
        update: Partial widget configuration update
        db: Database session

    Returns:
        WidgetConfigEnvelope with updated widget configuration

    Raises:
        APIError: If authentication fails, merchant not found, or save fails
    """
    try:
        merchant_id = _get_merchant_id(request)

        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalars().first()

        if not merchant:
            raise APIError(
                ErrorCode.WIDGET_SETTINGS_NOT_FOUND,
                f"Merchant with ID {merchant_id} not found",
            )

        logger.info(
            "updating_widget_config",
            merchant_id=merchant_id,
            update_fields=update.model_dump(exclude_none=True),
        )

        current_config = merchant.config or {}
        new_widget_config = _merge_widget_config(current_config, update)

        new_config = dict(current_config)
        new_config["widget_config"] = new_widget_config

        merchant.config = new_config

        try:
            await db.commit()
            await db.refresh(merchant)
        except Exception as e:
            await db.rollback()
            logger.error("widget_config_save_failed", error=str(e))
            raise APIError(
                ErrorCode.WIDGET_SETTINGS_SAVE_FAILED,
                f"Failed to save widget configuration: {str(e)}",
            )

        widget_config = _parse_widget_config(merchant.config)

        logger.info(
            "widget_config_updated",
            merchant_id=merchant_id,
            enabled=widget_config.enabled,
            bot_name=widget_config.bot_name,
        )

        return WidgetConfigEnvelope(
            data=WidgetConfigResponse(
                bot_name=widget_config.bot_name,
                welcome_message=widget_config.welcome_message,
                theme=widget_config.theme,
                enabled=widget_config.enabled,
            ),
            meta=_create_meta(),
        )
    except APIError:
        raise
    except Exception as e:
        logger.error("update_widget_config_failed", error=str(e))
        raise APIError(
            ErrorCode.WIDGET_SETTINGS_SAVE_FAILED,
            f"Failed to update widget configuration: {str(e)}",
        )
