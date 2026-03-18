"""GDPR/CCPA deletion request processing service.

Story 6-6: GDPR Deletion Processing

Orchestrates GDPR/CCPA deletion workflow with 30-day compliance window:
- Logs deletion requests with tracking fields
- Immediately deletes voluntary data (conversations, preferences)
- Marks customer as "do not process" for operational data
- Queues confirmation email (if email provided)
- Provides compliance monitoring
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.conversation import Conversation
from app.models.deletion_audit_log import (
    DeletionAuditLog,
    DeletionRequestType,
    DeletionTrigger,
)
from app.services.privacy.data_tier_service import DataTier

logger = structlog.get_logger(__name__)


class GDPRDeletionService:
    """Service for processing GDPR/CCPA deletion requests.

    GDPR/CCPA Compliance:
    - GDPR Article 17: Right to erasure (30-day window)
    - CCPA Section 1798.105: Right to deletion
    - Immediate deletion of voluntary data
    - Customer-level "do not process" tracking for operational data
    """

    async def process_deletion_request(
        self,
        db: AsyncSession,
        customer_id: str,
        merchant_id: int,
        request_type: DeletionRequestType,
        customer_email: str | None = None,
        session_id: str | None = None,
        visitor_id: str | None = None,
    ) -> DeletionAuditLog:
        """Process GDPR/CCPA deletion request within 30-day window.

        Args:
            db: Database session
            customer_id: Customer ID requesting deletion
            merchant_id: Merchant ID
            request_type: Type of deletion request (manual/gdpr_formal/ccpa_request)
            customer_email: Optional email for confirmation
            session_id: Optional session ID (for session-level tracking)
            visitor_id: Optional visitor ID (for cross-platform tracking)

        Returns:
            DeletionAuditLog: Created audit log entry

        Raises:
            APIError: If duplicate request exists (GDPR_REQUEST_PENDING)
        """
        # Check for existing pending request
        existing = await db.execute(
            select(DeletionAuditLog)
            .where(DeletionAuditLog.customer_id == customer_id)
            .where(DeletionAuditLog.merchant_id == merchant_id)
            .where(DeletionAuditLog.completion_date.is_(None))
        )
        if existing.scalar_one_or_none():
            raise APIError(
                ErrorCode.GDPR_REQUEST_PENDING,
                "Deletion request already pending for this customer",
                {"customer_id": customer_id},
            )

        # Log the request with deadline
        request_timestamp = datetime.now(UTC)
        processing_deadline = request_timestamp + timedelta(days=30)

        audit_log = DeletionAuditLog(
            session_id=session_id or f"gdpr_{customer_id[:16]}",
            visitor_id=visitor_id,
            customer_id=customer_id,
            merchant_id=merchant_id,
            deletion_trigger=DeletionTrigger.MANUAL.value,
            request_type=request_type,
            request_timestamp=request_timestamp,
            processing_deadline=processing_deadline,
            confirmation_email_sent=False,
        )
        db.add(audit_log)
        await db.flush()

        # Immediately delete voluntary data (including Redis)
        conv_deleted, redis_deleted = await self._delete_voluntary_data_by_customer(
            db, customer_id, merchant_id
        )

        # Update audit log with deletion counts
        audit_log.mark_completed(
            conversations=conv_deleted,
            messages=0,  # Messages cascade deleted
            redis_keys=redis_deleted,
        )

        # Queue confirmation email (if email provided)
        if customer_email:
            await self._queue_confirmation_email(
                db, customer_id, merchant_id, customer_email, audit_log.id
            )

        await db.commit()

        logger.info(
            "gdpr_deletion_request_processed",
            customer_id=customer_id,
            merchant_id=merchant_id,
            request_type=request_type,
            deadline=processing_deadline.isoformat(),
            conversations_deleted=conv_deleted,
            redis_keys_deleted=redis_deleted,
        )

        return audit_log

    async def _delete_voluntary_data_by_customer(
        self,
        db: AsyncSession,
        customer_id: str,
        merchant_id: int,
    ) -> tuple[int, int]:
        """Delete voluntary data for GDPR request by customer_id.

        Args:
            db: Database session
            customer_id: Customer ID (platform_sender_id) to delete data for
            merchant_id: Merchant ID

        Returns:
            Tuple[int, int]: (conversations_deleted, redis_keys_cleared)

        Note:
            In this system, customer_id maps to Conversation.platform_sender_id.
            We only delete VOLUNTARY tier conversations - operational data is retained.
        """
        # Get all platform_sender_ids for this customer for Redis cleanup
        # Note: platform_sender_id IS the customer identifier in our system
        sender_ids_result = await db.execute(
            select(Conversation.platform_sender_id)
            .where(Conversation.platform_sender_id == customer_id)
            .where(Conversation.merchant_id == merchant_id)
            .distinct()
        )
        sender_ids = sender_ids_result.scalars().all()

        # Delete VOLUNTARY tier conversations for this customer only
        # Note: Messages cascade deleted via FK relationship
        # Note: OPERATIONAL and ANONYMIZED tier data is retained per GDPR exceptions
        conv_result = await db.execute(
            delete(Conversation)
            .where(Conversation.platform_sender_id == customer_id)
            .where(Conversation.merchant_id == merchant_id)
            .where(Conversation.data_tier == DataTier.VOLUNTARY.value)
            .returning(Conversation.id)
        )
        conv_deleted = len(conv_result.scalars().all())

        # Clear Redis PII data (cart, preferences) for all associated sender_ids
        # Note: Redis cleanup would be implemented when Redis is available
        # For now, return 0 for redis_keys_cleared
        redis_deleted = 0

        # TODO: When Redis is integrated:
        # redis_client = get_redis()
        # for sender_id in sender_ids:
        #     await redis_client.delete(f"cart:{merchant_id}:{sender_id}")
        #     await redis_client.delete(f"prefs:{merchant_id}:{sender_id}")
        #     redis_deleted += 2

        logger.info(
            "voluntary_data_deleted",
            customer_id=customer_id,
            merchant_id=merchant_id,
            conversations_deleted=conv_deleted,
            redis_keys_deleted=redis_deleted,
        )

        return conv_deleted, redis_deleted

    async def _queue_confirmation_email(
        self,
        db: AsyncSession,
        customer_id: str,
        merchant_id: int,
        customer_email: str,
        audit_log_id: int,
    ) -> None:
        """Queue confirmation email for async sending.

        Args:
            db: Database session
            customer_id: Customer ID
            merchant_id: Merchant ID
            customer_email: Customer email address
            audit_log_id: Audit log ID for tracking
        """
        # Story 6-6 Task 4.5: The background job `send_pending_gdpr_emails` checks
        # for audit logs where confirmation_email_sent == False and customer_email is set.

        audit_log = await db.get(DeletionAuditLog, audit_log_id)
        if audit_log:
            audit_log.customer_email = customer_email
            await db.flush()

        logger.info(
            "gdpr_confirmation_email_queued",
            audit_log_id=audit_log_id,
            customer_id=customer_id,
            to_email=customer_email,
        )

    async def mark_deletion_complete(
        self,
        db: AsyncSession,
        audit_log_id: int,
    ) -> DeletionAuditLog:
        """Mark GDPR deletion as complete.

        Args:
            db: Database session
            audit_log_id: Audit log ID to mark complete

        Returns:
            DeletionAuditLog: Updated audit log

        Raises:
            APIError: If audit log not found
        """
        result = await db.execute(
            update(DeletionAuditLog)
            .where(DeletionAuditLog.id == audit_log_id)
            .values(completion_date=datetime.now(UTC))
            .returning(DeletionAuditLog)
        )

        audit_log = result.scalar_one_or_none()
        if not audit_log:
            raise APIError(
                ErrorCode.GDPR_REQUEST_NOT_FOUND,
                "Deletion request not found",
                {"audit_log_id": audit_log_id},
            )

        await db.commit()

        completion_dt = audit_log.completion_date
        logger.info(
            "gdpr_deletion_marked_complete",
            audit_log_id=audit_log_id,
            customer_id=audit_log.customer_id,
            completion_date=completion_dt.isoformat() if completion_dt else None,
        )

        return audit_log

    async def is_customer_processing_restricted(
        self,
        db: AsyncSession,
        customer_id: str,
        merchant_id: int,
    ) -> bool:
        """Check if customer has active GDPR deletion request.

        Args:
            db: Database session
            customer_id: Customer ID to check
            merchant_id: Merchant ID

        Returns:
            bool: True if customer has active GDPR/CCPA request, False otherwise
        """
        result = await db.execute(
            select(DeletionAuditLog)
            .where(DeletionAuditLog.customer_id == customer_id)
            .where(DeletionAuditLog.merchant_id == merchant_id)
            .where(
                DeletionAuditLog.request_type.in_(
                    [
                        DeletionRequestType.GDPR_FORMAL,
                        DeletionRequestType.CCPA_REQUEST,
                    ]
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def revoke_gdpr_request(
        self,
        db: AsyncSession,
        customer_id: str,
        merchant_id: int,
    ) -> bool:
        """Revoke GDPR deletion request (admin action for reversals).

        Args:
            db: Database session
            customer_id: Customer ID
            merchant_id: Merchant ID

        Returns:
            bool: True if request was revoked, False if no request found
        """
        result = await db.execute(
            delete(DeletionAuditLog)
            .where(DeletionAuditLog.customer_id == customer_id)
            .where(DeletionAuditLog.merchant_id == merchant_id)
            .where(DeletionAuditLog.completion_date.is_(None))
            .returning(DeletionAuditLog.id)
        )

        deleted = result.scalar_one_or_none()
        if deleted:
            await db.commit()
            logger.info(
                "gdpr_request_revoked",
                customer_id=customer_id,
                merchant_id=merchant_id,
                audit_log_id=deleted,
            )
            return True

        return False
