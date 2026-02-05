"""Pydantic schemas for order confirmation (Story 2.9).

Defines order data models and confirmation status.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ConfirmationStatus(str, Enum):
    """Order confirmation status."""

    CONFIRMED = "confirmed"
    SKIPPED = "skipped"
    FAILED = "failed"


class OrderConfirmationRequest(BaseModel):
    """Request for order confirmation processing."""

    order_id: str = Field(description="Shopify order ID")
    order_number: int = Field(description="Shopify order number")
    order_url: str = Field(description="Shopify order URL")
    financial_status: str = Field(description="Order financial status (paid, pending, etc.)")
    customer_email: Optional[str] = Field(None, description="Customer email")
    psid: Optional[str] = Field(None, description="Facebook PSID from order attributes")
    created_at: str = Field(description="Order creation timestamp (ISO-8601)")
    note_attributes: Optional[list[dict[str, str]]] = Field(
        default_factory=list,
        description="Order note attributes for PSID lookup"
    )
    attributes: Optional[list[dict[str, str]]] = Field(
        default_factory=list,
        description="Order attributes for PSID lookup (GraphQL/Plus)"
    )


class OrderConfirmationResult(BaseModel):
    """Result from order confirmation processing."""

    status: ConfirmationStatus = Field(description="Confirmation status")
    order_id: str = Field(description="Shopify order ID")
    order_number: int = Field(description="Shopify order number")
    psid: Optional[str] = Field(None, description="Facebook PSID")
    message: str = Field(description="User-facing message")
    cart_cleared: bool = Field(default=False, description="Whether cart was cleared")
    confirmed_at: Optional[str] = Field(None, description="Confirmation timestamp (ISO-8601)")

    class Config:
        use_enum_values = True


class OrderReference(BaseModel):
    """Order reference stored in Redis for tracking (Story 2.9)."""

    order_id: str = Field(description="Shopify order ID")
    order_number: int = Field(description="Shopify order number")
    order_url: str = Field(description="Shopify order URL")
    psid: str = Field(description="Facebook PSID")
    financial_status: str = Field(description="Order financial status")
    created_at: str = Field(description="Order creation timestamp")
    confirmed_at: str = Field(description="Order confirmation timestamp")

    @field_validator("created_at", "confirmed_at", mode="before")
    @classmethod
    def parse_datetime(cls, v: Any) -> str:
        """Validate datetime fields are ISO-8601 strings."""
        if isinstance(v, datetime):
            return v.isoformat()
        if isinstance(v, str):
            # Basic ISO-8601 validation
            return v
        raise ValueError("DateTime must be ISO-8601 string or datetime object")
