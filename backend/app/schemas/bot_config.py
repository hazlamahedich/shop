"""Pydantic schemas for Bot configuration.

Story 1.12: Bot Naming

Provides request/response schemas for bot configuration CRUD operations.
"""

from __future__ import annotations

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, MinimalEnvelope


class BotNameUpdate(BaseSchema):
    """Request schema for updating bot name.

    Story 1.12 AC 2: Bot name validation and persistence.

    Attributes:
        bot_name: Custom bot name (max 50 chars, optional)
    """

    bot_name: str | None = Field(
        default=None,
        max_length=50,
        description="Custom bot name that appears in all bot messages (max 50 characters)",
    )

    @field_validator("bot_name")
    @classmethod
    def strip_whitespace(cls, v: str | None) -> str | None:
        """Strip leading/trailing whitespace from bot name.

        Args:
            v: The value to validate

        Returns:
            The stripped value or None if input was None/empty
        """
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


class BotConfigResponse(BaseSchema):
    """Response schema for bot configuration.

    Story 1.12 AC 1, 4: Bot configuration response fields.

    Attributes:
        bot_name: Custom bot name
        personality: Bot personality type
        custom_greeting: Custom greeting message
    """

    bot_name: str | None = Field(
        default=None,
        description="Custom bot name",
    )
    personality: str | None = Field(
        default=None,
        description="Bot personality type",
    )
    custom_greeting: str | None = Field(
        default=None,
        description="Custom greeting message",
    )


class BotConfigEnvelope(MinimalEnvelope):
    """Minimal envelope for bot config responses.

    Story 1.12 AC 5: Use MinimalEnvelope response format.

    Attributes:
        data: Bot config response
        meta: Response metadata
    """

    data: BotConfigResponse


__all__ = [
    "BotNameUpdate",
    "BotConfigResponse",
    "BotConfigEnvelope",
]
