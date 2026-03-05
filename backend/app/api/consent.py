"""Consent management API endpoints.

Story 6-4: Data Tier Separation
Task 8: API integration tests
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.consent.extended_consent_service import ConversationConsentService
from app.services.privacy.data_tier_service import DataTier
from structlog import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/opt-out",
    summary="Opt out of data collection",
    description="Revoke consent and anonymize conversation data",
)
async def opt_out(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Handle consent opt-out request.

    Story 6-4: When user opts out:
    1. Revoke consent in database
    2. Update data tier to ANONYMIZED for conversations/messages
    3. Keep operational data (orders) intact

    Args:
        request: FastAPI request
        db: Database session

    Returns:
        Dict with opt-out confirmation
    """
    body = await request.json()
    merchant_id = body.get("merchantId")
    session_id = body.get("sessionId")
    visitor_id = body.get("visitorId")

    if not merchant_id:
        return {
            "success": False,
            "error": "merchantId is required",
        }

    if not session_id:
        return {
            "success": True,
            "message": "Opt-out completed",
            "session_id": None,
            "merchant_id": merchant_id,
        }

    from sqlalchemy import select, update
    from app.models.conversation import Conversation
    from app.models.message import Message

    consent_service = ConversationConsentService(db=db)

    result = await consent_service.record_conversation_consent(
        session_id=session_id,
        merchant_id=merchant_id,
        consent_granted=False,
        source="api_opt_out",
        visitor_id=visitor_id,
    )

    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.merchant_id == merchant_id,
            Conversation.platform_sender_id == session_id,
        )
    )
    conversations = conv_result.scalars().all()

    logger.info(
        "consent_opt_out_conversations_found",
        session_id=session_id,
        merchant_id=merchant_id,
        conversations_count=len(conversations),
    )

    for conv in conversations:
        logger.info(
            "updating_conversation_tier",
            conversation_id=conv.id,
            old_tier=conv.data_tier,
            new_tier=DataTier.ANONYMIZED,
        )
        conv.data_tier = DataTier.ANONYMIZED

        await db.execute(
            update(Message)
            .where(Message.conversation_id == conv.id)
            .values(data_tier=DataTier.ANONYMIZED)
        )

    await db.commit()

    logger.info(
        "consent_opt_out_completed",
        session_id=session_id,
        merchant_id=merchant_id,
        visitor_id=visitor_id,
    )

    return {
        "success": True,
        "message": "Opt-out completed successfully",
        "session_id": session_id,
        "merchant_id": merchant_id,
        "status": result.get("status"),
        "clear_visitor_id": result.get("clear_visitor_id", True),
    }
