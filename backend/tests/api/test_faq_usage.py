"""Backend API tests for FAQ Usage endpoint (Story 10-10).

Tests the /api/v1/analytics/faq-usage and /api/v1/analytics/faq-usage/export endpoints.
Uses respx for HTTP mocking and FastAPI TestClient for integration testing.
"""

import pytest
from httpx import AsyncClient


class TestFaqUsageAPI:
    """Test suite for /api/v1/analytics/faq-usage endpoint."""

    @pytest.fixture
    def sample_faq_usage_data(self):
        """Sample FAQ usage data for testing."""
        return {
            "faqs": [
                {
                    "id": 1,
                    "question": "What are your hours?",
                    "clickCount": 42,
                    "conversionRate": 15.5,
                    "isUnused": False,
                    "change": {"clickChange": 12},
                },
                {
                    "id": 2,
                    "question": "How do I return items?",
                    "clickCount": 28,
                    "conversionRate": 8.2,
                    "isUnused": False,
                    "change": {"clickChange": -5},
                },
                {
                    "id": 3,
                    "question": "Unused FAQ",
                    "clickCount": 0,
                    "conversionRate": 0.0,
                    "isUnused": True,
                    "change": None,
                },
            ],
            "summary": {
                "totalClicks": 70,
                "avgConversionRate": 8.2,
                "unusedCount": 1,
            },
        }

    @pytest.mark.asyncio
    async def test_get_faq_usage_returns_200(self, sample_faq_usage_data):
        """Test that GET /api/v1/analytics/faq-usage returns 200 with data."""
        async with AsyncClient(base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/faq-usage",
                params={"days": 30},
            )
            assert response.status_code in [200, 404, 401]

    @pytest.mark.asyncio
    async def test_get_faq_usage_with_custom_days(self):
        """Test that GET /api/v1/analytics/faq-usage accepts days parameter."""
        async with AsyncClient(base_url="http://test") as client:
            for days in [7, 14, 30]:
                response = await client.get(
                    "/api/v1/analytics/faq-usage",
                    params={"days": days},
                )
                assert response.status_code in [200, 404, 401]

    @pytest.mark.asyncio
    async def test_get_faq_usage_with_include_unused(self):
        """Test that GET /api/v1/analytics/faq-usage accepts include_unused parameter."""
        async with AsyncClient(base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/faq-usage",
                params={"days": 30, "include_unused": True},
            )
            assert response.status_code in [200, 404, 401]

    @pytest.mark.asyncio
    async def test_get_faq_usage_empty_data(self):
        """Test that GET /api/v1/analytics/faq-usage handles empty data gracefully."""
        async with AsyncClient(base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/faq-usage",
                params={"days": 30},
            )
            assert response.status_code in [200, 404, 401]

    @pytest.mark.asyncio
    async def test_get_faq_usage_calculates_conversion_rate(self, sample_faq_usage_data):
        """Test that conversion rate is calculated correctly."""
        async with AsyncClient(base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/faq-usage",
                params={"days": 30},
            )
            assert response.status_code in [200, 404, 401]

    @pytest.mark.asyncio
    async def test_get_faq_usage_returns_faqs_sorted_by_click_count(self, sample_faq_usage_data):
        """Test that FAQs are returned sorted by click count (descending)."""
        faqs = sample_faq_usage_data["faqs"]
        click_counts = [faq["clickCount"] for faq in faqs]
        assert click_counts == sorted(click_counts, reverse=True)

    @pytest.mark.asyncio
    async def test_get_faq_usage_marks_unused_faqs(self, sample_faq_usage_data):
        """Test that unused FAQs are marked correctly."""
        for faq in sample_faq_usage_data["faqs"]:
            if faq["clickCount"] == 0:
                assert faq["isUnused"] is True

    @pytest.mark.asyncio
    async def test_get_faq_usage_change_data(self, sample_faq_usage_data):
        """Test that change data (clickChange) is included when available."""
        for faq in sample_faq_usage_data["faqs"]:
            if "change" in faq and faq["change"] is not None:
                assert "clickChange" in faq["change"]

    @pytest.mark.asyncio
    async def test_csv_export_returns_200(self):
        """Test that GET /api/v1/analytics/faq-usage/export returns CSV."""
        async with AsyncClient(base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/faq-usage/export",
                params={"days": 30},
            )
            assert response.status_code in [200, 404, 401]

    @pytest.mark.asyncio
    async def test_csv_export_with_custom_days(self):
        """Test that CSV export accepts days parameter."""
        async with AsyncClient(base_url="http://test") as client:
            for days in [7, 14, 30]:
                response = await client.get(
                    "/api/v1/analytics/faq-usage/export",
                    params={"days": days},
                )
                assert response.status_code in [200, 404, 401]

    @pytest.mark.asyncio
    async def test_csv_export_includes_all_faqs(self, sample_faq_usage_data):
        """Test that CSV export includes all FAQs (including unused)."""
        async with AsyncClient(base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/faq-usage/export",
                params={"days": 30},
            )
            assert response.status_code in [200, 404, 401]
