"""SummarizeHandler for customer-facing conversation summarization.

Story 11-9: Conversation Summarization
Handles SUMMARIZE intent with customer-facing formatted summaries.
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
from app.services.context_summarizer import ContextSummarizerService
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

logger = structlog.get_logger(__name__)


class SummarizeHandler(BaseHandler):
    """Handles SUMMARIZE intent - customer-facing conversation summary.

    Story 11-9: Conversation Summarization
    """

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

            if turn_count < 3:
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

        if mode == "general":
            topics = []
            for msg in history:
                if isinstance(msg, dict) and msg.get("content"):
                    topics.append(msg["content"][:80])
            return "Summary:\n" + "\n".join(f"- {t}" for t in topics)

        key_points = []
        for msg in history:
            if isinstance(msg, dict) and msg.get("content"):
                key_points.append(msg["content"][:100])
        return "Summary:\n" + "\n".join(f"- {p}" for p in key_points)
