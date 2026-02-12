"""Pydantic schemas for Product Pin API.

Story 1.15: Product Highlight Pins

Provides request/response schemas for product pin CRUD operations.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.base import BaseSchema, MinimalEnvelope, MetaData


class ProductPinRequest(BaseSchema):
    """Request schema for pinning a product.

    Story 1.15 AC 2: Pin and Unpin Products.

    Attributes:
        product_id: Shopify product ID to pin
    """
    product_id: str = Field(
        default=...,
        min_length=1,
        max_length=255,
        description="Shopify product ID to pin",
    )

    @field_validator("product_id")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip whitespace from product ID."""
        return v.strip() if v else v

    class Config:
        # Use camelCase for API
        alias_generator = BaseSchema.model_config["alias_generator"]
        populate_by_name = True


class ReorderPinsRequest(BaseSchema):
    """Request schema for reordering pinned products.

    Story 1.15 AC 1: Pin Products List Management.
    """
    product_orders: list[dict[str, int]] = Field(
        default=...,
        min_length=1,
        description="List of product IDs with their new order values",
    )

    class Config:
        alias_generator = BaseSchema.model_config["alias_generator"]
        populate_by_name = True


class ProductPinItem(BaseSchema):
    """Single product item in pin list response.

    Story 1.15 AC 1: Pin Products List Management.
    """
    product_id: str = Field(
        default=...,
        description="Shopify product ID",
    )
    title: str = Field(
        default=...,
        description="Product title",
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Product image URL",
    )
    is_pinned: bool = Field(
        default=False,
        description="Whether product is pinned",
    )
    pinned_order: Optional[int] = Field(
        default=None,
        description="Order priority (1-10) for pinned products",
    )
    pinned_at: Optional[str] = Field(
        default=None,
        description="ISO-8601 timestamp when product was pinned",
    )


class ProductListResponse(BaseSchema):
    """Response schema for product list with pin status.

    Story 1.15 AC 1: Pin Products List Management.

    Attributes:
        products: List of products with pin status
        pagination: Pagination metadata
        pin_limit: Maximum pinned products allowed
        pinned_count: Current number of pinned products
    """
    products: list[ProductPinItem] = Field(
        default=[],
        description="List of products with pin status",
    )
    pagination: Optional["PaginationMeta"] = Field(
        default=None,
        description="Pagination metadata (page, limit, total, has_more)",
    )
    pin_limit: int = Field(
        default=10,
        description="Maximum number of products that can be pinned",
    )
    pinned_count: int = Field(
        default=0,
        description="Current number of pinned products",
    )


class PaginationMeta(BaseSchema):
    """Pagination metadata for product list.

    Story 1.15 AC 1: Pin Products List Management.
    """
    page: int = Field(
        default=1,
        description="Current page number",
    )
    limit: int = Field(
        default=20,
        description="Items per page",
    )
    total: int = Field(
        default=0,
        description="Total number of products",
    )
    has_more: bool = Field(
        default=False,
        description="Whether more products are available",
    )


class ProductPinEnvelope(MinimalEnvelope):
    """Minimal envelope for product pin responses.

    Story 1.15 AC 1: Pin Products List Management.

    Uses Minimal Envelope pattern for consistent API responses.
    """
    data: ProductListResponse

    class Config:
        # Use camelCase for API
        alias_generator = BaseSchema.model_config["alias_generator"]
        populate_by_name = True


class ProductPinResponse(BaseSchema):
    """Response schema for single product pin operation.

    Story 1.15 AC 2: Pin and Unpin Products.
    """
    product_id: str = Field(
        default=...,
        description="Shopify product ID",
    )
    is_pinned: bool = Field(
        default=False,
        description="Updated pin status",
    )
    pinned_order: Optional[int] = Field(
        default=None,
        description="Assigned order priority (1-10)",
    )
    pinned_at: Optional[str] = Field(
        default=None,
        description="ISO-8601 timestamp when product was pinned",
    )


class ProductPinDetailEnvelope(MinimalEnvelope):
    """Minimal envelope for single product pin response.

    Story 1.15 AC 2: Pin and Unpin Products.
    """
    data: ProductPinResponse


__all__ = [
    "ProductPinRequest",
    "ReorderPinsRequest",
    "ProductPinItem",
    "ProductListResponse",
    "PaginationMeta",
    "ProductPinEnvelope",
    "ProductPinDetailEnvelope",
    "ProductPinResponse",
]
