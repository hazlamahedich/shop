"""Integration tests for natural error recovery flows (Story 11-7).

Tests that handlers correctly delegate to NaturalErrorRecoveryService
when errors occur, producing personality-consistent responses with
context-aware suggestions.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.error_recovery_service import (
    ErrorType,
    NaturalErrorRecoveryService,
)
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    SessionShoppingState,
)
from app.services.personality.conversation_templates import register_conversation_templates
from app.services.personality.error_recovery_templates import register_error_recovery_templates

register_conversation_templates()
register_error_recovery_templates()


def _make_merchant(
    personality: PersonalityType = PersonalityType.FRIENDLY,
    merchant_id: int = 1,
) -> MagicMock:
    merchant = MagicMock()
    merchant.id = merchant_id
    merchant.personality = personality
    merchant.business_name = "Test Shop"
    merchant.shopify_domain = "test.myshopify.com"
    merchant.onboarding_mode = "ecommerce"
    return merchant


def _make_context(
    last_search_query: str | None = None,
    last_viewed_products: list[dict] | None = None,
    last_cart_item_count: int = 0,
) -> ConversationContext:
    return ConversationContext(
        session_id="sess_test",
        merchant_id=1,
        channel=Channel.WIDGET,
        shopping_state=SessionShoppingState(
            last_search_query=last_search_query,
            last_viewed_products=last_viewed_products or [],
            last_cart_item_count=last_cart_item_count,
        ),
    )


class TestErrorRecoveryServiceEndToEnd:
    # GIVEN a friendly merchant with a last search query
    # WHEN NaturalErrorRecoveryService handles a SEARCH_FAILED error
    # THEN the response includes the original query in its message and correct metadata
    @pytest.mark.asyncio
    async def test_search_failed_with_context_produces_suggestion(self):
        service = NaturalErrorRecoveryService()
        merchant = _make_merchant(PersonalityType.FRIENDLY)
        context = _make_context(last_search_query="blue sneakers")
        response = await service.recover(
            error_type=ErrorType.SEARCH_FAILED,
            merchant=merchant,
            context=context,
            error=RuntimeError("Shopify API timeout"),
            intent="product_search",
            conversation_id="sess_test",
        )
        assert response.fallback is True
        assert response.intent == "product_search"
        assert "blue sneakers" in response.message
        assert response.metadata["error_type"] == "search_failed"
        assert response.metadata["error_class"] == "RuntimeError"
        assert response.metadata["recovered"] is True

    # GIVEN a professional merchant with cart items
    # WHEN NaturalErrorRecoveryService handles a CHECKOUT_FAILED error
    # THEN the response includes a fallback URL from the circuit breaker
    @pytest.mark.asyncio
    async def test_checkout_failed_with_cart_items_suggests_retry(self):
        service = NaturalErrorRecoveryService()
        merchant = _make_merchant(PersonalityType.PROFESSIONAL)
        context = _make_context(last_cart_item_count=3)
        with patch(
            "app.services.shopify.circuit_breaker.ShopifyCircuitBreaker.get_fallback_url",
            return_value="https://fallback.example.com",
        ):
            response = await service.recover(
                error_type=ErrorType.CHECKOUT_FAILED,
                merchant=merchant,
                context=context,
                error=Exception("test"),
                intent="checkout",
            )
            assert response.fallback is True
            assert response.fallback_url == "https://fallback.example.com"

    # GIVEN an enthusiastic merchant with a last search query
    # WHEN NaturalErrorRecoveryService handles an LLM_TIMEOUT error
    # THEN the response includes the original query in its message
    @pytest.mark.asyncio
    async def test_llm_timeout_with_search_query_includes_suggestion(self):
        service = NaturalErrorRecoveryService()
        merchant = _make_merchant(PersonalityType.ENTHUSIASTIC)
        context = _make_context(last_search_query="red dress")
        response = await service.recover(
            error_type=ErrorType.LLM_TIMEOUT,
            merchant=merchant,
            context=context,
            error=TimeoutError("LLM took too long"),
            intent="chat",
        )
        assert response.fallback is True
        assert "red dress" in response.message

    # GIVEN a merchant with no context
    # WHEN NaturalErrorRecoveryService handles a CONTEXT_LOST error
    # THEN the response suggests a fresh start with correct metadata
    @pytest.mark.asyncio
    async def test_context_lost_always_suggests_fresh_start(self):
        service = NaturalErrorRecoveryService()
        merchant = _make_merchant()
        context = _make_context()
        response = await service.recover(
            error_type=ErrorType.CONTEXT_LOST,
            merchant=merchant,
            context=context,
            error=Exception("Session expired"),
            intent="chat",
        )
        assert response.fallback is True
        assert response.message
        assert response.metadata["error_type"] == "context_lost"


class TestPersonalityConsistencyAcrossErrorTypes:
    # GIVEN any personality type with full shopping context
    # WHEN NaturalErrorRecoveryService handles every error type
    # THEN each response is non-empty with fallback=True and confidence=1.0
    @pytest.mark.parametrize(
        "personality",
        list(PersonalityType),
        ids=["friendly", "professional", "enthusiastic"],
    )
    @pytest.mark.asyncio
    async def test_all_error_types_produce_nonempty_message_for_all_personalities(
        self, personality
    ):
        service = NaturalErrorRecoveryService()
        merchant = _make_merchant(personality)
        context = _make_context(
            last_search_query="test query",
            last_viewed_products=[{"id": "1", "title": "Product"}],
            last_cart_item_count=2,
        )
        for error_type in ErrorType:
            response = await service.recover(
                error_type=error_type,
                merchant=merchant,
                context=context,
                error=Exception("test error"),
                intent="test",
                conversation_id="sess_test",
            )
            assert response.message, f"Empty message for {error_type} / {personality}"
            assert response.fallback is True
            assert response.confidence == 1.0


class TestHandlerErrorRecoveryIntegration:
    # GIVEN a CartHandler with a CartService that throws RuntimeError
    # WHEN the handler processes a "show my cart" message
    # THEN the real NaturalErrorRecoveryService produces a fallback
    #   response with cart_failed metadata
    @pytest.mark.asyncio
    async def test_cart_handler_error_uses_recovery_service(self):
        from app.services.conversation.handlers.cart_handler import CartHandler

        handler = CartHandler()
        merchant = _make_merchant()
        context = _make_context()
        db = AsyncMock()
        llm_service = AsyncMock()
        mock_cart_svc = AsyncMock()
        mock_cart_svc.get_cart.side_effect = RuntimeError("DB connection lost")
        with patch("app.services.cart.cart_service.CartService", return_value=mock_cart_svc):
            result = await handler.handle(db, merchant, llm_service, "show my cart", context)
            assert result is not None
            assert result.fallback is True
            assert result.metadata.get("error_type") == "cart_failed"

    # GIVEN an OrderHandler with _handle_order_tracking that throws RuntimeError
    # WHEN the handler processes an order tracking message
    # THEN the real NaturalErrorRecoveryService produces a fallback
    #   response with order_lookup_failed metadata
    @pytest.mark.asyncio
    async def test_order_handler_error_uses_recovery_service(self):
        from app.services.conversation.handlers.order_handler import OrderHandler

        handler = OrderHandler()
        merchant = _make_merchant()
        context = _make_context()
        db = AsyncMock()
        llm_service = AsyncMock()
        with patch.object(
            handler,
            "_handle_order_tracking",
            side_effect=RuntimeError("Shopify API down"),
        ):
            result = await handler.handle(db, merchant, llm_service, "where is my order", context)
            assert result is not None
            assert result.fallback is True
            assert result.metadata.get("error_type") == "order_lookup_failed"


class TestContextPreservation:
    # GIVEN a context with viewed products
    # WHEN NaturalErrorRecoveryService handles a CART_FAILED error
    # THEN the viewed_products list is not mutated
    @pytest.mark.asyncio
    async def test_recovery_does_not_mutate_viewed_products(self):
        service = NaturalErrorRecoveryService()
        merchant = _make_merchant()
        original_products = [{"id": "1", "title": "Shoes"}]
        context = _make_context(last_viewed_products=list(original_products))
        await service.recover(
            error_type=ErrorType.CART_FAILED,
            merchant=merchant,
            context=context,
            error=Exception("test"),
            intent="cart_add",
        )
        assert context.shopping_state.last_viewed_products == original_products

    # GIVEN a context with 5 cart items
    # WHEN recovery processes a CHECKOUT_FAILED error
    # THEN the last_cart_item_count is not mutated
    # GIVEN a context with a cart item count
    # WHEN NaturalErrorRecoveryService handles a CHECKOUT_FAILED error
    # THEN the cart count is not mutated
    @pytest.mark.asyncio
    async def test_recovery_does_not_mutate_cart_count(self):
        service = NaturalErrorRecoveryService()
        merchant = _make_merchant()
        context = _make_context(last_cart_item_count=5)
        await service.recover(
            error_type=ErrorType.CHECKOUT_FAILED,
            merchant=merchant,
            context=context,
            error=Exception("test"),
            intent="checkout",
        )
        assert context.shopping_state.last_cart_item_count == 5
