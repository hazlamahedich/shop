"""Merchant settings service for budget recommendations and settings management.

Provides business logic for:
- Budget cap recommendations based on cost history
- Merchant settings validation and processing
- Audit logging for budget changes

Story 3-6: Budget Cap Configuration
"""

from __future__ import annotations

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
import structlog

from app.models.llm_conversation_cost import LLMConversationCost
from app.core.errors import APIError, ErrorCode


logger = structlog.get_logger(__name__)


class BudgetRecommendation:
    """Budget recommendation result."""

    def __init__(
        self,
        recommended_budget: float,
        rationale: str,
        current_avg_daily_cost: float,
        projected_monthly_spend: float,
    ):
        self.recommended_budget = recommended_budget
        self.rationale = rationale
        self.current_avg_daily_cost = current_avg_daily_cost
        self.projected_monthly_spend = projected_monthly_spend

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "recommendedBudget": self.recommended_budget,
            "rationale": self.rationale,
            "currentAvgDailyCost": self.current_avg_daily_cost,
            "projectedMonthlySpend": self.projected_monthly_spend,
        }


async def get_budget_recommendation(
    db: AsyncSession,
    merchant_id: int,
    days_to_analyze: int = 30,
) -> BudgetRecommendation:
    """
    Calculate budget recommendation based on cost history.

    Args:
        db: Database session
        merchant_id: Merchant ID for which to calculate recommendation
        days_to_analyze: Number of days to look back for cost data (default: 30)

    Returns:
        BudgetRecommendation with recommended budget and rationale

    Raises:
        APIError: If budget calculation fails
    """
    try:
        # Calculate date range for analysis
        # Use datetime.now(timezone.utc) and then make it naive since the DB column is TIMESTAMP WITHOUT TIME ZONE
        end_date = datetime.now(timezone.utc).replace(tzinfo=None)
        start_date = end_date - timedelta(days=days_to_analyze)

        # Query total cost and request count for the period
        result = await db.execute(
            select(
                func.sum(LLMConversationCost.total_cost_usd).label("total_cost"),
                func.count(LLMConversationCost.id).label("request_count"),
            )
            .where(LLMConversationCost.merchant_id == merchant_id)
            .where(LLMConversationCost.request_timestamp >= start_date)
            .where(LLMConversationCost.request_timestamp < end_date)
        )

        row = result.one()
        total_cost = float(row.total_cost or 0)
        request_count = row.request_count or 0

        logger.info(
            "budget_recommendation_calculation",
            merchant_id=merchant_id,
            days_analyzed=days_to_analyze,
            total_cost=total_cost,
            request_count=request_count,
        )

        # Calculate average daily cost
        avg_daily_cost = total_cost / days_to_analyze

        # Calculate projected monthly spend (30 days)
        projected_monthly_spend = avg_daily_cost * 30

        # Apply buffer for recommended budget
        # Formula: avg_daily_cost * 30 * 1.5 (50% buffer)
        recommended_budget = projected_monthly_spend * 1.5

        # Round to 2 decimal places
        recommended_budget = round(recommended_budget, 2)
        avg_daily_cost = round(avg_daily_cost, 4)
        projected_monthly_spend = round(projected_monthly_spend, 2)

        # Build rationale
        if request_count > 0 and total_cost > 0:
            rationale = (
                f"Based on your average daily cost of ${avg_daily_cost:.4f} "
                f"over the last {days_to_analyze} days, we recommend ${recommended_budget:.2f}/month "
                f"(30 days × 1.5 buffer for growth)"
            )
        else:
            # Default recommendation for new merchants
            recommended_budget = 50.0
            rationale = (
                f"Based on typical usage patterns, we recommend ${recommended_budget:.2f}/month. "
                f"This will be adjusted as your cost data accumulates."
            )

        return BudgetRecommendation(
            recommended_budget=recommended_budget,
            rationale=rationale,
            current_avg_daily_cost=avg_daily_cost,
            projected_monthly_spend=projected_monthly_spend,
        )

    except Exception as e:
        logger.error(
            "budget_recommendation_failed",
            merchant_id=merchant_id,
            error=str(e),
        )
        raise APIError(
            ErrorCode.MERCHANT_BUDGET_CALCULATION_FAILED,
            "Failed to calculate budget recommendation",
        ) from e


def validate_budget_cap(budget_cap: Optional[float]) -> None:
    """
    Validate budget cap value.

    Args:
        budget_cap: Budget cap value to validate (None means no limit)

    Raises:
        ValidationError: If budget cap is invalid
    """
    from app.core.errors import ValidationError

    if budget_cap is None:
        # None is valid - means no limit
        return

    if not isinstance(budget_cap, (int, float)):
        raise ValidationError(
            "Budget cap must be a number",
            fields={"budget_cap": "Must be a numeric value or null for no limit"},
        )

    if budget_cap < 0:
        raise ValidationError(
            "Budget cap cannot be negative",
            fields={"budget_cap": "Must be a positive number or null for no limit"},
        )

    if budget_cap == 0:
        raise ValidationError(
            "Budget cap cannot be zero",
            fields={
                "budget_cap": "Must be greater than 0 or null for no limit (remove budget cap)"
            },
        )


def log_budget_change(
    merchant_id: int,
    old_budget: Optional[float],
    new_budget: Optional[float],
    db: AsyncSession,
) -> None:
    """
    Log budget cap changes for audit purposes.

    Args:
        merchant_id: Merchant ID
        old_budget: Previous budget cap value
        new_budget: New budget cap value
        db: Database session for potential audit table writes
    """
    logger.info(
        "budget_cap_changed",
        merchant_id=merchant_id,
        old_budget=old_budget,
        new_budget=new_budget,
        change_type="budget_update",
    )

    # Future: Write to audit table if needed
    # For now, structured logging is sufficient for audit trail
