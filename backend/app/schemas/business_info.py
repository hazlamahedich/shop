"""Pydantic schemas for Business Info configuration.

Story 1.11: Business Info & FAQ Configuration

Provides request/response schemas for business information CRUD operations.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.base import BaseSchema, MinimalEnvelope, MetaData


class BusinessInfoRequest(BaseSchema):
    """Request schema for updating business information.

    Story 1.11 AC 1, 4, 7: Business info fields with validation.

    Attributes:
        business_name: Business name (max 100 chars, optional)
        business_description: Business description (max 500 chars, optional)
        business_hours: Business hours (max 200 chars, optional)
    """

    business_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Business name (max 100 characters)",
    )
    business_description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Business description (max 500 characters)",
    )
    business_hours: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Business hours (e.g., '9 AM - 6 PM PST, Mon-Fri')",
    )

    @field_validator("business_name", "business_description", "business_hours")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Strip leading/trailing whitespace from string fields.

        Args:
            v: The value to validate

        Returns:
            The stripped value or None if input was None/empty
        """
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


class BusinessInfoResponse(BaseSchema):
    """Response schema for business information.

    Story 1.11 AC 1, 7: Business info response fields.

    Attributes:
        business_name: Business name
        business_description: Business description
        business_hours: Business hours
    """

    business_name: Optional[str] = Field(
        default=None,
        description="Business name",
    )
    business_description: Optional[str] = Field(
        default=None,
        description="Business description",
    )
    business_hours: Optional[str] = Field(
        default=None,
        description="Business hours",
    )


class BusinessInfoEnvelope(MinimalEnvelope):
    """Minimal envelope for business info responses.

    Story 1.11 AC 7: Use MinimalEnvelope response format.

    Attributes:
        data: Business info response
        meta: Response metadata
    """

    data: BusinessInfoResponse


__all__ = [
    "BusinessInfoRequest",
    "BusinessInfoResponse",
    "BusinessInfoEnvelope",
]
