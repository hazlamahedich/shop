"""Natural error recovery service (Story 11-7).

Transforms robotic error responses into personality-consistent, natural messages.
Uses context-aware suggestions to keep conversations moving forward.

No LLM calls - template-based formatting only (performance/cost/reliability).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

import structlog

from app.models.merchant import Merchant
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

logger = structlog.get_logger(__name__)


class ErrorType(str, Enum):
    """Categorised error types for recovery message selection."""

    SEARCH_FAILED = "search_failed"
    CART_FAILED = "cart_failed"
    CHECKOUT_FAILED = "checkout_failed"
    ORDER_LOOKUP_FAILED = "order_lookup_failed"
    LLM_TIMEOUT = "llm_timeout"
    CONTEXT_LOST = "context_lost"
    GENERAL = "general"


class NaturalErrorRecoveryService:
    """Creates natural, personality-consistent error responses.

    Replaces robotic error messages with context-aware, helpful responses
    that suggest next actions using conversation context.

    Usage:
        service = NaturalErrorRecoveryService()
        response = await service.recover(
            error_type=ErrorType.SEARCH_FAILED,
            merchant=merchant,
            context=context,
            error=exc,
            intent="product_search",
            conversation_id="sess_123",
        )
    """

    _ERROR_TYPE_TO_TEMPLATE_KEY: dict[ErrorType, str] = {
        ErrorType.SEARCH_FAILED: "search_failed",
        ErrorType.CART_FAILED: "cart_failed",
        ErrorType.CHECKOUT_FAILED: "checkout_failed",
        ErrorType.ORDER_LOOKUP_FAILED: "order_lookup_failed",
        ErrorType.LLM_TIMEOUT: "llm_timeout",
        ErrorType.CONTEXT_LOST: "context_lost",
        ErrorType.GENERAL: "general",
    }

    async def recover(
        self,
        error_type: ErrorType,
        merchant: Merchant,
        context: ConversationContext,
        error: Exception,
        intent: str,
        conversation_id: str | None = None,
    ) -> ConversationResponse:
        """Generate a natural error recovery response.

        Args:
            error_type: Category of the error.
            merchant: Merchant with personality settings.
            context: Current conversation context (READ-ONLY).
            error: The original exception.
            intent: Intent being handled when error occurred.
            conversation_id: Session ID for anti-repetition.

        Returns:
            ConversationResponse with personality-consistent error message
            and context-aware suggestions.
        """
        personality = merchant.personality
        template_key = self._ERROR_TYPE_TO_TEMPLATE_KEY.get(error_type, "general")

        logger.info(
            "error_recovery_started",
            error_type=error_type.value,
            intent=intent,
            merchant_id=merchant.id,
            error_class=type(error).__name__,
        )

        message = PersonalityAwareResponseFormatter.format_response(
            "error",
            template_key,
            personality,
            include_transition=True,
            conversation_id=conversation_id,
            mode="ecommerce",
        )

        suggestion = self._build_suggestion(error_type, context, personality, conversation_id)
        if suggestion:
            message = f"{message}\n\n{suggestion}"

        metadata: dict[str, Any] = {
            "error_type": error_type.value,
            "error_class": type(error).__name__,
            "recovered": True,
        }

        fallback_url = self._get_fallback_url(error_type, merchant)

        return ConversationResponse(
            message=message,
            intent=intent,
            confidence=1.0,
            fallback=True,
            fallback_url=fallback_url,
            metadata=metadata,
        )

    def _build_suggestion(
        self,
        error_type: ErrorType,
        context: ConversationContext,
        personality: Any,
        conversation_id: str | None = None,
    ) -> str | None:
        """Build a context-aware suggestion based on error type and conversation state.

        Uses shopping_state from context to provide actionable next steps.
        Returns None when no relevant context is available.
        """
        shopping_state = context.shopping_state

        if error_type == ErrorType.SEARCH_FAILED:
            return self._search_failed_suggestion(shopping_state, personality, conversation_id)
        elif error_type == ErrorType.CART_FAILED:
            return self._cart_failed_suggestion(shopping_state, personality, conversation_id)
        elif error_type == ErrorType.CHECKOUT_FAILED:
            return self._checkout_failed_suggestion(shopping_state, personality, conversation_id)
        elif error_type == ErrorType.ORDER_LOOKUP_FAILED:
            return self._order_lookup_suggestion(personality, conversation_id)
        elif error_type == ErrorType.LLM_TIMEOUT:
            return self._llm_timeout_suggestion(shopping_state, personality, conversation_id)
        elif error_type == ErrorType.CONTEXT_LOST:
            return self._context_lost_suggestion(personality, conversation_id)

        return None

    def _search_failed_suggestion(
        self,
        shopping_state: Any,
        personality: Any,
        conversation_id: str | None,
    ) -> str | None:
        if shopping_state.last_search_query:
            return PersonalityAwareResponseFormatter.format_response(
                "error_recovery",
                "search_retry_with_last_query",
                personality,
                conversation_id=conversation_id,
                mode="ecommerce",
                last_query=shopping_state.last_search_query,
            )
        if shopping_state.last_viewed_products:
            return PersonalityAwareResponseFormatter.format_response(
                "error_recovery",
                "search_browse_viewed",
                personality,
                conversation_id=conversation_id,
                mode="ecommerce",
            )
        return None

    def _cart_failed_suggestion(
        self,
        shopping_state: Any,
        personality: Any,
        conversation_id: str | None,
    ) -> str | None:
        if shopping_state.last_viewed_products:
            return PersonalityAwareResponseFormatter.format_response(
                "error_recovery",
                "cart_retry_viewed_product",
                personality,
                conversation_id=conversation_id,
                mode="ecommerce",
            )
        return None

    def _checkout_failed_suggestion(
        self,
        shopping_state: Any,
        personality: Any,
        conversation_id: str | None,
    ) -> str | None:
        if shopping_state.last_cart_item_count and shopping_state.last_cart_item_count > 0:
            return PersonalityAwareResponseFormatter.format_response(
                "error_recovery",
                "checkout_retry_with_cart",
                personality,
                conversation_id=conversation_id,
                mode="ecommerce",
            )
        return None

    def _order_lookup_suggestion(
        self,
        personality: Any,
        conversation_id: str | None,
    ) -> str | None:
        return PersonalityAwareResponseFormatter.format_response(
            "error_recovery",
            "order_lookup_retry",
            personality,
            conversation_id=conversation_id,
            mode="ecommerce",
        )

    def _llm_timeout_suggestion(
        self,
        shopping_state: Any,
        personality: Any,
        conversation_id: str | None,
    ) -> str | None:
        if shopping_state.last_search_query:
            return PersonalityAwareResponseFormatter.format_response(
                "error_recovery",
                "llm_timeout_with_last_query",
                personality,
                conversation_id=conversation_id,
                mode="ecommerce",
                last_query=shopping_state.last_search_query,
            )
        return PersonalityAwareResponseFormatter.format_response(
            "error_recovery",
            "llm_timeout_generic",
            personality,
            conversation_id=conversation_id,
            mode="ecommerce",
        )

    def _context_lost_suggestion(
        self,
        personality: Any,
        conversation_id: str | None,
    ) -> str | None:
        return PersonalityAwareResponseFormatter.format_response(
            "error_recovery",
            "context_lost_suggestion",
            personality,
            conversation_id=conversation_id,
            mode="ecommerce",
        )

    def _get_fallback_url(
        self,
        error_type: ErrorType,
        merchant: Merchant,
    ) -> str | None:
        """Get fallback URL for external redirects when applicable."""
        if error_type in (
            ErrorType.CHECKOUT_FAILED,
            ErrorType.CART_FAILED,
        ):
            try:
                from app.services.shopify.circuit_breaker import ShopifyCircuitBreaker

                return ShopifyCircuitBreaker.get_fallback_url(merchant)
            except Exception:
                return None
        return None
