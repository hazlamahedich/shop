"""Handoff handler for unified conversation processing.

Story 5-10 Code Review Fix (C9):
- Added HandoffHandler for human handoff intent
- Integrates with business hours handoff service
- Updates conversation status to 'handoff' in database
"""

from __future__ import annotations

from typing import Any, Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.llm.base_llm_service import BaseLLMService


logger = structlog.get_logger(__name__)


class HandoffHandler(BaseHandler):
    """Handler for HUMAN_HANDOFF intent.

    Triggers handoff to human support with:
    - Business hours-aware messaging
    - Conversation status update in database
    - Handoff notification creation
    """

    async def handle(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: BaseLLMService,
        message: str,
        context: ConversationContext,
        entities: Optional[dict[str, Any]] = None,
    ) -> ConversationResponse:
        """Handle human handoff request.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service (not used for handoff)
            message: User's message
            context: Conversation context
            entities: Extracted entities (may include handoff reason)

        Returns:
            ConversationResponse with handoff message
        """
        from app.services.handoff.business_hours_handoff_service import BusinessHoursHandoffService

        business_name = merchant.business_name or "our store"
        handoff_service = BusinessHoursHandoffService()

        business_hours_config = getattr(merchant, "business_hours_config", None)

        try:
            handoff_message = handoff_service.build_handoff_message(business_hours_config)
        except Exception as e:
            logger.warning(
                "handoff_message_failed",
                merchant_id=merchant.id,
                error=str(e),
            )
            handoff_message = (
                f"Thanks for reaching out! A member of our team will be with you shortly. "
                f"In the meantime, feel free to continue browsing {business_name}."
            )

        await self._update_conversation_handoff_status(
            db=db,
            session_id=context.session_id,
            merchant_id=merchant.id,
            channel=context.channel,
            reason=entities.get("reason", "user_request") if entities else "user_request",
        )

        logger.info(
            "handoff_triggered_unified",
            merchant_id=merchant.id,
            channel=context.channel,
            session_id=context.session_id,
        )

        return ConversationResponse(
            message=handoff_message,
            intent="human_handoff",
            confidence=1.0,
            metadata={"handoff_triggered": True},
        )

    async def _update_conversation_handoff_status(
        self,
        db: AsyncSession,
        session_id: str,
        merchant_id: int,
        channel: str,
        reason: str,
    ) -> None:
        """Update conversation status to handoff in database.

        For widget channels, this also creates a conversation record
        if one doesn't exist (C8 fix).

        Args:
            db: Database session
            session_id: Session/conversation identifier
            merchant_id: Merchant ID
            channel: Channel type
            reason: Handoff reason
        """
        try:
            from app.models.conversation import Conversation
            from datetime import datetime, timezone

            result = await db.execute(
                select(Conversation).where(
                    Conversation.merchant_id == merchant_id,
                    Conversation.platform_sender_id == session_id,
                )
            )
            conversation = result.scalars().first()

            if conversation:
                conversation.status = "handoff"
                conversation.handoff_status = "pending"
                conversation.handoff_triggered_at = datetime.now(timezone.utc)
                conversation.handoff_reason = reason
            else:
                conversation = Conversation(
                    merchant_id=merchant_id,
                    platform_sender_id=session_id,
                    platform="widget" if channel == "widget" else channel,
                    status="handoff",
                    handoff_status="pending",
                    handoff_triggered_at=datetime.now(timezone.utc),
                    handoff_reason=reason,
                )
                db.add(conversation)

            await db.flush()

            logger.info(
                "handoff_status_updated",
                merchant_id=merchant_id,
                session_id=session_id,
                conversation_id=conversation.id if conversation else None,
            )

        except Exception as e:
            logger.warning(
                "handoff_status_update_failed",
                merchant_id=merchant_id,
                session_id=session_id,
                error=str(e),
            )
