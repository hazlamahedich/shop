"""Budget Alert schemas for API requests/responses.

Provides Pydantic models for budget alert notifications.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BudgetAlertResponse(BaseModel):
    """Response schema for a budget alert."""

    id: int = Field(description="Alert ID")
    threshold: int = Field(description="Threshold percentage (80 or 100)")
    message: str = Field(description="Alert message")
    created_at: datetime = Field(description="Alert creation timestamp")
    is_read: bool = Field(description="Whether alert has been read")

    model_config = ConfigDict(from_attributes=True)


class BudgetAlertListResponse(BaseModel):
    """Response schema for list of budget alerts."""

    alerts: list[BudgetAlertResponse] = Field(
        default_factory=list,
        description="List of budget alerts",
    )
    unread_count: int = Field(description="Number of unread alerts")


class BotStatusResponse(BaseModel):
    """Response schema for bot status."""

    is_paused: bool = Field(description="Whether bot is paused")
    pause_reason: str | None = Field(
        default=None,
        description="Reason for pause if paused",
    )
    budget_percentage: float | None = Field(
        default=None,
        description="Current budget usage percentage",
    )
    budget_cap: float | None = Field(
        default=None,
        description="Monthly budget cap in USD",
    )
    monthly_spend: float | None = Field(
        default=None,
        description="Current month spending in USD",
    )


class ResumeBotResponse(BaseModel):
    """Response schema for bot resume."""

    success: bool = Field(description="Whether bot was successfully resumed")
    message: str = Field(description="Status message")
    new_budget: float | None = Field(
        default=None,
        description="New budget cap if updated",
    )
