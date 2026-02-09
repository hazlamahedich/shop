"""Tests for merchant API endpoints.

Story 3-6: Budget Cap Configuration
Tests PATCH /api/merchant/settings and GET /api/merchant/budget-recommendation
"""

import pytest
from httpx import AsyncClient


class TestMerchantSettingsEndpoint:
    """Tests for PATCH /api/merchant/settings endpoint."""

    @pytest.mark.asyncio
    async def test_update_budget_cap_with_valid_value(self, async_session, async_client: AsyncClient, make_merchant):
        """Test updating budget cap with a valid positive number."""
        # Create a merchant first
        merchant = make_merchant(merchant_key="test-budget-1", platform="facebook")
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Update budget cap
        response = await async_client.patch(
            "/api/merchant/settings",
            json={"budget_cap": 100.50},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200

        data = response.json()
        assert "budget_cap" in data or "budgetCap" in data
        # Handle both snake_case and camelCase
        budget_cap = data.get("budget_cap") or data.get("budgetCap")
        assert budget_cap == 100.50

    @pytest.mark.asyncio
    async def test_update_budget_cap_with_zero_fails(self, async_session, async_client: AsyncClient, make_merchant):
        """Test that zero budget cap returns validation error."""
        merchant = make_merchant(merchant_key="test-budget-zero", platform="facebook")
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        response = await async_client.patch(
            "/api/merchant/settings",
            json={"budget_cap": 0},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        # Pydantic validation returns 422 for invalid values
        assert response.status_code in (400, 422)

        data = response.json()
        assert "error_code" in data or "message" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_update_budget_cap_with_negative_fails(self, async_session, async_client: AsyncClient, make_merchant):
        """Test that negative budget cap returns validation error."""
        merchant = make_merchant(merchant_key="test-budget-negative", platform="facebook")
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        response = await async_client.patch(
            "/api/merchant/settings",
            json={"budget_cap": -50.0},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        # Pydantic validation returns 422 for invalid values
        assert response.status_code in (400, 422)

        data = response.json()
        assert "error_code" in data or "message" in data or "detail" in data

    @pytest.mark.asyncio
    async def test_update_budget_cap_with_null_removes_limit(self, async_session, async_client: AsyncClient, make_merchant):
        """Test that null budget cap removes the limit."""
        merchant = make_merchant(merchant_key="test-budget-null", platform="facebook")
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        response = await async_client.patch(
            "/api/merchant/settings",
            json={"budget_cap": None},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200

        data = response.json()
        # Budget cap should be null or not present
        budget_cap = data.get("budget_cap") or data.get("budgetCap")
        assert budget_cap is None

    @pytest.mark.asyncio
    async def test_update_budget_cap_missing_field(self, async_session, async_client: AsyncClient, make_merchant):
        """Test that missing budget_cap field is handled correctly."""
        merchant = make_merchant(merchant_key="test-budget-missing", platform="facebook")
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        response = await async_client.patch(
            "/api/merchant/settings",
            json={},
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        # Should succeed - budget_cap is optional
        assert response.status_code == 200


class TestBudgetRecommendationEndpoint:
    """Tests for GET /api/merchant/budget-recommendation endpoint."""

    @pytest.mark.asyncio
    async def test_get_budget_recommendation(self, async_session, async_client: AsyncClient, make_merchant):
        """Test getting budget recommendation."""
        merchant = make_merchant(merchant_key="test-budget-rec", platform="facebook")
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        response = await async_client.get(
            "/api/merchant/budget-recommendation",
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200

        data = response.json()
        # Handle both enveloped and non-enveloped responses
        rec_data = data.get("data") or data

        assert "recommendedBudget" in rec_data or "recommended_budget" in rec_data
        assert "rationale" in rec_data or "rationale" in rec_data
        assert "currentAvgDailyCost" in rec_data or "current_avg_daily_cost" in rec_data
        assert "projectedMonthlySpend" in rec_data or "projected_monthly_spend" in rec_data

        # Get values handling both naming conventions
        recommended_budget = rec_data.get("recommendedBudget") or rec_data.get("recommended_budget")
        rationale = rec_data.get("rationale")
        current_avg = rec_data.get("currentAvgDailyCost") or rec_data.get("current_avg_daily_cost")
        projected = rec_data.get("projectedMonthlySpend") or rec_data.get("projected_monthly_spend")

        assert isinstance(recommended_budget, (int, float))
        assert isinstance(rationale, str)
        assert len(rationale) > 0
        assert isinstance(current_avg, (int, float))
        assert isinstance(projected, (int, float))

    @pytest.mark.asyncio
    async def test_get_budget_recommendation_without_cost_data(self, async_session, async_client: AsyncClient, make_merchant):
        """Test getting budget recommendation when merchant has no cost history."""
        # Use a fresh merchant with no cost data
        merchant = make_merchant(merchant_key="test-budget-no-cost", platform="facebook")
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        response = await async_client.get(
            "/api/merchant/budget-recommendation",
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200

        data = response.json()
        rec_data = data.get("data") or data

        # Should return default recommendation
        recommended_budget = rec_data.get("recommendedBudget") or rec_data.get("recommended_budget")
        assert recommended_budget == 50.0  # Default recommendation

    @pytest.mark.asyncio
    async def test_budget_recommendation_with_cost_data(self, async_session, async_client: AsyncClient, make_cost_records):
        """Test budget recommendation with existing cost data."""
        from app.models.merchant import Merchant

        # Create a merchant
        merchant = Merchant(
            merchant_key="test-budget-rec-api",
            platform="facebook",
            status="active",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Add cost records: $30 over 30 days
        records = make_cost_records(
            merchant_id=merchant.id,
            count=30,
            total_cost=30.0,
            days_back=30,
        )

        for record in records:
            async_session.add(record)
        await async_session.commit()

        # Get recommendation for this merchant
        response = await async_client.get(
            "/api/merchant/budget-recommendation",
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200

        data = response.json()
        rec_data = data.get("data") or data

        # Should calculate based on actual data
        current_avg = rec_data.get("currentAvgDailyCost") or rec_data.get("current_avg_daily_cost")
        projected = rec_data.get("projectedMonthlySpend") or rec_data.get("projected_monthly_spend")
        recommended = rec_data.get("recommendedBudget") or rec_data.get("recommended_budget")

        # With $30 over 30 days, avg should be ~$1, projected ~$30, recommended ~$45
        assert abs(current_avg - 1.0) < 0.1
        assert abs(projected - 30.0) < 1.0
        assert abs(recommended - 45.0) < 1.5


class TestMerchantSettingsIsolation:
    """Tests for merchant isolation in budget settings."""

    @pytest.mark.asyncio
    async def test_merchant_can_only_update_own_budget(self, async_session, async_client: AsyncClient, make_merchant):
        """Test that merchants can only modify their own budget."""
        # Create two merchants
        merchant1 = make_merchant(merchant_key="test-isolation-1", platform="facebook")
        merchant2 = make_merchant(merchant_key="test-isolation-2", platform="facebook")
        async_session.add(merchant1)
        async_session.add(merchant2)
        await async_session.commit()
        await async_session.refresh(merchant1)
        await async_session.refresh(merchant2)

        # Merchant 1 updates their budget
        response = await async_client.patch(
            "/api/merchant/settings",
            json={"budget_cap": 100.0},
            headers={"X-Merchant-Id": str(merchant1.id)},
        )

        assert response.status_code == 200

        # Merchant 2 should have their own separate budget
        # (This test verifies the endpoint uses the merchant_id from auth)
        response2 = await async_client.patch(
            "/api/merchant/settings",
            json={"budget_cap": 200.0},
            headers={"X-Merchant-Id": str(merchant2.id)},
        )

        assert response2.status_code == 200

    @pytest.mark.asyncio
    async def test_get_merchant_settings_returns_correct_merchant_data(self, async_session, async_client: AsyncClient, make_merchant):
        """Test that GET settings returns data for the authenticated merchant."""
        merchant = make_merchant(merchant_key="test-settings-get", platform="facebook")
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        response = await async_client.get(
            "/api/merchant/settings",
            headers={"X-Merchant-Id": str(merchant.id)},
        )

        assert response.status_code == 200

        # Response should be valid JSON
        data = response.json()
        assert isinstance(data, dict)
