"""Tests for Conversation ORM model."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.merchant import Merchant


class TestConversationModel:
    """Tests for Conversation ORM model."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, db_session):
        """Test creating a conversation record."""
        merchant = Merchant(
            merchant_key="test_merchant_conv",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="1234567890",
            status="active",
        )
        db_session.add(conversation)
        await db_session.flush()

        # Verify conversation was created
        result = await db_session.execute(
            select(Conversation).where(Conversation.merchant_id == merchant.id)
        )
        found = result.scalars().first()

        assert found is not None
        assert found.platform == "facebook"
        assert found.platform_sender_id == "1234567890"
        assert found.status == "active"

    @pytest.mark.asyncio
    async def test_conversation_defaults(self, db_session):
        """Test default values for conversation."""
        merchant = Merchant(
            merchant_key="test_merchant_conv2",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        conversation = Conversation(
            merchant_id=merchant.id,
            platform="facebook",
            platform_sender_id="0987654321",
        )
        db_session.add(conversation)
        await db_session.flush()

        # Check defaults
        assert conversation.status == "active"
        assert conversation.created_at is not None
        assert conversation.updated_at is not None

    @pytest.mark.asyncio
    async def test_conversation_status_enum(self, db_session):
        """Test that status accepts valid enum values."""
        merchant = Merchant(
            merchant_key="test_merchant_status",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        # Test each valid status
        for status_value in ["active", "handoff", "closed"]:
            conversation = Conversation(
                merchant_id=merchant.id,
                platform="facebook",
                platform_sender_id=f"sender_{status_value}",
                status=status_value,
            )
            db_session.add(conversation)
            await db_session.flush()

            assert conversation.status == status_value

    @pytest.mark.asyncio
    async def test_multiple_platforms(self, db_session):
        """Test conversations from different platforms."""
        merchant = Merchant(
            merchant_key="test_merchant_multi",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.flush()

        # Create conversations for different platforms
        platforms = ["facebook", "instagram", "whatsapp"]
        for platform in platforms:
            conversation = Conversation(
                merchant_id=merchant.id,
                platform=platform,
                platform_sender_id=f"sender_{platform}",
            )
            db_session.add(conversation)
        await db_session.flush()

        # Verify all were created
        result = await db_session.execute(
            select(Conversation).where(Conversation.merchant_id == merchant.id)
        )
        conversations = result.scalars().all()

        assert len(conversations) == len(platforms)
        platform_values = {c.platform for c in conversations}
        assert platform_values == set(platforms)
