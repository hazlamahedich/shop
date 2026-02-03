"""Integration tests for Shopify webhook processing.

Tests webhook signature verification and payload handling.
"""

from __future__ import annotations

import json
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_shopify_webhook_invalid_signature(async_client: AsyncClient) -> None:
    """Test Shopify webhook with invalid HMAC signature is rejected.

    Args:
        async_client: Test HTTP client
    """
    payload = {"id": "123", "email": "test@example.com"}
    headers = {
        "X-Shopify-Hmac-Sha256": "invalid_signature",
        "X-Shopify-Topic": "orders/create",
        "X-Shopify-Shop-Domain": "test.myshopify.com",
    }

    response = await async_client.post(
        "/api/webhooks/shopify",
        json=payload,
        headers=headers
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_shopify_webhook_valid_signature(async_client: AsyncClient, monkeypatch) -> None:
    """Test Shopify webhook with valid HMAC signature is accepted.

    Args:
        async_client: Test HTTP client
        monkeypatch: pytest monkeypatch fixture
    """
    import hmac
    import hashlib
    import base64

    # Mock config
    def mock_settings():
        return {"SHOPIFY_API_SECRET": "test_secret", "IS_TESTING": True}

    monkeypatch.setattr("app.api.webhooks.shopify.settings", mock_settings)

    payload = {"id": "123", "email": "test@example.com"}
    raw_payload = json.dumps(payload).encode()

    # Generate valid HMAC
    computed_hmac = hmac.new(
        b"test_secret",
        raw_payload,
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(computed_hmac).decode()

    headers = {
        "X-Shopify-Hmac-Sha256": signature,
        "X-Shopify-Topic": "orders/create",
        "X-Shopify-Shop-Domain": "test.myshopify.com",
    }

    response = await async_client.post(
        "/api/webhooks/shopify",
        content=raw_payload,
        headers=headers
    )

    # Should return 200 OK immediately (async processing)
    assert response.status_code == 200
    assert response.text == "OK"


@pytest.mark.asyncio
async def test_shopify_webhook_orders_create(async_client: AsyncClient, monkeypatch) -> None:
    """Test orders/create webhook handling.

    Args:
        async_client: Test HTTP client
        monkeypatch: pytest monkeypatch fixture
    """
    import hmac
    import hashlib
    import base64

    # Mock config
    def mock_settings():
        return {"SHOPIFY_API_SECRET": "test_secret", "IS_TESTING": True}

    monkeypatch.setattr("app.api.webhooks.shopify.settings", mock_settings)

    payload = {
        "id": "123456789",
        "email": "customer@example.com",
        "financial_status": "paid",
    }
    raw_payload = json.dumps(payload).encode()

    # Generate valid HMAC
    computed_hmac = hmac.new(
        b"test_secret",
        raw_payload,
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(computed_hmac).decode()

    headers = {
        "X-Shopify-Hmac-Sha256": signature,
        "X-Shopify-Topic": "orders/create",
        "X-Shopify-Shop-Domain": "test.myshopify.com",
    }

    response = await async_client.post(
        "/api/webhooks/shopify",
        content=raw_payload,
        headers=headers
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_shopify_webhook_orders_updated(async_client: AsyncClient, monkeypatch) -> None:
    """Test orders/updated webhook handling.

    Args:
        async_client: Test HTTP client
        monkeypatch: pytest monkeypatch fixture
    """
    import hmac
    import hashlib
    import base64

    # Mock config
    def mock_settings():
        return {"SHOPIFY_API_SECRET": "test_secret", "IS_TESTING": True}

    monkeypatch.setattr("app.api.webhooks.shopify.settings", mock_settings)

    payload = {
        "id": "123456789",
        "financial_status": "refunded",
    }
    raw_payload = json.dumps(payload).encode()

    # Generate valid HMAC
    computed_hmac = hmac.new(
        b"test_secret",
        raw_payload,
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(computed_hmac).decode()

    headers = {
        "X-Shopify-Hmac-Sha256": signature,
        "X-Shopify-Topic": "orders/updated",
        "X-Shopify-Shop-Domain": "test.myshopify.com",
    }

    response = await async_client.post(
        "/api/webhooks/shopify",
        content=raw_payload,
        headers=headers
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_shopify_webhook_orders_fulfilled(async_client: AsyncClient, monkeypatch) -> None:
    """Test orders/fulfilled webhook handling.

    Args:
        async_client: Test HTTP client
        monkeypatch: pytest monkeypatch fixture
    """
    import hmac
    import hashlib
    import base64

    # Mock config
    def mock_settings():
        return {"SHOPIFY_API_SECRET": "test_secret", "IS_TESTING": True}

    monkeypatch.setattr("app.api.webhooks.shopify.settings", mock_settings)

    payload = {
        "id": "123456789",
        "tracking_numbers": ["1Z999AA10123456784"],
    }
    raw_payload = json.dumps(payload).encode()

    # Generate valid HMAC
    computed_hmac = hmac.new(
        b"test_secret",
        raw_payload,
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(computed_hmac).decode()

    headers = {
        "X-Shopify-Hmac-Sha256": signature,
        "X-Shopify-Topic": "orders/fulfilled",
        "X-Shopify-Shop-Domain": "test.myshopify.com",
    }

    response = await async_client.post(
        "/api/webhooks/shopify",
        content=raw_payload,
        headers=headers
    )

    assert response.status_code == 200
