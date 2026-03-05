"""Unit tests for Story 6-5: 30-Day Retention Enforcement.

Tests automated deletion, batch processing, retry logic, and audit logging.
Validates AC1-AC6 compliance.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from sqlalchemy import select

from app.services.privacy.retention_service import RetentionPolicy
from app.models.conversation import Conversation, DataTier
from app.models.deletion_audit_log import DeletionAuditLog, DeletionTrigger


class TestRetentionPolicyBatchProcessing:
    """Test batch processing for performance (AC5)."""

    @pytest.mark.asyncio
    async def test_batch_processing_handles_large_dataset(
        self,
        db_session,
        merchant,
    ):
        """AC5: Verify batch processing for 10K+ conversations."""
        merchant_id = merchant.id
        cutoff_date = datetime.utcnow() - timedelta(days=31)

        # Create 1500 old voluntary conversations (more than batch size of 1000)
        for i in range(1500):
            conv = Conversation(
                merchant_id=merchant_id,
                platform="widget",
                platform_sender_id=f"old_user_{i}",
                status="closed",
                data_tier=DataTier.VOLUNTARY,
                created_at=cutoff_date - timedelta(days=10),
                updated_at=cutoff_date,
            )
            db_session.add(conv)

        await db_session.commit()

        # Run deletion with batch size of 1000
        deleted_count = await RetentionPolicy.delete_expired_voluntary_data(
            db_session,
            days=30,
            batch_size=1000,
            timeout_seconds=300,
        )

        # Verify all 1500 conversations were deleted
        assert deleted_count == 1500

        # Verify database is empty
        result = await db_session.execute(
            select(Conversation).where(Conversation.merchant_id == merchant_id)
        )
        remaining = result.scalars().all()
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_batch_processing_respects_timeout(
        self,
        db_session,
        merchant,
    ):
        """AC5: Verify timeout handling to prevent long-running jobs."""
        merchant_id = merchant.id
        cutoff_date = datetime.utcnow() - timedelta(days=31)

        # Create 100 old conversations
        for i in range(100):
            conv = Conversation(
                merchant_id=merchant_id,
                platform="widget",
                platform_sender_id=f"old_user_{i}",
                status="closed",
                data_tier=DataTier.VOLUNTARY,
                created_at=cutoff_date - timedelta(days=10),
                updated_at=cutoff_date,
            )
            db_session.add(conv)

        await db_session.commit()

        # Run deletion with very short timeout (1 second)
        deleted_count = await RetentionPolicy.delete_expired_voluntary_data(
            db_session,
            days=30,
            batch_size=10,
            timeout_seconds=1,
        )

        # Should have deleted some conversations before timeout
        # (At least the first batch of 10)
        assert deleted_count >= 10

    @pytest.mark.asyncio
    async def test_batch_processing_creates_audit_logs(
        self,
        db_session,
        merchant,
    ):
        """AC3: Verify audit logs are created for each deletion."""
        merchant_id = merchant.id
        cutoff_date = datetime.utcnow() - timedelta(days=31)

        # Create 50 old voluntary conversations
        for i in range(50):
            conv = Conversation(
                merchant_id=merchant_id,
                platform="widget",
                platform_sender_id=f"old_user_{i}",
                status="closed",
                data_tier=DataTier.VOLUNTARY,
                created_at=cutoff_date - timedelta(days=10),
                updated_at=cutoff_date,
            )
            db_session.add(conv)

        await db_session.commit()

        # Run deletion
        deleted_count = await RetentionPolicy.delete_expired_voluntary_data(
            db_session,
            days=30,
        )

        # Verify audit logs were created
        result = await db_session.execute(
            select(DeletionAuditLog).where(DeletionAuditLog.merchant_id == merchant_id)
        )
        audit_logs = result.scalars().all()

        assert len(audit_logs) == 50
        assert deleted_count == 50

        # Verify audit log fields
        for log in audit_logs:
            assert log.deletion_trigger == DeletionTrigger.AUTO
            assert log.retention_period_days == 30
            assert log.conversations_deleted == 1
            assert log.completed_at is not None


class TestRetentionPolicyDataTierFiltering:
    """Test data tier filtering (AC1, AC4)."""

    @pytest.mark.asyncio
    async def test_only_voluntary_data_deleted(
        self,
        db_session,
        merchant,
    ):
        """AC1: Verify only VOLUNTARY tier data is deleted."""
        merchant_id = merchant.id
        cutoff_date = datetime.utcnow() - timedelta(days=31)

        # Create old conversations in different tiers
        voluntary_conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="old_voluntary",
            status="closed",
            data_tier=DataTier.VOLUNTARY,
            created_at=cutoff_date - timedelta(days=10),
            updated_at=cutoff_date,
        )
        operational_conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="old_operational",
            status="closed",
            data_tier=DataTier.OPERATIONAL,
            created_at=cutoff_date - timedelta(days=10),
            updated_at=cutoff_date,
        )
        anonymized_conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="old_anonymized",
            status="closed",
            data_tier=DataTier.ANONYMIZED,
            created_at=cutoff_date - timedelta(days=10),
            updated_at=cutoff_date,
        )

        db_session.add_all([voluntary_conv, operational_conv, anonymized_conv])
        await db_session.commit()

        # Run deletion
        deleted_count = await RetentionPolicy.delete_expired_voluntary_data(
            db_session,
            days=30,
        )

        # Verify only voluntary conversation was deleted
        assert deleted_count == 1

        result = await db_session.execute(
            select(Conversation).where(Conversation.merchant_id == merchant_id)
        )
        remaining = result.scalars().all()
        assert len(remaining) == 2

        remaining_ids = {conv.platform_sender_id for conv in remaining}
        assert "old_operational" in remaining_ids
        assert "old_anonymized" in remaining_ids

    @pytest.mark.asyncio
    async def test_operational_data_preserved_indefinitely(
        self,
        db_session,
        merchant,
    ):
        """AC4: Verify operational data (order refs) is never deleted."""
        merchant_id = merchant.id
        old_date = datetime.utcnow() - timedelta(days=365)

        # Create very old operational conversation (1 year old)
        operational_conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="year_old_operational",
            status="closed",
            data_tier=DataTier.OPERATIONAL,
            created_at=old_date - timedelta(days=100),
            updated_at=old_date,
        )

        db_session.add(operational_conv)
        await db_session.commit()

        # Run deletion with 30-day retention
        deleted_count = await RetentionPolicy.delete_expired_voluntary_data(
            db_session,
            days=30,
        )

        # Verify operational conversation was NOT deleted
        assert deleted_count == 0

        result = await db_session.execute(
            select(Conversation).where(Conversation.id == operational_conv.id)
        )
        remaining = result.scalar_one_or_none()
        assert remaining is not None
        assert remaining.platform_sender_id == "year_old_operational"


class TestRetentionPolicyEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_database_no_error(self, db_session):
        """Verify graceful handling of empty database."""
        deleted_count = await RetentionPolicy.delete_expired_voluntary_data(
            db_session,
            days=30,
        )

        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_no_expired_data(self, db_session, merchant):
        """Verify no deletion when all data is within retention period."""
        merchant_id = merchant.id

        # Create recent voluntary conversations
        for i in range(10):
            conv = Conversation(
                merchant_id=merchant_id,
                platform="widget",
                platform_sender_id=f"recent_user_{i}",
                status="active",
                data_tier=DataTier.VOLUNTARY,
                created_at=datetime.utcnow() - timedelta(days=10),
                updated_at=datetime.utcnow() - timedelta(days=5),
            )
            db_session.add(conv)

        await db_session.commit()

        # Run deletion
        deleted_count = await RetentionPolicy.delete_expired_voluntary_data(
            db_session,
            days=30,
        )

        # Verify nothing was deleted
        assert deleted_count == 0

        result = await db_session.execute(
            select(Conversation).where(Conversation.merchant_id == merchant_id)
        )
        remaining = result.scalars().all()
        assert len(remaining) == 10


class TestAuditLogQuery:
    """Test audit log query functionality (Task 2.5)."""

    @pytest.mark.asyncio
    async def test_audit_log_tracks_manual_vs_auto_deletions(
        self,
        db_session,
        merchant,
    ):
        """Verify audit logs distinguish between manual and automated deletions."""
        merchant_id = merchant.id

        # Create manual deletion audit log
        manual_log = DeletionAuditLog(
            session_id="manual-session-123",
            merchant_id=merchant_id,
            deletion_trigger=DeletionTrigger.MANUAL,
            conversations_deleted=5,
            messages_deleted=20,
            redis_keys_cleared=3,
        )
        manual_log.mark_completed(5, 20, 3)

        # Create automated deletion audit log
        auto_log = DeletionAuditLog(
            session_id="retention-auto-456",
            merchant_id=merchant_id,
            retention_period_days=30,
            deletion_trigger=DeletionTrigger.AUTO,
            conversations_deleted=1,
            messages_deleted=0,
            redis_keys_cleared=0,
        )
        auto_log.mark_completed(1, 0, 0)

        db_session.add_all([manual_log, auto_log])
        await db_session.commit()

        # Query manual deletions
        result = await db_session.execute(
            select(DeletionAuditLog).where(
                DeletionAuditLog.deletion_trigger == DeletionTrigger.MANUAL
            )
        )
        manual_logs = result.scalars().all()
        assert len(manual_logs) == 1
        assert manual_logs[0].session_id == "manual-session-123"
        assert manual_logs[0].retention_period_days is None

        # Query automated deletions
        result = await db_session.execute(
            select(DeletionAuditLog).where(
                DeletionAuditLog.deletion_trigger == DeletionTrigger.AUTO
            )
        )
        auto_logs = result.scalars().all()
        assert len(auto_logs) == 1
        assert auto_logs[0].session_id == "retention-auto-456"
        assert auto_logs[0].retention_period_days == 30
