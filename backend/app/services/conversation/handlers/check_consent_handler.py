"""Check consent status handler for unified conversation processing.

Handles CHECK_CONSENT_STATUS intent:
- Retrieves current consent status from database
- Returns personality-aware status message with date
- Provides quick replies for consent management
"""

from __future__ import annotations

from typing import Any, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.llm.base_llm_service import BaseLLMService
from app.services.consent.extended_consent_service import ConversationConsentService
from app.services.consent.consent_prompt_service import ConsentPromptService
from app.schemas.consent import ConsentStatus


logger = structlog.get_logger(__name__)


class CheckConsentHandler(BaseHandler):
    """Handler for CHECK_CONSENT_STATUS intent.

    Retrieves and reports user's current consent status:
    - Queries ConversationConsentService for current status
    - Returns personality-aware message with status details
    - Includes quick replies for consent management
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
        """Handle consent status check request.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service (not used)
            message: User's message
            context: Conversation context with consent_state
            entities: Extracted entities

        Returns:
            ConversationResponse with consent status details
        """
        visitor_id = context.consent_state.visitor_id
        locale = context.metadata.get("locale", "en_US") if context.metadata else "en_US"

        try:
            consent_service = ConversationConsentService(db=db)
            consent = await consent_service.get_consent_for_conversation(
                session_id=context.session_id,
                merchant_id=merchant.id,
                visitor_id=visitor_id,
            )

            prompt_service = ConsentPromptService()

            if consent is None:
                status = ConsentStatus.PENDING
                granted_at = None
            else:
                if consent.granted and consent.revoked_at is None:
                    status = ConsentStatus.OPTED_IN
                elif consent.granted is False or consent.revoked_at is not None:
                    status = ConsentStatus.OPTED_OUT
                else:
                    status = ConsentStatus.PENDING
                granted_at = consent.granted_at

            status_message = prompt_service.get_status_check_message(
                personality=merchant.personality,
                status=status,
                granted_at=granted_at,
                locale=locale,
            )

            quick_replies = prompt_service.get_consent_management_quick_replies(status)

            should_show_prompt = status == ConsentStatus.PENDING

            logger.info(
                "consent_status_checked",
                merchant_id=merchant.id,
                session_id=context.session_id,
                visitor_id=visitor_id,
                status=status.value,
            )

            return ConversationResponse(
                message=status_message,
                intent="check_consent_status",
                confidence=1.0,
                checkout_url=None,
                fallback=False,
                fallback_url=None,
                products=None,
                cart=None,
                order=None,
                metadata={
                    "consent_status": status.value,
                    "consent_granted_at": granted_at.isoformat() if granted_at else None,
                    "quick_replies": quick_replies,
                    "consent_prompt_required": should_show_prompt,
                },
            )

        except Exception as e:
            logger.error(
                "consent_status_check_failed",
                merchant_id=merchant.id,
                session_id=context.session_id,
                error=str(e),
                exc_info=True,
            )
            return ConversationResponse(
                message="I couldn't check your preferences right now. Please try again later.",
                intent="check_consent_status",
                confidence=1.0,
                checkout_url=None,
                fallback=False,
                fallback_url=None,
                products=None,
                cart=None,
                order=None,
                metadata={"error": str(e)},
            )
