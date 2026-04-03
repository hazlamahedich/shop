"""Recommendation data models for Story 11-6."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.shopify import Product


class RecommendationScore(BaseModel):
    """Score breakdown for a contextual recommendation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

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
