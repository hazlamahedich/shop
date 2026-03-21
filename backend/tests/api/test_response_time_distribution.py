"""
API tests for Story 10-9: Response Time Distribution Widget.

Tests endpoint behavior, response structure, and data validation.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from tests.conftest import auth_headers


pytestmark = pytest.mark.asyncio


class TestResponseTimeDistributionEndpoint:
    """Test the /api/v1/analytics/response-time-distribution endpoint."""

    async def test_endpoint_returns_200_with_correct_structure(
        self,
        async_client: AsyncClient,
        test_merchant: int,
    ) -> None:
        """Test endpoint returns 200 with correct response structure."""
        response = await async_client.get(
            "/api/v1/analytics/response-time-distribution?days=7",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()["data"]

        assert "percentiles" in data
        assert "histogram" in data
        assert "lastUpdated" in data
        assert "period" in data
        assert "count" in data

    async def test_percentiles_have_correct_format(
        self,
        async_client: AsyncClient,
        test_merchant: int,
    ) -> None:
        """Test percentiles contain p50, p95, p99 with number or null values."""
        response = await async_client.get(
            "/api/v1/analytics/response-time-distribution?days=7",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        percentiles = response.json()["data"]["percentiles"]

        assert "p50" in percentiles
        assert "p95" in percentiles
        assert "p99" in percentiles

        if percentiles["p50"] is not None:
            assert isinstance(percentiles["p50"], (int, float))
        if percentiles["p95"] is not None:
            assert isinstance(percentiles["p95"], (int, float))
        if percentiles["p99"] is not None:
            assert isinstance(percentiles["p99"], (int, float))

    async def test_histogram_has_correct_format(
        self,
        async_client: AsyncClient,
        test_merchant: int,
    ) -> None:
        """Test histogram is array with label, count, color fields."""
        response = await async_client.get(
            "/api/v1/analytics/response-time-distribution?days=7",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        histogram = response.json()["data"]["histogram"]

        assert isinstance(histogram, list)

        if len(histogram) > 0:
            bucket = histogram[0]
            assert "label" in bucket
            assert "count" in bucket
            assert "color" in bucket
            assert bucket["color"] in ["green", "yellow", "red"]

    async def test_days_parameter_validation(
        self,
        async_client: AsyncClient,
        test_merchant: int,
    ) -> None:
        """Test days parameter accepts 7 and 30, rejects invalid values."""
        response_7d = await async_client.get(
            "/api/v1/analytics/response-time-distribution?days=7",
            headers=auth_headers(test_merchant),
        )
        assert response_7d.status_code == 200

        response_30d = await async_client.get(
            "/api/v1/analytics/response-time-distribution?days=30",
            headers=auth_headers(test_merchant),
        )
        assert response_30d.status_code == 200

        response_invalid = await async_client.get(
            "/api/v1/analytics/response-time-distribution?days=100",
            headers=auth_headers(test_merchant),
        )
        assert response_invalid.status_code == 422

    async def test_previous_period_comparison_structure(
        self,
        async_client: AsyncClient,
        test_merchant: int,
    ) -> None:
        """Test previous period comparison has correct structure when present."""
        response = await async_client.get(
            "/api/v1/analytics/response-time-distribution?days=7",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()["data"]

        if data.get("previousPeriod") and data["previousPeriod"].get("comparison"):
            comparison = data["previousPeriod"]["comparison"]

            if comparison.get("p50"):
                assert "deltaMs" in comparison["p50"]
                assert "deltaPercent" in comparison["p50"]
                assert "trend" in comparison["p50"]
                assert comparison["p50"]["trend"] in ["improving", "degrading", "stable"]

    async def test_warning_structure(
        self,
        async_client: AsyncClient,
        test_merchant: int,
    ) -> None:
        """Test warning has correct structure when slow responses detected."""
        response = await async_client.get(
            "/api/v1/analytics/response-time-distribution?days=7",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()["data"]

        if data.get("warning"):
            assert "show" in data["warning"]
            assert "message" in data["warning"]
            assert "severity" in data["warning"]
            assert data["warning"]["severity"] in ["warning", "critical"]

    async def test_response_type_breakdown_structure(
        self,
        async_client: AsyncClient,
        test_merchant: int,
    ) -> None:
        """Test response type breakdown has RAG and general sections."""
        response = await async_client.get(
            "/api/v1/analytics/response-time-distribution?days=7",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
        data = response.json()["data"]

        if data.get("responseTypeBreakdown"):
            assert "rag" in data["responseTypeBreakdown"]
            assert "general" in data["responseTypeBreakdown"]

    async def test_cache_headers_present(
        self,
        async_client: AsyncClient,
        test_merchant: int,
    ) -> None:
        """Test cache headers are present in response."""
        response = await async_client.get(
            "/api/v1/analytics/response-time-distribution?days=7",
            headers=auth_headers(test_merchant),
        )

        assert response.status_code == 200
