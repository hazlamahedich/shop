"""Pydantic schemas for FAQ (Frequently Asked Questions) management.

Story 1.11: Business Info & FAQ Configuration

Provides request/response schemas for FAQ CRUD operations.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.schemas.base import BaseSchema, MinimalEnvelope, MetaData


class FaqRequest(BaseSchema):
    """Request schema for creating an FAQ item.

    Story 1.11 AC 3, 4, 7: FAQ item fields with validation.

    Attributes:
        question: FAQ question (max 200 chars, required)
        answer: FAQ answer (max 1000 chars, required)
        keywords: Comma-separated keywords (max 500 chars, optional)
        order_index: Display order (default 0)
    """

    question: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="FAQ question (max 200 characters, required)",
    )
    answer: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="FAQ answer (max 1000 characters, required)",
    )
    keywords: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Comma-separated keywords for matching (max 500 chars)",
    )
    order_index: int = Field(
        default=0,
        ge=0,
        description="Display order for FAQ items",
    )

    @field_validator("question", "answer", "keywords")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Strip leading/trailing whitespace from string fields.

        Args:
            v: The value to validate

        Returns:
            The stripped value or None if input was None/empty
        """
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


class FaqUpdateRequest(BaseSchema):
    """Request schema for updating an FAQ item.

    Story 1.11 AC 3, 4, 7: FAQ item fields with validation.

    All fields are optional for partial updates.

    Attributes:
        question: FAQ question (max 200 chars, optional)
        answer: FAQ answer (max 1000 chars, optional)
        keywords: Comma-separated keywords (max 500 chars, optional)
        order_index: Display order (optional)
    """

    question: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="FAQ question (max 200 characters, optional)",
    )
    answer: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=1000,
        description="FAQ answer (max 1000 characters, optional)",
    )
    keywords: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Comma-separated keywords for matching (max 500 chars)",
    )
    order_index: Optional[int] = Field(
        default=None,
        ge=0,
        description="Display order for FAQ items",
    )

    @field_validator("question", "answer", "keywords")
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Strip leading/trailing whitespace from string fields.

        Args:
            v: The value to validate

        Returns:
            The stripped value or None if input was None/empty
        """
        if v is None:
            return None
        stripped = v.strip()
        return stripped if stripped else None


class FaqResponse(BaseSchema):
    """Response schema for an FAQ item.

    Story 1.11 AC 2, 3, 7: FAQ item response fields.

    Attributes:
        id: FAQ item ID
        question: FAQ question
        answer: FAQ answer (truncated at 50 chars for preview)
        keywords: Comma-separated keywords
        order_index: Display order
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: int = Field(description="FAQ item ID")
    question: str = Field(description="FAQ question")
    answer: str = Field(description="FAQ answer")
    keywords: Optional[str] = Field(default=None, description="Comma-separated keywords")
    order_index: int = Field(description="Display order")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class FaqListEnvelope(MinimalEnvelope):
    """Minimal envelope for FAQ list responses.

    Story 1.11 AC 2, 7: Use MinimalEnvelope for FAQ list.

    Attributes:
        data: List of FAQ items
        meta: Response metadata
    """

    data: List[FaqResponse]


class FaqEnvelope(MinimalEnvelope):
    """Minimal envelope for single FAQ responses.

    Story 1.11 AC 7: Use MinimalEnvelope for single FAQ.

    Attributes:
        data: Single FAQ item
        meta: Response metadata
    """

    data: FaqResponse


class FaqReorderRequest(BaseSchema):
    """Request schema for reordering FAQ items.

    Story 1.11 AC 2, 7: FAQ reordering with drag-and-drop.

    Attributes:
        faq_ids: List of FAQ IDs in new order
    """

    faq_ids: List[int] = Field(
        ...,
        min_length=1,
        description="List of FAQ IDs in the desired display order",
    )


__all__ = [
    "FaqRequest",
    "FaqUpdateRequest",
    "FaqResponse",
    "FaqListEnvelope",
    "FaqEnvelope",
    "FaqReorderRequest",
]
