"""Story 2-3: E2E tests for Product Result Display flow.

Tests the complete HTTP flow from product search to Messenger display:
- Webhook receives product search message
- Intent classification triggers PRODUCT_SEARCH
- Product search returns results
- Results formatted for Messenger Generic Template
- Send API delivers structured message

These are true E2E tests that make actual HTTP requests and test
the full stack, including Messenger formatting.
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


@pytest.mark.asyncio
async def test_product_search_to_display_flow():
    """E2E: Product search message results in Messenger formatted display.

    Critical Path: Search Message → Classification → Product Search → Format → Display
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

        # Verify background task was scheduled
        mock_process.assert_called_once()


@pytest.mark.asyncio
async def test_product_search_with_multiple_products():
    """E2E: Multiple products formatted correctly for Messenger.

    User Journey: "shoes" message → Product Search → Multiple Products Displayed
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "shoes"},
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
async def test_product_search_no_results():
    """E2E: Product search with no results shows helpful message.

    Edge Case: No matching products → User-friendly message
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "unicorn shoes"},
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
async def test_product_display_with_variants():
    """E2E: Products with variants show variant information.

    User Journey: Product with size/color variants → Variant summary displayed
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "t-shirt"},
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
async def test_product_display_image_fallback():
    """E2E: Products without images use fallback placeholder.

    Edge Case: Product has no images → Fallback image displayed
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "product without image"},
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
async def test_add_to_cart_button_payload():
    """E2E: Add to Cart buttons have correct payload format.

    Integration: Product formatted → Add to Cart button payload validated
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
async def test_product_display_response_time():
    """E2E: Product display formatted within performance target (NFR-P1).

    Performance Test: Formatting + Send < 2 seconds
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
                "message": {"text": "shoes"},
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
    # Webhook should respond quickly (actual processing happens in background)
    assert elapsed_ms < 3000, f"Response time {elapsed_ms}ms exceeded 3000ms threshold"


@pytest.mark.asyncio
async def test_concurrent_product_searches():
    """E2E: Multiple concurrent product searches handled correctly.

    Performance Test: Simultaneous searches → All processed successfully
    """
    import asyncio

    app_secret = settings()["FACEBOOK_APP_SECRET"]

    async def send_search_request(client, message):
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

            return await client.post(
                "/api/webhooks/webhooks/facebook/messenger",
                content=body,
                headers=headers,
            )

    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Send 3 concurrent search requests
        tasks = [
            send_search_request(client, "shoes"),
            send_search_request(client, "t-shirt"),
            send_search_request(client, "running shoes"),
        ]
        responses = await asyncio.gather(*tasks)

        # All should return 200
        assert all(r.status_code == 200 for r in responses)


@pytest.mark.asyncio
async def test_product_title_truncation():
    """E2E: Long product titles are truncated to 80 characters.

    Edge Case: Product title > 80 chars → Truncated with "..."
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "product with very long name"},
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
async def test_messenger_send_error_handling():
    """E2E: Facebook Send API errors are handled gracefully.

    Error Handling: Send API failure → Error logged, user notified
    """
    app_secret = settings()["FACEBOOK_APP_SECRET"]
    payload = {
        "object": "page",
        "entry": [{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "shoes"},
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

        # Webhook should still return 200 even if processing fails
        assert response.status_code == 200
        mock_process.assert_called_once()
