"""Test budget threshold detection with Decimal precision.

Story 3.8: Budget Alert Notifications

Tests edge cases for threshold detection including:
- 79.99% -> ok
- 80.00% -> warning (exact boundary)
- 99.99% -> warning
- 100.00% -> exceeded (exact boundary)
- budget_cap == 0 -> exceeded (immediate pause)
- null budget_cap -> ok (no alerts)
- Decimal precision: $99.999 on $100 budget -> ok
"""

import pytest
from decimal import Decimal


def check_budget_threshold_sync(
    monthly_spend: Decimal,
    budget_cap: Decimal | None,
) -> str:
    """Synchronous version of threshold check for unit testing.

    Args:
        monthly_spend: Current month's spending
        budget_cap: Monthly budget cap (None = no limit)

    Returns:
        "ok": Under 80% or no budget set
        "warning": 80% or above
        "exceeded": 100% or above, or budget is $0
    """
    if budget_cap is None:
        return "ok"

    if budget_cap == Decimal("0"):
        return "exceeded"

    if budget_cap <= Decimal("0"):
        return "exceeded"

    percentage = (monthly_spend / budget_cap) * Decimal("100")

    if percentage >= Decimal("100"):
        return "exceeded"
    elif percentage >= Decimal("80"):
        return "warning"

    return "ok"


class TestBudgetThresholdDetection:
    """Test budget threshold detection with Decimal precision."""

    @pytest.mark.parametrize(
        "spend,cap,expected",
        [
            (Decimal("79.99"), Decimal("100.00"), "ok"),
            (Decimal("80.00"), Decimal("100.00"), "warning"),
            (Decimal("80.01"), Decimal("100.00"), "warning"),
            (Decimal("99.99"), Decimal("100.00"), "warning"),
            (Decimal("100.00"), Decimal("100.00"), "exceeded"),
            (Decimal("100.01"), Decimal("100.00"), "exceeded"),
            (Decimal("0.00"), Decimal("0.00"), "exceeded"),
            (Decimal("50.00"), Decimal("0.00"), "exceeded"),
            (Decimal("50.00"), None, "ok"),
            (Decimal("99.99"), Decimal("100.00"), "warning"),
            (Decimal("0.00"), Decimal("100.00"), "ok"),
            (Decimal("50.00"), Decimal("100.00"), "ok"),
            (Decimal("150.00"), Decimal("100.00"), "exceeded"),
        ],
    )
    def test_threshold_edge_cases(
        self,
        spend: Decimal,
        cap: Decimal | None,
        expected: str,
    ) -> None:
        """Test threshold detection with various edge cases."""
        result = check_budget_threshold_sync(monthly_spend=spend, budget_cap=cap)
        assert result == expected

    def test_null_budget_no_alerts(self) -> None:
        """Test that null budget_cap returns ok (no alerts)."""
        result = check_budget_threshold_sync(
            monthly_spend=Decimal("999999.99"),
            budget_cap=None,
        )
        assert result == "ok"

    def test_zero_budget_immediate_exceeded(self) -> None:
        """Test that $0 budget returns exceeded immediately."""
        result = check_budget_threshold_sync(
            monthly_spend=Decimal("0.00"),
            budget_cap=Decimal("0.00"),
        )
        assert result == "exceeded"

    def test_negative_budget_cap_exceeded(self) -> None:
        """Test that negative budget cap returns exceeded."""
        result = check_budget_threshold_sync(
            monthly_spend=Decimal("0.00"),
            budget_cap=Decimal("-10.00"),
        )
        assert result == "exceeded"

    def test_decimal_precision_exact_80_percent(self) -> None:
        """Test that 80.00% exactly triggers warning."""
        result = check_budget_threshold_sync(
            monthly_spend=Decimal("80.00"),
            budget_cap=Decimal("100.00"),
        )
        assert result == "warning"

    def test_decimal_precision_just_under_80_percent(self) -> None:
        """Test that 79.99% returns ok."""
        result = check_budget_threshold_sync(
            monthly_spend=Decimal("79.99"),
            budget_cap=Decimal("100.00"),
        )
        assert result == "ok"

    def test_decimal_precision_just_under_100_percent(self) -> None:
        """Test that 99.99% returns warning, not exceeded."""
        result = check_budget_threshold_sync(
            monthly_spend=Decimal("99.99"),
            budget_cap=Decimal("100.00"),
        )
        assert result == "warning"

    def test_decimal_precision_exact_100_percent(self) -> None:
        """Test that 100.00% exactly triggers exceeded."""
        result = check_budget_threshold_sync(
            monthly_spend=Decimal("100.00"),
            budget_cap=Decimal("100.00"),
        )
        assert result == "exceeded"

    def test_decimal_precision_99_99_on_100(self) -> None:
        """Test Decimal precision: $99.99 on $100 budget -> warning (still >= 80%)."""
        result = check_budget_threshold_sync(
            monthly_spend=Decimal("99.99"),
            budget_cap=Decimal("100.00"),
        )
        assert result == "warning"

    def test_large_budget_amounts(self) -> None:
        """Test threshold detection with large budget amounts."""
        result = check_budget_threshold_sync(
            monthly_spend=Decimal("7999.99"),
            budget_cap=Decimal("10000.00"),
        )
        assert result == "warning"

    def test_small_budget_amounts(self) -> None:
        """Test threshold detection with small budget amounts."""
        result = check_budget_threshold_sync(
            monthly_spend=Decimal("0.80"),
            budget_cap=Decimal("1.00"),
        )
        assert result == "warning"
