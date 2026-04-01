"""Unit tests for constraint accumulator.

Story 11-2: Tests constraint merging, duplicate detection,
contradiction detection, max constraint limit.
"""

import pytest

from app.services.multi_turn.constraint_accumulator import (
    ConstraintAccumulator,
    MAX_CONSTRAINTS,
)


@pytest.fixture
def accumulator() -> ConstraintAccumulator:
    return ConstraintAccumulator()


class TestEcommerceConstraintExtraction:
    def test_budget_max(self, accumulator: ConstraintAccumulator):
        result = accumulator.accumulate("under $100", {}, "ecommerce")
        assert result["budget_max"] == 100.0

    def test_budget_min(self, accumulator: ConstraintAccumulator):
        result = accumulator.accumulate("over $50", {}, "ecommerce")
        assert result["budget_min"] == 50.0

    def test_brand(self, accumulator: ConstraintAccumulator):
        result = accumulator.accumulate("Nike", {}, "ecommerce")
        assert result["brand"] == "nike"

    def test_size(self, accumulator: ConstraintAccumulator):
        result = accumulator.accumulate("size M", {}, "ecommerce")
        assert result["size"] == "m"

    def test_color(self, accumulator: ConstraintAccumulator):
        result = accumulator.accumulate("in blue", {}, "ecommerce")
        assert result["color"] == "blue"

    def test_category(self, accumulator: ConstraintAccumulator):
        result = accumulator.accumulate("shoes", {}, "ecommerce")
        assert result["category"] == "shoes"

    def test_product_type(self, accumulator: ConstraintAccumulator):
        result = accumulator.accumulate("running shoes", {}, "ecommerce")
        assert result.get("product_type") == "running"

    def test_no_constraints_extracted(self, accumulator: ConstraintAccumulator):
        result = accumulator.accumulate("hello there", {}, "ecommerce")
        assert result == {}


class TestGeneralConstraintExtraction:
    def test_severity(self, accumulator: ConstraintAccumulator):
        result = accumulator.accumulate("this is urgent", {}, "general")
        assert result["severity"] == "urgent"

    def test_timeframe(self, accumulator: ConstraintAccumulator):
        result = accumulator.accumulate("I need it today", {}, "general")
        assert result["timeframe"] == "today"

    def test_issue_type(self, accumulator: ConstraintAccumulator):
        result = accumulator.accumulate("I have a login problem", {}, "general")
        assert result["issue_type"] == "login"


class TestConstraintMerging:
    def test_merges_new_constraints(self, accumulator: ConstraintAccumulator):
        existing = {"brand": "nike"}
        result = accumulator.accumulate("in red", existing, "ecommerce")
        assert result["brand"] == "nike"
        assert result["color"] == "red"

    def test_preserves_existing(self, accumulator: ConstraintAccumulator):
        existing = {"brand": "nike", "category": "shoes"}
        result = accumulator.accumulate("under $100", existing, "ecommerce")
        assert result["brand"] == "nike"
        assert result["category"] == "shoes"
        assert result["budget_max"] == 100.0

    def test_duplicate_not_overwritten(self, accumulator: ConstraintAccumulator):
        existing = {"brand": "nike"}
        result = accumulator.accumulate("Nike", existing, "ecommerce")
        assert result["brand"] == "nike"


class TestConstraintAccumulationAcrossTurns:
    def test_three_turns(self, accumulator: ConstraintAccumulator):
        constraints: dict = {}
        constraints = accumulator.accumulate("running shoes", constraints, "ecommerce")
        constraints = accumulator.accumulate("under $100", constraints, "ecommerce")
        constraints = accumulator.accumulate("Nike", constraints, "ecommerce")
        assert "category" in constraints or "product_type" in constraints
        assert constraints.get("budget_max") == 100.0
        assert constraints.get("brand") == "nike"


class TestContradictionDetection:
    def test_budget_min_exceeds_max(self, accumulator: ConstraintAccumulator):
        existing: dict = {"budget_max": 50.0}
        result = accumulator.accumulate("over $100", existing, "ecommerce")
        assert "budget_min_conflict" in result
        assert result["budget_min"] == 100.0

    def test_budget_max_below_min(self, accumulator: ConstraintAccumulator):
        existing: dict = {"budget_min": 100.0}
        result = accumulator.accumulate("under $50", existing, "ecommerce")
        assert "budget_max_conflict" in result
        assert result["budget_max"] == 50.0


class TestMaxConstraintLimit:
    def test_truncation_at_max(self, accumulator: ConstraintAccumulator):
        constraints = {f"key_{i}": f"value_{i}" for i in range(MAX_CONSTRAINTS + 5)}
        result = accumulator._truncate_oldest_constraints(constraints)
        assert len(result) <= MAX_CONSTRAINTS

    def test_no_truncation_under_limit(self, accumulator: ConstraintAccumulator):
        constraints = {"a": 1, "b": 2, "c": 3}
        result = accumulator._truncate_oldest_constraints(constraints)
        assert len(result) == 3


class TestFormatConstraintSummary:
    def test_ecommerce_summary(self, accumulator: ConstraintAccumulator):
        constraints = {
            "category": "shoes",
            "brand": "nike",
            "budget_max": 100.0,
            "color": "blue",
        }
        summary = accumulator.format_constraint_summary(constraints, "ecommerce")
        assert "shoes" in summary
        assert "Nike" in summary
        assert "100" in summary
        assert "blue" in summary

    def test_general_summary(self, accumulator: ConstraintAccumulator):
        constraints = {
            "issue_type": "login",
            "severity": "urgent",
            "timeframe": "today",
        }
        summary = accumulator.format_constraint_summary(constraints, "general")
        assert "login" in summary
        assert "urgent" in summary
        assert "today" in summary

    def test_empty_constraints(self, accumulator: ConstraintAccumulator):
        summary = accumulator.format_constraint_summary({}, "ecommerce")
        assert summary == "No specific preferences yet."

    def test_conflict_keys_excluded(self, accumulator: ConstraintAccumulator):
        constraints = {"brand": "nike", "brand_conflict": {"previous": "adidas", "new": "nike"}}
        summary = accumulator.format_constraint_summary(constraints, "ecommerce")
        assert "Nike" in summary
        assert "adidas" not in summary


class TestDetectDuplicateConstraints:
    def test_finds_duplicates(self, accumulator: ConstraintAccumulator):
        new = {"brand": "nike", "color": "red"}
        existing = {"brand": "nike", "size": "M"}
        duplicates = accumulator.detect_duplicate_constraints(new, existing)
        assert "brand" in duplicates
        assert "color" not in duplicates

    def test_no_duplicates(self, accumulator: ConstraintAccumulator):
        new = {"brand": "nike"}
        existing = {"color": "red"}
        duplicates = accumulator.detect_duplicate_constraints(new, existing)
        assert len(duplicates) == 0
