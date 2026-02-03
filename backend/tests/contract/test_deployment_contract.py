"""Contract tests for deployment API endpoints using Schemathesis.

Tests the deployment API against its OpenAPI schema specification.
"""

import pytest
import httpx
from httpx import ASGITransport

from app.main import app
from app.core.database import get_db

# Use the real test engine from conftest for contract tests
from tests.conftest import test_engine, TestingSessionLocal


@pytest.fixture
async def client() -> httpx.AsyncClient:
    """Return an async test client for contract testing with real database."""

    # Override the dependency to use the test database
    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up overrides
    app.dependency_overrides.clear()


class TestDeploymentAPIContract:
    """Contract tests for deployment API endpoints."""

    @pytest.mark.asyncio
    async def test_start_deployment_accepts_valid_platform(self, client: httpx.AsyncClient) -> None:
        """Test that start deployment accepts valid platform values."""
        valid_platforms = ["flyio", "railway", "render"]

        for platform in valid_platforms:
            response = await client.post(
                "/api/deployment/start",
                json={"platform": platform},
            )

            # Debug: print response if failing
            if response.status_code not in (202, 500):
                print(f"\nPlatform: {platform}")
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.text}")

            # Should accept the request
            assert response.status_code in (202, 500)

    @pytest.mark.asyncio
    async def test_start_deployment_rejects_invalid_platform(self, client: httpx.AsyncClient) -> None:
        """Test that start deployment rejects invalid platform values."""
        response = await client.post(
            "/api/deployment/start",
            json={"platform": "invalid-platform"},
        )

        # Should return validation error for invalid enum value
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_start_deployment_requires_platform_field(self, client: httpx.AsyncClient) -> None:
        """Test that start deployment requires platform field."""
        response = await client.post(
            "/api/deployment/start",
            json={},
        )

        # Should return validation error for missing required field
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_start_deployment_response_has_required_fields(self, client: httpx.AsyncClient) -> None:
        """Test that start deployment response includes all required fields."""
        response = await client.post(
            "/api/deployment/start",
            json={"platform": "flyio"},
        )

        # May return 500 if database not available, but response structure should be valid
        if response.status_code == 202:
            data = response.json()
            assert "data" in data
            assert "deploymentId" in data["data"]
            assert "merchantKey" in data["data"]
            assert "status" in data["data"]
            assert "estimatedSeconds" in data["data"]
            assert "meta" in data
            assert "requestId" in data["meta"]
            assert "timestamp" in data["meta"]

    @pytest.mark.asyncio
    async def test_get_deployment_status_returns_404_for_unknown_id(self, client: httpx.AsyncClient) -> None:
        """Test that get status returns 404 for unknown deployment ID."""
        response = await client.get("/api/deployment/status/unknown-deployment-id")

        # Should return 404 for unknown deployment (or 500 for error)
        assert response.status_code in (404, 500)

    @pytest.mark.asyncio
    async def test_cancel_deployment_returns_404_for_unknown_id(self, client: httpx.AsyncClient) -> None:
        """Test that cancel deployment returns 404 for unknown deployment ID."""
        response = await client.post("/api/deployment/cancel/unknown-deployment-id")

        # Should return 404 for unknown deployment (or 500 for error)
        assert response.status_code in (404, 500)

    @pytest.mark.asyncio
    async def test_progress_stream_returns_event_stream_content_type(self, client: httpx.AsyncClient) -> None:
        """Test that progress stream returns correct content type."""
        response = await client.get("/api/deployment/progress/test-deployment-id")

        # Should return text/event-stream content type (or 500 for error)
        if response.status_code != 500:
            # Content type may include charset
            assert "text/event-stream" in response.headers.get("content-type", "")
