"""Widget settings schemas for merchant dashboard UI.

Provides partial update schemas for the widget configuration UI.
Story 5.6: Merchant Widget Settings UI
Story 10-2: FAQ Quick Buttons Configuration
Story 10-5: Contact Options Configuration
"""

from __future__ import annotations

from pydantic import Field

from app.schemas.base import BaseSchema
from app.schemas.widget import ContactOptionSchema


class PartialWidgetTheme(BaseSchema):
    """Partial theme update for settings UI.

    Only includes fields exposed in the settings UI:
    - primary_color: Main brand color
    - position: Widget position on page
    """

    primary_color: str | None = Field(
        None,
        pattern=r"^#[0-9a-fA-F]{6}$",
        description="Primary brand color in hex format (#RRGGBB)",
    )
    position: str | None = Field(
        None,
        pattern=r"^(bottom-right|bottom-left)$",
        description="Widget position on page",
    )


class FAQQuickButtonsConfigUpdate(BaseSchema):
    """FAQ quick buttons configuration update.

    Story 10-2: AC5 Merchant Configuration UI

    Attributes:
        enabled: Whether FAQ quick buttons are enabled
        faq_ids: List of FAQ IDs to show as quick buttons (max 5)
    """

    enabled: bool | None = Field(
        None,
        description="Whether FAQ quick buttons are enabled",
    )
    faq_ids: list[int] | None = Field(
        None,
        max_length=5,
        description="List of FAQ IDs to show as quick buttons (max 5)",
    )


class WidgetConfigUpdateRequest(BaseSchema):
    """Request for partial widget config update.

    All fields are optional - only provided fields are updated.
    This allows granular updates without sending full config.

    Story 10-4: Added feedback_enabled for feedback rating toggle.
    """

    enabled: bool | None = Field(
        None,
        description="Whether widget is enabled",
    )
    bot_name: str | None = Field(
        None,
        max_length=50,
        description="Display name for the bot (max 50 chars)",
    )
    welcome_message: str | None = Field(
        None,
        max_length=500,
        description="Initial greeting message (max 500 chars)",
    )
    theme: PartialWidgetTheme | None = Field(
        None,
        description="Partial theme update",
    )
    faq_quick_buttons: FAQQuickButtonsConfigUpdate | None = Field(
        None,
        description="FAQ quick buttons configuration (Story 10-2)",
    )
    feedback_enabled: bool | None = Field(
        None,
        description="Whether feedback rating collection is enabled (Story 10-4)",
    )
    contact_options: list[ContactOptionSchema] | None = Field(
        None,
        description="Contact options for escalation (Story 10-5)",
    )
