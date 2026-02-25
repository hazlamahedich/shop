"""Pydantic schemas for Order responses (Story 4-13).

Defines order response models with payment breakdown and profit data.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.models.order import Order


class PaymentBreakdown(BaseModel):
    """Payment breakdown for an order."""

    subtotal: Decimal = Field(description="Order subtotal before shipping/tax")
    total: Decimal = Field(description="Order total including all charges")
    shipping: Optional[Decimal] = Field(None, description="Shipping cost")
    tax: Optional[Decimal] = Field(None, description="Tax amount")
    discount: Optional[Decimal] = Field(None, description="Total discount amount")
    discount_codes: Optional[list[dict[str, Any]]] = Field(
        None, description="Discount codes applied"
    )
    payment_method: Optional[str] = Field(None, description="Payment method used")
    currency: str = Field(default="USD", description="Currency code")


class ProfitData(BaseModel):
    """Profit/margin data for an order."""

    revenue: Decimal = Field(description="Total order revenue")
    cogs: Optional[Decimal] = Field(None, description="Cost of goods sold")
    margin: Optional[Decimal] = Field(None, description="Profit margin (revenue - cogs)")
    margin_percent: Optional[float] = Field(None, description="Profit margin as percentage")
    cogs_fetched_at: Optional[datetime] = Field(None, description="When COGS was last fetched")


class OrderResponse(BaseModel):
    """Full order response with payment breakdown and profit data."""

    id: int = Field(description="Order database ID")
    order_number: str = Field(description="Order number")
    status: str = Field(description="Order status")
    items: Optional[list[dict[str, Any]]] = Field(None, description="Order items")
    currency_code: str = Field(description="Currency code")

    customer_email: Optional[str] = Field(None, description="Customer email")
    customer_first_name: Optional[str] = Field(None, description="Customer first name")
    customer_last_name: Optional[str] = Field(None, description="Customer last name")

    tracking_number: Optional[str] = Field(None, description="Tracking number")
    tracking_url: Optional[str] = Field(None, description="Tracking URL")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery")

    payment_breakdown: PaymentBreakdown = Field(description="Payment breakdown")
    profit_data: Optional[ProfitData] = Field(None, description="Profit data")

    created_at: datetime = Field(description="Order creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        from_attributes = True

    @classmethod
    def from_order(cls, order: "Order") -> "OrderResponse":
        """Create OrderResponse from Order model instance.

        Args:
            order: Order model instance

        Returns:
            OrderResponse with payment breakdown and profit data
        """
        payment_breakdown = PaymentBreakdown(
            subtotal=order.subtotal,
            total=order.total,
            shipping=order.total_shipping,
            tax=order.total_tax,
            discount=order.total_discount,
            discount_codes=order.discount_codes if isinstance(order.discount_codes, list) else None,
            payment_method=order.payment_method,
            currency=order.currency_code,
        )

        profit_data = None
        if order.cogs_total is not None:
            margin = order.total - order.cogs_total
            margin_percent = float(margin / order.total * 100) if order.total else 0
            profit_data = ProfitData(
                revenue=order.total,
                cogs=order.cogs_total,
                margin=margin,
                margin_percent=round(margin_percent, 2),
                cogs_fetched_at=order.cogs_fetched_at,
            )

        return cls(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            items=order.items if isinstance(order.items, list) else None,
            currency_code=order.currency_code,
            customer_email=order.customer_email,
            customer_first_name=order.customer_first_name,
            customer_last_name=order.customer_last_name,
            tracking_number=order.tracking_number,
            tracking_url=order.tracking_url,
            estimated_delivery=order.estimated_delivery,
            payment_breakdown=payment_breakdown,
            profit_data=profit_data,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


class OrderListResponse(BaseModel):
    """List of orders response."""

    orders: list[OrderResponse] = Field(description="List of orders")
    total: int = Field(description="Total number of orders")
    page: int = Field(default=1, description="Current page")
    page_size: int = Field(default=20, description="Items per page")


class OrderSummary(BaseModel):
    """Minimal order summary for lists."""

    id: int
    order_number: str
    status: str
    total: Decimal
    currency_code: str
    created_at: datetime

    class Config:
        from_attributes = True
