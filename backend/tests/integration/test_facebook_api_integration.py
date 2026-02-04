"""Integration tests for Facebook API endpoints.

Tests the complete OAuth flow and connection status endpoints.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport
from sqlalchemy import select

from app.models.facebook_integration import FacebookIntegration
from app.models.merchant import Merchant
from app.core.security import encrypt_access_token
from app.core.config import settings


class TestFacebookOAuthFlow:
    """Integration tests for Facebook OAuth flow."""

    @pytest.mark.asyncio
    async def test_authorize_endpoint_returns_oauth_url(self, async_client):
        """Test that authorize endpoint returns valid OAuth URL."""
        response = await async_client.get("/api/integrations/facebook/authorize?merchant_id=1")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "authUrl" in data["data"]
        assert "state" in data["data"]
        assert data["data"]["authUrl"].startswith("https://www.facebook.com")
        assert len(data["data"]["state"]) >= 32

    @pytest.mark.asyncio
    async def test_authorize_missing_config_returns_error(self, async_client, monkeypatch):
        """Test that missing configuration returns appropriate error."""
        monkeypatch.delenv("FACEBOOK_APP_ID", raising=False)

        response = await async_client.get("/api/integrations/facebook/authorize?merchant_id=1")

        # Should return 400 with error details
        assert response.status_code in (400, 422)  # FastAPI may return either

    @pytest.mark.asyncio
    async def test_status_not_connected(self, async_client):
        """Test status endpoint when Facebook not connected."""
        response = await async_client.get("/api/integrations/facebook/status?merchant_id=1")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["connected"] is False

    @pytest.mark.asyncio
    async def test_status_connected(self, async_client, db_session):
        """Test status endpoint when Facebook is connected."""
        # Create merchant and integration
        merchant = Merchant(
            merchant_key="test_merchant_status",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        integration = FacebookIntegration(
            merchant_id=merchant.id,
            page_id="123456789",
            page_name="Test Store",
            page_picture_url="https://example.com/pic.jpg",
            access_token_encrypted=encrypt_access_token("test_token"),
            scopes=["pages_messaging"],
            status="active",
            webhook_verified=True,
        )
        db_session.add(integration)
        await db_session.flush()

        # Query with the actual merchant_id we just created
        response = await async_client.get(f"/api/integrations/facebook/status?merchant_id={merchant.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["connected"] is True
        assert data["data"]["pageId"] == "123456789"
        assert data["data"]["pageName"] == "Test Store"

    @pytest.mark.asyncio
    async def test_disconnect_not_connected(self, async_client):
        """Test disconnect when Facebook not connected."""
        response = await async_client.delete("/api/integrations/facebook/disconnect?merchant_id=999")

        # Should return error (400 or 404 depending on implementation)
        assert response.status_code in (400, 404)
        data = response.json()
        # Verify error structure
        assert "detail" in data or "error_code" in data


class TestFacebookWebhookEndpoints:
    """Integration tests for Facebook webhook endpoints."""

    @pytest.mark.asyncio
    async def test_webhook_verify_success(self, async_client, monkeypatch):
        """Test webhook verification with correct token."""
        settings.cache_clear()
        monkeypatch.setenv("FACEBOOK_WEBHOOK_VERIFY_TOKEN", "test_token")

        response = await async_client.get(
            "/api/webhooks/facebook",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "challenge_value",
                "hub.verify_token": "test_token",
            }
        )

        assert response.status_code == 200
        assert response.text == "challenge_value"

    @pytest.mark.asyncio
    async def test_webhook_verify_wrong_token(self, async_client, monkeypatch):
        """Test webhook verification fails with wrong token."""
        settings.cache_clear()
        monkeypatch.setenv("FACEBOOK_WEBHOOK_VERIFY_TOKEN", "correct_token")

        response = await async_client.get(
            "/api/webhooks/facebook",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "challenge_value",
                "hub.verify_token": "wrong_token",
            }
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_webhook_post_success(self, async_client, monkeypatch):
        """Test receiving webhook POST with valid signature."""
        import hmac
        import hashlib
        import json

        settings.cache_clear()
        monkeypatch.setenv("FACEBOOK_APP_SECRET", "test_secret")

        # Create webhook payload
        payload = {
            "object": "page",
            "entry": [{
                "id": "123456789",
                "time": 1458692752478,
                "messaging": [{
                    "sender": {"id": "111111111"},
                    "recipient": {"id": "123456789"},
                    "timestamp": 1458692752478,
                    "message": {
                        "mid": "mid.1457764197618:41d102a3e1ae206a38",
                        "text": "hello, world!",
                    }
                }]
            }]
        }

        raw_payload = json.dumps(payload).encode()
        signature = hmac.new(
            b"test_secret",
            raw_payload,
            hashlib.sha256
        ).hexdigest()
        signature_header = f"sha256={signature}"

        response = await async_client.post(
            "/api/webhooks/facebook",
            content=raw_payload,
            headers={"X-Hub-Signature-256": signature_header}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_webhook_post_invalid_signature(self, async_client, monkeypatch):
        """Test webhook POST fails with invalid signature."""
        settings.cache_clear()
        monkeypatch.setenv("FACEBOOK_APP_SECRET", "test_secret")

        response = await async_client.post(
            "/api/webhooks/facebook",
            content=b'{"test": "payload"}',
            headers={"X-Hub-Signature-256": "sha256=invalid_signature"}
        )

        assert response.status_code == 403


class TestFacebookWebhookTesting:
    """Integration tests for webhook testing endpoints."""

    @pytest.mark.asyncio
    async def test_test_webhook_not_connected(self, async_client):
        """Test webhook test endpoint when not connected."""
        response = await async_client.post("/api/integrations/facebook/test-webhook?merchant_id=1")

        assert response.status_code in (400, 404)
        data = response.json()
        assert "not connected" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_resubscribe_webhook_not_connected(self, async_client):
        """Test webhook resubscribe when not connected."""
        response = await async_client.post("/api/integrations/facebook/resubscribe-webhook?merchant_id=1")

        assert response.status_code in (400, 404)
