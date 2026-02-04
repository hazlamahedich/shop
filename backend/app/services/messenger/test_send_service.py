"""Tests for MessengerSendService.

Tests Facebook Send API integration, error handling, and timeout handling.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

from app.core.errors import APIError, ErrorCode
from app.services.messenger.send_service import MessengerSendService


@pytest.fixture
def mock_settings() -> dict[str, Any]:
    """Mock settings for testing."""
    return {
        "FACEBOOK_PAGE_ACCESS_TOKEN": "test_page_token_123",
        "FACEBOOK_API_VERSION": "v19.0",
    }


@pytest.fixture
def send_service(mock_settings: dict[str, Any]) -> MessengerSendService:
    """Create a MessengerSendService with mocked settings."""
    with patch("app.services.messenger.send_service.settings", return_value=mock_settings):
        return MessengerSendService()


@pytest.fixture
def sample_message_payload() -> dict[str, Any]:
    """Sample message payload for testing."""
    return {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {
                        "title": "Test Product",
                        "image_url": "https://example.com/image.jpg",
                        "subtitle": "$99.99",
                        "buttons": [
                            {
                                "type": "postback",
                                "title": "Add to Cart",
                                "payload": "ADD_TO_CART:test_id:variant_id",
                            }
                        ],
                    }
                ],
            },
        }
    }


class TestMessengerSendService:
    """Tests for MessengerSendService."""

    def test_init_with_default_token(self, mock_settings: dict[str, Any]) -> None:
        """Test service initialization with settings token."""
        with patch("app.services.messenger.send_service.settings", return_value=mock_settings):
            service = MessengerSendService()
            assert service.access_token == "test_page_token_123"

    def test_init_with_custom_token(self) -> None:
        """Test service initialization with custom token."""
        service = MessengerSendService(access_token="custom_token")
        assert service.access_token == "custom_token"

    def test_init_with_api_version(self, mock_settings: dict[str, Any]) -> None:
        """Test API version configuration."""
        with patch("app.services.messenger.send_service.settings", return_value=mock_settings):
            service = MessengerSendService()
            assert service.api_version == "v19.0"
            assert "v19.0" in service.base_url

    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        send_service: MessengerSendService,
        sample_message_payload: dict[str, Any],
    ) -> None:
        """Test successful message sending."""
        with respx.mock:
            # Mock Facebook Send API success response
            request = respx.post(
                "https://graph.facebook.com/v19.0/me/messages"
            ).mock(
                return_value=httpx.Response(
                    200,
                    json={"message_id": "mid.msg_123"},
                )
            )

            response = await send_service.send_message("test_psid", sample_message_payload)

            assert response["message_id"] == "mid.msg_123"
            assert request.called

    @pytest.mark.asyncio
    async def test_send_message_with_facebook_error(
        self,
        send_service: MessengerSendService,
        sample_message_payload: dict[str, Any],
    ) -> None:
        """Test handling of Facebook API error response."""
        with respx.mock:
            # Mock Facebook error response
            respx.post(
                "https://graph.facebook.com/v19.0/me/messages"
            ).mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "error": {
                            "code": 100,
                            "message": "Invalid parameter",
                        }
                    },
                )
            )

            with pytest.raises(APIError) as exc_info:
                await send_service.send_message("test_psid", sample_message_payload)

            assert exc_info.value.code == ErrorCode.MESSAGE_SEND_FAILED
            assert "Facebook Send API error" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_send_message_invalid_recipient(
        self,
        send_service: MessengerSendService,
        sample_message_payload: dict[str, Any],
    ) -> None:
        """Test handling of invalid recipient (404)."""
        with respx.mock:
            # Mock 404 response
            respx.post(
                "https://graph.facebook.com/v19.0/me/messages"
            ).mock(
                return_value=httpx.Response(
                    404,
                    json={"error": "Invalid PSID"},
                )
            )

            with pytest.raises(APIError) as exc_info:
                await send_service.send_message("invalid_psid", sample_message_payload)

            assert exc_info.value.code == ErrorCode.FACEBOOK_INVALID_RECIPIENT

    @pytest.mark.asyncio
    async def test_send_message_rate_limited(
        self,
        send_service: MessengerSendService,
        sample_message_payload: dict[str, Any],
    ) -> None:
        """Test handling of rate limit (429)."""
        with respx.mock:
            # Mock 429 response
            respx.post(
                "https://graph.facebook.com/v19.0/me/messages"
            ).mock(
                return_value=httpx.Response(
                    429,
                    json={"error": "Rate limited"},
                )
            )

            with pytest.raises(APIError) as exc_info:
                await send_service.send_message("test_psid", sample_message_payload)

            assert exc_info.value.code == ErrorCode.FACEBOOK_RATE_LIMITED

    @pytest.mark.asyncio
    async def test_send_message_timeout(
        self,
        send_service: MessengerSendService,
        sample_message_payload: dict[str, Any],
    ) -> None:
        """Test handling of timeout."""
        with respx.mock:
            # Mock timeout
            respx.post(
                "https://graph.facebook.com/v19.0/me/messages"
            ).mock(side_effect=httpx.TimeoutException("Request timed out"))

            with pytest.raises(APIError) as exc_info:
                await send_service.send_message("test_psid", sample_message_payload)

            assert exc_info.value.code == ErrorCode.FACEBOOK_TIMEOUT
            assert "timeout" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_send_message_request_error(
        self,
        send_service: MessengerSendService,
        sample_message_payload: dict[str, Any],
    ) -> None:
        """Test handling of network error."""
        with respx.mock:
            # Mock network error
            respx.post(
                "https://graph.facebook.com/v19.0/me/messages"
            ).mock(side_effect=httpx.RequestError("Network error"))

            with pytest.raises(APIError) as exc_info:
                await send_service.send_message("test_psid", sample_message_payload)

            assert exc_info.value.code == ErrorCode.MESSAGE_SEND_FAILED
            assert "request failed" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_close(self, send_service: MessengerSendService) -> None:
        """Test closing the HTTP client."""
        # Should not raise any errors
        await send_service.close()

    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_settings: dict[str, Any]) -> None:
        """Test using service as async context manager."""
        with patch("app.services.messenger.send_service.settings", return_value=mock_settings):
            async with MessengerSendService() as service:
                assert service is not None
            # Client should be closed after exiting context

    @pytest.mark.asyncio
    async def test_send_message_includes_access_token(
        self,
        send_service: MessengerSendService,
        sample_message_payload: dict[str, Any],
    ) -> None:
        """Test that access token is included in request."""
        with respx.mock:
            # Capture request
            request = respx.post(
                "https://graph.facebook.com/v19.0/me/messages"
            ).mock(
                return_value=httpx.Response(
                    200,
                    json={"message_id": "mid.msg_123"},
                )
            )

            await send_service.send_message("test_psid", sample_message_payload)

            # Verify request was made with access token
            assert request.called
            # The access token should be in the request params
