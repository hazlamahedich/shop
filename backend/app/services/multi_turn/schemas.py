"""Pydantic schemas for multi-turn query handling.

Story 11-2: Multi-Turn Query Handling
Defines state machine states, message types, constraints, and configuration.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class MessageType(StrEnum):
    NEW_QUERY = "new_query"
    CLARIFICATION_RESPONSE = "clarification_response"
    CONSTRAINT_ADDITION = "constraint_addition"
    TOPIC_CHANGE = "topic_change"
    INVALID_RESPONSE = "invalid_response"


class MultiTurnStateEnum(StrEnum):
    IDLE = "IDLE"
    CLARIFYING = "CLARIFYING"
    REFINE_RESULTS = "REFINE_RESULTS"
    COMPLETE = "COMPLETE"


class MultiTurnConfig(BaseModel):
    max_clarification_turns: int = Field(
        default=3,
        ge=2,
        le=5,
        description="Maximum clarification turns (min 2, max 5, default 3)",
    )
    max_invalid_responses: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Maximum consecutive invalid responses before best-effort",
    )

    @field_validator("max_clarification_turns")
    @classmethod
    def validate_turn_bounds(cls, v: int) -> int:
        if v < 2 or v > 5:
            raise ValueError("max_clarification_turns must be between 2 and 5")
        return v


class ClarificationTurn(BaseModel):
    question_asked: str = Field(description="The clarification question asked")
    constraint_name: str = Field(description="Name of the constraint being asked about")
    user_response: str | None = Field(default=None, description="User's response")
    is_valid: bool = Field(default=False, description="Whether the response was valid")


class EcommerceConstraints(BaseModel):
    budget_min: float | None = Field(default=None, alias="budgetMin")
    budget_max: float | None = Field(default=None, alias="budgetMax")
    brand: str | None = Field(default=None)
    size: str | None = Field(default=None)
    color: str | None = Field(default=None)
    category: str | None = Field(default=None)
    product_type: str | None = Field(default=None, alias="productType")

    class Config:
        populate_by_name = True


class GeneralConstraints(BaseModel):
    issue_type: str | None = Field(default=None, alias="issueType")
    severity: str | None = Field(default=None)
    timeframe: str | None = Field(default=None)
    topic: str | None = Field(default=None)
    resolution_attempts: list[str] = Field(default_factory=list, alias="resolutionAttempts")

    class Config:
        populate_by_name = True


class MultiTurnState(BaseModel):
    state: str = Field(default=MultiTurnStateEnum.IDLE, description="Current state machine state")
    turn_count: int = Field(default=0, ge=0, description="Number of clarification turns completed")
    accumulated_constraints: dict[str, Any] = Field(
        default_factory=dict,
        description="Mode-specific accumulated constraints",
    )
    questions_asked: list[str] = Field(
        default_factory=list,
        description="List of constraint names already asked about",
    )
    pending_questions: list[str] = Field(
        default_factory=list,
        description="Remaining constraint names to ask about",
    )
    original_query: str | None = Field(
        default=None,
        description="The query that started the multi-turn flow",
    )
    invalid_response_count: int = Field(
        default=0,
        ge=0,
        description="Consecutive invalid responses counter",
    )
    mode: str = Field(
        default="ecommerce",
        description="Bot mode (ecommerce or general)",
    )
    clarification_turns: list[ClarificationTurn] = Field(
        default_factory=list,
        description="History of clarification turns",
    )

    class Config:
        use_enum_values = True
