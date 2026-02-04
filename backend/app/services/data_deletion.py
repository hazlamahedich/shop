"""Data deletion service for GDPR/CCPA compliance.

Handles user data deletion requests with background processing.
Supports 30-day deletion window and audit trail requirements.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, Optional

import structlog
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_deletion_request import DataDeletionRequest, DeletionStatus
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.errors import APIError, ErrorCode


logger = structlog.get_logger(__name__)


class DataDeletionService:
    """Service for handling GDPR/CCPA data deletion requests."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize data deletion service.

        Args:
            db: Database session
        """
        self.db = db

    async def request_deletion(
        self,
        customer_id: str,
        platform: str,
    ) -> DataDeletionRequest:
        """Create a data deletion request.

        Args:
            customer_id: Platform customer ID (sender_id from Facebook, etc.)
            platform: Platform name (facebook, instagram, etc.)

        Returns:
            Created DataDeletionRequest record

        Raises:
            APIError: If deletion request already exists and is pending/processing
        """
        # Check for existing pending/processing request
        result = await self.db.execute(
            select(DataDeletionRequest).where(
                DataDeletionRequest.customer_id == customer_id,
                DataDeletionRequest.platform == platform,
                DataDeletionRequest.status.in_([
                    DeletionStatus.PENDING,
                    DeletionStatus.PROCESSING,
                ]),
            )
        )
        existing = result.scalars().first()

        if existing:
            logger.warning(
                "deletion_request_already_exists",
                customer_id=customer_id,
                platform=platform,
                existing_id=existing.id,
            )
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                "A deletion request is already in progress for this account",
            )

        # Create new deletion request
        request = DataDeletionRequest(
            customer_id=customer_id,
            platform=platform,
            status=DeletionStatus.PENDING,
        )
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)

        logger.info(
            "deletion_request_created",
            request_id=request.id,
            customer_id=customer_id,
            platform=platform,
        )

        return request

    async def process_deletion(
        self,
        request_id: int,
    ) -> Dict[str, int]:
        """Process a deletion request.

        Deletes:
        - Conversation messages
        - Conversations

        Keeps (business requirement):
        - Order references (for accounting/compliance)

        Args:
            request_id: Deletion request ID

        Returns:
            Dictionary with counts of deleted items

        Raises:
            APIError: If request not found or already processed
        """
        # Get the deletion request
        result = await self.db.execute(
            select(DataDeletionRequest).where(
                DataDeletionRequest.id == request_id,
            )
        )
        request = result.scalars().first()

        if not request:
            logger.error("deletion_request_not_found", request_id=request_id)
            raise APIError(
                ErrorCode.MERCHANT_NOT_FOUND,
                f"Deletion request not found: {request_id}",
            )

        if request.status == DeletionStatus.COMPLETED:
            logger.warning(
                "deletion_request_already_completed",
                request_id=request_id,
            )
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                "Deletion request already completed",
            )

        # Update status to processing
        request.status = DeletionStatus.PROCESSING
        await self.db.commit()

        logger.info(
            "deletion_processing_started",
            request_id=request_id,
            customer_id=request.customer_id,
        )

        deleted: Dict[str, int] = {}
        error_message: Optional[str] = None

        try:
            # 1. Delete messages in conversations for this customer
            # Get all conversation IDs for this customer
            conv_result = await self.db.execute(
                select(Conversation.id).where(
                    Conversation.platform_sender_id == request.customer_id,
                    Conversation.platform == request.platform,
                )
            )
            conversation_ids = [row[0] for row in conv_result.all()]

            if conversation_ids:
                # Delete messages
                msg_result = await self.db.execute(
                    delete(Message).where(
                        Message.conversation_id.in_(conversation_ids)
                    )
                )
                deleted["messages"] = msg_result.rowcount or 0

                # 2. Delete conversations
                conv_delete_result = await self.db.execute(
                    delete(Conversation).where(
                        Conversation.id.in_(conversation_ids)
                    )
                )
                deleted["conversations"] = conv_delete_result.rowcount or 0
            else:
                deleted["messages"] = 0
                deleted["conversations"] = 0

            # 3. Order references are kept (business requirement)
            # When order model is implemented, customer_id would be set to NULL
            # TODO: Anonymize order references when Order model is implemented

            # Update request as completed
            request.status = DeletionStatus.COMPLETED
            request.processed_at = datetime.utcnow()
            request.deleted_items = json.dumps(deleted)

            await self.db.commit()

            logger.info(
                "deletion_completed",
                request_id=request_id,
                customer_id=request.customer_id,
                deleted_items=deleted,
            )

            return deleted

        except Exception as e:
            # Mark as failed
            request.status = DeletionStatus.FAILED
            request.processed_at = datetime.utcnow()
            request.error_message = str(e)
            await self.db.commit()

            logger.error(
                "deletion_failed",
                request_id=request_id,
                customer_id=request.customer_id,
                error=str(e),
            )

            raise APIError(
                ErrorCode.INTERNAL_ERROR,
                f"Deletion processing failed: {str(e)}",
            )

    async def get_deletion_status(
        self,
        request_id: int,
    ) -> DataDeletionRequest:
        """Get status of a deletion request.

        Args:
            request_id: Deletion request ID

        Returns:
            DataDeletionRequest record

        Raises:
            APIError: If request not found
        """
        result = await self.db.execute(
            select(DataDeletionRequest).where(
                DataDeletionRequest.id == request_id,
            )
        )
        request = result.scalars().first()

        if not request:
            raise APIError(
                ErrorCode.MERCHANT_NOT_FOUND,
                f"Deletion request not found: {request_id}",
            )

        return request

    async def get_pending_requests(
        self,
        platform: Optional[str] = None,
    ) -> list[DataDeletionRequest]:
        """Get all pending deletion requests.

        Args:
            platform: Optional platform filter

        Returns:
            List of pending deletion requests
        """
        query = select(DataDeletionRequest).where(
            DataDeletionRequest.status == DeletionStatus.PENDING,
        )

        if platform:
            query = query.where(DataDeletionRequest.platform == platform)

        result = await self.db.execute(query.order_by(DataDeletionRequest.requested_at))
        return list(result.scalars().all())
