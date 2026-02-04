"""Tests for Facebook webhook endpoint.

Unit tests for webhook parsing, signature verification, and response handling.
"""

from __future__ import annotations

import json
from typing import Optional, Dict, Any
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from app.api.webhooks.facebook import (
    facebook_messenger_webhook,
    facebook_webhook_verify,
    process_webhook_message,
    send_messenger_response,
    verify_facebook_webhook_signature,
)


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    from fastapi import Request

    class MockRequest:
        def __init__(self, body: bytes, headers: dict | None = None):
            self._body = body
            self._headers = headers or {}

        async def body(self):
            return self._body

        def headers(self):
            return self._headers

        @property
        def headers(self):
            return self._headers

        async def json(self):
            return json.loads(self._body.decode())

    return MockRequest


@pytest.mark.asyncio
async def test_webhook_signature_valid():
    """Test valid webhook signature verification."""
    from fastapi import Request

    with patch("app.api.webhooks.facebook.settings") as mock_settings:
        mock_settings.return_value = {"FACEBOOK_APP_SECRET": "test_secret"}

        app_secret = "test_secret"
        raw_body = b'{"test": "data"}'

        # Compute valid signature
        import hmac
        import hashlib
        expected_sig = hmac.new(
            app_secret.encode(),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        class MockRequest:
            headers = {"x-hub-signature-256": f"sha256={expected_sig}"}

        request = MockRequest()
        result = verify_facebook_webhook_signature(request, raw_body)

        assert result is True


@pytest.mark.asyncio
async def test_webhook_signature_invalid():
    """Test invalid webhook signature verification."""
    class MockRequest:
        headers = {"x-hub-signature-256": "sha256=invalid_signature"}

    request = MockRequest()
    raw_body = b'{"test": "data"}'

    with patch("app.api.webhooks.facebook.settings") as mock_settings:
        mock_settings.return_value = {"FACEBOOK_APP_SECRET": "test_secret"}

        result = verify_facebook_webhook_signature(request, raw_body)

        assert result is False


@pytest.mark.asyncio
async def test_webhook_signature_missing():
    """Test missing webhook signature."""
    class MockRequest:
        headers = {}

    request = MockRequest()
    raw_body = b'{"test": "data"}'

    result = verify_facebook_webhook_signature(request, raw_body)

    assert result is False


@pytest.mark.asyncio
async def test_facebook_webhook_verify_valid():
    """Test Facebook webhook verification with valid token."""
    from fastapi import Request

    with patch("app.api.webhooks.facebook.settings") as mock_settings:
        mock_settings.return_value = {"FACEBOOK_WEBHOOK_VERIFY_TOKEN": "test_token"}

        class MockRequest:
            query_params = {
                "hub.mode": "subscribe",
                "hub.verify_token": "test_token",
                "hub.challenge": "challenge_code",
            }

        request = MockRequest()
        response = await facebook_webhook_verify(request)

        assert response.status_code == 200
        assert "challenge" in response.body.decode()


@pytest.mark.asyncio
async def test_facebook_webhook_verify_invalid_token():
    """Test Facebook webhook verification with invalid token."""
    with patch("app.api.webhooks.facebook.settings") as mock_settings:
        mock_settings.return_value = {"FACEBOOK_WEBHOOK_VERIFY_TOKEN": "correct_token"}

        class MockRequest:
            query_params = {
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "challenge_code",
            }

        request = MockRequest()

        with pytest.raises(HTTPException) as exc_info:
            await facebook_webhook_verify(request)

        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_facebook_messenger_webhook_valid():
    """Test processing valid Facebook Messenger webhook."""
    with patch("app.api.webhooks.facebook.verify_facebook_webhook_signature") as mock_verify:
        mock_verify.return_value = True

        with patch("app.api.webhooks.facebook.MessageProcessor") as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor_class.return_value = mock_processor

            payload_data = {
                "object": "page",
                "entry": [{
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "123456"},
                        "message": {"text": "test message"},
                    }],
                }],
            }

            from fastapi import Request

            class MockRequest:
                async def body(self):
                    return json.dumps(payload_data).encode()

                async def json(self):
                    return payload_data

                headers = {}

            request = MockRequest()

            with patch("app.api.webhooks.facebook.BackgroundTasks") as mock_bg:
                mock_bg = MagicMock()
                response = await facebook_messenger_webhook(request, mock_bg)

                assert response.status_code == 200


@pytest.mark.asyncio
async def test_facebook_messenger_webhook_invalid_signature():
    """Test webhook with invalid signature raises 403."""
    with patch("app.api.webhooks.facebook.verify_facebook_webhook_signature") as mock_verify:
        mock_verify.return_value = False

        payload_data = {
            "object": "page",
            "entry": [],
        }

        from fastapi import Request

        class MockRequest:
            async def body(self):
                return json.dumps(payload_data).encode()

            async def json(self):
                return payload_data

            headers = {}

        request = MockRequest()

        with patch("app.api.webhooks.facebook.BackgroundTasks"):
            with pytest.raises(HTTPException) as exc_info:
                await facebook_messenger_webhook(request, MagicMock())

            assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_facebook_messenger_webhook_invalid_payload():
    """Test webhook with invalid payload raises 400."""
    with patch("app.api.webhooks.facebook.verify_facebook_webhook_signature") as mock_verify:
        mock_verify.return_value = True

        from fastapi import Request

        class MockRequest:
            async def body(self):
                return b"invalid json"

            async def json(self):
                raise ValueError("Invalid JSON")

            headers = {}

        request = MockRequest()

        with patch("app.api.webhooks.facebook.BackgroundTasks"):
            with pytest.raises(HTTPException) as exc_info:
                await facebook_messenger_webhook(request, MagicMock())

            assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_process_webhook_message():
    """Test processing webhook message in background."""
    with patch("app.api.webhooks.facebook.MessageProcessor") as mock_processor_class:
        mock_processor = AsyncMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_response.recipient_id = "123456"
        mock_processor.process_message.return_value = mock_response
        mock_processor_class.return_value = mock_processor

        from app.schemas.messaging import FacebookWebhookPayload

        payload = FacebookWebhookPayload(
            object="page",
            entry=[{
                "id": "123456789",
                "time": 1234567890,
                "messaging": [{
                    "sender": {"id": "123456"},
                    "message": {"text": "test message"},
                }],
            }],
        )

        with patch("app.api.webhooks.facebook.send_messenger_response") as mock_send:
            await process_webhook_message(mock_processor, payload)

            mock_processor.process_message.assert_called_once_with(payload)
            mock_send.assert_called_once_with(mock_response)
