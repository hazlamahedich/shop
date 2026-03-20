"""API tests for Knowledge Effectiveness endpoint.

Story 10-7: Knowledge Effectiveness Widget

Tests the HTTP layer of knowledge effectiveness API using FastAPI TestClient.
"""

from __future__ import annotations

import os
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

os.environ["IS_TESTING"] = "true"

from fastapi.testclient import TestClient


class TestKnowledgeEffectivenessAPI:
    """API contract tests for /analytics/knowledge-effectiveness endpoint."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        from sqlalchemy.ext.asyncio import AsyncSession

        db = MagicMock(spec=AsyncSession)
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def client(self):
        """Create test client."""
        from app.main import app

        return TestClient(app)

    def test_get_knowledge_effectiveness_returns_correct_structure(self, client, mock_db):
        """Test that GET /analytics/knowledge-effectiveness returns correct structure."""
        response = client.get(
            "/api/v1/analytics/knowledge-effectiveness?days=7",
            headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "totalQueries" in data["data"]
        assert "successfulMatches" in data["data"]
        assert "noMatchRate" in data["data"]
        assert "avgConfidence" in data["data"]
        assert "trend" in data["data"]
        assert "lastUpdated" in data["data"]

    def test_get_knowledge_effectiveness_no_data(self, client, mock_db):
        """Test that no data returns zeros gracefully."""
        response = client.get(
            "/api/v1/analytics/knowledge-effectiveness?days=7",
            headers={"X-Test-Mode": "true", "X-Merchant-Id": "1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["totalQueries"] == 0
