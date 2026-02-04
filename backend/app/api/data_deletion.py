"""Data deletion API endpoints for GDPR/CCPA compliance.

Provides endpoints for user data deletion requests and status tracking.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db, async_session
from app.core.errors import APIError, ErrorCode
from app.schemas.base import MinimalEnvelope, MetaData
from app.services.data_deletion import DataDeletionService
from app.models.data_deletion_request import DeletionStatus


router = APIRouter()
logger = structlog.get_logger(__name__)


def create_response(data: dict) -> dict:
    """Create standard API response envelope.

    Args:
        data: Response data

    Returns:
        Dict with data and meta fields
    """
    return {
        "data": data,
        "meta": {
            "requestId": str(uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
        }
    }


@router.post(
    "/deletion/request",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_data_deletion(
    request: Request,
    customer_id: str,
    platform: str,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Request deletion of user data (GDPR/CCPA compliance).

    Creates a deletion request and queues background processing.
    User data will be deleted within 30 days as required by law.

    Data to be deleted:
    - Conversation history
    - Product preferences
    - Voluntary memory

    Data retained (business requirement):
    - Order references (read-only for accounting/compliance)

    Args:
        request: FastAPI Request object
        customer_id: Platform customer ID
        platform: Platform name (facebook, instagram, etc.)
        db: Database session

    Returns:
        Confirmation with request ID and status

    Raises:
        APIError: If deletion request already in progress
    """
    request_id = str(uuid4())
    log = logger.bind(request_id=request_id, customer_id=customer_id, platform=platform)

    try:
        service = DataDeletionService(db)
        deletion_request = await service.request_deletion(customer_id, platform)

        # Start background processing
        asyncio.create_task(
            _process_deletion_background(deletion_request.id)
        )

        log.info(
            "deletion_request_accepted",
            deletion_request_id=deletion_request.id,
        )

        response_data = {
            "status": "pending",
            "message": (
                "Your data deletion request has been received. "
                "Your conversation history and preferences will be deleted within 30 days. "
                "You will receive confirmation when processing is complete."
            ),
            "requestId": deletion_request.id,
            "requestedAt": deletion_request.requested_at.isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=create_response(response_data),
        )

    except APIError as e:
        log.warning("deletion_request_failed", error_code=e.code, message=e.message)
        raise
    except Exception as e:
        log.error("deletion_request_error", error=str(e))
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            "Failed to process deletion request",
        )


async def _process_deletion_background(request_id: int) -> None:
    """Background task to process deletion request.

    Creates its own database session to avoid concurrent operations error.

    Args:
        request_id: Deletion request ID
    """
    async with async_session() as db:
        try:
            service = DataDeletionService(db)
            deleted = await service.process_deletion(request_id)

            logger.info(
                "background_deletion_completed",
                request_id=request_id,
                deleted_items=deleted,
            )

        except Exception as e:
            logger.error(
                "background_deletion_failed",
                request_id=request_id,
                error=str(e),
            )


@router.get(
    "/deletion/status/{request_id}",
    response_model=MinimalEnvelope,
)
async def get_deletion_status(
    request_id: int,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Get status of a data deletion request.

    Args:
        request_id: Deletion request ID
        db: Database session

    Returns:
        Current status of deletion request

    Raises:
        APIError: If request not found
    """
    try:
        service = DataDeletionService(db)
        deletion_request = await service.get_deletion_status(request_id)

        response_data = {
            "requestId": deletion_request.id,
            "customerId": deletion_request.customer_id,
            "platform": deletion_request.platform,
            "status": deletion_request.status.value,
            "requestedAt": deletion_request.requested_at.isoformat(),
        }

        if deletion_request.processed_at:
            response_data["processedAt"] = deletion_request.processed_at.isoformat()

        if deletion_request.deleted_items:
            import json
            response_data["deletedItems"] = json.loads(deletion_request.deleted_items)

        if deletion_request.error_message:
            response_data["errorMessage"] = deletion_request.error_message

        return JSONResponse(content=create_response(response_data))

    except APIError:
        raise
    except Exception as e:
        logger.error("get_deletion_status_error", request_id=request_id, error=str(e))
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            "Failed to retrieve deletion status",
        )
