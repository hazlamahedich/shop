"""Authentication schemas for request/response validation.

Story: Merchant Registration
Pydantic models for registration endpoint.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Registration request schema."""

    email: EmailStr = Field(..., description="Merchant email address")
    password: str = Field(
        ...,
        min_length=8,
        description="Merchant password (min 8 chars, uppercase, lowercase)",
    )
    business_name: Optional[str] = Field(
        None,
        alias="businessName",
        description="Business name",
    )
    mode: Optional[str] = Field(
        "general",
        pattern="^(general|ecommerce)$",
        description="Onboarding mode: 'general' for chatbot-only, 'ecommerce' for shopping",
    )
