"""Greeting handler for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService

Handles GREETING intent with personality-based responses.
Enhanced to showcase pinned/featured products in greeting.
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
from app.services.personality.greeting_service import substitute_greeting_variables


logger = structlog.get_logger(__name__)


class GreetingHandler(BaseHandler):
    """Handler for GREETING intent.

    Story 5-10 Enhancement: Added returning shopper detection for personalized greetings.
    Enhanced: Shows pinned products in greeting message.

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
            ConversationResponse with greeting message and optional featured products
        """
        bot_name = merchant.bot_name or "Shopping Assistant"
        business_name = merchant.business_name or "our store"
        is_returning = context.is_returning_shopper

        # Fetch pinned products to showcase
        pinned_products = await self._get_greeting_pinned_products(db, merchant)

        if merchant.use_custom_greeting and merchant.custom_greeting:
            greeting_text = substitute_greeting_variables(
                merchant.custom_greeting,
                {
                    "bot_name": bot_name,
                    "business_name": business_name,
                    "business_hours": merchant.business_hours,
                },
            )
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

        # Add featured products mention if we have them
        if pinned_products:
            featured_names = [p["title"] for p in pinned_products[:2]]
            if len(featured_names) == 1:
                featured_text = f" Check out our featured item: {featured_names[0]}!"
            else:
                featured_text = f" Check out our featured items: {' and '.join(featured_names)}!"
            greeting_text = greeting_text + featured_text

        logger.debug(
            "greeting_handled",
            merchant_id=merchant.id,
            bot_name=bot_name,
            use_custom=merchant.use_custom_greeting,
            is_returning_shopper=is_returning,
            featured_products_count=len(pinned_products) if pinned_products else 0,
        )

        return ConversationResponse(
            message=greeting_text,
            intent="greeting",
            confidence=1.0,
            products=pinned_products if pinned_products else None,
            metadata={
                "bot_name": bot_name,
                "business_name": business_name,
                "is_returning_shopper": is_returning,
                "featured_products_shown": len(pinned_products) if pinned_products else 0,
            },
        )

    async def _get_greeting_pinned_products(
        self,
        db: AsyncSession,
        merchant: Merchant,
        max_products: int = 2,
    ) -> Optional[list[dict[str, Any]]]:
        """Fetch pinned products to showcase in greeting.

        Args:
            db: Database session
            merchant: Merchant configuration
            max_products: Maximum number of products to return

        Returns:
            List of pinned products with is_pinned=True, or None if none found
        """
        try:
            from app.services.product_pin_service import get_pinned_product_ids
            from app.services.shopify.product_search_service import ProductSearchService
            from app.services.intent.classification_schema import ExtractedEntities

            pinned_ids = await get_pinned_product_ids(db, merchant.id)
            if not pinned_ids:
                return None

            pinned_ids_set = {str(pid) for pid in pinned_ids}

            search_service = ProductSearchService(db=db)
            entities = ExtractedEntities()
            result = await search_service.search_products(entities, merchant.id)

            pinned_products = [p for p in result.products if str(p.id) in pinned_ids_set][
                :max_products
            ]

            if not pinned_products:
                return None

            formatted = [
                {
                    "id": p.id,
                    "product_id": p.id,
                    "variant_id": str(p.variants[0].id) if p.variants else None,
                    "title": p.title,
                    "price": float(p.price) if p.price else None,
                    "currency": str(p.currency_code) if p.currency_code else "USD",
                    "image_url": p.images[0].url if p.images else None,
                    "available": (
                        any(v.available_for_sale for v in p.variants) if p.variants else True
                    ),
                    "is_pinned": True,
                }
                for p in pinned_products
            ]

            logger.info(
                "greeting_pinned_products_fetched",
                merchant_id=merchant.id,
                count=len(formatted),
            )

            return formatted

        except Exception as e:
            logger.warning(
                "greeting_pinned_products_failed",
                merchant_id=merchant.id,
                error=str(e),
            )
            return None
