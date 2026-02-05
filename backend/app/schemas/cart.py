"""Pydantic schemas for shopping cart.

Defines CartItem and Cart models with validation, camelCase aliases,
and automatic subtotal calculation.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field, field_validator
from pydantic.alias_generators import to_camel


class CurrencyCode(str, Enum):
    """ISO 4217 currency codes."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"


class CartItem(BaseModel):
    """Single item in shopping cart."""

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    product_id: str = Field(description="Shopify product ID")
    variant_id: str = Field(description="Shopify variant ID (unique identifier)")
    title: str = Field(description="Product title")
    price: float = Field(gt=0, description="Item price (must be positive)")
    image_url: str = Field(description="Product image URL")
    currency_code: CurrencyCode = Field(
        default=CurrencyCode.USD,
        description="Price currency code"
    )
    quantity: int = Field(
        ge=1,
        le=10,
        default=1,
        description="Item quantity (1-10)"
    )
    added_at: Optional[str] = Field(
        None,
        description="ISO timestamp when item was added"
    )

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        """Validate price is positive."""
        if v <= 0:
            raise ValueError("Price must be positive")
        return v


class Cart(BaseModel):
    """Shopping cart containing multiple items."""

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    items: List[CartItem] = Field(
        default_factory=list,
        description="Cart items"
    )
    subtotal: float = Field(
        default=0.0,
        ge=0,
        description="Subtotal of all items (sum of price * quantity)"
    )
    currency_code: CurrencyCode = Field(
        default=CurrencyCode.USD,
        description="Cart currency code"
    )
    created_at: Optional[str] = Field(
        None,
        description="ISO timestamp when cart was created"
    )
    updated_at: Optional[str] = Field(
        None,
        description="ISO timestamp when cart was last updated"
    )

    @computed_field  # type: ignore[misc]
    @property
    def item_count(self) -> int:
        """Calculate item count from items list."""
        return sum(item.quantity for item in self.items)

    @property
    def is_empty(self) -> bool:
        """Check if cart is empty."""
        return len(self.items) == 0
