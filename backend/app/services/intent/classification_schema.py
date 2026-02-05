"""Pydantic schemas for intent classification results.

Defines the data structures for intent classification, entity extraction,
and confidence scoring for natural language product discovery.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Supported intent types for product discovery."""

    PRODUCT_SEARCH = "product_search"
    GREETING = "greeting"
    CLARIFICATION = "clarification"
    CART_VIEW = "cart_view"
    CART_ADD = "cart_add"
    CHECKOUT = "checkout"
    ORDER_TRACKING = "order_tracking"
    HUMAN_HANDOFF = "human_handoff"
    FORGET_PREFERENCES = "forget_preferences"  # Story 2.7: Clear cart and data
    UNKNOWN = "unknown"


def to_camel(value: str) -> str:
    """Convert snake_case to camelCase for API compatibility.

    Args:
        value: snake_case string

    Returns:
        camelCase string
    """
    components = value.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class ExtractedEntities(BaseModel):
    """Entities extracted from user message."""

    category: Optional[str] = Field(None, description="Product category (e.g., 'shoes', 'electronics')")
    budget: Optional[float] = Field(None, description="Maximum budget in USD")
    budget_currency: str = Field("USD", description="Budget currency")
    size: Optional[str] = Field(None, description="Product size (e.g., '8', 'M', '42')")
    color: Optional[str] = Field(None, description="Preferred color")
    brand: Optional[str] = Field(None, description="Preferred brand")
    constraints: dict[str, Any] = Field(default_factory=dict, description="Additional constraints")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class ClassificationResult(BaseModel):
    """Result from LLM intent classification."""

    intent: IntentType = Field(description="Classified intent type")
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence score")
    entities: ExtractedEntities = Field(description="Extracted entities")
    raw_message: str = Field(description="Original user message")
    reasoning: Optional[str] = Field(None, description="Classification reasoning")
    llm_provider: str = Field(description="LLM provider used")
    model: str = Field(description="LLM model used")
    processing_time_ms: float = Field(description="Processing time in milliseconds")

    # Threshold for triggering clarification
    CLARIFICATION_THRESHOLD: float = 0.80

    @property
    def needs_clarification(self) -> bool:
        """Check if classification confidence is below threshold."""
        return self.confidence < self.CLARIFICATION_THRESHOLD

    class Config:
        alias_generator = to_camel
        populate_by_name = True
