"""Tests for Facebook integration service.

Tests OAuth flow, token management, and Graph API interactions.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.services.facebook import (
    FacebookService,
    get_facebook_service,
)
from app.models.facebook_integration import FacebookIntegration
from app.models.conversation import Conversation
from app.models.merchant import Merchant
from app.core.errors import APIError, ErrorCode
from app.core.security import encrypt_access_token


class TestFacebookServiceOAuth:
    """Tests for Facebook OAuth flow."""

    @pytest.mark.asyncio
    async def test_generate_oauth_url(self, db_session, monkeypatch):
        """Test generating OAuth URL with state parameter."""
        # Set required environment variables
        monkeypatch.setenv("FACEBOOK_APP_ID", "test_app_id")
        monkeypatch.setenv("FACEBOOK_REDIRECT_URI", "https://example.com/callback")

        service = FacebookService(db_session, is_testing=True)
        auth_url, state = await service.generate_oauth_url(1)

        assert auth_url.startswith("https://www.facebook.com/v18.0/dialog/oauth?")
        assert "client_id=test_app_id" in auth_url
        assert "pages_messaging" in auth_url
        assert "pages_manage_metadata" in auth_url
        assert state is not None
        assert len(state) >= 32  # token_urlsafe(32) produces 43 chars

    @pytest.mark.asyncio
    async def test_generate_oauth_url_missing_config(self, db_session, monkeypatch):
        """Test error when Facebook config is missing."""
        monkeypatch.delenv("FACEBOOK_APP_ID", raising=False)

        service = FacebookService(db_session, is_testing=True)

        with pytest.raises(APIError) as exc_info:
            await service.generate_oauth_url(1)

        assert exc_info.value.code == ErrorCode.FACEBOOK_ENCRYPTION_KEY_MISSING
        assert "App ID not configured" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_success(self, db_session):
        """Test successful code exchange for access token."""
        service = FacebookService(db_session, is_testing=True)
        result = await service.exchange_code_for_token(
            code="test_code",
            state="test_state",
            expected_state="test_state"
        )

        assert result["access_token"] == "test_short_lived_token"
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == 5183949

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_state_mismatch(self, db_session):
        """Test state mismatch raises error."""
        service = FacebookService(db_session, is_testing=True)

        with pytest.raises(APIError) as exc_info:
            await service.exchange_code_for_token(
                code="test_code",
                state="wrong_state",
                expected_state="correct_state"
            )

        assert exc_info.value.code == ErrorCode.FACEBOOK_OAUTH_STATE_MISMATCH
        assert "state mismatch" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_get_long_lived_token(self, db_session):
        """Test getting long-lived token."""
        service = FacebookService(db_session, is_testing=True)
        token = await service.get_long_lived_token("short_token")

        assert token == "test_long_lived_token"

    @pytest.mark.asyncio
    async def test_verify_page_access_success(self, db_session):
        """Test successful page access verification."""
        service = FacebookService(db_session, is_testing=True)
        result = await service.verify_page_access("test_token")

        assert result["id"] == "123456789"
        assert result["name"] == "Test Store"
        assert result["picture"]["data"]["url"] == "https://example.com/picture.jpg"

    @pytest.mark.asyncio
    async def test_verify_page_access_denied(self, db_session):
        """Test page access denied with invalid token."""
        service = FacebookService(db_session, is_testing=False)

        with patch.object(service.async_client, "get") as mock_get:
            # Simulate 401/403 response
            mock_response = AsyncMock()
            mock_response.status_code = 401
            mock_response.text = "Invalid access token"
            mock_response.raise_for_status.side_effect = Exception("401")

            mock_get.return_value = mock_response

            with pytest.raises(APIError) as exc_info:
                await service.verify_page_access("invalid_token")

            # Should raise either page access denied or token exchange failed
            assert exc_info.value.code in (
                ErrorCode.FACEBOOK_PAGE_ACCESS_DENIED,
                ErrorCode.FACEBOOK_TOKEN_EXCHANGE_FAILED
            )


class TestFacebookServiceIntegration:
    """Tests for Facebook integration CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_facebook_integration(self, db_session):
        """Test creating Facebook integration record."""
        # Create merchant
        merchant = Merchant(
            merchant_key="test_merchant_fb_integration",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        service = FacebookService(db_session, is_testing=True)
        integration = await service.create_facebook_integration(
            merchant_id=merchant.id,
            page_id="123456789",
            page_name="Test Store",
            page_picture_url="https://example.com/pic.jpg",
            access_token="test_token",
            scopes=["pages_messaging", "pages_manage_metadata"],
        )

        assert integration.merchant_id == merchant.id
        assert integration.page_id == "123456789"
        assert integration.page_name == "Test Store"
        assert integration.status == "active"

    @pytest.mark.asyncio
    async def test_create_facebook_integration_already_exists(self, db_session):
        """Test error when merchant already has Facebook integration."""
        merchant = Merchant(
            merchant_key="test_merchant_fb_exists",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        # Create first integration
        service = FacebookService(db_session, is_testing=True)
        await service.create_facebook_integration(
            merchant_id=merchant.id,
            page_id="111111111",
            page_name="First Page",
            page_picture_url="https://example.com/pic1.jpg",
            access_token="token1",
            scopes=["pages_messaging"],
        )

        # Try to create second integration
        with pytest.raises(APIError) as exc_info:
            await service.create_facebook_integration(
                merchant_id=merchant.id,
                page_id="222222222",
                page_name="Second Page",
                page_picture_url="https://example.com/pic2.jpg",
                access_token="token2",
                scopes=["pages_messaging"],
            )

        assert exc_info.value.code == ErrorCode.FACEBOOK_ALREADY_CONNECTED

    @pytest.mark.asyncio
    async def test_get_facebook_integration(self, db_session):
        """Test retrieving Facebook integration."""
        merchant = Merchant(
            merchant_key="test_merchant_get_fb",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        service = FacebookService(db_session, is_testing=True)
        created = await service.create_facebook_integration(
            merchant_id=merchant.id,
            page_id="123456789",
            page_name="Test Store",
            page_picture_url="https://example.com/pic.jpg",
            access_token="test_token",
            scopes=["pages_messaging"],
        )

        retrieved = await service.get_facebook_integration(merchant.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.page_name == "Test Store"

    @pytest.mark.asyncio
    async def test_get_facebook_integration_not_found(self, db_session):
        """Test getting non-existent Facebook integration."""
        service = FacebookService(db_session, is_testing=True)
        result = await service.get_facebook_integration(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_page_access_token(self, db_session):
        """Test getting decrypted page access token."""
        merchant = Merchant(
            merchant_key="test_merchant_token",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        original_token = "EAAtest_token"
        service = FacebookService(db_session, is_testing=True)
        await service.create_facebook_integration(
            merchant_id=merchant.id,
            page_id="123456789",
            page_name="Test Store",
            page_picture_url="https://example.com/pic.jpg",
            access_token=original_token,
            scopes=["pages_messaging"],
        )

        retrieved_token = await service.get_page_access_token(merchant.id)

        assert retrieved_token == original_token

    @pytest.mark.asyncio
    async def test_get_page_access_token_not_connected(self, db_session):
        """Test error when getting token for non-existent integration."""
        service = FacebookService(db_session, is_testing=True)

        with pytest.raises(APIError) as exc_info:
            await service.get_page_access_token(999)

        assert exc_info.value.code == ErrorCode.FACEBOOK_NOT_CONNECTED

    @pytest.mark.asyncio
    async def test_disconnect_facebook(self, db_session):
        """Test disconnecting Facebook integration."""
        merchant = Merchant(
            merchant_key="test_merchant_disconnect",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        service = FacebookService(db_session, is_testing=True)
        await service.create_facebook_integration(
            merchant_id=merchant.id,
            page_id="123456789",
            page_name="Test Store",
            page_picture_url="https://example.com/pic.jpg",
            access_token="test_token",
            scopes=["pages_messaging"],
        )

        await service.disconnect_facebook(merchant.id)

        # Verify integration is deleted
        result = await service.get_facebook_integration(merchant.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_disconnect_facebook_not_connected(self, db_session):
        """Test error when disconnecting non-existent integration."""
        service = FacebookService(db_session, is_testing=True)

        with pytest.raises(APIError) as exc_info:
            await service.disconnect_facebook(999)

        assert exc_info.value.code == ErrorCode.FACEBOOK_NOT_CONNECTED


class TestFacebookServiceConversations:
    """Tests for conversation and message handling."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, db_session):
        """Test creating a new conversation."""
        merchant = Merchant(
            merchant_key="test_merchant_conv",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        service = FacebookService(db_session, is_testing=True)
        conversation = await service.create_or_update_conversation(
            merchant_id=merchant.id,
            platform="facebook",
            sender_id="customer_psid",
        )

        assert conversation.merchant_id == merchant.id
        assert conversation.platform == "facebook"
        assert conversation.platform_sender_id == "customer_psid"
        assert conversation.status == "active"

    @pytest.mark.asyncio
    async def test_update_existing_conversation(self, db_session):
        """Test updating existing active conversation."""
        merchant = Merchant(
            merchant_key="test_merchant_conv_update",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        service = FacebookService(db_session, is_testing=True)

        # Create first conversation
        conv1 = await service.create_or_update_conversation(
            merchant_id=merchant.id,
            platform="facebook",
            sender_id="customer_psid",
        )

        # Try to create again - should return existing
        conv2 = await service.create_or_update_conversation(
            merchant_id=merchant.id,
            platform="facebook",
            sender_id="customer_psid",
        )

        assert conv1.id == conv2.id

    @pytest.mark.asyncio
    async def test_store_message(self, db_session):
        """Test storing a message in conversation."""
        merchant = Merchant(
            merchant_key="test_merchant_msg",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        service = FacebookService(db_session, is_testing=True)
        conversation = await service.create_or_update_conversation(
            merchant_id=merchant.id,
            platform="facebook",
            sender_id="customer_psid",
        )

        message = await service.store_message(
            conversation_id=conversation.id,
            sender="customer",
            content="Hello!",
            message_type="text",
        )

        assert message.conversation_id == conversation.id
        assert message.sender == "customer"
        assert message.content == "Hello!"
        assert message.message_type == "text"

    @pytest.mark.asyncio
    async def test_store_message_with_metadata(self, db_session):
        """Test storing message with metadata."""
        merchant = Merchant(
            merchant_key="test_merchant_msg_meta",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        service = FacebookService(db_session, is_testing=True)
        conversation = await service.create_or_update_conversation(
            merchant_id=merchant.id,
            platform="facebook",
            sender_id="customer_psid",
        )

        metadata = {"attachment_url": "https://example.com/image.jpg"}
        message = await service.store_message(
            conversation_id=conversation.id,
            sender="customer",
            content="Check this image",
            message_type="attachment",
            metadata=metadata,
        )

        assert message.message_type == "attachment"
        assert message.metadata == metadata

    @pytest.mark.asyncio
    async def test_get_facebook_service_factory(self, db_session):
        """Test get_facebook_service factory function."""
        service = await get_facebook_service(db_session)

        assert isinstance(service, FacebookService)
        assert service.db == db_session
