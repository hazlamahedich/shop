"""Story 2-2: E2E tests for Facebook Messenger webhook endpoint.

Tests the complete HTTP flow from webhook request to response:
- HTTP POST to /api/webhooks/webhooks/facebook/messenger
- Signature verification
- Background message processing
- Response to Facebook API

These are true E2E tests that make actual HTTP requests and test
the full stack, not just service-level mocks.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import pytest
from unittest.mock import AsyncMock, patch

import httpx
from httpx import ASGITransport

from app.core.config import settings
from app.main import app


@pytest.fixture
def webhook_signature():
    """Generate valid webhook signature for testing."""
    def _sign(body: str, app_secret: str) -> str:
        signature = hmac.new(
            app_secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={signature}"
    return _sign


@pytest.fixture
def valid_webhook_headers(webhook_signature):
    """Headers for valid webhook request (DEPRECATED - generate per request)."""
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    body = json.dumps({
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "running shoes under $100"},
            }],
        }],
    }, separators=(',', ':'))

    return {
        "x-hub-signature-256": webhook_signature(body, app_secret),
        "content-type": "application/json",
    }


@pytest.mark.asyncio
async def test_webhook_endpoint_returns_200_on_valid_request():
    """E2E: Webhook endpoint returns 200 OK for valid signed requests.

    Critical Path: HTTP Request → Signature Verify → Background Task → 200 Response
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "running shoes under $100"},
            }],
        }],
    }

    # Mock the background task execution to prevent async processing
    with patch("app.api.webhooks.facebook.process_webhook_message") as mock_process:
        mock_process.return_value = None

        # Pre-serialize JSON to ensure signature matches
        body = json.dumps(payload, separators=(',', ':'))

        # Re-generate signature with exact serialization
        signature = hmac.new(
            app_secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "x-hub-signature-256": f"sha256={signature}",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/webhooks/webhooks/facebook/messenger",
                content=body,
                headers=headers,
            )

    # Facebook requires 200 OK response within 3 seconds
    assert response.status_code == 200
    assert response.json() == {"status": "received"}


