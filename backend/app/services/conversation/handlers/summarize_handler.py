"""SummarizeHandler for customer-facing conversation summarization.

Story 11-9: Conversation Summarization
Handles SUMMARIZE intent with customer-facing formatted summaries.
"""

from __future__ import annotations

import re
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.services.context_summarizer import ContextSummarizerService
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

logger = structlog.get_logger(__name__)

_PRODUCT_PATTERN = re.compile(
    r"\b(shoes?|shirt|dress|jacket|pants?|hat|bag|phone|laptop|watch|headphones?)\b",
    re.IGNORECASE,
)
_PRICE_PATTERN = re.compile(r"\$\d+[\d,.]*|\d+\s?(?:dollars?|bucks?)", re.IGNORECASE)
_SIZE_PATTERN = re.compile(r"\bsize\s+([\w]+)\b", re.IGNORECASE)
_COLOR_PATTERN = re.compile(
    r"\b(red|blue|green|black|white|yellow|orange|pink|purple|brown|gray|grey|navy)\b",
    re.IGNORECASE,
)


class SummarizeHandler(BaseHandler):
    """Handles SUMMARIZE intent - customer-facing conversation summary.

    Story 11-9: Conversation Summarization
    """

    MIN_CUSTOMER_TURNS_FOR_SUMMARY = 3

    def __init__(self) -> None:
        super().__init__()

    async def handle(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: Any,
        message: str,
        context: ConversationContext,
        entities: dict[str, Any] | None = None,
    ) -> ConversationResponse:
        """Generate a customer-facing conversation summary.

        Args:
            db: Database session
            merchant: Merchant model
            llm_service: LLM service (unused; SummarizeHandler gets its own)
            message: User's message
            context: Conversation context
            entities: Extracted entities (unused)

        Returns:
            ConversationResponse with summary content
        """
        try:
            personality = merchant.personality or "friendly"
            bot_name = merchant.bot_name or "Mantisbot"
            mode = merchant.onboarding_mode or "ecommerce"
            conversation_id = context.session_id

            customer_turns = [
                msg
                for msg in context.conversation_history
                if msg.get("role") in ("customer", "user")
            ]
            turn_count = len(customer_turns)
            total_turn_count = len(context.conversation_history)

            if turn_count < self.MIN_CUSTOMER_TURNS_FOR_SUMMARY:
                short_response = PersonalityAwareResponseFormatter.format_response(
                    "summarization",
                    "short_conversation",
                    personality,
                    include_transition=True,
                    mode=mode,
                    conversation_id=conversation_id,
                    bot_name=bot_name,
                )
                return ConversationResponse(
                    message=short_response,
                    intent="summarize",
                    confidence=1.0,
                    metadata={
                        "summary_generated": True,
                        "summary_turn_count": total_turn_count,
                    },
                )

            context_dict = context.model_dump(exclude_none=True)

            summarizer_service = ContextSummarizerService(db=db, llm_service=llm_service)

            try:
                summary_text = await summarizer_service.summarize_for_customer(
                    context_dict=context_dict,
                    mode=mode,
                    conversation_id=conversation_id,
                )
            except Exception as e:
                logger.warning(
                    "summarize_llm_failed_using_fallback",
                    error=str(e),
                    conversation_id=conversation_id,
                )
                summary_text = self._fallback_summary(context_dict, mode)

            intro = PersonalityAwareResponseFormatter.format_response(
                "summarization",
                "summary_intro",
                personality,
                include_transition=True,
                mode=mode,
                conversation_id=conversation_id,
                bot_name=bot_name,
            )

            closing = PersonalityAwareResponseFormatter.format_response(
                "summarization",
                "summary_closing",
                personality,
                include_transition=True,
                mode=mode,
                conversation_id=conversation_id,
                bot_name=bot_name,
            )

            full_message = f"{intro}\n\n{summary_text}\n\n{closing}"

            return ConversationResponse(
                message=full_message,
                intent="summarize",
                confidence=1.0,
                metadata={
                    "summary_generated": True,
                    "summary_turn_count": total_turn_count,
                },
            )

        except Exception as e:
            logger.error(
                "summarize_handler_failed",
                error=str(e),
                conversation_id=context.session_id,
                error_code=7100,
            )
            fallback_text = self._fallback_summary(
                context.model_dump(exclude_none=True) if context.conversation_history else {},
                merchant.onboarding_mode or "ecommerce",
            )
            return ConversationResponse(
                message=fallback_text,
                intent="summarize",
                confidence=1.0,
                metadata={
                    "summary_generated": True,
                    "summary_turn_count": len(context.conversation_history),
                    "fallback": True,
                },
            )

    @staticmethod
    def _fallback_summary(
        context_dict: dict[str, Any],
        mode: str,
    ) -> str:
        """Rule-based fallback summary without LLM."""
        history = context_dict.get("conversation_history", [])
        if not history:
            return "No conversation history to summarize."

        customer_messages = [
            msg.get("content", "")
            for msg in history
            if isinstance(msg, dict)
            and msg.get("role") in ("customer", "user")
            and msg.get("content")
        ]
        all_text = " ".join(customer_messages)

        if mode == "ecommerce":
            products = set(m.group(1).lower() for m in _PRODUCT_PATTERN.finditer(all_text))
            prices = _PRICE_PATTERN.findall(all_text)
            sizes = _SIZE_PATTERN.findall(all_text)
            colors = _COLOR_PATTERN.findall(all_text)

            lines = ["🛍️ **Discussion Summary:**"]
            if products:
                lines.append(f"- Products mentioned: {', '.join(sorted(products))}")
            if prices:
                lines.append(f"- Budget/price mentions: {', '.join(prices)}")
            if sizes:
                lines.append(f"- Size preferences: {', '.join(sizes)}")
            if colors:
                lines.append(f"- Color preferences: {', '.join(colors)}")
            if not any([products, prices, sizes, colors]):
                lines.append(
                    f"- {customer_messages[-1][:120]}"
                    if customer_messages
                    else "- No details extracted"
                )
            return "\n".join(lines)

        topics = [msg[:80] for msg in customer_messages] if customer_messages else []
        lines = ["📝 **Topics Covered:**"]
        for t in topics[:5]:
            lines.append(f"- {t}")
        if not topics:
            lines.append("- No topics extracted")
        return "\n".join(lines)
