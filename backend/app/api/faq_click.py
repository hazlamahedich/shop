"""FAQ Click tracking API endpoint.

Story 10-10: FAQ Usage Widget

Tracks when users click on FAQ buttons in the widget, recording
the interaction to the FaqInteractionLog table for analytics.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import ErrorCode
from app.models.faq import Faq
from app.models.faq_interaction_log import FaqInteractionLog

logger = logging.getLogger(__name__)

router = APIRouter()


class FaqClickRequest(BaseModel):
    """Request schema for tracking FAQ clicks.

    Attributes:
        faq_id: ID of the FAQ that was clicked
        session_id: Widget session ID
        merchant_id: Merchant ID
    """

    faq_id: int = Field(description="FAQ ID that was clicked")
    session_id: str = Field(description="Widget session ID")
    merchant_id: int = Field(description="Merchant ID")


class FaqClickResponse(BaseModel):
    """Response schema for FAQ click tracking.

    Attributes:
        success: Whether the click was tracked successfully
        click_id: ID of the created interaction log entry
    """

    success: bool = Field(description="Whether tracking succeeded")
    click_id: int | None = Field(default=None, description="Interaction log ID")


@router.post("/faq-click", response_model=FaqClickResponse)
async def track_faq_click(
    request: FaqClickRequest,
    db: AsyncSession = Depends(get_db),
) -> FaqClickResponse:
    """Track FAQ button click from widget.

    Story 10-10: FAQ Usage Widget

    Records when a user clicks an FAQ button in the widget.
    This data is used to generate FAQ usage analytics in the dashboard.

    Args:
        request: FAQ click data with faq_id, session_id, and merchant_id
        db: Database session

    Returns:
        Success status and created interaction log ID

    Raises:
        HTTPException: If FAQ not found or merchant doesn't own it
    """
    try:
        # Verify the FAQ exists and belongs to the merchant
        faq = await db.get(Faq, request.faq_id)
        if not faq:
            raise HTTPException(
                status_code=404,
                detail={
                    "error_code": ErrorCode.FAQ_NOT_FOUND,
                    "message": "FAQ not found",
                    "details": f"FAQ ID {request.faq_id} does not exist",
                },
            )

        if faq.merchant_id != request.merchant_id:
            raise HTTPException(
                status_code=403,
                detail={
                    "error_code": ErrorCode.FORBIDDEN,
                    "message": "FAQ does not belong to this merchant",
                    "details": f"FAQ {request.faq_id} is not owned by merchant {request.merchant_id}",
                },
            )

        # Create interaction log entry
        interaction_log = FaqInteractionLog(
            faq_id=request.faq_id,
            merchant_id=request.merchant_id,
            session_id=request.session_id,
            clicked_at=datetime.now(UTC),
            had_followup=False,  # Will be updated if user sends a follow-up message
        )

        db.add(interaction_log)
        await db.commit()
        await db.refresh(interaction_log)

        logger.info(
            "faq_click_tracked: faq_id=%s merchant_id=%s session_id=%s interaction_id=%s",
            request.faq_id,
            request.merchant_id,
            request.session_id[:8] + "...",  # Log first 8 chars for privacy
            interaction_log.id,
        )

        return FaqClickResponse(success=True, click_id=interaction_log.id)

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            "faq_click_tracking_failed: faq_id=%s merchant_id=%s error=%s",
            request.faq_id,
            request.merchant_id,
            str(e),
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": ErrorCode.INTERNAL_ERROR,
                "message": "Failed to track FAQ click",
                "details": str(e),
            },
        )