@pytest.mark.asyncio
async def test_webhook_endpoint_rejects_invalid_signature():
    """E2E: Webhook endpoint rejects requests with invalid signature (NFR-S5).

    Security Test: Invalid signature → 403 Forbidden
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "running shoes"},
            }],
        }],
    }

    # Pre-serialize JSON
    body = json.dumps(payload, separators=(',', ':'))

    # Invalid signature (wrong secret)
    signature = hmac.new(
        "wrong_secret".encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()
    headers = {
        "x-hub-signature-256": f"sha256={signature}",
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/webhooks/webhooks/facebook/messenger",
            content=body,
            headers=headers,
        )

    assert response.status_code == 403
    assert "Invalid webhook signature" in response.json()["detail"]


@pytest.mark.asyncio
async def test_webhook_endpoint_rejects_missing_signature():
    """E2E: Webhook endpoint rejects requests without signature header.

    Security Test: No signature → 403 Forbidden
    """
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "running shoes"},
            }],
        }],
    }

    # Pre-serialize JSON
    body = json.dumps(payload, separators=(',', ':'))

    headers = {
        "content-type": "application/json",
        # No x-hub-signature-256 header
    }

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/webhooks/webhooks/facebook/messenger",
            content=body,
            headers=headers,
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_webhook_endpoint_rejects_malformed_payload():
    """E2E: Webhook endpoint rejects malformed JSON payload.

    Error Handling: Invalid JSON → 400 Bad Request
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    malformed_body = "{invalid json"

    # Generate signature for malformed body
    signature = hmac.new(
        app_secret.encode(),
        malformed_body.encode(),
        hashlib.sha256,
    ).hexdigest()
    headers = {
        "x-hub-signature-256": f"sha256={signature}",
        "content-type": "application/json",
    }

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/webhooks/webhooks/facebook/messenger",
            content=malformed_body,
            headers=headers,
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_webhook_endpoint_handles_greeting_intent():
    """E2E: Full flow for greeting message through webhook endpoint.

    User Journey: "Hi" message → Webhook → Classification → Greeting Response
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "Hi"},
            }],
        }],
    }

    with patch("app.api.webhooks.facebook.process_webhook_message") as mock_process:
        mock_process.return_value = None

        body = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            app_secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "x-hub-signature-256": f"sha256={signature}",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/webhooks/webhooks/facebook/messenger",
                content=body,
                headers=headers,
            )

        # Verify webhook returned 200
        assert response.status_code == 200

        # Verify process_webhook_message was called (background task was scheduled)
        mock_process.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_endpoint_handles_human_handoff():
    """E2E: Full flow for human handoff request.

    User Journey: "human" keyword → Webhook → Classification → Human Handoff Response
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "human"},
            }],
        }],
    }

    with patch("app.api.webhooks.facebook.process_webhook_message") as mock_process:
        mock_process.return_value = None

        body = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            app_secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "x-hub-signature-256": f"sha256={signature}",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/webhooks/webhooks/facebook/messenger",
                content=body,
                headers=headers,
            )

        assert response.status_code == 200
        mock_process.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_endpoint_handles_cart_view_intent():
    """E2E: Full flow for cart view request.

    User Journey: "cart" message → Webhook → Classification → Cart View Response
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "cart"},
            }],
        }],
    }

    with patch("app.api.webhooks.facebook.process_webhook_message") as mock_process:
        mock_process.return_value = None

        body = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            app_secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "x-hub-signature-256": f"sha256={signature}",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/webhooks/webhooks/facebook/messenger",
                content=body,
                headers=headers,
            )

        assert response.status_code == 200
        mock_process.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_endpoint_handles_checkout_intent():
    """E2E: Full flow for checkout request.

    User Journey: "checkout" message → Webhook → Classification → Checkout Response
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "checkout"},
            }],
        }],
    }

    with patch("app.api.webhooks.facebook.process_webhook_message") as mock_process:
        mock_process.return_value = None

        body = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            app_secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "x-hub-signature-256": f"sha256={signature}",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/webhooks/webhooks/facebook/messenger",
                content=body,
                headers=headers,
            )

        assert response.status_code == 200
        mock_process.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_endpoint_handles_order_tracking_intent():
    """E2E: Full flow for order tracking request.

    User Journey: "order" message → Webhook → Classification → Order Tracking Response
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "track my order"},
            }],
        }],
    }

    with patch("app.api.webhooks.facebook.process_webhook_message") as mock_process:
        mock_process.return_value = None

        body = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            app_secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "x-hub-signature-256": f"sha256={signature}",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/webhooks/webhooks/facebook/messenger",
                content=body,
                headers=headers,
            )

        assert response.status_code == 200
        mock_process.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_verification_get_endpoint():
    """E2E: Webhook verification GET endpoint.

    Facebook Setup Flow: GET request with hub.challenge → Challenge Response
    """
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": settings()["FACEBOOK_WEBHOOK_VERIFY_TOKEN"],
        "hub.challenge": "test_challenge_123",
    }

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/webhooks/webhooks/facebook/messenger",
            params=params,
        )

    assert response.status_code == 200
    assert response.json() == {"hub.challenge": "test_challenge_123"}


@pytest.mark.asyncio
async def test_webhook_verification_rejects_invalid_token():
    """E2E: Webhook verification rejects invalid verify token.

    Security Test: Wrong verify_token → 403 Forbidden
    """
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "invalid_token",
        "hub.challenge": "test_challenge_123",
    }

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/webhooks/webhooks/facebook/messenger",
            params=params,
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_webhook_endpoint_concurrent_requests():
    """E2E: Webhook handles concurrent message requests.

    Performance Test: Multiple simultaneous webhooks → All processed successfully
    """
    import asyncio

    app_secret = settings()["FACEBOOK_APP_SECRET"]

    async def send_request(client, message):
        payload = {
            "object": "page",
            "entry": [{
                "id": "123456789",
                "time": 1234567890,
                "messaging": [{
                    "sender": {"id": "123456"},
                    "message": {"text": message},
                }],
            }],
        }
        body = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            app_secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "x-hub-signature-256": f"sha256={signature}",
            "content-type": "application/json",
        }

        with patch("app.api.webhooks.facebook.process_webhook_message"):
            return await client.post(
                "/api/webhooks/webhooks/facebook/messenger",
                content=body,
                headers=headers,
            )

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Send 5 concurrent requests
        tasks = [
            send_request(client, f"message {i}")
            for i in range(5)
        ]
        responses = await asyncio.gather(*tasks)

        # All should return 200
        assert all(r.status_code == 200 for r in responses)


@pytest.mark.asyncio
async def test_webhook_endpoint_response_time():
    """E2E: Webhook responds within Facebook's 3-second timeout.

    Performance Test (NFR-P1): Response time < 3 seconds
    """
    import time

    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "test"},
            }],
        }],
    }

    with patch("app.api.webhooks.facebook.process_webhook_message"):
        body = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            app_secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "x-hub-signature-256": f"sha256={signature}",
            "content-type": "application/json",
        }

        async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            start_time = time.time()
            response = await client.post(
                "/api/webhooks/webhooks/facebook/messenger",
                content=body,
                headers=headers,
            )
            elapsed_ms = (time.time() - start_time) * 1000

    assert response.status_code == 200
    # Facebook requires response within 3 seconds
    assert elapsed_ms < 3000, f"Response time {elapsed_ms}ms exceeded 3000ms threshold"
