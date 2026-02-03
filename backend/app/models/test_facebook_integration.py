"""Tests for FacebookIntegration ORM model.

Tests CRUD operations and encryption/decryption of access tokens.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from datetime import datetime

from app.models.facebook_integration import FacebookIntegration
from app.models.merchant import Merchant
from app.core.security import encrypt_access_token, decrypt_access_token


class TestFacebookIntegrationModel:
    """Tests for FacebookIntegration ORM model."""

    @pytest.mark.asyncio
    async def test_create_facebook_integration(self, db_session):
        """Test creating a Facebook integration record."""
        # Create merchant first
        merchant = Merchant(
            merchant_key="test_merchant_fb",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        # Create Facebook integration
        encrypted_token = encrypt_access_token("test_access_token")
        integration = FacebookIntegration(
            merchant_id=merchant.id,
            page_id="123456789",
            page_name="Test Store",
            page_picture_url="https://example.com/picture.jpg",
            access_token_encrypted=encrypted_token,
            scopes=["pages_messaging", "pages_manage_metadata"],
            status="active",
        )
        db_session.add(integration)
        await db_session.flush()

        # Verify integration was created
        result = await db_session.execute(
            select(FacebookIntegration).where(FacebookIntegration.merchant_id == merchant.id)
        )
        found_integration = result.scalars().first()

        assert found_integration is not None
        assert found_integration.page_id == "123456789"
        assert found_integration.page_name == "Test Store"
        assert found_integration.status == "active"

    @pytest.mark.asyncio
    async def test_facebook_integration_defaults(self, db_session):
        """Test default values for Facebook integration."""
        merchant = Merchant(
            merchant_key="test_merchant_fb2",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        integration = FacebookIntegration(
            merchant_id=merchant.id,
            page_id="987654321",
            page_name="Test Store 2",
            access_token_encrypted=encrypt_access_token("token"),
            scopes=["pages_messaging"],
        )
        db_session.add(integration)
        await db_session.flush()

        # Check defaults
        assert integration.status == "pending"
        assert integration.webhook_verified is False
        assert integration.connected_at is not None
        assert integration.created_at is not None

    @pytest.mark.asyncio
    async def test_merchant_unique_constraint(self, db_session):
        """Test that merchant_id is unique (one Facebook page per merchant)."""
        merchant = Merchant(
            merchant_key="test_merchant_unique",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        # Create first integration
        integration1 = FacebookIntegration(
            merchant_id=merchant.id,
            page_id="111111111",
            page_name="First Page",
            access_token_encrypted=encrypt_access_token("token1"),
            scopes=["pages_messaging"],
        )
        db_session.add(integration1)
        await db_session.flush()

        # Try to create second integration for same merchant
        integration2 = FacebookIntegration(
            merchant_id=merchant.id,
            page_id="222222222",
            page_name="Second Page",
            access_token_encrypted=encrypt_access_token("token2"),
            scopes=["pages_messaging"],
        )
        db_session.add(integration2)

        # Should raise integrity error due to unique constraint
        with pytest.raises(Exception):  # IntegrityError from SQLAlchemy
            await db_session.flush()

    @pytest.mark.asyncio
    async def test_token_encryption_decryption(self, db_session):
        """Test that access tokens are properly encrypted/decrypted."""
        original_token = "EAAabcdef123456"
        encrypted_token = encrypt_access_token(original_token)

        # Verify encrypted token is different from original
        assert encrypted_token != original_token

        # Verify decryption works
        decrypted_token = decrypt_access_token(encrypted_token)
        assert decrypted_token == original_token

    @pytest.mark.asyncio
    async def test_updated_at_auto_updates(self, db_session):
        """Test that updated_at automatically updates on save."""
        merchant = Merchant(
            merchant_key="test_merchant_updated",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        integration = FacebookIntegration(
            merchant_id=merchant.id,
            page_id="333333333",
            page_name="Update Test",
            access_token_encrypted=encrypt_access_token("token"),
            scopes=["pages_messaging"],
        )
        db_session.add(integration)
        await db_session.flush()

        original_updated_at = integration.updated_at
        assert original_updated_at is not None

        # Update the integration
        integration.page_name = "Updated Page Name"
        await db_session.flush()

        # Refresh from database
        await db_session.refresh(integration)

        # updated_at should be different (later)
        assert integration.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_webhook_verified_field(self, db_session):
        """Test webhook verification status tracking."""
        merchant = Merchant(
            merchant_key="test_merchant_webhook",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        integration = FacebookIntegration(
            merchant_id=merchant.id,
            page_id="444444444",
            page_name="Webhook Test",
            access_token_encrypted=encrypt_access_token("token"),
            scopes=["pages_messaging"],
            webhook_verified=False,
        )
        db_session.add(integration)
        await db_session.flush()

        assert integration.webhook_verified is False
        assert integration.last_webhook_at is None

        # Simulate webhook verification
        integration.webhook_verified = True
        integration.last_webhook_at = datetime.utcnow()
        await db_session.flush()

        await db_session.refresh(integration)
        assert integration.webhook_verified is True
        assert integration.last_webhook_at is not None

    @pytest.mark.asyncio
    async def test_delete_cascade(self, db_session):
        """Test that deleting merchant cascades to Facebook integration."""
        merchant = Merchant(
            merchant_key="test_merchant_cascade",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        integration = FacebookIntegration(
            merchant_id=merchant.id,
            page_id="555555555",
            page_name="Cascade Test",
            access_token_encrypted=encrypt_access_token("token"),
            scopes=["pages_messaging"],
        )
        db_session.add(integration)
        await db_session.flush()

        integration_id = integration.id

        # Delete merchant (should cascade to integration)
        await db_session.delete(merchant)
        await db_session.flush()

        # Verify integration is also deleted
        result = await db_session.execute(
            select(FacebookIntegration).where(FacebookIntegration.id == integration_id)
        )
        found = result.scalars().first()
        assert found is None
