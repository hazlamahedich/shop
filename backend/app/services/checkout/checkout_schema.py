"""Pydantic schemas for checkout URL generation.

Defines CheckoutStatus enum and checkout-related data structures.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class CheckoutStatus(str, Enum):
    """Checkout generation status."""

    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    EMPTY_CART = "empty_cart"


class CheckoutResult(BaseModel):
    """Result from checkout URL generation."""

    status: CheckoutStatus = Field(description="Checkout generation status")
    checkout_url: Optional[str] = Field(None, description="Generated checkout URL")
    checkout_token: Optional[str] = Field(None, description="Checkout token for order confirmation")
    message: str = Field(description="User-facing message")
    retry_count: int = Field(default=0, description="Number of retry attempts made")

    class Config:
        use_enum_values = True
