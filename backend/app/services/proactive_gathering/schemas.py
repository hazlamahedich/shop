from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.services.intent.classification_schema import IntentType


class MissingField(BaseModel):
    field_name: str = Field(description="Internal field name (e.g., 'budget', 'order_number')")
    display_name: str = Field(description="Human-readable name for question generation")
    priority: int = Field(ge=1, le=3, description="1=critical, 2=important, 3=nice-to-have")
    mode: str = Field(description="ecommerce, general, or both")
    example_values: list[str] = Field(
        default_factory=list, description="Example values for guidance"
    )


class GatheringState(BaseModel):
    active: bool = Field(default=False, description="Whether proactive gathering is active")
    round_count: int = Field(default=0, ge=0, description="Current gathering round (max 2)")
    original_intent: IntentType | None = Field(
        default=None, description="Original classified intent"
    )
    original_query: str | None = Field(default=None, description="Original user query")
    missing_fields: list[MissingField] = Field(
        default_factory=list, description="Fields still needed"
    )
    gathered_data: dict[str, Any] = Field(default_factory=dict, description="Extracted data so far")
    is_complete: bool = Field(default=False, description="Whether gathering is complete")

    class Config:
        use_enum_values = True
