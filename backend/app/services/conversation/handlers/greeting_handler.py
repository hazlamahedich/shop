"""Greeting handler for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService

Handles GREETING intent with personality-based responses.
"""

from __future__ import annotations

from typing import Any, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant, PersonalityType
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.llm.base_llm_service import BaseLLMService
from app.services.personality.personality_prompts import get_personality_system_prompt


logger = structlog.get_logger(__name__)


class GreetingHandler(BaseHandler):
    """Handler for GREETING intent.

    Story 5-10 Enhancement: Added returning shopper detection for personalized greetings.

    Returns a personality-based greeting for the merchant.
    Uses custom greeting if configured, otherwise generates
    based on personality type and returning shopper status.
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
        """Handle greeting intent.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service for this merchant
            message: User's message
            context: Conversation context
            entities: Extracted entities (not used for greetings)

        Returns:
            ConversationResponse with greeting message
        """
        bot_name = merchant.bot_name or "Shopping Assistant"
        business_name = merchant.business_name or "our store"
        is_returning = context.is_returning_shopper

        if merchant.use_custom_greeting and merchant.custom_greeting:
            greeting_text = merchant.custom_greeting
            if is_returning:
                greeting_text = f"Welcome back! {greeting_text}"
        else:
            personality_type: PersonalityType = merchant.personality or PersonalityType.FRIENDLY

            if is_returning:
                greeting_prompts = {
                    PersonalityType.FRIENDLY: f"Welcome back to {business_name}! Great to see you again. What can I help you find today?",
                    PersonalityType.PROFESSIONAL: f"Welcome back to {business_name}. I trust your previous experience was satisfactory. How may I assist you today?",
                    PersonalityType.ENTHUSIASTIC: f"You're back! Welcome back to {business_name}! I'm SO happy to see you again! Ready to find something amazing?",
                }
            else:
                greeting_prompts = {
                    PersonalityType.FRIENDLY: f"Hi there! I'm {bot_name}, your shopping assistant at {business_name}. How can I help you find something great today?",
                    PersonalityType.PROFESSIONAL: f"Hello, I'm {bot_name} at {business_name}. I'm here to assist you with your shopping needs. How may I help you?",
                    PersonalityType.ENTHUSIASTIC: f"Hey! Welcome to {business_name}! I'm {bot_name}, and I'm SO excited to help you shop! What are you looking for today?",
                }
            greeting_text = greeting_prompts.get(
                personality_type,
                greeting_prompts[PersonalityType.FRIENDLY],
            )

        logger.debug(
            "greeting_handled",
            merchant_id=merchant.id,
            bot_name=bot_name,
            use_custom=merchant.use_custom_greeting,
            is_returning_shopper=is_returning,
        )

        return ConversationResponse(
            message=greeting_text,
            intent="greeting",
            confidence=1.0,
            metadata={
                "bot_name": bot_name,
                "business_name": business_name,
                "is_returning_shopper": is_returning,
            },
        )
