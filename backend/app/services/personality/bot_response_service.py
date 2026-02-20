"""Bot response service with personality integration (Story 1.10).

Generates personality-appropriate responses for conversational interactions.
Uses merchant's personality type and custom greeting to tailor bot responses.
Story 1.14: Integrated with greeting service for variable substitution.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.merchant import Merchant, PersonalityType
from app.services.personality.personality_prompts import get_personality_system_prompt
from app.services.personality.greeting_service import get_effective_greeting
from app.services.llm.base_llm_service import LLMMessage
from app.services.llm.llm_factory import LLMProviderFactory
from app.core.config import settings
import structlog


logger = structlog.get_logger(__name__)


# Personality-based greeting templates (with bot name placeholder)
GREETING_TEMPLATES = {
    PersonalityType.FRIENDLY: [
        "Hey! 👋 I'm {bot_name} from {business_name}. How can I help you today?",
        "Hi! I'm {bot_name} from {business_name}. What can I help you find?",
        "Hello! I'm {bot_name} from {business_name}. Happy to help you find what you're looking for!",
    ],
    PersonalityType.PROFESSIONAL: [
        "Good day. I'm {bot_name} from {business_name}. How may I assist you with your shopping needs?",
        "Hello. I'm {bot_name} from {business_name}. How may I help you today?",
        "Welcome. I'm {bot_name} from {business_name}. How may I be of assistance?",
    ],
    PersonalityType.ENTHUSIASTIC: [
        "Hey there!!! 🎉 I'm {bot_name} from {business_name} - so excited to help you find something amazing today!!!",
        "YAY!!! I'm {bot_name} from {business_name}!!! What awesome stuff can I help you find?!",
        "HI!!! ✨ I'm {bot_name} from {business_name}!!! Let's find you something great!!!",
    ],
}

# Personality-based help templates
HELP_TEMPLATES = {
    PersonalityType.FRIENDLY: [
        "Sure thing! Here's what I can help with: search products, view your cart, or checkout. What would you like to do?",
        "No problem! I can help you find products, check your cart, or complete checkout. What sounds good?",
    ],
    PersonalityType.PROFESSIONAL: [
        "Certainly. I can assist you with product searches, cart management, or checkout. How may I proceed?",
        "I would be happy to help. Available services include product search, cart viewing, and checkout assistance.",
    ],
    PersonalityType.ENTHUSIASTIC: [
        "OMG YAY!!! I can help you find AMAZING products, check your cart, or complete checkout!!! What do you want to do first?!",
        "WOOHOO!!! Let's do this!!! I can help you search products, view cart, or checkout!!! What's it gonna be?!",
    ],
}

# Personality-based error templates
ERROR_TEMPLATES = {
    PersonalityType.FRIENDLY: [
        "Oops, I ran into a little issue. Could you try again or let me know what you need help with?",
        "Sorry about that! Something went wrong on my end. Can you give it another shot?",
    ],
    PersonalityType.PROFESSIONAL: [
        "I apologize for the inconvenience. An error occurred. Please try again or contact support if the issue persists.",
        "My apologies. I encountered a technical issue. Please attempt your request again.",
    ],
    PersonalityType.ENTHUSIASTIC: [
        "OH NO!!! Something went wrong!!! 😢 But don't worry, let's try again!!! What were you trying to do?!",
        "AWWW MAN!!! Hit a little snag!!! But no worries!!! Let's give it another go!!! What can I help you with?!",
    ],
}


class BotResponseService:
    """Service for generating personality-appropriate bot responses.

    This service provides responses tailored to the merchant's personality type
    and custom greeting configuration.

    Story 1.10: Bot Personality Configuration
    """

    def __init__(self, db: Optional[AsyncSession] = None) -> None:
        """Initialize the bot response service.

        Args:
            db: Database session (creates new one if not provided)
        """
        self.db = db
        self.logger = structlog.get_logger(__name__)

    async def _get_merchant(
        self, merchant_id: int, db: Optional[AsyncSession] = None
    ) -> Optional[Merchant]:
        """Get merchant by ID.

        Args:
            merchant_id: Merchant ID
            db: Database session (uses instance db if not provided)

        Returns:
            Merchant object or None if not found
        """
        if db is None:
            if self.db is None:
                # Create new session if none exists
                async with get_db() as session:
                    result = await session.execute(
                        select(Merchant).where(Merchant.id == merchant_id)
                    )
                    return result.scalars().first()
            else:
                result = await self.db.execute(select(Merchant).where(Merchant.id == merchant_id))
                return result.scalars().first()
        else:
            result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
            return result.scalars().first()

    async def get_greeting(
        self,
        merchant_id: int,
        db: Optional[AsyncSession] = None,
    ) -> str:
        """Get personality-appropriate greeting for merchant.

        Story 1.12: Integrates bot name into greeting messages.
        Story 1.14: Uses greeting service with variable substitution.

        Args:
            merchant_id: Merchant ID
            db: Optional database session

        Returns:
            Greeting message string

        Examples:
            >>> await service.get_greeting(1)
            "Hey! 👋 I'm GearBot from Alex's Athletic Gear. How can I help you today?"
        """
        merchant = await self._get_merchant(merchant_id, db)

        if not merchant:
            # Return default friendly greeting
            return "Hi! How can I help you today?"

        # Build merchant config for greeting service
        merchant_config = {
            "personality": merchant.personality or PersonalityType.FRIENDLY,
            "custom_greeting": merchant.custom_greeting,
            "use_custom_greeting": merchant.use_custom_greeting,
            "bot_name": merchant.bot_name,
            "business_name": merchant.business_name,
            "business_hours": merchant.business_hours,
        }

        # Use greeting service (Story 1.14)
        return get_effective_greeting(merchant_config)

    async def get_help_response(
        self,
        merchant_id: int,
        db: Optional[AsyncSession] = None,
    ) -> str:
        """Get personality-appropriate help response.

        Args:
            merchant_id: Merchant ID
            db: Optional database session

        Returns:
            Help message string
        """
        merchant = await self._get_merchant(merchant_id, db)
        personality = merchant.personality if merchant else PersonalityType.FRIENDLY

        import random

        templates = HELP_TEMPLATES.get(personality, HELP_TEMPLATES[PersonalityType.FRIENDLY])
        return random.choice(templates)

    async def get_error_response(
        self,
        merchant_id: int,
        db: Optional[AsyncSession] = None,
    ) -> str:
        """Get personality-appropriate error response.

        Args:
            merchant_id: Merchant ID
            db: Optional database session

        Returns:
            Error message string
        """
        merchant = await self._get_merchant(merchant_id, db)
        personality = merchant.personality if merchant else PersonalityType.FRIENDLY

        import random

        templates = ERROR_TEMPLATES.get(personality, ERROR_TEMPLATES[PersonalityType.FRIENDLY])
        return random.choice(templates)

    async def get_system_prompt(
        self,
        merchant_id: int,
        db: Optional[AsyncSession] = None,
    ) -> str:
        """Get full system prompt with personality for LLM calls.

        Args:
            merchant_id: Merchant ID
            db: Optional database session

        Returns:
            System prompt string with personality guidelines
        """
        merchant = await self._get_merchant(merchant_id, db)

        if not merchant:
            return get_personality_system_prompt(PersonalityType.FRIENDLY)

        personality = merchant.personality or PersonalityType.FRIENDLY
        custom_greeting = merchant.custom_greeting
        business_name = merchant.business_name
        business_description = merchant.business_description
        business_hours = merchant.business_hours
        bot_name = merchant.bot_name

        product_context = ""
        order_context = ""
        if db:
            try:
                from app.services.product_context_service import (
                    get_product_context_prompt_section,
                    get_order_context_prompt_section,
                )

                product_context = await get_product_context_prompt_section(db, merchant_id)
            except Exception as e:
                self.logger.warning(
                    "product_context_fetch_failed",
                    merchant_id=merchant_id,
                    error=str(e),
                )

            try:
                from app.services.product_context_service import get_order_context_prompt_section

                order_context = await get_order_context_prompt_section(db, merchant_id)
            except Exception as e:
                self.logger.warning(
                    "order_context_fetch_failed",
                    merchant_id=merchant_id,
                    error=str(e),
                )

        return get_personality_system_prompt(
            personality,
            custom_greeting,
            business_name,
            business_description,
            business_hours,
            bot_name,
            product_context,
            order_context,
        )


async def get_pinned_product_ids(
    self,
    merchant_id: int,
    db: Optional[AsyncSession] = None,
) -> list[str]:
    """Get list of pinned product IDs for a merchant.

    Used by bot recommendation service to boost pinned products.

    Story 1.15 AC 4: Integration with Bot Recommendation Engine

    Args:
        merchant_id: Merchant ID
        db: Optional database session

    Returns:
        List of product IDs that are pinned
    """
    from app.services.product_pin_service import get_pinned_product_ids

    if db is None:
        if self.db is None:
            async with get_db() as session:
                result = await session.execute(
                    select(ProductPin).where(ProductPin.merchant_id == merchant_id)
                )
                return [p.product_id for p in result.scalars().all()]
        else:
            result = await self.db.execute(
                select(ProductPin).where(ProductPin.merchant_id == merchant_id)
            )
            return [p.product_id for p in result.scalars().all()]
    else:
        result = await self.db.execute(
            select(ProductPin).where(ProductPin.merchant_id == merchant_id)
        )
        return [p.product_id for p in result.scalars().all()]


async def add_pin_status_to_products(
    self,
    products: list[dict],
    pinned_product_ids: list[str],
) -> list[dict]:
    """Add pin status and ordering to product list.

    Pinned products appear first in recommendation results
    with 2x relevance boost.

    Story 1.15 AC 4: Integration with Bot Recommendation Engine

    Args:
        products: List of product dictionaries from search
        pinned_product_ids: List of pinned product IDs

    Returns:
        Product list with is_pinned flag and relevance_score
    """
    pinned_set = set(pinned_product_ids) if pinned_product_ids else set()

    result = []
    for product in products:
        product_id = product.get("id", "")
        is_pinned = product_id in pinned_set

        # Add pin status and calculate relevance score
        # Pinned products get 2x boost
        base_score = product.get("relevance_score", 1.0)
        if is_pinned:
            # Pinned products get 2x relevance boost
            # Minimum score of 2.0 for pinned products
            adjusted_score = base_score * 2.0
        else:
            adjusted_score = base_score

        enhanced_product = {
            **product,
            "is_pinned": is_pinned,
            "relevance_score": adjusted_score,
        }
        result.append(enhanced_product)

    # Sort: pinned products first (by their pinned_order), then by relevance
    # For now, since we don't have pinned_order from product search,
    # we sort by is_pinned flag first, then relevance_score
    result.sort(key=lambda p: (not p["is_pinned"], -p["relevance_score"]))

    return result
