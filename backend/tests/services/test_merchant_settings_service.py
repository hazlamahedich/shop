"""Tests for merchant settings service.

Story 3-6: Budget Cap Configuration
Tests budget validation, recommendation calculation, and error handling.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.merchant_settings_service import (
    get_budget_recommendation,
    validate_budget_cap,
    log_budget_change,
    BudgetRecommendation,
)
from app.core.errors import ValidationError, APIError, ErrorCode


class TestValidateBudgetCap:
    """Tests for budget cap validation."""

    def test_validate_positive_budget(self):
        """Test that positive budget values are valid."""
        # Should not raise
        validate_budget_cap(50.0)
        validate_budget_cap(100)
        validate_budget_cap(0.01)

    def test_validate_null_budget(self):
        """Test that null budget (no limit) is valid."""
        # Should not raise
        validate_budget_cap(None)

    def test_validate_negative_budget_raises_error(self):
        """Test that negative budget values raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_budget_cap(-10.0)

        assert "cannot be negative" in str(exc_info.value).lower()
        assert exc_info.value.details["fields"]["budget_cap"]

    def test_validate_zero_budget_raises_error(self):
        """Test that zero budget raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_budget_cap(0)

        assert "cannot be zero" in str(exc_info.value).lower()
        assert exc_info.value.details["fields"]["budget_cap"]

    def test_validate_non_numeric_budget_raises_error(self):
        """Test that non-numeric budget raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_budget_cap("invalid")  # type: ignore

        assert "must be a number" in str(exc_info.value).lower()
        assert exc_info.value.details["fields"]["budget_cap"]


class TestGetBudgetRecommendation:
    """Tests for budget recommendation calculation."""

    @pytest.mark.asyncio
    async def test_recommendation_with_cost_data(
        self, async_session: AsyncSession, make_cost_records
    ):
        """Test budget recommendation with existing cost data."""
        # Create a merchant first to use a unique merchant_id
        from app.models.merchant import Merchant

        merchant = Merchant(
            merchant_key="test-budget-rec",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create cost records: $30 over 30 days (consistent with analysis period)
        total_cost = 30.0
        records = make_cost_records(
            merchant_id=merchant.id,
            count=30,
            total_cost=total_cost,
            days_back=30,
        )

        # Add records to database
        for record in records:
            async_session.add(record)
        await async_session.commit()

        # First, verify there are cost records for this merchant
        from sqlalchemy import select, func
        from app.models.llm_conversation_cost import LLMConversationCost

        result = await async_session.execute(
            select(func.sum(LLMConversationCost.total_cost_usd))
            .where(LLMConversationCost.merchant_id == merchant.id)
        )
        actual_total = result.scalar() or 0

        recommendation = await get_budget_recommendation(
            async_session, merchant.id, days_to_analyze=30
        )

        assert isinstance(recommendation, BudgetRecommendation)
        assert recommendation.recommended_budget > 0

        # The recommendation should be based on actual data in the database
        # avg_daily_cost = total_cost / 30 days
        expected_avg = actual_total / 30.0
        assert abs(recommendation.current_avg_daily_cost - expected_avg) < 0.1

        # projected = avg_daily * 30
        expected_projected = expected_avg * 30.0
        assert abs(recommendation.projected_monthly_spend - expected_projected) < 1.0

        # recommended = projected * 1.5
        expected_recommended = expected_projected * 1.5
        assert abs(recommendation.recommended_budget - expected_recommended) < 1.5

        # Check rationale contains expected elements
        assert "buffer" in recommendation.rationale.lower()
        assert "30" in recommendation.rationale

    @pytest.mark.asyncio
    async def test_recommendation_without_cost_data(
        self, async_session: AsyncSession
    ):
        """Test budget recommendation without cost data (new merchant)."""
        merchant_id = 999  # No cost records for this merchant

        recommendation = await get_budget_recommendation(
            async_session, merchant_id, days_to_analyze=30
        )

        assert isinstance(recommendation, BudgetRecommendation)

        # Default recommendation
        assert recommendation.recommended_budget == 50.0
        assert recommendation.current_avg_daily_cost == 0.0
        assert recommendation.projected_monthly_spend == 0.0

        # Check default rationale
        assert "typical usage patterns" in recommendation.rationale
        assert "$50.00" in recommendation.rationale

    @pytest.mark.asyncio
    async def test_recommendation_to_dict_conversion(
        self, async_session: AsyncSession
    ):
        """Test BudgetRecommendation.to_dict() method."""
        merchant_id = 1
        recommendation = await get_budget_recommendation(
            async_session, merchant_id, days_to_analyze=30
        )

        result_dict = recommendation.to_dict()

        assert "recommendedBudget" in result_dict
        assert "rationale" in result_dict
        assert "currentAvgDailyCost" in result_dict
        assert "projectedMonthlySpend" in result_dict

        assert result_dict["recommendedBudget"] == recommendation.recommended_budget
        assert result_dict["rationale"] == recommendation.rationale

    @pytest.mark.asyncio
    async def test_recommendation_with_different_periods(
        self, async_session: AsyncSession, make_cost_records
    ):
        """Test recommendation with different analysis periods."""
        from app.models.merchant import Merchant

        merchant = Merchant(
            merchant_key="test-budget-rec-period",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create cost records: $30 over 30 days
        records = make_cost_records(
            merchant_id=merchant.id,
            count=30,
            total_cost=30.0,
            days_back=30,
        )

        # Add records to database
        for record in records:
            async_session.add(record)
        await async_session.commit()

        # Analyze 7 days only
        recommendation = await get_budget_recommendation(
            async_session, merchant.id, days_to_analyze=7
        )

        # Should calculate based on 7-day period
        assert recommendation.current_avg_daily_cost > 0
        assert recommendation.recommended_budget > 0


class TestLogBudgetChange:
    """Tests for budget change audit logging."""

    @pytest.mark.asyncio
    async def test_log_budget_increase(self, async_session: AsyncSession):
        """Test logging budget increase."""
        # Should not raise
        log_budget_change(
            merchant_id=1,
            old_budget=50.0,
            new_budget=100.0,
            db=async_session,
        )

    @pytest.mark.asyncio
    async def test_log_budget_decrease(self, async_session: AsyncSession):
        """Test logging budget decrease."""
        # Should not raise
        log_budget_change(
            merchant_id=1,
            old_budget=100.0,
            new_budget=50.0,
            db=async_session,
        )

    @pytest.mark.asyncio
    async def test_log_budget_removal(self, async_session: AsyncSession):
        """Test logging budget removal (setting to null)."""
        # Should not raise
        log_budget_change(
            merchant_id=1,
            old_budget=100.0,
            new_budget=None,
            db=async_session,
        )

    @pytest.mark.asyncio
    async def test_log_budget_initial_set(self, async_session: AsyncSession):
        """Test logging initial budget set."""
        # Should not raise
        log_budget_change(
            merchant_id=1,
            old_budget=None,
            new_budget=100.0,
            db=async_session,
        )
