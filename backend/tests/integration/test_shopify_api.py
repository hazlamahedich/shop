"""Integration tests for Shopify API endpoints.

Tests the complete OAuth flow and API endpoints with database integration.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_shopify_authorize_endpoint(async_client: AsyncClient, monkeypatch) -> None:
    """Test Shopify OAuth authorization endpoint.

    Args:
        async_client: Test HTTP client
        monkeypatch: pytest monkeypatch fixture
    """
    # Mock config
    def mock_settings():
        return {
            "SHOPIFY_API_KEY": "test_api_key",
            "SHOPIFY_REDIRECT_URI": "https://example.com/callback",
            "IS_TESTING": True,
        }

    monkeypatch.setattr("app.services.shopify.settings", mock_settings)

    response = await async_client.get(
        "/api/integrations/shopify/authorize",
        params={"merchant_id": 1, "shop_domain": "test-store.myshopify.com"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["authUrl"] is not None
    assert "test-store.myshopify.com" in data["data"]["authUrl"]
    assert data["data"]["state"] is not None


@pytest.mark.asyncio
async def test_shopify_authorize_invalid_domain(async_client: AsyncClient) -> None:
    """Test Shopify OAuth authorization with invalid domain.

    Args:
        async_client: Test HTTP client
    """
    response = await async_client.get(
        "/api/integrations/shopify/authorize",
        params={"merchant_id": 1, "shop_domain": "invalid.com"}
    )

    assert response.status_code == 400
    data = response.json()
    assert "Shop domain format is invalid" in data["detail"]["message"]


@pytest.mark.asyncio
async def test_shopify_status_not_connected(async_client: AsyncClient) -> None:
    """Test Shopify status endpoint when not connected.

    Args:
        async_client: Test HTTP client
    """
    response = await async_client.get(
        "/api/integrations/shopify/status",
        params={"merchant_id": 999}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["connected"] is False


@pytest.mark.asyncio
async def test_shopify_disconnect_not_connected(async_client: AsyncClient) -> None:
    """Test Shopify disconnect when not connected.

    Args:
        async_client: Test HTTP client
    """
    response = await async_client.delete(
        "/api/integrations/shopify/disconnect",
        params={"merchant_id": 999}
    )

    assert response.status_code == 400
    data = response.json()
    assert "not connected" in data["detail"]["message"].lower()


@pytest.mark.asyncio
async def test_shopify_test_webhook_not_connected(async_client: AsyncClient) -> None:
    """Test Shopify webhook test when not connected.

    Args:
        async_client: Test HTTP client
    """
    response = await async_client.post(
        "/api/integrations/shopify/test-webhook",
        params={"merchant_id": 999}
    )

    assert response.status_code == 400
    data = response.json()
    assert "not connected" in data["detail"]["message"].lower()
