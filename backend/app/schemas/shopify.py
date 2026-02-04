from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CurrencyCode(str, Enum):
    """ISO 4217 currency codes."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"


class ProductVariant(BaseModel):
    """Product variant from Shopify."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str = Field(description="Shopify variant ID")
    product_id: str = Field(description="Parent product ID")
    title: str = Field(description="Variant title (e.g., 'Size 8, Red')")
    price: float = Field(description="Variant price")
    currency_code: CurrencyCode = Field(
        default=CurrencyCode.USD,
        description="Price currency code"
    )
    available_for_sale: bool = Field(default=False, description="Is variant in stock")
    selected_options: Dict[str, str] = Field(
        default_factory=dict, description="Variant options (size, color, etc.)"
    )
    weight: Optional[float] = Field(None, description="Variant weight in grams")
    weight_unit: Optional[str] = Field(None, description="Weight unit (e.g., 'g')")


class ProductImage(BaseModel):
    """Product image from Shopify."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    url: str = Field(description="Image URL")
    alt_text: Optional[str] = Field(None, description="Image alt text")
    width: Optional[int] = Field(None, description="Image width in pixels")
    height: Optional[int] = Field(None, description="Image height in pixels")


class Product(BaseModel):
    """Product from Shopify Storefront API."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: str = Field(description="Shopify product ID")
    title: str = Field(description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    description_html: Optional[str] = Field(None, description="Product description HTML")
    product_type: str = Field(description="Product type/category")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    vendor: Optional[str] = Field(None, description="Product vendor/brand")
    price: float = Field(description="Product price (min variant price)")
    currency_code: CurrencyCode = Field(
        default=CurrencyCode.USD,
        description="Price currency code"
    )
    images: List[ProductImage] = Field(
        default_factory=list,
        description="Product images"
    )
    variants: List[ProductVariant] = Field(
        default_factory=list,
        description="Product variants"
    )
    relevance_score: float = Field(
        default=0.0,
        description="Search relevance score"
    )
    total_inventory: Optional[int] = Field(None, description="Total inventory across variants")
    tracks_inventory: bool = Field(default=True, description="Whether inventory is tracked")


class ProductSearchResult(BaseModel):
    """Result from product search operation."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    products: List[Product] = Field(description="Ranked product results")
    total_count: int = Field(description="Total results count")
    search_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Search parameters used"
    )
    has_alternatives: bool = Field(
        default=False,
        description="Whether alternative suggestions are available"
    )
    search_time_ms: Optional[float] = Field(None, description="Search time in milliseconds")
