"""Handoff handler for unified conversation processing.

Story 5-10 Code Review Fix (C9):
- Added HandoffHandler for human handoff intent
- Integrates with business hours handoff service
- Updates conversation status to 'handoff' in database
- Creates HandoffAlert for queue visibility
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
        from app.services.handoff.business_hours_handoff_service import (
            BusinessHoursHandoffService,
            STANDARD_HANDOFF_MESSAGE,
        )

        business_name = merchant.business_name or "our store"
        business_description = getattr(merchant, "business_description", None)
        handoff_service = BusinessHoursHandoffService()

        business_hours_config = getattr(merchant, "business_hours_config", None)

        try:
            handoff_message = handoff_service.build_handoff_message(
                business_hours_config,
                business_name=business_name if business_name != "our store" else None,
                business_description=business_description,
                customer_message=message,
            )
        except Exception as e:
            logger.warning(
                "handoff_message_failed",
                merchant_id=merchant.id,
                error=str(e),
            )
            fallback_name = business_name if business_name != "our store" else None
            if fallback_name:
                handoff_message = (
                    f"Thanks for reaching out to {fallback_name}! A member of our team will be with you shortly. "
                    f"We've received your message and will respond as soon as possible."
                )
            else:
                handoff_message = STANDARD_HANDOFF_MESSAGE

        conversation = await self._update_conversation_handoff_status(
            db=db,
            session_id=context.session_id,
            merchant_id=merchant.id,
            channel=context.channel,
            reason=entities.get("reason", "user_request") if entities else "user_request",
        )

        if conversation:
            await self._create_handoff_alert(
                db=db,
                conversation=conversation,
                message=message,
                merchant=merchant,
                business_hours_config=business_hours_config,
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
    ) -> Any:
        """Update conversation status to handoff in database.

        For widget channels, this also creates a conversation record
        if one doesn't exist (C8 fix).

        Args:
            db: Database session
            session_id: Session/conversation identifier
            merchant_id: Merchant ID
            channel: Channel type
            reason: Handoff reason

        Returns:
            The conversation object if successful, None otherwise.
        """
        try:
            from app.models.conversation import Conversation
            from datetime import datetime

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
                conversation.handoff_triggered_at = datetime.utcnow()
                conversation.handoff_reason = reason
            else:
                conversation = Conversation(
                    merchant_id=merchant_id,
                    platform_sender_id=session_id,
                    platform="widget" if channel == "widget" else channel,
                    status="handoff",
                    handoff_status="pending",
                    handoff_triggered_at=datetime.utcnow(),
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

            return conversation

        except Exception as e:
            logger.warning(
                "handoff_status_update_failed",
                merchant_id=merchant_id,
                session_id=session_id,
                error=str(e),
            )
            return None

    async def _create_handoff_alert(
        self,
        db: AsyncSession,
        conversation: Any,
        message: str,
        merchant: Merchant,
        business_hours_config: Any,
    ) -> None:
        """Create HandoffAlert for queue visibility.

        Urgency Logic (Story 4-12: Business Hours Aware):
        - HIGH: Checkout mentioned (revenue at risk)
        - MEDIUM: Low confidence or clarification loop (bot failed)
        - LOW: Keyword trigger (routine request)
        - After hours: All become LOW (no one available)

        Args:
            db: Database session
            conversation: Conversation ORM model
            message: User's message that triggered handoff
            merchant: Merchant ORM model
            business_hours_config: Business hours configuration
        """
        try:
            from app.models.handoff_alert import HandoffAlert
            from app.services.handoff.business_hours_handoff_service import (
                BusinessHoursHandoffService,
            )

            bh_service = BusinessHoursHandoffService()
            is_offline = bh_service.is_offline_handoff(business_hours_config)

            # Urgency classification based on issue type
            urgency_level = "low"
            message_lower = (message or "").lower()

            # High priority: Revenue at risk or urgent customer needs
            high_priority_keywords = [
                "checkout",
                "payment",
                "charged",
                "refund",
                "cancel",
                "can't pay",
                "payment failed",
                "billing",
                "dispute",
                "fraud",
                "stolen",
            ]

            # Medium priority: Issues needing attention but not revenue-critical
            medium_priority_keywords = [
                "order",
                "delivery",
                "shipping",
                "track",
                "where is",
                "not received",
                "missing",
                "damaged",
                "wrong",
                "return",
                "exchange",
                "account",
                "login",
                "password",
            ]

            if is_offline:
                # After hours: reduce urgency (no one available anyway)
                # But still differentiate for when team returns
                if any(kw in message_lower for kw in high_priority_keywords):
                    urgency_level = "medium"  # Downgrade from high since offline
                else:
                    urgency_level = "low"
            elif any(kw in message_lower for kw in high_priority_keywords):
                urgency_level = "high"
            elif conversation.handoff_reason in ("low_confidence", "clarification_loop"):
                urgency_level = "medium"
            elif any(kw in message_lower for kw in medium_priority_keywords):
                urgency_level = "medium"
            else:
                urgency_level = "low"

            alert = HandoffAlert(
                merchant_id=conversation.merchant_id,
                conversation_id=conversation.id,
                urgency_level=urgency_level,
                is_offline=is_offline,
                customer_name=None,
                customer_id=conversation.platform_sender_id,
                conversation_preview=message[:500] if message else None,
                wait_time_seconds=0,
                is_read=False,
            )

            db.add(alert)
            await db.flush()

            logger.info(
                "handoff_alert_created",
                alert_id=alert.id,
                conversation_id=conversation.id,
                merchant_id=conversation.merchant_id,
                urgency=urgency_level,
                is_offline=is_offline,
            )

        except Exception as e:
            logger.warning(
                "handoff_alert_creation_failed",
                conversation_id=conversation.id,
                error=str(e),
            )
