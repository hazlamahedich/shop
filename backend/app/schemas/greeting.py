"""Pydantic schemas for greeting configuration (Story 1.14).

Provides request/response schemas for greeting config GET/PUT endpoints.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, validator

from app.models.merchant import PersonalityType
from app.schemas.base import MetaData


def serialize_personality(v: Optional[PersonalityType]) -> Optional[str]:
    """Serialize PersonalityType enum to string value."""
    if v is None:
        return None
    # Return the value, not the name
    return v.value


class GreetingConfigUpdate(BaseModel):
    """Request schema for updating greeting configuration.

    Story 1.14 AC 4: Greeting Template Customization

    Attributes:
        greeting_template: Optional custom greeting message
        use_custom_greeting: Boolean flag to enable custom greeting
    """
    greeting_template: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Custom greeting message (max 500 characters)",
    )
    use_custom_greeting: bool = Field(
        default=False,
        description="Use custom greeting instead of personality default",
    )


class GreetingConfigResponse(BaseModel):
    """Response schema for greeting configuration GET/PUT endpoints.

    Attributes:
        greeting_template: Current greeting template
        use_custom_greeting: Whether custom greeting is enabled
        personality: Current personality type
        default_template: Default greeting template for personality type
        available_variables: List of available placeholder variables
    """
    greeting_template: Optional[str] = Field(
        default=None,
        description="Current greeting template",
    )
    use_custom_greeting: Optional[bool] = Field(
        default=False,
        description="Whether custom greeting is enabled",
    )
    personality: Optional[PersonalityType] = Field(
        default=None,
        description="Current personality type",
        serializer=serialize_personality,
    )
    default_template: Optional[str] = Field(
        default=None,
        description="Default greeting template for personality type",
    )
    available_variables: list[str] = Field(
        default_factory=list,
        description="List of available placeholder variables",
    )


class GreetingEnvelope(BaseModel):
    """Minimal envelope wrapper for greeting config responses.

    Attributes:
        data: GreetingConfigResponse
        meta: Response metadata
    """
    data: GreetingConfigResponse
    meta: MetaData


__all__ = [
    "GreetingConfigUpdate",
    "GreetingConfigResponse",
    "GreetingEnvelope",
]
