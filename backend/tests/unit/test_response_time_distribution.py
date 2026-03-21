"""
Unit tests for Story 10-9: Response Time Distribution Widget.

Tests utility functions for percentile calculation, histogram bucket assignment,
comparison logic, and and warning threshold detection.
"""

from __future__ import annotations

import pytest


def _calculate_percentiles(times: list[int]) -> dict:
    """Calculate P50, P95, P99 percentiles from a list of times."""
    if not times:
        return {"p50": None, "p95": None, "p99": None}

    sorted_times = sorted(times)
    n = len(sorted_times)

    def percentile(p: float) -> int:
        idx = min(int((p / 100) * n), n - 1)
        return sorted_times[idx]

    return {
        "p50": percentile(50),
        "p95": percentile(95),
        "p99": percentile(99),
    }


def _assign_bucket(time_ms: int) -> str:
    """Assign a time in ms to the correct histogram bucket."""
    if time_ms < 1000:
        return "0-1s"
    elif time_ms < 2000:
        return "1-2s"
    elif time_ms < 3000:
        return "2-3s"
    elif time_ms < 5000:
        return "3-5s"
    else:
        return "5s+"


def _calculate_comparison(current_ms: int | None, previous_ms: int | None) -> dict | None:
    """Calculate comparison between current and previous period."""
    if previous_ms is None or current_ms is None:
        return None

    delta_ms = current_ms - previous_ms
    delta_percent = round((delta_ms / previous_ms) * 100, 1) if previous_ms > 0 else 0

    if delta_percent > 5:
        trend = "degrading"
    elif delta_percent < -5:
        trend = "improving"
    else:
        trend = "stable"

    return {
        "deltaMs": delta_ms,
        "deltaPercent": delta_percent,
        "trend": trend,
    }


def _get_warning(p95: int | None) -> dict:
    """Determine warning state based on P95 value."""
    if p95 is None:
        return {"show": False, "message": "", "severity": "warning"}

    if p95 > 5000:
        return {
            "show": True,
            "message": "Consider optimizing knowledge base for faster responses",
            "severity": "critical",
        }
    elif p95 > 3000:
        return {
            "show": True,
            "message": "Response times are elevated, consider reviewing RAG configuration",
            "severity": "warning",
        }

    return {"show": False, "message": "", "severity": "warning"}


class TestPercentileCalculation:
    """Test percentile calculation logic."""

    def test_empty_data_returns_none(self):
        """Empty data should return None for all percentiles."""
        result = _calculate_percentiles([])
        assert result == {"p50": None, "p95": None, "p99": None}

    def test_single_value_returns_same_for_all(self):
        """Single value should return same value for all percentiles."""
        result = _calculate_percentiles([1000])
        assert result["p50"] == 1000
        assert result["p95"] == 1000
        assert result["p99"] == 1000

    def test_even_distribution(self):
        """Even distribution returns percentiles in order."""
        times = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
        result = _calculate_percentiles(times)
        assert result["p50"] == 600
        assert result["p95"] == 1000
        assert result["p99"] == 1000

    def test_skewed_distribution(self):
        """Skewed distribution returns correct percentiles."""
        times = [100, 100, 100, 100, 100, 100, 100, 5000]
        result = _calculate_percentiles(times)
        assert result["p50"] == 100
        assert result["p95"] == 5000


class TestHistogramBucketAssignment:
    """Test histogram bucket assignment logic."""

    def test_bucket_boundaries(self):
        """Test correct bucket assignment for various times."""
        assert _assign_bucket(500) == "0-1s"
        assert _assign_bucket(1500) == "1-2s"
        assert _assign_bucket(2500) == "2-3s"
        assert _assign_bucket(4000) == "3-5s"
        assert _assign_bucket(6000) == "5s+"

    def test_boundary_values(self):
        """Test boundary values between buckets."""
        assert _assign_bucket(999) == "0-1s"
        assert _assign_bucket(1000) == "1-2s"
        assert _assign_bucket(1999) == "1-2s"
        assert _assign_bucket(2000) == "2-3s"
        assert _assign_bucket(2999) == "2-3s"
        assert _assign_bucket(3000) == "3-5s"
        assert _assign_bucket(4999) == "3-5s"
        assert _assign_bucket(5000) == "5s+"


class TestPreviousPeriodComparison:
    """Test previous period comparison logic."""

    def test_improving_trend(self):
        """Lower current = improvement."""
        result = _calculate_comparison(1500, 2000)
        assert result is not None
        assert result["deltaMs"] == -500
        assert result["deltaPercent"] == -25.0
        assert result["trend"] == "improving"

    def test_degrading_trend(self):
        """Higher current = degrading."""
        result = _calculate_comparison(2500, 2000)
        assert result is not None
        assert result["deltaMs"] == 500
        assert result["deltaPercent"] == 25.0
        assert result["trend"] == "degrading"

    def test_stable_trend(self):
        """Same value = stable."""
        result = _calculate_comparison(2000, 2000)
        assert result is not None
        assert result["deltaMs"] == 0
        assert result["deltaPercent"] == 0
        assert result["trend"] == "stable"

    def test_null_previous_returns_null(self):
        """Null previous value returns null comparison."""
        result = _calculate_comparison(2000, None)
        assert result is None


class TestWarningThreshold:
    """Test warning detection logic."""

    def test_critical_warning(self):
        """P95 > 5000ms triggers critical warning."""
        result = _get_warning(5500)
        assert result["show"] is True
        assert result["severity"] == "critical"
        assert "optimizing" in result["message"].lower()

    def test_warning_threshold(self):
        """P95 > 3000ms triggers warning."""
        result = _get_warning(3500)
        assert result["show"] is True
        assert result["severity"] == "warning"

    def test_no_warning(self):
        """P95 < 3000ms triggers no warning."""
        result = _get_warning(2500)
        assert result["show"] is False

    def test_null_p95_no_warning(self):
        """Null P95 returns no warning."""
        result = _get_warning(None)
        assert result["show"] is False
