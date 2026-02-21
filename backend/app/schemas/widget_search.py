"""Widget search schemas for product search API.

Story 5-10: Widget Full App Integration
Task 4: Add Product Search API

Provides request/response schemas for widget product search.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseSchema, MinimalEnvelope, MetaData


class WidgetSearchRequest(BaseSchema):
    """Request for widget product search.

    Attributes:
        session_id: Widget session identifier
        query: Search query text
    """

    session_id: str = Field(description="Widget session identifier")
    query: str = Field(min_length=1, max_length=200, description="Search query")


class ProductSummary(BaseSchema):
    """Summary of a product for search results.

    Attributes:
        product_id: Shopify product ID
        variant_id: Default variant ID for cart operations
        title: Product title
        price: Price as float
        currency: Currency code (USD, EUR, etc.)
        image_url: Product image URL
        available: Whether product is in stock
        relevance_score: Search relevance score (optional)
    """

    product_id: str = Field(description="Shopify product ID")
    variant_id: str = Field(description="Default variant ID for cart operations")
    title: str = Field(description="Product title")
    price: float = Field(description="Price as float")
    currency: str = Field(default="USD", description="Currency code")
    image_url: Optional[str] = Field(default=None, description="Product image URL")
    available: bool = Field(default=True, description="Whether product is in stock")
    relevance_score: Optional[float] = Field(default=None, description="Search relevance score")


class WidgetSearchResult(BaseSchema):
    """Response data for widget product search.

    Attributes:
        products: List of matching products
        total_count: Total number of matching products
        search_time_ms: Search processing time in milliseconds
        alternatives_available: Whether alternative products exist
    """

    products: list[ProductSummary] = Field(
        default_factory=list, description="List of matching products"
    )
    total_count: int = Field(default=0, description="Total matching products")
    search_time_ms: float = Field(description="Search time in milliseconds")
    alternatives_available: bool = Field(default=False, description="Whether alternatives exist")


class WidgetSearchEnvelope(MinimalEnvelope):
    """Envelope for search response."""

    data: WidgetSearchResult


class WidgetCartRequest(BaseSchema):
    """Request to modify widget cart.

    Attributes:
        session_id: Widget session identifier
        variant_id: Product variant ID to add/remove
        quantity: Quantity to add (default 1)
    """

    session_id: str = Field(description="Widget session identifier")
    variant_id: str = Field(description="Product variant ID")
    title: str = Field(default="Product", description="Product title")
    price: float = Field(default=1.0, gt=0, description="Product price")
    image_url: Optional[str] = Field(default=None, description="Product image URL")
    quantity: int = Field(default=1, ge=1, le=10, description="Quantity to add")


class WidgetCartUpdateRequest(BaseSchema):
    """Request to update cart item quantity.

    Attributes:
        session_id: Widget session identifier
        quantity: New quantity (1-10)
    """

    session_id: str = Field(description="Widget session identifier")
    quantity: int = Field(ge=1, le=10, description="New quantity (1-10)")


class WidgetCartItem(BaseSchema):
    """Item in widget cart.

    Attributes:
        variant_id: Product variant ID
        title: Product title
        price: Price per unit
        quantity: Quantity in cart
    """

    variant_id: str = Field(description="Product variant ID")
    title: str = Field(description="Product title")
    price: float = Field(description="Price per unit")
    quantity: int = Field(description="Quantity in cart")


class WidgetCartResponse(BaseSchema):
    """Response for widget cart.

    Attributes:
        items: List of cart items
        subtotal: Cart subtotal
        currency: Currency code
        item_count: Total number of items
    """

    items: list[WidgetCartItem] = Field(default_factory=list, description="Cart items")
    subtotal: float = Field(default=0.0, description="Cart subtotal")
    currency: str = Field(default="USD", description="Currency code")
    item_count: int = Field(default=0, description="Total item count")


class WidgetCartEnvelope(MinimalEnvelope):
    """Envelope for cart response."""

    data: WidgetCartResponse


class WidgetCheckoutRequest(BaseSchema):
    """Request for widget checkout.

    Attributes:
        session_id: Widget session identifier
    """

    session_id: str = Field(description="Widget session identifier")


class WidgetCheckoutResponse(BaseSchema):
    """Response for widget checkout.

    Attributes:
        checkout_url: Shopify checkout URL
        cart_total: Cart total amount
        currency: Currency code
        item_count: Number of items in cart
        expires_at: Checkout expiration time (optional)
    """

    checkout_url: str = Field(description="Shopify checkout URL")
    cart_total: float = Field(description="Cart total amount")
    currency: str = Field(default="USD", description="Currency code")
    item_count: int = Field(description="Number of items in cart")
    expires_at: Optional[datetime] = Field(default=None, description="Checkout expiration time")


class WidgetCheckoutEnvelope(MinimalEnvelope):
    """Envelope for checkout response."""

    data: WidgetCheckoutResponse
