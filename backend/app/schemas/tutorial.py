"""Pydantic schemas for Tutorial API.

Request and response schemas for tutorial endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TutorialStatusResponse(BaseModel):
    """Response schema for tutorial status."""

    is_started: bool = Field(..., alias="isStarted")
    is_completed: bool = Field(..., alias="isCompleted")
    is_skipped: bool = Field(..., alias="isSkipped")
    current_step: int = Field(..., alias="currentStep")
    completed_steps: list[str] = Field(default_factory=list, alias="completedSteps")
    steps_total: int = Field(..., alias="stepsTotal")

    class Config:
        populate_by_name = True


class TutorialStartResponse(BaseModel):
    """Response schema for starting tutorial."""

    started_at: datetime = Field(..., alias="startedAt")
    current_step: int = Field(..., alias="currentStep")

    class Config:
        populate_by_name = True


class TutorialCompleteResponse(BaseModel):
    """Response schema for completing tutorial."""

    completed_at: datetime = Field(..., alias="completedAt")
    completed_steps: list[str] = Field(..., alias="completedSteps")

    class Config:
        populate_by_name = True


class TutorialSkipResponse(BaseModel):
    """Response schema for skipping tutorial."""

    skipped: bool
    skipped_at: datetime = Field(..., alias="skippedAt")

    class Config:
        populate_by_name = True


class TutorialResetResponse(BaseModel):
    """Response schema for resetting tutorial."""

    reset: bool
    message: str = "Tutorial progress has been reset"
