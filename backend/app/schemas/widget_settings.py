"""Widget settings schemas for merchant dashboard UI.

Provides partial update schemas for the widget configuration UI.
Story 5.6: Merchant Widget Settings UI
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from app.schemas.base import BaseSchema


class PartialWidgetTheme(BaseSchema):
    """Partial theme update for settings UI.

    Only includes fields exposed in the settings UI:
    - primary_color: Main brand color
    - position: Widget position on page
    """

    primary_color: Optional[str] = Field(
        None,
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Primary brand color in hex format (#RRGGBB)",
    )
    position: Optional[str] = Field(
        None,
        pattern=r"^(bottom-right|bottom-left)$",
        description="Widget position on page",
    )


class WidgetConfigUpdateRequest(BaseSchema):
    """Request for partial widget config update.

    All fields are optional - only provided fields are updated.
    This allows granular updates without sending full config.
    """

    enabled: Optional[bool] = Field(
        None,
        description="Whether widget is enabled",
    )
    bot_name: Optional[str] = Field(
        None,
        max_length=50,
        description="Display name for the bot (max 50 chars)",
    )
    welcome_message: Optional[str] = Field(
        None,
        max_length=500,
        description="Initial greeting message (max 500 chars)",
    )
    theme: Optional[PartialWidgetTheme] = Field(
        None,
        description="Partial theme update",
    )
