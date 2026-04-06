"""Data deletion API endpoints for GDPR/CCPA compliance.

Provides endpoints for user data deletion requests and status tracking.
Story 6-6: GDPR deletion processing with 30-day compliance tracking.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session, get_db
from app.core.errors import APIError, ErrorCode
from app.models.deletion_audit_log import DeletionRequestType
from app.schemas.base import MinimalEnvelope
from app.services.data_deletion import DataDeletionService
from app.services.privacy.compliance_monitor import GDPRComplianceMonitor
from app.services.privacy.gdpr_service import GDPRDeletionService

router = APIRouter()
logger = structlog.get_logger(__name__)


class GDPRRequestSchema(BaseModel):
    """GDPR/CCPA deletion request schema."""

    customer_id: str = Field(..., description="Customer ID requesting deletion")
    request_type: DeletionRequestType = Field(
        default=DeletionRequestType.MANUAL,
        description="Type of deletion request (manual/gdpr_formal/ccpa_request)",
    )
    email: str | None = Field(None, description="Customer email for confirmation (optional)")
    session_id: str | None = Field(None, description="Session ID for tracking (optional)")
    visitor_id: str | None = Field(
        None, description="Visitor ID for cross-platform tracking (optional)"
    )

    class Config:
        json_encoders = {
            DeletionRequestType: lambda v: v.value,
        }


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
        },
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
        asyncio.create_task(_process_deletion_background(deletion_request.id))

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
    async with async_session()() as db:
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


@router.post(
    "/gdpr-request",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_200_OK,
)
async def submit_gdpr_request(
    request: Request,
    gdpr_request: GDPRRequestSchema,
    db: AsyncSession = Depends(get_db),
    merchant_id: int = Depends(lambda: 1),  # TODO: Get from auth
) -> JSONResponse:
    """Submit GDPR/CCPA deletion request with 30-day compliance tracking.

    Story 6-6: GDPR Deletion Processing

    Processes GDPR/CCPA deletion request:
    - Logs request with 30-day deadline
    - Immediately deletes voluntary data (conversations, preferences)
    - Marks customer as "do not process" for operational data
    - Queues confirmation email (if email provided)

    Args:
        request: FastAPI Request object
        gdpr_request: GDPR request payload
        db: Database session
        merchant_id: Merchant ID (from auth)

    Returns:
        Request ID and 30-day deadline

    Raises:
        APIError: If duplicate request exists (GDPR_REQUEST_PENDING)
    """
    log = logger.bind(
        customer_id=gdpr_request.customer_id,
        merchant_id=merchant_id,
        request_type=gdpr_request.request_type.value,
    )

    try:
        service = GDPRDeletionService()
        audit_log = await service.process_deletion_request(
            db=db,
            customer_id=gdpr_request.customer_id,
            merchant_id=merchant_id,
            request_type=gdpr_request.request_type,
            customer_email=gdpr_request.email,
            session_id=gdpr_request.session_id,
            visitor_id=gdpr_request.visitor_id,
        )

        log.info(
            "gdpr_request_processed",
            request_id=audit_log.id,
            deadline=audit_log.processing_deadline.isoformat()
            if audit_log.processing_deadline
            else None,
        )

        deadline_str = (
            audit_log.processing_deadline.isoformat() if audit_log.processing_deadline else None
        )
        deadline_date = (
            audit_log.processing_deadline.strftime("%Y-%m-%d")
            if audit_log.processing_deadline
            else "N/A"
        )

        response_data = {
            "requestId": audit_log.id,
            "customerId": audit_log.customer_id,
            "requestType": audit_log.request_type,
            "deadline": deadline_str,
            "message": (
                "Your GDPR deletion request has been received. "
                "Your voluntary data has been deleted. "
                f"Processing will complete by {deadline_date}."
            ),
        }

        if gdpr_request.email:
            response_data["emailConfirmation"] = "queued"

        return JSONResponse(content=create_response(response_data))

    except APIError:
        raise
    except Exception as e:
        log.error("gdpr_request_error", error=str(e))
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            "Failed to process GDPR request",
        )


@router.get(
    "/compliance/status",
    response_model=MinimalEnvelope,
)
async def get_compliance_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
    merchant_id: int = Depends(lambda: 1),  # TODO: Get from auth
) -> JSONResponse:
    """Get GDPR/CCPA compliance status for merchant.

    Story 6-6: GDPR Deletion Processing - Task 5.3

    Returns compliance dashboard data:
    - Current compliance status (compliant/non_compliant)
    - Count of overdue requests
    - Count of requests approaching deadline
    - List of at-risk requests

    Args:
        request: FastAPI Request object
        db: Database session
        merchant_id: Merchant ID (from auth)

    Returns:
        Compliance status summary
    """
    try:
        monitor = GDPRComplianceMonitor()
        status_data = await monitor.check_compliance_status(db)

        compliance_status = "compliant" if status_data["overdue_count"] == 0 else "non_compliant"

        response_data = {
            "status": compliance_status,
            "overdueRequests": status_data["overdue_count"],
            "approachingDeadline": status_data["approaching_count"],
            "lastChecked": datetime.now(UTC).isoformat(),
        }

        if status_data["overdue_requests"]:
            response_data["overdueDetails"] = status_data["overdue_requests"]

        if status_data["approaching_requests"]:
            response_data["approachingDetails"] = status_data["approaching_requests"]

        return JSONResponse(content=create_response(response_data))

    except Exception as e:
        logger.error("compliance_status_error", error=str(e))
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            "Failed to retrieve compliance status",
        )


@router.post(
    "/customers/{customer_id}/revoke-gdpr-request",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_200_OK,
)
async def revoke_gdpr_request(
    request: Request,
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    merchant_id: int = Depends(lambda: 1),  # TODO: Get from auth
) -> JSONResponse:
    """Revoke a GDPR deletion request (admin action for reversals).

    Story 6-6: GDPR Deletion Processing - Task 3.4

    Allows admin to revoke a pending GDPR request to resume order processing.
    Only revokes PENDING requests - completed requests cannot be revoked.

    Args:
        request: FastAPI Request object
        customer_id: Customer ID to revoke request for
        db: Database session
        merchant_id: Merchant ID (from auth)

    Returns:
        Revocation status

    Raises:
        APIError: If no pending request found
    """
    log = logger.bind(
        customer_id=customer_id,
        merchant_id=merchant_id,
    )

    try:
        service = GDPRDeletionService()
        revoked = await service.revoke_gdpr_request(db, customer_id, merchant_id)

        if not revoked:
            raise APIError(
                ErrorCode.GDPR_REQUEST_NOT_FOUND,
                "No pending GDPR request found for this customer",
                {"customer_id": customer_id},
            )

        log.info("gdpr_request_revoked", customer_id=customer_id)

        response_data = {
            "revoked": True,
            "customerId": customer_id,
            "message": "GDPR request has been revoked. Order processing will resume.",
        }

        return JSONResponse(content=create_response(response_data))

    except APIError:
        raise
    except Exception as e:
        log.error("gdpr_revoke_error", error=str(e))
        raise APIError(
            ErrorCode.INTERNAL_ERROR,
            "Failed to revoke GDPR request",
        )
