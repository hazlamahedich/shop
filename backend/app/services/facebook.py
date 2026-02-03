"""Facebook integration service.

Handles OAuth flow, token management, and Graph API interactions.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional, Any, Dict
from urllib.parse import urlencode

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.facebook_integration import FacebookIntegration
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.merchant import Merchant
from app.core.security import (
    encrypt_access_token,
    decrypt_access_token,
    generate_oauth_state,
)
from app.core.errors import APIError, ErrorCode
from app.core.config import settings


# Facebook API endpoints
FACEBOOK_OAUTH_DIALOG_URL = "https://www.facebook.com/v18.0/dialog/oauth"
FACEBOOK_TOKEN_EXCHANGE_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
FACEBOOK_LONG_LIVED_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"
FACEBOOK_GRAPH_API_URL = "https://graph.facebook.com/v18.0"

# Required OAuth scopes
REQUIRED_SCOPES = ["pages_messaging", "pages_manage_metadata"]

# Structlog configuration
logger = structlog.get_logger(__name__)


class FacebookService:
    """Service for Facebook integration operations."""

    def __init__(self, db: AsyncSession, is_testing: bool = False):
        """Initialize Facebook service.

        Args:
            db: Database session
            is_testing: Whether running in test mode (uses mock client)
        """
        self.db = db
        self.is_testing = is_testing
        self._async_client = None

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client.

        Returns:
            httpx.AsyncClient: Configured HTTP client
        """
        if self._async_client is None:
            if self.is_testing:
                # Use ASGITransport for testing
                from httpx import ASGITransport
                self._async_client = httpx.AsyncClient(
                    transport=ASGITransport(),
                    base_url="http://test"
                )
            else:
                self._async_client = httpx.AsyncClient()
        return self._async_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    async def generate_oauth_url(self, merchant_id: int) -> tuple[str, str]:
        """Generate Facebook OAuth URL with state parameter.

        Args:
            merchant_id: Merchant ID initiating OAuth

        Returns:
            Tuple of (auth_url, state_token)

        Raises:
            APIError: If Facebook configuration is missing
        """
        config = settings()
        app_id = config.get("FACEBOOK_APP_ID")
        redirect_uri = config.get("FACEBOOK_REDIRECT_URI")

        if not app_id:
            raise APIError(
                ErrorCode.FACEBOOK_ENCRYPTION_KEY_MISSING,
                "Facebook App ID not configured"
            )

        if not redirect_uri:
            raise APIError(
                ErrorCode.FACEBOOK_ENCRYPTION_KEY_MISSING,
                "Facebook redirect URI not configured"
            )

        # Generate state token for CSRF protection (stores merchant_id)
        state = generate_oauth_state(merchant_id)

        # Build OAuth URL
        params = {
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "scope": ",".join(REQUIRED_SCOPES),
            "response_type": "code",
            "state": state,
        }

        auth_url = f"{FACEBOOK_OAUTH_DIALOG_URL}?{urlencode(params)}"
        return auth_url, state

    async def exchange_code_for_token(
        self,
        code: str,
        state: str,
        expected_state: str
    ) -> dict[str, Any]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from Facebook
            state: State parameter from callback
            expected_state: Expected state for CSRF validation

        Returns:
            Dict with access_token, token_type, expires_in

        Raises:
            APIError: If state mismatch or token exchange fails
        """
        # Validate state for CSRF protection
        if state != expected_state:
            raise APIError(
                ErrorCode.FACEBOOK_OAUTH_STATE_MISMATCH,
                "OAuth state mismatch - possible CSRF attack"
            )

        config = settings()
        app_id = config.get("FACEBOOK_APP_ID")
        app_secret = config.get("FACEBOOK_APP_SECRET")
        redirect_uri = config.get("FACEBOOK_REDIRECT_URI")

        # Exchange code for short-lived token
        params = {
            "client_id": app_id,
            "client_secret": app_secret,
            "redirect_uri": redirect_uri,
            "code": code,
        }

        try:
            if self.is_testing:
                # Return mock token in test mode
                return {
                    "access_token": "test_short_lived_token",
                    "token_type": "bearer",
                    "expires_in": 5183949  # ~60 days
                }

            response = await self.async_client.post(
                FACEBOOK_TOKEN_EXCHANGE_URL,
                params=params
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise APIError(
                ErrorCode.FACEBOOK_TOKEN_EXCHANGE_FAILED,
                f"Failed to exchange authorization code: {e.response.text}"
            )

    async def get_long_lived_token(self, short_lived_token: str) -> str:
        """Exchange short-lived token for long-lived token (60 days).

        Args:
            short_lived_token: Short-lived access token

        Returns:
            Long-lived access token

        Raises:
            APIError: If token exchange fails
        """
        config = settings()
        app_id = config.get("FACEBOOK_APP_ID")
        app_secret = config.get("FACEBOOK_APP_SECRET")

        params = {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_lived_token,
        }

        try:
            if self.is_testing:
                # Return mock long-lived token in test mode
                return "test_long_lived_token"

            response = await self.async_client.get(
                FACEBOOK_LONG_LIVED_TOKEN_URL,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data["access_token"]

        except httpx.HTTPStatusError as e:
            raise APIError(
                ErrorCode.FACEBOOK_TOKEN_EXCHANGE_FAILED,
                f"Failed to get long-lived token: {e.response.text}"
            )

    async def verify_page_access(
        self,
        access_token: str
    ) -> dict[str, Any]:
        """Verify page access token and fetch page details.

        Args:
            access_token: Page access token

        Returns:
            Dict with page id, name, picture URL

        Raises:
            APIError: If token verification fails
        """
        params = {
            "fields": "id,name,picture{url}",
            "access_token": access_token,
        }

        try:
            if self.is_testing:
                # Return mock page data in test mode
                return {
                    "id": "123456789",
                    "name": "Test Store",
                    "picture": {"data": {"url": "https://example.com/picture.jpg"}}
                }

            response = await self.async_client.get(
                f"{FACEBOOK_GRAPH_API_URL}/me",
                params=params
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401 or e.response.status_code == 403:
                raise APIError(
                    ErrorCode.FACEBOOK_PAGE_ACCESS_DENIED,
                    "Insufficient permissions - please grant pages_messaging and pages_manage_metadata"
                )
            raise APIError(
                ErrorCode.FACEBOOK_PAGE_ACCESS_DENIED,
                f"Failed to verify page access: {e.response.text}"
            )

    async def resubscribe_webhook(self, integration: FacebookIntegration) -> bool:
        """Re-subscribe to Facebook webhook via Graph API.

        Args:
            integration: Facebook integration record

        Returns:
            True if resubscription successful, False otherwise
        """
        access_token = await self.get_page_access_token(integration.merchant_id)

        params = {
            "access_token": access_token,
            "subscribed_fields": "messages,messaging_postbacks",
        }

        try:
            if self.is_testing:
                # Return success in test mode
                return True

            response = await self.async_client.post(
                f"{FACEBOOK_GRAPH_API_URL}/{integration.page_id}/subscribed_apps",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("success", False)

        except httpx.HTTPStatusError as e:
            logger.error(
                "webhook_resubscribe_failed",
                page_id=integration.page_id,
                status_code=e.response.status_code,
                response=e.response.text
            )
            return False

    async def create_facebook_integration(
        self,
        merchant_id: int,
        page_id: str,
        page_name: str,
        page_picture_url: str,
        access_token: str,
        scopes: list[str],
    ) -> FacebookIntegration:
        """Create Facebook integration record.

        Args:
            merchant_id: Merchant ID
            page_id: Facebook Page ID
            page_name: Facebook Page name
            page_picture_url: Page profile picture URL
            access_token: Page access token (will be encrypted)
            scopes: Granted OAuth scopes

        Returns:
            Created FacebookIntegration record

        Raises:
            APIError: If merchant already has Facebook connected
        """
        # Check if merchant already has Facebook integration
        result = await self.db.execute(
            select(FacebookIntegration).where(
                FacebookIntegration.merchant_id == merchant_id
            )
        )
        existing = result.scalars().first()

        if existing:
            raise APIError(
                ErrorCode.FACEBOOK_ALREADY_CONNECTED,
                "Facebook Page already connected to this merchant"
            )

        # Encrypt access token
        encrypted_token = encrypt_access_token(access_token)

        # Create integration record
        integration = FacebookIntegration(
            merchant_id=merchant_id,
            page_id=page_id,
            page_name=page_name,
            page_picture_url=page_picture_url,
            access_token_encrypted=encrypted_token,
            scopes=scopes,
            status="active",
        )

        self.db.add(integration)
        await self.db.commit()
        await self.db.refresh(integration)

        return integration

    async def get_facebook_integration(
        self,
        merchant_id: int
    ) -> Optional[FacebookIntegration]:
        """Get Facebook integration for merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            FacebookIntegration record or None
        """
        result = await self.db.execute(
            select(FacebookIntegration).where(
                FacebookIntegration.merchant_id == merchant_id
            )
        )
        return result.scalars().first()

    async def get_page_access_token(self, merchant_id: int) -> str:
        """Get decrypted page access token for merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            Decrypted page access token

        Raises:
            APIError: If Facebook not connected
        """
        integration = await self.get_facebook_integration(merchant_id)

        if not integration:
            raise APIError(
                ErrorCode.FACEBOOK_NOT_CONNECTED,
                "Facebook Page not connected"
            )

        return decrypt_access_token(integration.access_token_encrypted)

    async def disconnect_facebook(self, merchant_id: int) -> None:
        """Disconnect Facebook integration for merchant.

        Args:
            merchant_id: Merchant ID

        Raises:
            APIError: If Facebook not connected
        """
        integration = await self.get_facebook_integration(merchant_id)

        if not integration:
            raise APIError(
                ErrorCode.FACEBOOK_NOT_CONNECTED,
                "Facebook Page not connected"
            )

        await self.db.delete(integration)
        await self.db.commit()

    async def create_or_update_conversation(
        self,
        merchant_id: int,
        platform: str,
        sender_id: str
    ) -> Conversation:
        """Create or update conversation for incoming message.

        Args:
            merchant_id: Merchant ID
            platform: Platform name (facebook, instagram)
            sender_id: Platform sender ID (PSID)

        Returns:
            Conversation record
        """
        # Try to find existing active conversation
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.merchant_id == merchant_id,
                Conversation.platform == platform,
                Conversation.platform_sender_id == sender_id,
                Conversation.status == "active"
            )
        )
        conversation = result.scalars().first()

        if not conversation:
            # Create new conversation
            conversation = Conversation(
                merchant_id=merchant_id,
                platform=platform,
                platform_sender_id=sender_id,
                status="active",
            )
            self.db.add(conversation)
            await self.db.commit()
            await self.db.refresh(conversation)

        return conversation

    async def store_message(
        self,
        conversation_id: int,
        sender: str,
        content: str,
        message_type: str = "text",
        message_metadata: Optional[dict] = None
    ) -> Message:
        """Store message in conversation.

        Args:
            conversation_id: Conversation ID
            sender: Message sender (customer or bot)
            content: Message content
            message_type: Message type (text, attachment, postback)
            message_metadata: Optional message metadata dict

        Returns:
            Created Message record
        """
        message = Message(
            conversation_id=conversation_id,
            sender=sender,
            content=content,
            message_type=message_type,
            message_metadata=message_metadata,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)

        return message


async def get_facebook_service(db: AsyncSession) -> FacebookService:
    """Get Facebook service instance.

    Args:
        db: Database session

    Returns:
        FacebookService instance
    """
    from app.core.config import is_testing
    return FacebookService(db, is_testing=is_testing())
