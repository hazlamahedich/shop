"""General mode fallback handler for e-commerce intents.

Story 8-5: Backend - RAG Integration in Conversation
Task 3: Add General Chatbot Mode Fallback Handlers

Handles e-commerce intents (product search, cart, checkout, order tracking)
when detected in General Chatbot Mode, returning a friendly fallback message.
"""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.llm.base_llm_service import BaseLLMService
from app.services.personality.response_formatter import (
    PersonalityAwareResponseFormatter,
    PersonalityType,
)

logger = structlog.get_logger(__name__)


class GeneralModeFallbackHandler(BaseHandler):
    """Handle e-commerce intents in General Chatbot Mode.

    Returns a friendly message explaining that shopping features
    require a connected Shopify store, while offering to help with
    general questions.

    AC3: Graceful fallback for e-commerce intents in General mode
    """

    ECOMMERCE_INTENTS = {
        "PRODUCT_SEARCH",
        "ADD_TO_CART",
        "VIEW_CART",
        "REMOVE_CART",
        "CHECKOUT",
        "ORDER_TRACKING",
        "PRODUCT_INQUIRY",
        "PRODUCT_COMPARISON",
        "CART_VIEW",
        "CART_ADD",
        "CART_REMOVE",
        "CART_CLEAR",
    }

    async def handle(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: BaseLLMService,
        message: str,
        context: ConversationContext,
        entities: dict[str, Any] | None = None,
    ) -> ConversationResponse:
        """Handle e-commerce intent with fallback message.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service (not used, but required by interface)
            message: User's message
            context: Conversation context
            entities: Extracted entities (not used)

        Returns:
            ConversationResponse with personality-aware fallback message
        """
        formatter = PersonalityAwareResponseFormatter()

        personality_type: PersonalityType = merchant.personality or PersonalityType.FRIENDLY

        fallback_message = formatter.format_response(
            response_type="general_mode_fallback",
            message_key="ecommerce_not_supported",
            personality=personality_type,
        )

        logger.info(
            "general_mode_fallback_triggered",
            merchant_id=merchant.id,
            session_id=context.session_id,
            message_preview=message[:50],
        )

        return ConversationResponse(
            message=fallback_message,
            intent="general_mode_fallback",
            confidence=1.0,
            metadata={
                "fallback_reason": "ecommerce_intent_in_general_mode",
                "original_intent": entities.get("original_intent") if entities else None,
            },
        )
