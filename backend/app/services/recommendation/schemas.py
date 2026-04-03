"""Recommendation data models for Story 11-6."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.schemas.shopify import Product


@dataclass
class RecommendationScore:
    """Score breakdown for a contextual recommendation."""

    product: Product
    total_score: float
    preference_score: float
    budget_score: float
    reason: str
    novelty_score: float = 0.0
    diversity_score: float = 0.0


class RecommendationResult(BaseModel):
    """Result of contextual recommendation generation."""

    recommendations: list[RecommendationScore] = Field(default_factory=list)
    empty: bool = Field(default=False)
    fallback_message: str = Field(default="")
    total_candidates: int = Field(default=0)
    filtered_out: int = Field(default=0)
