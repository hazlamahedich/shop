"""Integration tests for onboarding API endpoints.

Tests prerequisite validation endpoint behavior.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_check_prerequisites_all_complete(async_client: AsyncClient) -> None:
    """Test check endpoint returns success when all prerequisites complete."""
    response = await async_client.get(
        "/api/onboarding/prerequisites/check",
        params={
            "cloudAccount": True,
            "facebookAccount": True,
            "shopifyAccess": True,
            "llmProviderChoice": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["isComplete"] is True
    assert data["data"]["missing"] == []
    assert "requestId" in data["meta"]
    assert "timestamp" in data["meta"]


@pytest.mark.asyncio
async def test_check_prerequisites_incomplete_raises_error(async_client: AsyncClient) -> None:
    """Test check endpoint raises error when prerequisites incomplete."""
    response = await async_client.get(
        "/api/onboarding/prerequisites/check",
        params={
            "cloudAccount": True,
            "facebookAccount": False,
            "shopifyAccess": True,
            "llmProviderChoice": True,
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == 2004  # PREREQUISITES_INCOMPLETE
    assert "Complete all prerequisites" in data["message"]
    assert "missing" in data["details"]
    assert "facebookAccount" in data["details"]["missing"]


@pytest.mark.asyncio
async def test_validate_prerequisites_all_complete(async_client: AsyncClient) -> None:
    """Test validate endpoint returns completion state without error."""
    response = await async_client.post(
        "/api/onboarding/prerequisites/validate",
        json={
            "cloudAccount": True,
            "facebookAccount": True,
            "shopifyAccess": True,
            "llmProviderChoice": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["isComplete"] is True
    assert data["data"]["missing"] == []


@pytest.mark.asyncio
async def test_validate_prerequisites_incomplete(async_client: AsyncClient) -> None:
    """Test validate endpoint returns missing items without error."""
    response = await async_client.post(
        "/api/onboarding/prerequisites/validate",
        json={
            "cloudAccount": False,
            "facebookAccount": False,
            "shopifyAccess": True,
            "llmProviderChoice": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["isComplete"] is False
    assert len(data["data"]["missing"]) == 2
    assert "cloudAccount" in data["data"]["missing"]
    assert "facebookAccount" in data["data"]["missing"]


@pytest.mark.asyncio
async def test_check_prerequisites_multiple_missing(async_client: AsyncClient) -> None:
    """Test check endpoint returns all missing prerequisites."""
    response = await async_client.get(
        "/api/onboarding/prerequisites/check",
        params={
            "cloudAccount": False,
            "facebookAccount": False,
            "shopifyAccess": False,
            "llmProviderChoice": False,
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert len(data["details"]["missing"]) == 4
    assert set(data["details"]["missing"]) == {
        "cloudAccount",
        "facebookAccount",
        "shopifyAccess",
        "llmProviderChoice",
    }


@pytest.fixture
async def async_client() -> AsyncClient:
    """Fixture for async HTTP client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
