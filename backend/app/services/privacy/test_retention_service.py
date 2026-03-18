"""Unit tests for Retention Policy Service.

Story 6-4: Data Tier Separation
Task 7.2: Test retention policy execution for each tier
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.order import Order
from app.services.privacy.data_tier_service import DataTier
from app.services.privacy.retention_service import RetentionPolicy


class TestRetentionPolicy:
    """Test suite for RetentionPolicy."""

    @pytest.fixture
    def policy(self) -> RetentionPolicy:
        """Create retention policy instance."""
        return RetentionPolicy()

    @pytest.mark.asyncio
    async def test_delete_expired_voluntary_data_deletes_old_conversations(
        self,
        policy: RetentionPolicy,
        db_session: AsyncSession,
        test_merchant,
    ) -> None:
        """Test that VOLUNTARY data older than 30 days is deleted."""
        merchant_id = test_merchant.id

        # Create old voluntary conversation (35 days old)
        old_conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="old_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
            created_at=datetime.utcnow() - timedelta(days=35),
            updated_at=datetime.utcnow() - timedelta(days=35),
        )
        db_session.add(old_conv)
        await db_session.commit()

        # Create recent voluntary conversation (15 days old)
        recent_conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="recent_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
            created_at=datetime.utcnow() - timedelta(days=15),
            updated_at=datetime.utcnow() - timedelta(days=15),
        )
        db_session.add(recent_conv)
        await db_session.commit()

        deleted_count = await policy.delete_expired_voluntary_data(db_session)

        # Should delete old conversation
        assert deleted_count >= 1

        # Verify old conversation deleted
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == old_conv.id)
        )
        assert result.scalars().first() is None

        # Verify recent conversation retained
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == recent_conv.id)
        )
        assert result.scalars().first() is not None

    @pytest.mark.asyncio
    async def test_delete_expired_voluntary_data_preserves_operational(
        self,
        policy: RetentionPolicy,
        db_session: AsyncSession,
        test_merchant,
    ) -> None:
        """Test that OPERATIONAL data is never deleted, regardless of age."""
        merchant_id = test_merchant.id

        # Create very old operational conversation (100 days old)
        old_operational_conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="old_operational_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.OPERATIONAL,
            created_at=datetime.utcnow() - timedelta(days=100),
            updated_at=datetime.utcnow() - timedelta(days=100),
        )
        db_session.add(old_operational_conv)
        await db_session.commit()

        deleted_count = await policy.delete_expired_voluntary_data(db_session)

        # Should NOT delete operational data
        assert deleted_count == 0

        # Verify operational conversation retained
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == old_operational_conv.id)
        )
        assert result.scalars().first() is not None

    @pytest.mark.asyncio
    async def test_delete_expired_voluntary_data_preserves_anonymized(
        self,
        policy: RetentionPolicy,
        db_session: AsyncSession,
        test_merchant,
    ) -> None:
        """Test that ANONYMIZED data is never deleted, regardless of age."""
        merchant_id = test_merchant.id

        # Create very old anonymized conversation
        old_anonymized_conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="old_anonymized_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.ANONYMIZED,
            created_at=datetime.utcnow() - timedelta(days=200),
            updated_at=datetime.utcnow() - timedelta(days=200),
        )
        db_session.add(old_anonymized_conv)
        await db_session.commit()

        deleted_count = await policy.delete_expired_voluntary_data(db_session)

        # Should NOT delete anonymized data
        assert deleted_count == 0

        # Verify anonymized conversation retained
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == old_anonymized_conv.id)
        )
        assert result.scalars().first() is not None

    @pytest.mark.asyncio
    async def test_delete_expired_voluntary_data_cascades_to_messages(
        self,
        policy: RetentionPolicy,
        db_session: AsyncSession,
        test_merchant,
    ) -> None:
        """Test that deleting conversations also deletes associated messages."""
        merchant_id = test_merchant.id

        # Create old voluntary conversation with messages
        old_conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="user_with_messages",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
            created_at=datetime.utcnow() - timedelta(days=35),
            updated_at=datetime.utcnow() - timedelta(days=35),
        )
        db_session.add(old_conv)
        await db_session.commit()

        # Create messages for this conversation
        msg1 = Message(
            conversation_id=old_conv.id,
            sender="customer",
            content="Old message 1",
            message_type="text",
            data_tier=DataTier.VOLUNTARY,
        )
        msg2 = Message(
            conversation_id=old_conv.id,
            sender="bot",
            content="Old message 2",
            message_type="text",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add_all([msg1, msg2])
        await db_session.commit()

        deleted_count = await policy.delete_expired_voluntary_data(db_session)

        # Should delete conversation and cascade to messages
        assert deleted_count >= 1

        # Verify messages deleted
        result = await db_session.execute(
            select(Message).where(Message.conversation_id == old_conv.id)
        )
        messages = result.scalars().all()
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_delete_expired_voluntary_data_respects_cutoff_date(
        self,
        policy: RetentionPolicy,
        db_session: AsyncSession,
        test_merchant,
    ) -> None:
        """Test that exactly 30-day-old data is deleted, not 29-day-old."""
        merchant_id = test_merchant.id

        # Create conversation exactly 30 days old
        conv_30_days = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="user_30_days",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
            created_at=datetime.utcnow() - timedelta(days=30),
            updated_at=datetime.utcnow() - timedelta(days=30),
        )
        db_session.add(conv_30_days)

        # Create conversation 29 days old
        conv_29_days = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="user_29_days",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
            created_at=datetime.utcnow() - timedelta(days=29),
            updated_at=datetime.utcnow() - timedelta(days=29),
        )
        db_session.add(conv_29_days)
        await db_session.commit()

        deleted_count = await policy.delete_expired_voluntary_data(db_session)

        # Should delete 30-day-old conversation
        assert deleted_count >= 1

        # Verify 30-day conversation deleted
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == conv_30_days.id)
        )
        assert result.scalars().first() is None

        # Verify 29-day conversation retained
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == conv_29_days.id)
        )
        assert result.scalars().first() is not None

    @pytest.mark.asyncio
    async def test_delete_expired_voluntary_data_handles_large_dataset(
        self,
        policy: RetentionPolicy,
        db_session: AsyncSession,
        test_merchant,
    ) -> None:
        """Test that retention policy handles large datasets efficiently."""
        merchant_id = test_merchant.id

        # Create 100 old voluntary conversations
        conversations = []
        for i in range(100):
            conv = Conversation(
                merchant_id=merchant_id,
                platform="widget",
                platform_sender_id=f"batch_user_{i}",
                status="active",
                handoff_status="none",
                data_tier=DataTier.VOLUNTARY,
                created_at=datetime.utcnow() - timedelta(days=35),
                updated_at=datetime.utcnow() - timedelta(days=35),
            )
            conversations.append(conv)

        db_session.add_all(conversations)
        await db_session.commit()

        deleted_count = await policy.delete_expired_voluntary_data(db_session)

        # Should delete all 100 conversations
        assert deleted_count == 100

        # Verify all deleted
        result = await db_session.execute(
            select(Conversation).where(
                Conversation.merchant_id == merchant_id,
                Conversation.data_tier == DataTier.VOLUNTARY,
            )
        )
        remaining = result.scalars().all()
        assert len(remaining) == 0


class TestRetentionPolicyEdgeCases:
    """Edge case tests for retention policy."""

    @pytest.fixture
    def policy(self) -> RetentionPolicy:
        """Create retention policy instance."""
        return RetentionPolicy()

    @pytest.mark.asyncio
    async def test_delete_expired_voluntary_data_empty_database(
        self,
        policy: RetentionPolicy,
        db_session: AsyncSession,
    ) -> None:
        """Test retention policy with no data."""
        deleted_count = await policy.delete_expired_voluntary_data(db_session)

        # Should return 0, not error
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_delete_expired_voluntary_data_mixed_tiers(
        self,
        policy: RetentionPolicy,
        db_session: AsyncSession,
        test_merchant,
    ) -> None:
        """Test retention policy with mixed tier data."""
        merchant_id = test_merchant.id

        # Old voluntary (should delete)
        old_voluntary = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="old_voluntary",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
            created_at=datetime.utcnow() - timedelta(days=35),
            updated_at=datetime.utcnow() - timedelta(days=35),
        )
        db_session.add(old_voluntary)

        # Old operational (should keep)
        old_operational = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="old_operational",
            status="active",
            handoff_status="none",
            data_tier=DataTier.OPERATIONAL,
            created_at=datetime.utcnow() - timedelta(days=35),
            updated_at=datetime.utcnow() - timedelta(days=35),
        )
        db_session.add(old_operational)

        # Old anonymized (should keep)
        old_anonymized = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="old_anonymized",
            status="active",
            handoff_status="none",
            data_tier=DataTier.ANONYMIZED,
            created_at=datetime.utcnow() - timedelta(days=35),
            updated_at=datetime.utcnow() - timedelta(days=35),
        )
        db_session.add(old_anonymized)

        await db_session.commit()

        deleted_count = await policy.delete_expired_voluntary_data(db_session)

        # Should only delete voluntary
        assert deleted_count == 1

        # Verify voluntary deleted
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == old_voluntary.id)
        )
        assert result.scalars().first() is None

        # Verify operational retained
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == old_operational.id)
        )
        assert result.scalars().first() is not None

        # Verify anonymized retained
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == old_anonymized.id)
        )
        assert result.scalars().first() is not None

    @pytest.mark.asyncio
    async def test_delete_expired_voluntary_data_orders_never_deleted(
        self,
        policy: RetentionPolicy,
        db_session: AsyncSession,
        test_merchant,
    ) -> None:
        """Test that orders (operational data) are never deleted by retention."""
        merchant_id = test_merchant.id

        # Create very old order (should never delete)
        old_order = Order(
            merchant_id=merchant_id,
            order_number="ORD-OLD-001",
            platform_sender_id="old_customer",
            subtotal=99.99,
            total=99.99,
            is_test=False,
            data_tier=DataTier.OPERATIONAL,
            created_at=datetime.utcnow() - timedelta(days=365),
        )
        db_session.add(old_order)
        await db_session.commit()

        deleted_count = await policy.delete_expired_voluntary_data(db_session)

        # Should not delete orders
        assert deleted_count == 0

        # Verify order retained
        result = await db_session.execute(select(Order).where(Order.id == old_order.id))
        assert result.scalars().first() is not None
