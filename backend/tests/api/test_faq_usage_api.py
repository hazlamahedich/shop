"""Backend API tests for FAQ Usage endpoint (Story 10-10).
Tests the /api/v1/analytics/faq-usage and /api/v1/analytics/faq-usage/export endpoints.
Uses FastAPI TestClient for integration testing.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def sample_faq_usage_data():
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
                "clickCount": 27,
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
            "totalClicks": 69,
            "avgConversionRate": 7.9,
            "unusedCount": 1,
        },
    }


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestFaqUsageAPI:
    """Test suite for /api/v1/analytics/faq-usage endpoint."""

    def test_get_faq_usage_returns_200(self, client: TestClient):
        """Test that GET /api/v1/analytics/faq-usage returns 200."""
        response = client.get(
            "/api/v1/analytics/faq-usage?days=30",
            headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "faqs" in data
        assert "summary" in data

    def test_get_faq_usage_with_custom_days(self, client: TestClient):
        """Test that days parameter is accepted."""
        for days in [7, 14, 30]:
            response = client.get(
                f"/api/v1/analytics/faq-usage?days={days}",
                headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
            )
            assert response.status_code == 200

    def test_get_faq_usage_with_include_unused(self, client: TestClient):
        """Test that include_unused parameter is accepted."""
        response = client.get(
            "/api/v1/analytics/faq-usage?days=30&include_unused=true",
            headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
        )

        assert response.status_code == 200

    def test_get_faq_usage_empty_data(self, client: TestClient):
        """Test that empty data returns valid structure."""
        response = client.get(
            "/api/v1/analytics/faq-usage?days=30",
            headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "faqs" in data
        assert "summary" in data
        assert isinstance(data["faqs"], list)
        assert isinstance(data["summary"], dict)

    def test_get_faq_usage_response_structure(self, client: TestClient, sample_faq_usage_data):
        """Test that response has correct structure with sample data."""
        response = client.get(
            "/api/v1/analytics/faq-usage?days=30",
            headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "faqs" in data
        assert "summary" in data
        assert "period" in data

    def test_get_faq_usage_faqs_sorted_by_click_count(self, client: TestClient):
        """Test that FAQs are sorted by click count (descending)."""
        response = client.get(
            "/api/v1/analytics/faq-usage?days=30",
            headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()

        if len(data["faqs"]) > 1:
            click_counts = [faq["clickCount"] for faq in data["faqs"]]
            assert click_counts == sorted(click_counts, reverse=True)

    def test_get_faq_usage_marks_unused_faqs(self, client: TestClient):
        """Test that FAQs with 0 clicks are marked as unused."""
        response = client.get(
            "/api/v1/analytics/faq-usage?days=30&include_unused=true",
            headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()

        for faq in data["faqs"]:
            if faq["clickCount"] == 0:
                assert faq["isUnused"] is True

    def test_get_faq_usage_change_data_format(self, client: TestClient):
        """Test that change data has correct format when available."""
        response = client.get(
            "/api/v1/analytics/faq-usage?days=30",
            headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()

        for faq in data["faqs"]:
            if "change" in faq and faq["change"] is not None:
                assert "clickChange" in faq["change"]

    def test_csv_export_returns_200(self, client: TestClient):
        """Test that CSV export returns 200 with CSV content."""
        response = client.get(
            "/api/v1/analytics/faq-usage/export?days=30",
            headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_csv_export_with_custom_days(self, client: TestClient):
        """Test that CSV export accepts days parameter."""
        for days in [7, 14, 30]:
            response = client.get(
                f"/api/v1/analytics/faq-usage/export?days={days}",
                headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
            )
            assert response.status_code == 200

    def test_csv_export_includes_headers(self, client: TestClient):
        """Test that CSV export includes proper headers."""
        response = client.get(
            "/api/v1/analytics/faq-usage/export?days=30",
            headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        content = response.text
        assert "FAQ Question" in content
        assert "Clicks" in content
        assert "Conversion Rate" in content

    def test_csv_export_content_disposition_header(self, client: TestClient):
        """Test that CSV export has proper Content-Disposition header."""
        response = client.get(
            "/api/v1/analytics/faq-usage/export?days=30",
            headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        disposition = response.headers.get("content-disposition", "")
        assert "faq-usage" in disposition
        assert ".csv" in disposition
