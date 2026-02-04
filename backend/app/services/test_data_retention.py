"""Tests for data retention service (NFR-S11).

Validates 30-day conversation retention enforcement with separate
retention periods for different data tiers.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import pytest

from sqlalchemy import select

from app.services.data_retention import DataRetentionService
from app.models.conversation import Conversation
from app.models.message import Message


class TestDataRetentionService:
    """Test suite for DataRetentionService."""

    @pytest.fixture
    def retention_service(self):
        """Create a retention service instance."""
        return DataRetentionService(voluntary_days=30, session_hours=24)

    @pytest.fixture
    async def old_conversation(self, db_session, merchant_factory):
        """Create a conversation older than 30 days."""
        cutoff = datetime.utcnow() - timedelta(days=31)

        conv = Conversation(
            merchant_id=merchant_factory.id,
            platform="facebook",
            platform_sender_id="old_user_123",
            status="closed",
            created_at=cutoff - timedelta(days=10),
            updated_at=cutoff,
        )
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        # Add some messages
        for i in range(3):
            msg = Message(
                conversation_id=conv.id,
                sender="customer" if i % 2 == 0 else "bot",
                content=f"Old message {i}",
                message_type="text",
            )
            db_session.add(msg)

        await db_session.commit()
        return conv

    @pytest.fixture
    async def recent_conversation(self, db_session, merchant_factory):
        """Create a recent conversation within retention period."""
        conv = Conversation(
            merchant_id=merchant_factory.id,
            platform="facebook",
            platform_sender_id="recent_user_456",
            status="active",
            created_at=datetime.utcnow() - timedelta(days=5),
            updated_at=datetime.utcnow() - timedelta(days=1),
        )
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        # Add some messages
        for i in range(2):
            msg = Message(
                conversation_id=conv.id,
                sender="customer" if i % 2 == 0 else "bot",
                content=f"Recent message {i}",
                message_type="text",
            )
            db_session.add(msg)

        await db_session.commit()
        return conv

    @pytest.mark.asyncio
    async def test_cleanup_voluntary_data_deletes_old_conversations(
        self,
        db_session,
        retention_service,
        old_conversation,
        recent_conversation
    ):
        """Test that voluntary data cleanup deletes conversations older than retention period."""
        # Verify both conversations exist before cleanup
        result = await db_session.execute(select(Conversation))
        conversations = result.scalars().all()
        assert len(conversations) == 2

        # Run cleanup
        stats = await retention_service.cleanup_voluntary_data(db_session)

        # Verify cleanup stats
        assert stats["conversations_deleted"] == 1
        assert stats["messages_deleted"] == 3

        # Verify only old conversation was deleted
        result = await db_session.execute(select(Conversation))
        remaining_conversations = result.scalars().all()
        assert len(remaining_conversations) == 1
        assert remaining_conversations[0].id == recent_conversation.id

        # Verify old conversation's messages were deleted
        result = await db_session.execute(
            select(Message).where(Message.conversation_id == old_conversation.id)
        )
        old_messages = result.scalars().all()
        assert len(old_messages) == 0

        # Verify recent conversation's messages still exist
        result = await db_session.execute(
            select(Message).where(Message.conversation_id == recent_conversation.id)
        )
        recent_messages = result.scalars().all()
        assert len(recent_messages) == 2

    @pytest.mark.asyncio
    async def test_cleanup_voluntary_data_dry_run(
        self,
        db_session,
        retention_service,
        old_conversation,
        recent_conversation
    ):
        """Test that dry run mode reports deletions without actually deleting."""
        # Run cleanup in dry run mode
        stats = await retention_service.cleanup_voluntary_data(db_session, dry_run=True)

        # Verify dry run stats
        assert stats["conversations_to_delete"] == 1
        assert stats["messages_to_delete"] == 3
        assert stats["conversations_deleted"] == 0
        assert stats["messages_deleted"] == 0

        # Verify nothing was actually deleted
        result = await db_session.execute(select(Conversation))
        conversations = result.scalars().all()
        assert len(conversations) == 2

        result = await db_session.execute(select(Message))
        messages = result.scalars().all()
        assert len(messages) == 5  # 3 old + 2 recent

    @pytest.mark.asyncio
    async def test_cleanup_voluntary_data_custom_cutoff(
        self,
        db_session,
        retention_service,
        recent_conversation
    ):
        """Test cleanup with custom cutoff date."""
        # Set cutoff to delete even recent conversation
        custom_cutoff = datetime.utcnow() - timedelta(days=1)

        stats = await retention_service.cleanup_voluntary_data(
            db_session,
            before_date=custom_cutoff
        )

        # Should delete the recent conversation too
        assert stats["conversations_deleted"] == 1

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(
        self,
        db_session,
        retention_service
    ):
        """Test session cleanup (placeholder for future implementation)."""
        stats = await retention_service.cleanup_expired_sessions(db_session)

        # Currently returns empty stats as session data is in Redis
        assert "sessions_expired" in stats
        assert "cutoff_time" in stats

    @pytest.mark.asyncio
    async def test_get_retention_stats(
        self,
        db_session,
        retention_service,
        old_conversation,
        recent_conversation
    ):
        """Test getting retention statistics."""
        stats = await retention_service.get_retention_stats(db_session)

        # Verify structure
        assert "total_conversations" in stats
        assert "total_messages" in stats
        assert "conversations_by_age" in stats
        assert "retention_policy" in stats

        # Verify counts
        assert stats["total_conversations"] == 2
        assert stats["total_messages"] == 5

        # Verify retention policy
        assert stats["retention_policy"]["voluntary_days"] == 30
        assert stats["retention_policy"]["session_hours"] == 24

        # Verify age brackets
        assert "0_7_days" in stats["conversations_by_age"]
        assert "7_30_days" in stats["conversations_by_age"]
        assert "30_90_days" in stats["conversations_by_age"]
        assert "90_plus_days" in stats["conversations_by_age"]

    @pytest.mark.asyncio
    async def test_get_conversations_to_delete(
        self,
        db_session,
        retention_service,
        old_conversation,
        recent_conversation
    ):
        """Test getting list of conversations to delete."""
        conversations = await retention_service.get_conversations_to_delete(db_session)

        # Should only return old conversation
        assert len(conversations) == 1
        assert conversations[0]["id"] == old_conversation.id
        assert conversations[0]["platform"] == "facebook"
        assert conversations[0]["days_since_update"] >= 30

    @pytest.mark.asyncio
    async def test_get_conversations_to_delete_respects_limit(
        self,
        db_session,
        retention_service,
        merchant_factory
    ):
        """Test that get_conversations_to_delete respects the limit parameter."""
        # Create multiple old conversations
        cutoff = datetime.utcnow() - timedelta(days=31)

        for i in range(5):
            conv = Conversation(
                merchant_id=merchant_factory.id,
                platform="facebook",
                platform_sender_id=f"old_user_{i}",
                status="closed",
                created_at=cutoff - timedelta(days=10),
                updated_at=cutoff,
            )
            db_session.add(conv)

        await db_session.commit()

        # Request with limit
        conversations = await retention_service.get_conversations_to_delete(
            db_session,
            limit=3
        )

        # Should only return 3
        assert len(conversations) == 3

    @pytest.mark.asyncio
    async def test_order_references_not_deleted(
        self,
        db_session,
        retention_service,
        merchant_factory
    ):
        """Test that order references are preserved (operational data)."""
        # This is a placeholder test for when order references are implemented
        # Operational data should never be deleted by retention policy

        # The retention service should only delete voluntary conversation data
        # Any tables related to orders, transactions, or business records
        # should be excluded from retention cleanup

        # For now, we verify that the service doesn't touch unknown tables
        cutoff = datetime.utcnow() - timedelta(days=31)

        # Run cleanup
        stats = await retention_service.cleanup_voluntary_data(db_session)

        # Should only affect conversations and messages
        assert "conversations_deleted" in stats
        assert "messages_deleted" in stats

    @pytest.mark.asyncio
    async def test_configurable_retention_periods(
        self,
        db_session,
        merchant_factory
    ):
        """Test that retention periods are configurable."""
        # Create service with 7-day retention
        short_retention = DataRetentionService(voluntary_days=7)

        # Create conversation 10 days old
        cutoff = datetime.utcnow() - timedelta(days=10)
        conv = Conversation(
            merchant_id=merchant_factory.id,
            platform="facebook",
            platform_sender_id="user_123",
            status="closed",
            created_at=cutoff - timedelta(days=5),
            updated_at=cutoff,
        )
        db_session.add(conv)
        await db_session.commit()

        # Run cleanup with 7-day retention
        stats = await short_retention.cleanup_voluntary_data(db_session)

        # Should delete the 10-day-old conversation
        assert stats["conversations_deleted"] == 1

    @pytest.mark.asyncio
    async def test_empty_database_cleanup(
        self,
        db_session,
        retention_service
    ):
        """Test cleanup behavior with empty database."""
        stats = await retention_service.cleanup_voluntary_data(db_session)

        assert stats["conversations_deleted"] == 0
        assert stats["messages_deleted"] == 0

    @pytest.mark.asyncio
    async def test_messages_deleted_before_conversations(
        self,
        db_session,
        retention_service,
        merchant_factory
    ):
        """Test that messages are deleted before conversations (foreign key constraint)."""
        # Create old conversation with messages
        cutoff = datetime.utcnow() - timedelta(days=31)
        conv = Conversation(
            merchant_id=merchant_factory.id,
            platform="facebook",
            platform_sender_id="user_fk_test",
            status="closed",
            created_at=cutoff - timedelta(days=10),
            updated_at=cutoff,
        )
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)

        # Add messages
        for i in range(5):
            msg = Message(
                conversation_id=conv.id,
                sender="customer",
                content=f"Message {i}",
                message_type="text",
            )
            db_session.add(msg)

        await db_session.commit()

        # Run cleanup
        stats = await retention_service.cleanup_voluntary_data(db_session)

        # Verify all messages were deleted before conversation
        assert stats["messages_deleted"] == 5
        assert stats["conversations_deleted"] == 1

        # Verify no orphaned messages
        result = await db_session.execute(select(Message))
        all_messages = result.scalars().all()
        assert len(all_messages) == 0
