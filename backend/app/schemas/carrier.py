"""Carrier configuration schemas (Epic 6).

Pydantic models for carrier configuration CRUD operations and detection.
"""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.base import BaseSchema


class CarrierConfigBase(BaseSchema):
    """Base schema for carrier configuration."""

    carrier_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name of the carrier (e.g., 'LBC Express')",
    )
    tracking_url_template: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="URL template with {tracking_number} placeholder",
    )
    tracking_number_pattern: Optional[str] = Field(
        None,
        max_length=200,
        description="Optional regex pattern to auto-detect this carrier",
    )
    is_active: bool = Field(
        default=True,
        description="Whether this carrier config is active",
    )
    priority: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Detection priority (higher = checked first, 1-100)",
    )

    @field_validator("tracking_url_template")
    @classmethod
    def validate_url_template(cls, v: str) -> str:
        """Validate URL template has safe protocol and required placeholder."""
        if "{tracking_number}" not in v:
            raise ValueError("URL template must contain {tracking_number} placeholder")

        v_lower = v.lower().strip()
        if not (v_lower.startswith("http://") or v_lower.startswith("https://")):
            raise ValueError("URL template must use http:// or https:// protocol")

        dangerous_protocols = ["javascript:", "data:", "file:", "vbscript:"]
        for protocol in dangerous_protocols:
            if v_lower.startswith(protocol):
                raise ValueError(f"URL template cannot use {protocol} protocol")

        return v

    @field_validator("tracking_number_pattern")
    @classmethod
    def validate_regex_pattern(cls, v: Optional[str]) -> Optional[str]:
        """Validate regex pattern compiles and is not too complex."""
        if v is None:
            return v

        try:
            compiled = re.compile(v, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        pattern_lower = v.lower()
        dangerous_patterns = [
            r"(a+)+",
            r"(a*)*",
            r"(a|a)*",
            r"(a|a+)+",
            r"(\d+)+",
            r"(\w+)+",
            r"(.+)+",
        ]
        for dangerous in dangerous_patterns:
            if dangerous in pattern_lower:
                raise ValueError(
                    "Regex pattern contains dangerous nesting that could cause "
                    "performance issues (ReDoS vulnerability)"
                )

        if len(v) > 150:
            raise ValueError("Regex pattern too complex (max 150 characters)")

        return v


class CarrierConfigCreate(CarrierConfigBase):
    """Schema for creating a new carrier configuration."""

    pass


class CarrierConfigUpdate(BaseSchema):
    """Schema for updating an existing carrier configuration."""

    carrier_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
    )
    tracking_url_template: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
    )
    tracking_number_pattern: Optional[str] = Field(
        None,
        max_length=200,
    )
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=100)


class CarrierConfigResponse(CarrierConfigBase):
    """Schema for carrier configuration response."""

    id: int
    merchant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupportedCarrier(BaseSchema):
    """Information about a supported carrier."""

    name: str = Field(..., description="Carrier name")
    region: str = Field(..., description="Region (US, UK, PH, SEA, EU, etc.)")
    pattern: Optional[str] = Field(None, description="Tracking number regex pattern")
    tracking_url_template: str = Field(..., description="URL template for tracking")


class CarrierDetectionRequest(BaseSchema):
    """Request for carrier detection from tracking number."""

    tracking_number: str = Field(..., description="Tracking number to detect carrier for")
    merchant_id: Optional[int] = Field(None, description="Optional merchant ID for custom carriers")
    tracking_company: Optional[str] = Field(None, description="Optional carrier name from Shopify")


class CarrierDetectionResult(BaseSchema):
    """Result of carrier detection from tracking number."""

    carrier_name: Optional[str] = Field(None, description="Detected carrier name")
    tracking_url: Optional[str] = Field(None, description="Generated tracking URL")
    detection_method: str = Field(
        ...,
        description="How carrier was detected: custom, shopify, pattern, none",
    )
