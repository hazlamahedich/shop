"""Cost tracking API schemas.

Defines request/response schemas for cost tracking endpoints.
Uses Pydantic alias_generator for camelCase API responses.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CostRecord(BaseModel):
    """Individual LLM cost record."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: int
    request_timestamp: datetime
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    total_cost_usd: float
    processing_time_ms: Optional[float] = None


class ConversationCostResponse(BaseModel):
    """Conversation cost detail response."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    conversation_id: str = Field(..., description="Conversation identifier")
    total_cost_usd: float = Field(..., description="Total cost in USD")
    total_tokens: int = Field(..., description="Total tokens used")
    request_count: int = Field(..., description="Number of LLM requests")
    avg_cost_per_request: float = Field(..., description="Average cost per request")
    provider: str = Field(..., description="Primary provider used")
    model: str = Field(..., description="Primary model used")
    requests: list[CostRecord] = Field(default_factory=list, description="Individual cost records")


class TopConversation(BaseModel):
    """Top conversation by cost."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    conversation_id: str
    total_cost_usd: float
    request_count: int


class ProviderCostSummary(BaseModel):
    """Cost summary for a provider."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    cost_usd: float
    requests: int


class DailyCostBreakdown(BaseModel):
    """Daily cost summary."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    date: str
    total_cost_usd: float
    request_count: int


class CostComparisonResponse(BaseModel):
    """Cost comparison vs competitor (ManyChat)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    many_chat_estimate: float = Field(..., description="Estimated ManyChat monthly cost")
    savings_amount: float = Field(..., description="Amount saved with shop vs ManyChat")
    savings_percentage: float = Field(..., description="Percentage saved (0-100)")
    merchant_spend: float = Field(..., description="Merchant's actual shop spend")
    methodology: str = Field(..., description="Explanation of comparison methodology")


class CostSummaryResponse(BaseModel):
    """Cost summary response with period aggregates."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total_cost_usd: float = Field(..., description="Total cost in USD for period")
    total_tokens: int = Field(..., description="Total tokens used")
    request_count: int = Field(..., description="Total LLM requests")
    avg_cost_per_request: float = Field(..., description="Average cost per request")
    top_conversations: list[TopConversation] = Field(
        default_factory=list, description="Most expensive conversations"
    )
    costs_by_provider: dict[str, ProviderCostSummary] = Field(
        default_factory=dict, description="Cost breakdown by provider"
    )
    daily_breakdown: list[DailyCostBreakdown] = Field(
        default_factory=list, description="Daily cost summary (if multi-day range)"
    )
    previous_period_summary: Optional[dict] = Field(
        None, description="Aggregated data for the previous equivalent period"
    )
    cost_comparison: Optional[CostComparisonResponse] = Field(
        None, description="Cost comparison vs competitor pricing"
    )


class CostListResponse(BaseModel):
    """Cost list envelope response."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    data: Union[list[dict], dict]
    meta: dict
