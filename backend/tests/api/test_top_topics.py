"""API tests for Top Topics endpoint.

Story 10-8: Top Topics Widget

Tests the HTTP layer of top topics API using FastAPI TestClient.
Uses mocked service to avoid database dependency.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ["IS_TESTING"] = "true"

from fastapi.testclient import TestClient


class TestTopTopicsAPI:
    """API contract tests for /analytics/top-topics endpoint."""

    @pytest.fixture
    def client(self):
        from app.main import app

        return TestClient(app)

    @pytest.fixture
    def mock_service(self):
        mock = MagicMock()
        mock.get_top_topics = AsyncMock(
            return_value={
                "topics": [
                    {"name": "shipping cost", "queryCount": 45, "trend": "up"},
                    {"name": "return policy", "queryCount": 32, "trend": "stable"},
                ],
                "lastUpdated": "2026-03-20T00:00:00Z",
                "period": {
                    "days": 7,
                    "startDate": "2026-03-13T00:00:00Z",
                    "endDate": "2026-03-20T00:00:00Z",
                },
            }
        )
        return mock

    def test_get_top_topics_returns_correct_structure(self, client, mock_service):
        with patch("app.api.analytics.AggregatedAnalyticsService", return_value=mock_service):
            response = client.get(
                "/api/v1/analytics/top-topics?days=7",
                headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "topics" in data["data"]
        assert "lastUpdated" in data["data"]
        assert "period" in data["data"]
        assert isinstance(data["data"]["topics"], list)

    def test_get_top_topics_topic_structure(self, client, mock_service):
        with patch("app.api.analytics.AggregatedAnalyticsService", return_value=mock_service):
            response = client.get(
                "/api/v1/analytics/top-topics?days=7",
                headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
            )

        assert response.status_code == 200
        data = response.json()

        if len(data["data"]["topics"]) > 0:
            topic = data["data"]["topics"][0]
            assert "name" in topic
            assert "queryCount" in topic
            assert "trend" in topic
            assert topic["trend"] in ["up", "down", "stable", "new"]

    def test_get_top_topics_no_data_returns_empty_list(self, client):
        mock_service = MagicMock()
        mock_service.get_top_topics = AsyncMock(
            return_value={
                "topics": [],
                "lastUpdated": "2026-03-20T00:00:00Z",
                "period": {"days": 7},
            }
        )

        with patch("app.api.analytics.AggregatedAnalyticsService", return_value=mock_service):
            response = client.get(
                "/api/v1/analytics/top-topics?days=7",
                headers={"X-Test-Mode": "true", "X-Merchant-Id": "99999"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["topics"] == []
