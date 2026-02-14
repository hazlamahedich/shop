"""Test competitor pricing estimation.

Story 3.9: Cost Comparison Display

Tests for:
- ManyChat cost estimation at various message volumes
- Tier boundary conditions
- Decimal precision for monetary values
- Edge cases: zero messages, high volume
"""

import pytest
from decimal import Decimal


class TestManyChatEstimation:
    """Test ManyChat cost estimation logic."""

    def test_estimate_zero_messages_returns_zero(self) -> None:
        """Zero messages should return zero cost."""
        from app.services.cost_tracking.competitor_pricing import estimate_manychat_cost

        cost = estimate_manychat_cost(0)
        assert cost == Decimal("0")

    def test_estimate_small_volume_pro_tier(self) -> None:
        """Small volume (100 messages) should use Pro tier ($15 minimum)."""
        from app.services.cost_tracking.competitor_pricing import estimate_manychat_cost

        cost = estimate_manychat_cost(100)
        assert cost >= Decimal("15")
        assert cost <= Decimal("20")

    def test_estimate_medium_volume_business_tier(self) -> None:
        """Medium volume (1000 messages) should use Pro tier + message costs."""
        from app.services.cost_tracking.competitor_pricing import estimate_manychat_cost

        cost = estimate_manychat_cost(1000)
        assert cost >= Decimal("15")
        assert cost <= Decimal("30")

    def test_estimate_high_volume_business_plus_tier(self) -> None:
        """High volume (5000 messages) should use Business+ tier ($50)."""
        from app.services.cost_tracking.competitor_pricing import estimate_manychat_cost

        cost = estimate_manychat_cost(5000)
        assert cost >= Decimal("50")
        assert cost <= Decimal("80")

    def test_estimate_very_high_volume_business_plus_plus_tier(self) -> None:
        """Very high volume (10000 messages) should use Business++ tier ($99)."""
        from app.services.cost_tracking.competitor_pricing import estimate_manychat_cost

        cost = estimate_manychat_cost(10000)
        assert cost >= Decimal("99")
        assert cost <= Decimal("200")

    def test_cost_increases_with_volume(self) -> None:
        """Cost should increase as message volume increases."""
        from app.services.cost_tracking.competitor_pricing import estimate_manychat_cost

        low_cost = estimate_manychat_cost(100)
        medium_cost = estimate_manychat_cost(1000)
        high_cost = estimate_manychat_cost(5000)

        assert low_cost < medium_cost < high_cost

    def test_returns_decimal_type(self) -> None:
        """Function should return Decimal for monetary precision."""
        from app.services.cost_tracking.competitor_pricing import estimate_manychat_cost

        cost = estimate_manychat_cost(500)
        assert isinstance(cost, Decimal)

    def test_negative_messages_returns_zero(self) -> None:
        """Negative message count should return zero."""
        from app.services.cost_tracking.competitor_pricing import estimate_manychat_cost

        cost = estimate_manychat_cost(-100)
        assert cost == Decimal("0")


class TestCostComparisonCalculation:
    """Test cost comparison calculations."""

    def test_calculate_savings_positive(self) -> None:
        """When shop cost is lower, savings should be positive."""
        from app.services.cost_tracking.competitor_pricing import calculate_cost_comparison

        result = calculate_cost_comparison(merchant_spend=Decimal("5.00"), message_count=1000)

        assert result["savingsAmount"] > 0
        assert result["savingsPercentage"] > 0
        assert result["savingsPercentage"] <= 100

    def test_calculate_savings_percentage_accuracy(self) -> None:
        """Savings percentage should be calculated correctly."""
        from app.services.cost_tracking.competitor_pricing import calculate_cost_comparison

        result = calculate_cost_comparison(merchant_spend=Decimal("5.00"), message_count=1000)

        expected_percentage = (result["manyChatEstimate"] - 5.0) / result["manyChatEstimate"] * 100
        assert abs(result["savingsPercentage"] - expected_percentage) < 0.1

    def test_calculate_savings_zero_spend(self) -> None:
        """Zero spend should show 100% savings."""
        from app.services.cost_tracking.competitor_pricing import calculate_cost_comparison

        result = calculate_cost_comparison(merchant_spend=Decimal("0"), message_count=100)

        assert result["savingsAmount"] == result["manyChatEstimate"]
        assert result["savingsPercentage"] == 100

    def test_calculate_negative_savings(self) -> None:
        """When shop costs more, savings should be negative."""
        from app.services.cost_tracking.competitor_pricing import calculate_cost_comparison

        result = calculate_cost_comparison(merchant_spend=Decimal("500"), message_count=100)

        assert result["savingsAmount"] < 0

    def test_methodology_includes_pricing_info(self) -> None:
        """Methodology should include ManyChat pricing information."""
        from app.services.cost_tracking.competitor_pricing import calculate_cost_comparison

        result = calculate_cost_comparison(merchant_spend=Decimal("5.00"), message_count=1000)

        assert "ManyChat" in result["methodology"]
        assert "$" in result["methodology"]
        assert "1000" in result["methodology"]

    def test_returns_required_fields(self) -> None:
        """Should return all required fields."""
        from app.services.cost_tracking.competitor_pricing import calculate_cost_comparison

        result = calculate_cost_comparison(merchant_spend=Decimal("5.00"), message_count=1000)

        required_fields = [
            "manyChatEstimate",
            "savingsAmount",
            "savingsPercentage",
            "merchantSpend",
            "methodology",
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
