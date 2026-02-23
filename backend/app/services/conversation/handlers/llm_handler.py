"""LLM handler for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService

Handles GENERAL and UNKNOWN intents with LLM-powered responses.
Enhanced with automatic product mention detection for product cards.
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
from app.services.llm.base_llm_service import BaseLLMService, LLMMessage
from app.services.personality.personality_prompts import get_personality_system_prompt


logger = structlog.get_logger(__name__)


class LLMHandler(BaseHandler):
    """Handler for GENERAL and UNKNOWN intents.

    Generates responses using LLM with merchant's personality
    and business context.

    Enhanced to detect product mentions and attach product cards.
    Only shows products for shopping-related queries (intent-aware).
    """

    PRODUCT_RELATED_INTENTS = {
        "product_search",
        "product_inquiry",
        "product_comparison",
        "price_inquiry",
        "recommendation",
    }

    async def handle(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: BaseLLMService,
        message: str,
        context: ConversationContext,
        entities: Optional[dict[str, Any]] = None,
    ) -> ConversationResponse:
        """Handle general/unknown intent with LLM.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service for this merchant
            message: User's message
            context: Conversation context
            entities: Extracted entities (not used for general)

        Returns:
            ConversationResponse with LLM-generated message
        """
        bot_name = merchant.bot_name or "Shopping Assistant"
        business_name = merchant.business_name or "our store"
        personality_type: PersonalityType = merchant.personality or PersonalityType.FRIENDLY

        system_prompt = await self._build_system_prompt(
            db=db,
            merchant=merchant,
            bot_name=bot_name,
            business_name=business_name,
            personality_type=personality_type,
        )

        messages = [LLMMessage(role="system", content=system_prompt)]

        for msg in context.conversation_history[-5:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append(LLMMessage(role=role, content=msg.get("content", "")))

        messages.append(LLMMessage(role="user", content=message))

        try:
            response = await llm_service.chat(messages=messages, temperature=0.7)
            response_text = response.content
        except Exception as e:
            logger.warning(
                "llm_handler_fallback",
                merchant_id=merchant.id,
                error=str(e),
            )
            response_text = (
                f"I'm here to help you shop at {business_name}! "
                "You can ask me about products, check your cart, or place an order."
            )

        products = None
        if self._should_detect_products(message, response_text):
            products = await self._detect_product_mentions(
                response_text=response_text,
                merchant=merchant,
                llm_service=llm_service,
                db=db,
            )

        return ConversationResponse(
            message=response_text,
            intent="general",
            confidence=1.0,
            products=products,
            metadata={"bot_name": bot_name, "business_name": business_name},
        )

    def _should_detect_products(self, user_message: str, response_text: str) -> bool:
        """Determine if product cards should be shown based on message content.

        Product cards should only appear for shopping-related queries,
        not for informational questions like "where are you located?".

        Args:
            user_message: Original user message
            response_text: LLM's response

        Returns:
            True if product detection should run, False otherwise
        """
        lower_msg = user_message.lower().strip()

        non_product_patterns = [
            "where are you located",
            "where is your store",
            "what is your address",
            "what are your hours",
            "business hours",
            "shipping policy",
            "return policy",
            "how do i return",
            "track my order",
            "order status",
            "contact you",
            "phone number",
            "email address",
            "talk to human",
            "speak to someone",
        ]

        for pattern in non_product_patterns:
            if pattern in lower_msg:
                return False

        shopping_indicators = [
            "looking for",
            "do you have",
            "show me",
            "i want",
            "i need",
            "buy",
            "purchase",
            "how much",
            "price",
            "cost",
            "available",
            "in stock",
            "recommend",
            "suggest",
            "best seller",
            "featured",
            "popular",
            "what do you sell",
            "products",
            "items",
        ]

        for indicator in shopping_indicators:
            if indicator in lower_msg:
                return True

        return False

    async def _detect_product_mentions(
        self,
        response_text: str,
        merchant: Merchant,
        llm_service: BaseLLMService,
        db: AsyncSession,
    ) -> Optional[list[dict[str, Any]]]:
        """Detect product mentions in LLM response and fetch products.

        Args:
            response_text: The LLM's response text
            merchant: Merchant configuration
            llm_service: LLM service for detection
            db: Database session

        Returns:
            List of products if mentions detected, None otherwise
        """
        try:
            from app.services.conversation.product_mention_detector import ProductMentionDetector

            detector = ProductMentionDetector(llm_service=llm_service)

            products = await detector.detect_and_fetch(
                response_text=response_text,
                merchant_id=merchant.id,
                db=db,
                max_products=3,
            )

            if products:
                logger.info(
                    "llm_handler_products_detected",
                    merchant_id=merchant.id,
                    products_count=len(products),
                )

            return products

        except Exception as e:
            logger.warning(
                "llm_handler_product_detection_failed",
                merchant_id=merchant.id,
                error=str(e),
            )
            return None

    async def _build_system_prompt(
        self,
        db: AsyncSession,
        merchant: Merchant,
        bot_name: str,
        business_name: str,
        personality_type: PersonalityType,
    ) -> str:
        """Build system prompt with personality and context.

        Story 5-10: Fixed positional args bug - now passes all parameters correctly.
        Includes business_hours, custom_greeting, business_description, and product context.

        Args:
            db: Database session
            merchant: Merchant configuration
            bot_name: Bot's name
            business_name: Business name
            personality_type: Personality type

        Returns:
            Complete system prompt
        """
        custom_greeting = getattr(merchant, "custom_greeting", None)
        business_description = getattr(merchant, "business_description", None)
        business_hours = getattr(merchant, "business_hours", None)

        product_context = ""
        order_context = ""

        if db:
            try:
                from app.services.product_context_service import (
                    get_product_context_prompt_section,
                    get_order_context_prompt_section,
                )

                product_context = await get_product_context_prompt_section(db, merchant.id)
                order_context = await get_order_context_prompt_section(db, merchant.id)
            except Exception as e:
                logger.warning(
                    "llm_handler_context_failed",
                    merchant_id=merchant.id,
                    error=str(e),
                )

        personality_prompt = get_personality_system_prompt(
            personality_type,
            custom_greeting,
            business_name,
            business_description,
            business_hours,
            bot_name,
            product_context,
            order_context,
        )

        return personality_prompt
