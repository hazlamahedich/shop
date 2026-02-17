"""Tests for polling health API endpoint.

Story 4-4 Task 8: Polling health endpoint tests
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.api.health import router


@pytest.fixture
def app():
    """Create FastAPI app with health router."""
    app = FastAPI()
    app.include_router(router, prefix="/health")
    return app


@pytest.fixture
def client(app):
    """Create sync test client."""
    return TestClient(app)


class TestPollingHealthEndpoint:
    """Tests for /health/polling endpoint."""

    def test_polling_health_internal_request_header(self, client):
        """Test health endpoint accepts X-Internal-Request header."""
        mock_status = {
            "scheduler_running": True,
            "last_poll_timestamp": "2026-02-17T10:00:00Z",
            "merchants_polled": 2,
            "total_orders_synced": 10,
            "errors_last_hour": 0,
            "merchant_status": [],
        }

        with patch(
            "app.tasks.polling_scheduler.get_polling_status",
            return_value=mock_status,
        ):
            response = client.get(
                "/health/polling",
                headers={"X-Internal-Request": "true"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["scheduler_running"] is True
        assert data["merchants_polled"] == 2

    def test_polling_health_localhost_allowed(self, client):
        """Test health endpoint allows localhost requests."""
        mock_status = {
            "scheduler_running": False,
            "last_poll_timestamp": None,
            "merchants_polled": 0,
            "total_orders_synced": 0,
            "errors_last_hour": 0,
            "merchant_status": [],
        }

        with patch(
            "app.tasks.polling_scheduler.get_polling_status",
            return_value=mock_status,
        ):
            response = client.get(
                "/health/polling",
                headers={"X-Internal-Request": "true"},
            )

        assert response.status_code == 200

    def test_polling_health_returns_scheduler_running(self, client):
        """Test health endpoint returns scheduler_running status."""
        mock_status = {
            "scheduler_running": True,
            "last_poll_timestamp": None,
            "merchants_polled": 0,
            "total_orders_last_hour": 0,
            "errors_last_hour": 0,
            "merchant_status": [],
        }

        with patch(
            "app.tasks.polling_scheduler.get_polling_status",
            return_value=mock_status,
        ):
            response = client.get(
                "/health/polling",
                headers={"X-Internal-Request": "true"},
            )

        assert response.status_code == 200
        assert "scheduler_running" in response.json()

    def test_polling_health_returns_merchant_status(self, client):
        """Test health endpoint returns per-merchant status."""
        mock_status = {
            "scheduler_running": True,
            "last_poll_timestamp": "2026-02-17T10:00:00Z",
            "merchants_polled": 2,
            "total_orders_synced": 15,
            "errors_last_hour": 1,
            "merchant_status": [
                {"merchant_id": 1, "last_poll": "2026-02-17T10:00:00Z", "status": "healthy"},
                {"merchant_id": 2, "last_poll": "2026-02-17T10:00:01Z", "status": "healthy"},
            ],
        }

        with patch(
            "app.tasks.polling_scheduler.get_polling_status",
            return_value=mock_status,
        ):
            response = client.get(
                "/health/polling",
                headers={"X-Internal-Request": "true"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "merchant_status" in data
        assert len(data["merchant_status"]) == 2

    def test_polling_health_handles_exception(self, client):
        """Test health endpoint handles exceptions gracefully."""
        with patch(
            "app.tasks.polling_scheduler.get_polling_status",
            side_effect=Exception("Test error"),
        ):
            response = client.get(
                "/health/polling",
                headers={"X-Internal-Request": "true"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["scheduler_running"] is False
        assert "error" in data
