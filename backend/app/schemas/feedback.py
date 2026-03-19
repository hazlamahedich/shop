"""Feedback schemas for API request/response validation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""

    message_id: int = Field(alias="messageId", description="ID of the message being rated")
    conversation_id: Optional[int] = Field(
        default=None,
        alias="conversationId",
        description="ID of the conversation (optional, looked up from message if not provided)",
    )
    rating: str = Field(description="Rating value: 'positive' or 'negative'")
    comment: Optional[str] = Field(
        default=None, max_length=500, description="Optional comment for negative feedback"
    )
    session_id: str = Field(alias="sessionId", description="Widget session ID")

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: str) -> str:
        if v not in ("positive", "negative"):
            raise ValueError("Rating must be 'positive' or 'negative'")
        return v

    class Config:
        populate_by_name = True


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""

    id: int
    message_id: int = Field(alias="messageId")
    rating: str
    comment: Optional[str] = None
    created_at: datetime = Field(alias="createdAt")

    class Config:
        populate_by_name = True
        from_attributes = True


class FeedbackAnalyticsResponse(BaseModel):
    """Schema for feedback analytics response."""

    total_ratings: int = Field(alias="totalRatings")
    positive_count: int = Field(alias="positiveCount")
    negative_count: int = Field(alias="negativeCount")
    positive_percent: float = Field(alias="positivePercent")
    negative_percent: float = Field(alias="negativePercent")
    recent_negative: list[RecentNegativeFeedback] = Field(
        alias="recentNegative", default_factory=list
    )
    trend: list[DailyFeedbackTrend] = Field(default_factory=list)

    class Config:
        populate_by_name = True


class RecentNegativeFeedback(BaseModel):
    """Schema for recent negative feedback item."""

    message_id: int = Field(alias="messageId")
    comment: Optional[str] = None
    created_at: datetime = Field(alias="createdAt")

    class Config:
        populate_by_name = True
        from_attributes = True


class DailyFeedbackTrend(BaseModel):
    """Schema for daily feedback trend."""

    date: str
    positive: int
    negative: int
