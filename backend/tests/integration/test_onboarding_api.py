"""Integration tests for onboarding API endpoints.

Tests prerequisite validation and CRUD endpoint behavior.
Story 1.2: Tests localStorage to PostgreSQL migration endpoints.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.onboarding import PrerequisiteChecklist
from app.models.merchant import Merchant
from sqlalchemy import select


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


# ============================================================================
# Story 1.2: localStorage to PostgreSQL Migration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_prerequisite_state_not_found(async_client: AsyncClient) -> None:
    """Test GET /prerequisites returns null when no state exists."""
    response = await async_client.get("/api/onboarding/prerequisites?merchant_id=999")

    assert response.status_code == 200
    data = response.json()
    assert data["data"] is None
    assert "requestId" in data["meta"]


@pytest.mark.asyncio
async def test_upsert_prerequisite_state_create(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test POST /prerequisites creates new state."""
    # Create a merchant first
    merchant = Merchant(
        merchant_key="test_merchant_1",
        platform="shopify",
        status="pending",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    response = await async_client.post(
        f"/api/onboarding/prerequisites?merchant_id={merchant_id}",
        json={
            "hasCloudAccount": True,
            "hasFacebookAccount": True,
            "hasShopifyAccess": False,
            "hasLlmProviderChoice": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["merchantId"] == merchant_id
    assert data["data"]["hasCloudAccount"] is True
    assert data["data"]["hasFacebookAccount"] is True
    assert data["data"]["hasShopifyAccess"] is False
    assert data["data"]["hasLlmProviderChoice"] is True
    assert data["data"]["isComplete"] is False  # Not all complete
    assert data["data"]["completedAt"] is None
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_upsert_prerequisite_state_complete(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test POST /prerequisites with all complete sets completed_at."""
    # Create a merchant first
    merchant = Merchant(
        merchant_key="test_merchant_complete",
        platform="shopify",
        status="pending",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    response = await async_client.post(
        f"/api/onboarding/prerequisites?merchant_id={merchant_id}",
        json={
            "hasCloudAccount": True,
            "hasFacebookAccount": True,
            "hasShopifyAccess": True,
            "hasLlmProviderChoice": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["isComplete"] is True
    assert data["data"]["completedAt"] is not None


@pytest.mark.asyncio
async def test_upsert_prerequisite_state_update(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test POST /prerequisites updates existing state."""
    # Create a merchant first
    merchant = Merchant(
        merchant_key="test_merchant_update",
        platform="shopify",
        status="pending",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    # Create initial state
    await async_client.post(
        f"/api/onboarding/prerequisites?merchant_id={merchant_id}",
        json={
            "hasCloudAccount": False,
            "hasFacebookAccount": False,
            "hasShopifyAccess": False,
            "hasLlmProviderChoice": False,
        },
    )

    # Update to all complete
    response = await async_client.post(
        f"/api/onboarding/prerequisites?merchant_id={merchant_id}",
        json={
            "hasCloudAccount": True,
            "hasFacebookAccount": True,
            "hasShopifyAccess": True,
            "hasLlmProviderChoice": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["isComplete"] is True
    assert data["data"]["completedAt"] is not None


@pytest.mark.asyncio
async def test_sync_prerequisite_state(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test POST /prerequisites/sync migrates localStorage state."""
    # Create a merchant first
    merchant = Merchant(
        merchant_key="test_merchant_sync",
        platform="shopify",
        status="pending",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    # Simulate localStorage data migration
    response = await async_client.post(
        f"/api/onboarding/prerequisites/sync?merchant_id={merchant_id}",
        json={
            "cloudAccount": True,
            "facebookAccount": True,
            "shopifyAccess": True,
            "llmProviderChoice": False,
            "updatedAt": "2026-02-03T12:00:00Z",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["merchantId"] == merchant_id
    assert data["data"]["hasCloudAccount"] is True
    assert data["data"]["hasFacebookAccount"] is True
    assert data["data"]["hasShopifyAccess"] is True
    assert data["data"]["hasLlmProviderChoice"] is False
    assert data["data"]["isComplete"] is False


@pytest.mark.asyncio
async def test_delete_prerequisite_state(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test DELETE /prerequisites removes state."""
    # Create a merchant first
    merchant = Merchant(
        merchant_key="test_merchant_delete",
        platform="shopify",
        status="pending",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    # Create state first
    await async_client.post(
        f"/api/onboarding/prerequisites?merchant_id={merchant_id}",
        json={
            "hasCloudAccount": True,
            "hasFacebookAccount": True,
            "hasShopifyAccess": True,
            "hasLlmProviderChoice": True,
        },
    )

    # Delete it
    response = await async_client.delete(f"/api/onboarding/prerequisites?merchant_id={merchant_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["deleted"] is True

    # Verify it's gone
    get_response = await async_client.get(f"/api/onboarding/prerequisites?merchant_id={merchant_id}")
    get_data = get_response.json()
    assert get_data["data"] is None


@pytest.mark.asyncio
async def test_delete_prerequisite_state_not_found(async_client: AsyncClient) -> None:
    """Test DELETE /prerequisites with non-existent merchant."""
    response = await async_client.delete("/api/onboarding/prerequisites?merchant_id=999")

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["deleted"] is False


@pytest.mark.asyncio
async def test_get_after_create(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test GET /prerequisites returns previously created state."""
    # Create a merchant first
    merchant = Merchant(
        merchant_key="test_merchant_get_after",
        platform="shopify",
        status="pending",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    # Create state
    await async_client.post(
        f"/api/onboarding/prerequisites?merchant_id={merchant_id}",
        json={
            "hasCloudAccount": True,
            "hasFacebookAccount": False,
            "hasShopifyAccess": True,
            "hasLlmProviderChoice": True,
        },
    )

    # Get it back
    response = await async_client.get(f"/api/onboarding/prerequisites?merchant_id={merchant_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["merchantId"] == merchant_id
    assert data["data"]["hasCloudAccount"] is True
    assert data["data"]["hasFacebookAccount"] is False
    assert data["data"]["hasShopifyAccess"] is True
    assert data["data"]["hasLlmProviderChoice"] is True


@pytest.mark.asyncio
async def test_get_prerequisite_state_after_update(async_client: AsyncClient, db_session: AsyncSession) -> None:
    """Test GET /prerequisites returns updated state after modification."""
    # Create a merchant first
    merchant = Merchant(
        merchant_key="test_merchant_get_after_update",
        platform="shopify",
        status="pending",
    )
    db_session.add(merchant)
    await db_session.commit()
    merchant_id = merchant.id

    # Create initial state
    await async_client.post(
        f"/api/onboarding/prerequisites?merchant_id={merchant_id}",
        json={
            "hasCloudAccount": False,
            "hasFacebookAccount": False,
            "hasShopifyAccess": False,
            "hasLlmProviderChoice": False,
        },
    )

    # Update state
    await async_client.post(
        f"/api/onboarding/prerequisites?merchant_id={merchant_id}",
        json={
            "hasCloudAccount": True,
            "hasFacebookAccount": True,
            "hasShopifyAccess": True,
            "hasLlmProviderChoice": True,
        },
    )

    # Get updated state
    response = await async_client.get(f"/api/onboarding/prerequisites?merchant_id={merchant_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["hasCloudAccount"] is True
    assert data["data"]["hasFacebookAccount"] is True
    assert data["data"]["hasShopifyAccess"] is True
    assert data["data"]["hasLlmProviderChoice"] is True
    assert data["data"]["isComplete"] is True
    assert data["data"]["completedAt"] is not None
