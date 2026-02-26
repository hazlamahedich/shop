"""Forget preferences handler for unified conversation processing.

Story 6-1: Opt-In Consent Flow
Task 3.3: Implement "forget my preferences" handler
Story 6-2: Request Data Deletion
Task 2: Wire up handler to call enhanced deletion

Handles FORGET_PREFERENCES intent:
- Resets consent to PENDING state
- Deletes voluntary data (conversation history, preferences)
- Returns personality-aware confirmation message
"""

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
from app.core.errors import APIError, ErrorCode


logger = structlog.get_logger(__name__)


class ForgetPreferencesHandler(BaseHandler):
    """Handler for FORGET_PREFERENCES intent.

    Resets consent and deletes voluntary data:
    - Calls ConversationConsentService.handle_forget_preferences_with_deletion()
    - Passes visitor_id from context for cross-platform deletion
    - Updates context consent state
    - Returns personality-aware confirmation
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
        """Handle forget preferences request.

        Story 6-2 Task 2: Wire up handler to call enhanced deletion.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service (not used)
            message: User's message
            context: Conversation context
            entities: Extracted entities

        Returns:
            ConversationResponse with confirmation message
        """
        visitor_id = context.consent_state.visitor_id

        try:
            consent_service = ConversationConsentService(db=db)

            result = await consent_service.handle_forget_preferences_with_deletion(
                session_id=context.session_id,
                merchant_id=merchant.id,
                visitor_id=visitor_id,
            )

            context.consent_state.status = "pending"
            context.consent_state.can_store_conversation = False
            context.consent_state.prompt_shown = False
            context.consent_state.visitor_id = None
            context.consent_status = "pending"

            logger.info(
                "preferences_forgotten_handler",
                merchant_id=merchant.id,
                session_id=context.session_id,
                visitor_id=visitor_id,
                deletion_summary=result.get("deletion_summary"),
            )

        except APIError as e:
            if e.code == ErrorCode.VALIDATION_ERROR and "Rate limit" in str(e.message):
                logger.warning(
                    "forget_preferences_rate_limited",
                    merchant_id=merchant.id,
                    session_id=context.session_id,
                )
                return ConversationResponse(
                    message="You've already requested data deletion recently. Please wait before trying again.",
                    intent="forget_preferences",
                    confidence=1.0,
                    checkout_url=None,
                    fallback=False,
                    fallback_url=None,
                    products=None,
                    cart=None,
                    order=None,
                    metadata={
                        "preferences_forgotten": False,
                        "rate_limited": True,
                        "error": e.message,
                    },
                )

            logger.warning(
                "forget_preferences_failed",
                merchant_id=merchant.id,
                session_id=context.session_id,
                error=str(e),
            )
            return ConversationResponse(
                message="I encountered an error while trying to delete your preferences. Please try again later.",
                intent="forget_preferences",
                confidence=1.0,
                checkout_url=None,
                fallback=False,
                fallback_url=None,
                products=None,
                cart=None,
                order=None,
                metadata={
                    "preferences_forgotten": False,
                    "error": str(e),
                },
            )

        except Exception as e:
            logger.error(
                "forget_preferences_unexpected_error",
                merchant_id=merchant.id,
                session_id=context.session_id,
                error=str(e),
                exc_info=True,
            )
            return ConversationResponse(
                message="I encountered an unexpected error. Please try again later.",
                intent="forget_preferences",
                confidence=1.0,
                checkout_url=None,
                fallback=False,
                fallback_url=None,
                products=None,
                cart=None,
                order=None,
                metadata={
                    "preferences_forgotten": False,
                    "error": str(e),
                },
            )

        prompt_service = ConsentPromptService()
        confirmation_message = prompt_service.get_forget_confirm_message(
            personality=merchant.personality,
        )

        return ConversationResponse(
            message=confirmation_message,
            intent="forget_preferences",
            confidence=1.0,
            checkout_url=None,
            fallback=False,
            fallback_url=None,
            products=None,
            cart=None,
            order=None,
            metadata={
                "preferences_forgotten": True,
                "consent_reset": True,
                "clear_visitor_id": True,
            },
        )
