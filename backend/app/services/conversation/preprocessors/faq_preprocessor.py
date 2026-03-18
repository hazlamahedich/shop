"""FAQ preprocessor for unified conversation processing.

Story 5-10 Task 17: FAQ Pre-Processing

Checks incoming messages against merchant's FAQs before LLM processing.
Returns instant response if FAQ match found, saving LLM costs and
providing faster responses for common questions.

Enhanced with personality-aware rephrasing for consistent bot tone.

Priority order:
1. Check FAQ match (instant response)
2. Rephrase with personality if LLM service provided
3. If no match, proceed to intent classification (LLM)
"""

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import Faq
from app.services.conversation.schemas import ConversationContext, ConversationResponse
from app.services.faq import FaqMatch, FaqMatcher, match_faq, rephrase_faq_with_personality

logger = structlog.get_logger(__name__)


class FAQPreprocessor:
    """Pre-process messages for FAQ matches before LLM.

    Checks incoming messages against merchant's FAQs and returns
    instant responses for common questions. This saves LLM costs
    and provides faster responses.

    Usage:
        preprocessor = FAQPreprocessor()

        # Check for FAQ match before LLM
        response = await preprocessor.check_faq(
            db=db,
            merchant_id=merchant.id,
            message="What are your store hours?",
        )

        if response:
            return response  # FAQ matched, skip LLM

        # No FAQ match, proceed to LLM
    """

    FAQ_CONFIDENCE_THRESHOLD = 0.7
    CACHE_TTL_SECONDS = 300  # 5 minutes cache for FAQs

    def __init__(self) -> None:
        """Initialize FAQ preprocessor."""
        self.matcher = FaqMatcher()
        self.logger = structlog.get_logger(__name__)
        self._faq_cache: dict[int, tuple[list[Faq], float]] = {}

    async def check_faq(
        self,
        db: AsyncSession,
        merchant_id: int,
        message: str,
        context: ConversationContext | None = None,
        llm_service=None,
        merchant=None,
    ) -> ConversationResponse | None:
        """Check if message matches any merchant FAQ.

        Args:
            db: Database session
            merchant_id: Merchant ID to check FAQs for
            message: User's message
            context: Optional conversation context for personalization
            llm_service: Optional LLM service for personality rephrasing
            merchant: Optional merchant model for personality settings

        Returns:
            ConversationResponse if FAQ matched, None otherwise
        """
        if not message or not message.strip():
            return None

        merchant_faqs = await self._get_merchant_faqs(db, merchant_id)

        if not merchant_faqs:
            self.logger.debug(
                "faq_preprocessor_no_faqs",
                merchant_id=merchant_id,
            )
            return None

        faq_match = await match_faq(message, merchant_faqs)

        if not faq_match:
            self.logger.debug(
                "faq_preprocessor_no_match",
                merchant_id=merchant_id,
                message_preview=message[:50],
            )
            return None

        self.logger.info(
            "faq_preprocessor_match",
            merchant_id=merchant_id,
            faq_id=faq_match.faq.id,
            confidence=faq_match.confidence,
            match_type=faq_match.match_type,
        )

        return await self._create_response(
            faq_match=faq_match,
            context=context,
            llm_service=llm_service,
            merchant=merchant,
        )

    async def _get_merchant_faqs(
        self,
        db: AsyncSession,
        merchant_id: int,
    ) -> list[Faq]:
        """Get FAQs for a merchant from database.

        Args:
            db: Database session
            merchant_id: Merchant ID

        Returns:
            List of FAQ items
        """
        result = await db.execute(
            select(Faq).where(Faq.merchant_id == merchant_id).order_by(Faq.order_index)
        )
        return list(result.scalars().all())

    async def _create_response(
        self,
        faq_match: FaqMatch,
        context: ConversationContext | None,
        llm_service=None,
        merchant=None,
    ) -> ConversationResponse:
        """Create ConversationResponse from FAQ match.

        Args:
            faq_match: Matched FAQ with confidence
            context: Optional conversation context
            llm_service: Optional LLM service for personality rephrasing
            merchant: Optional merchant model for personality settings

        Returns:
            ConversationResponse with FAQ answer
        """
        answer = faq_match.faq.answer

        # Apply personality rephrasing if LLM service and merchant provided
        if llm_service and merchant:
            try:
                from app.models.merchant import PersonalityType

                personality_type = (
                    merchant.personality if merchant.personality else PersonalityType.FRIENDLY
                )
                business_name = merchant.business_name or "our store"
                bot_name = merchant.bot_name if merchant.bot_name else "Shopping Assistant"

                answer = await rephrase_faq_with_personality(
                    llm_service=llm_service,
                    faq_answer=faq_match.faq.answer,
                    personality_type=personality_type,
                    business_name=business_name,
                    bot_name=bot_name,
                )
                self.logger.info(
                    "faq_preprocessor_rephrased",
                    faq_id=faq_match.faq.id,
                    personality=personality_type.value
                    if hasattr(personality_type, "value")
                    else str(personality_type),
                )
            except Exception as e:
                self.logger.warning(
                    "faq_preprocessor_rephrase_failed",
                    faq_id=faq_match.faq.id,
                    error=str(e),
                )

        return ConversationResponse(
            message=answer,
            intent="faq",
            confidence=faq_match.confidence,
            checkout_url=None,
            fallback=False,
            fallback_url=None,
            products=None,
            cart=None,
            order=None,
            metadata={
                "faq_id": faq_match.faq.id,
                "faq_match_type": faq_match.match_type,
                "faq_question": faq_match.faq.question,
                "source": "faq_preprocessor",
            },
        )

    def clear_cache(self, merchant_id: int | None = None) -> None:
        """Clear FAQ cache.

        Args:
            merchant_id: Specific merchant to clear, or None for all
        """
        if merchant_id is not None:
            self._faq_cache.pop(merchant_id, None)
        else:
            self._faq_cache.clear()


class FAQPreprocessorMiddleware:
    """Middleware wrapper for FAQ preprocessor.

    Provides a middleware-style interface for integrating
    FAQ pre-processing into the conversation pipeline.
    """

    def __init__(self) -> None:
        """Initialize middleware."""
        self.preprocessor = FAQPreprocessor()
        self.logger = structlog.get_logger(__name__)

    async def process(
        self,
        db: AsyncSession,
        context: ConversationContext,
        message: str,
        llm_service=None,
        merchant=None,
    ) -> ConversationResponse | None:
        """Process message through FAQ preprocessor.

        Args:
            db: Database session
            context: Conversation context
            message: User's message
            llm_service: Optional LLM service for personality rephrasing
            merchant: Optional merchant model for personality settings

        Returns:
            ConversationResponse if FAQ matched, None to continue pipeline
        """
        return await self.preprocessor.check_faq(
            db=db,
            merchant_id=context.merchant_id,
            message=message,
            context=context,
            llm_service=llm_service,
            merchant=merchant,
        )

    def should_skip(self, context: ConversationContext) -> bool:
        """Check if FAQ processing should be skipped.

        Args:
            context: Conversation context

        Returns:
            True if should skip FAQ processing
        """
        skip_intents = context.metadata.get("skip_faq_for_intents", [])

        pending_consent = context.metadata.get("consent_pending")
        if pending_consent:
            return True

        clarification_active = context.metadata.get("clarification", {}).get("active")
        if clarification_active:
            return True

        return False
