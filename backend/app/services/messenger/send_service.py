"""Messenger Send Service.

Handles sending messages to Facebook Messenger using the Send API.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.errors import APIError, ErrorCode

import httpx
import structlog


class MessengerSendService:
    """Service for sending messages to Facebook Messenger.

    Uses Facebook Send API to deliver structured messages to users.
    Handles authentication, error handling, and retry logic.
    """

    # Facebook API configuration
    API_VERSION = "v19.0"
    SEND_TIMEOUT = 5.0  # 5 seconds

    def __init__(self, access_token: Optional[str] = None) -> None:
        """Initialize Messenger Send service.

        Args:
            access_token: Facebook Page Access Token (uses settings if not provided)
        """
        config = settings()
        self.access_token = access_token or config.get("FACEBOOK_PAGE_ACCESS_TOKEN", "")
        self.api_version = config.get("FACEBOOK_API_VERSION", self.API_VERSION)
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self.logger = structlog.get_logger(__name__)

        # Create async HTTP client
        self.client = httpx.AsyncClient(timeout=self.SEND_TIMEOUT)

    async def send_message(
        self,
        recipient_id: str,
        message_payload: Dict[str, Any],
        tag: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message to a Facebook Messenger recipient.

        Args:
            recipient_id: Facebook PSID (Page-Scoped ID)
            message_payload: Message payload (text or attachment)
            tag: Optional messaging tag for 24-hour rule compliance (Story 2.9)

        Returns:
            Facebook API response data

        Raises:
            APIError: If send fails or Facebook returns error
        """
        url = f"{self.base_url}/me/messages"

        payload = {
            "recipient": {"id": recipient_id},
            "message": message_payload,
        }

        # Story 2.9: Add messaging tag for 24-hour rule compliance
        if tag:
            payload["tag"] = tag

        headers = {
            "Content-Type": "application/json",
        }

        params = {
            "access_token": self.access_token,
        }

        try:
            response = await self.client.post(
                url,
                json=payload,
                headers=headers,
                params=params,
            )
            response.raise_for_status()

            data: Dict[str, Any] = response.json()

            # Check for Facebook errors
            if "error" in data:
                error = data["error"]
                self.logger.error(
                    "facebook_send_error",
                    error_code=error.get("code"),
                    error_message=error.get("message"),
                    recipient_id=recipient_id,
                )
                raise APIError(
                    ErrorCode.MESSAGE_SEND_FAILED,
                    f"Facebook Send API error: {error.get('message', 'Unknown error')}",
                    {"error": error},
                )

            self.logger.info(
                "message_sent",
                recipient_id=recipient_id,
                message_id=data.get("message_id"),
                tag=tag,
            )

            return data

        except httpx.HTTPStatusError as e:
            self.logger.error(
                "facebook_http_error",
                status=e.response.status_code,
                recipient_id=recipient_id,
            )

            # Map specific HTTP errors to error codes
            if e.response.status_code == 404:
                error_code = ErrorCode.FACEBOOK_INVALID_RECIPIENT
            elif e.response.status_code == 429:
                error_code = ErrorCode.FACEBOOK_RATE_LIMITED
            else:
                error_code = ErrorCode.MESSAGE_SEND_FAILED

            raise APIError(
                error_code,
                f"Facebook Send API error: {e.response.status_code}",
            )

        except httpx.TimeoutException:
            self.logger.error(
                "facebook_timeout",
                recipient_id=recipient_id,
            )
            raise APIError(
                ErrorCode.FACEBOOK_TIMEOUT,
                "Facebook Send API timeout",
            )

        except httpx.RequestError as e:
            self.logger.error(
                "facebook_request_error",
                error=str(e),
                recipient_id=recipient_id,
            )
            raise APIError(
                ErrorCode.MESSAGE_SEND_FAILED,
                f"Facebook Send API request failed: {str(e)}",
            )

    async def close(self) -> None:
        """Close the HTTP client.

        Should be called when done using the service.
        """
        await self.client.aclose()

    async def __aenter__(self) -> MessengerSendService:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
