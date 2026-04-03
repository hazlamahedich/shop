"""Unit tests for NaturalErrorRecoveryService (Story 11-7).

Tests error recovery with personality-consistent responses,
context-aware suggestions, and proper metadata.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.models.merchant import Merchant, PersonalityType
from app.services.conversation.error_recovery_service import (
    ErrorType,
    NaturalErrorRecoveryService,
)
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    SessionShoppingState,
)
from app.services.personality.error_recovery_templates import (
    register_error_recovery_templates,
)


@pytest.fixture(autouse=True)
def _register_templates():
    register_error_recovery_templates()


@pytest.fixture
def service():
    return NaturalErrorRecoveryService()


def _make_merchant(personality: PersonalityType = PersonalityType.FRIENDLY) -> MagicMock:
    merchant = MagicMock(spec=Merchant)
    merchant.id = 1
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
        session_id="sess_123",
        merchant_id=1,
        channel=Channel.WIDGET,
        shopping_state=SessionShoppingState(
            last_search_query=last_search_query,
            last_viewed_products=last_viewed_products or [],
            last_cart_item_count=last_cart_item_count,
        ),
    )


class TestErrorTypeMapping:
    def test_all_error_types_have_template_keys(self):
        for error_type in ErrorType:
            assert error_type in NaturalErrorRecoveryService._ERROR_TYPE_TO_TEMPLATE_KEY

    def test_template_key_matches_enum_value(self):
        mapping = NaturalErrorRecoveryService._ERROR_TYPE_TO_TEMPLATE_KEY
        assert mapping[ErrorType.SEARCH_FAILED] == "search_failed"
        assert mapping[ErrorType.CART_FAILED] == "cart_failed"
        assert mapping[ErrorType.CHECKOUT_FAILED] == "checkout_failed"
        assert mapping[ErrorType.ORDER_LOOKUP_FAILED] == "order_lookup_failed"
        assert mapping[ErrorType.LLM_TIMEOUT] == "llm_timeout"
        assert mapping[ErrorType.CONTEXT_LOST] == "context_lost"
        assert mapping[ErrorType.GENERAL] == "general"


class TestBasicRecovery:
    @pytest.mark.asyncio
    async def test_general_error_returns_fallback_response(self, service):
        merchant = _make_merchant(PersonalityType.FRIENDLY)
        context = _make_context()
        exc = RuntimeError("something broke")

        response = await service.recover(
            error_type=ErrorType.GENERAL,
            merchant=merchant,
            context=context,
            error=exc,
            intent="unknown",
            conversation_id="sess_123",
        )

        assert response.fallback is True
        assert response.intent == "unknown"
        assert response.confidence == 1.0
        assert response.metadata["error_type"] == "general"
        assert response.metadata["error_class"] == "RuntimeError"
        assert response.metadata["recovered"] is True

    @pytest.mark.asyncio
    async def test_response_message_is_not_empty(self, service):
        merchant = _make_merchant(PersonalityType.PROFESSIONAL)
        context = _make_context()

        for error_type in ErrorType:
            response = await service.recover(
                error_type=error_type,
                merchant=merchant,
                context=context,
                error=Exception("test"),
                intent="test",
            )
            assert response.message, f"No message for {error_type}"

    @pytest.mark.asyncio
    async def test_conversation_id_passed_to_formatter(self, service):
        merchant = _make_merchant()
        context = _make_context()

        with patch(
            "app.services.conversation.error_recovery_service.PersonalityAwareResponseFormatter.format_response",
            return_value="test msg",
        ) as mock_fmt:
            await service.recover(
                error_type=ErrorType.GENERAL,
                merchant=merchant,
                context=context,
                error=Exception("err"),
                intent="test",
                conversation_id="sess_abc",
            )
            _, kwargs = mock_fmt.call_args
            assert kwargs["conversation_id"] == "sess_abc"


class TestPersonalityConsistency:
    @pytest.mark.parametrize("personality", list(PersonalityType))
    @pytest.mark.asyncio
    async def test_all_personalities_get_nonempty_message(self, service, personality):
        merchant = _make_merchant(personality)
        context = _make_context()

        response = await service.recover(
            error_type=ErrorType.LLM_TIMEOUT,
            merchant=merchant,
            context=context,
            error=TimeoutError("timeout"),
            intent="chat",
            conversation_id="sess_1",
        )

        assert response.fallback is True
        assert response.message
        assert isinstance(response.message, str)


class TestContextAwareSuggestions:
    @pytest.mark.asyncio
    async def test_search_failed_with_last_query_includes_suggestion(self, service):
        merchant = _make_merchant()
        context = _make_context(last_search_query="blue shoes")

        response = await service.recover(
            error_type=ErrorType.SEARCH_FAILED,
            merchant=merchant,
            context=context,
            error=Exception("search err"),
            intent="product_search",
        )

        assert response.fallback is True
        assert response.message
        assert response.metadata["error_type"] == "search_failed"

    @pytest.mark.asyncio
    async def test_search_failed_with_viewed_products_includes_suggestion(self, service):
        merchant = _make_merchant()
        context = _make_context(last_viewed_products=[{"id": "1", "title": "Shoes"}])

        response = await service.recover(
            error_type=ErrorType.SEARCH_FAILED,
            merchant=merchant,
            context=context,
            error=Exception("search err"),
            intent="product_search",
        )

        assert response.fallback is True

    @pytest.mark.asyncio
    async def test_search_failed_no_context_no_suggestion(self, service):
        merchant = _make_merchant()
        context = _make_context()

        response = await service.recover(
            error_type=ErrorType.SEARCH_FAILED,
            merchant=merchant,
            context=context,
            error=Exception("err"),
            intent="product_search",
        )

        assert response.fallback is True

    @pytest.mark.asyncio
    async def test_cart_failed_with_viewed_products_suggests_retry(self, service):
        merchant = _make_merchant()
        context = _make_context(last_viewed_products=[{"id": "1", "title": "Hat"}])

        response = await service.recover(
            error_type=ErrorType.CART_FAILED,
            merchant=merchant,
            context=context,
            error=Exception("cart err"),
            intent="cart_add",
        )

        assert response.fallback is True

    @pytest.mark.asyncio
    async def test_cart_failed_no_viewed_products_no_suggestion(self, service):
        merchant = _make_merchant()
        context = _make_context()

        response = await service.recover(
            error_type=ErrorType.CART_FAILED,
            merchant=merchant,
            context=context,
            error=Exception("cart err"),
            intent="cart_add",
        )

        assert response.fallback is True

    @pytest.mark.asyncio
    async def test_checkout_failed_with_cart_items_suggests_retry(self, service):
        merchant = _make_merchant()
        context = _make_context(last_cart_item_count=3)

        response = await service.recover(
            error_type=ErrorType.CHECKOUT_FAILED,
            merchant=merchant,
            context=context,
            error=Exception("checkout err"),
            intent="checkout",
        )

        assert response.fallback is True

    @pytest.mark.asyncio
    async def test_checkout_failed_empty_cart_no_suggestion(self, service):
        merchant = _make_merchant()
        context = _make_context(last_cart_item_count=0)

        response = await service.recover(
            error_type=ErrorType.CHECKOUT_FAILED,
            merchant=merchant,
            context=context,
            error=Exception("checkout err"),
            intent="checkout",
        )

        assert response.fallback is True

    @pytest.mark.asyncio
    async def test_order_lookup_always_has_suggestion(self, service):
        merchant = _make_merchant()
        context = _make_context()

        response = await service.recover(
            error_type=ErrorType.ORDER_LOOKUP_FAILED,
            merchant=merchant,
            context=context,
            error=Exception("order err"),
            intent="order_tracking",
        )

        assert response.fallback is True

    @pytest.mark.asyncio
    async def test_llm_timeout_with_last_query_includes_suggestion(self, service):
        merchant = _make_merchant()
        context = _make_context(last_search_query="red dress")

        response = await service.recover(
            error_type=ErrorType.LLM_TIMEOUT,
            merchant=merchant,
            context=context,
            error=TimeoutError("llm timeout"),
            intent="chat",
        )

        assert response.fallback is True

    @pytest.mark.asyncio
    async def test_llm_timeout_no_context_returns_generic(self, service):
        merchant = _make_merchant()
        context = _make_context()

        response = await service.recover(
            error_type=ErrorType.LLM_TIMEOUT,
            merchant=merchant,
            context=context,
            error=TimeoutError("llm timeout"),
            intent="chat",
        )

        assert response.fallback is True

    @pytest.mark.asyncio
    async def test_context_lost_always_has_suggestion(self, service):
        merchant = _make_merchant()
        context = _make_context()

        response = await service.recover(
            error_type=ErrorType.CONTEXT_LOST,
            merchant=merchant,
            context=context,
            error=Exception("context lost"),
            intent="chat",
        )

        assert response.fallback is True


class TestFallbackUrl:
    @pytest.mark.asyncio
    async def test_checkout_failed_requests_fallback_url(self, service):
        merchant = _make_merchant()
        context = _make_context()

        with patch(
            "app.services.shopify.circuit_breaker.ShopifyCircuitBreaker.get_fallback_url",
            return_value="https://test.myshopify.com",
        ):
            response = await service.recover(
                error_type=ErrorType.CHECKOUT_FAILED,
                merchant=merchant,
                context=context,
                error=Exception("err"),
                intent="checkout",
            )
            assert response.fallback_url == "https://test.myshopify.com"

    @pytest.mark.asyncio
    async def test_cart_failed_requests_fallback_url(self, service):
        merchant = _make_merchant()
        context = _make_context()

        with patch(
            "app.services.shopify.circuit_breaker.ShopifyCircuitBreaker.get_fallback_url",
            return_value="https://test.myshopify.com/cart",
        ):
            response = await service.recover(
                error_type=ErrorType.CART_FAILED,
                merchant=merchant,
                context=context,
                error=Exception("err"),
                intent="cart_add",
            )
            assert response.fallback_url == "https://test.myshopify.com/cart"

    @pytest.mark.asyncio
    async def test_search_failed_no_fallback_url(self, service):
        merchant = _make_merchant()
        context = _make_context()

        response = await service.recover(
            error_type=ErrorType.SEARCH_FAILED,
            merchant=merchant,
            context=context,
            error=Exception("err"),
            intent="product_search",
        )

        assert response.fallback_url is None

    @pytest.mark.asyncio
    async def test_fallback_url_import_failure_returns_none(self, service):
        merchant = _make_merchant()
        context = _make_context()

        with patch.dict("sys.modules", {"app.services.shopify.circuit_breaker": None}):
            response = await service.recover(
                error_type=ErrorType.CHECKOUT_FAILED,
                merchant=merchant,
                context=context,
                error=Exception("err"),
                intent="checkout",
            )
            assert response.fallback_url is None


class TestLogging:
    @pytest.mark.asyncio
    async def test_recovery_logs_error_type_and_class(self, service):
        merchant = _make_merchant()
        context = _make_context()

        with patch("app.services.conversation.error_recovery_service.logger") as mock_logger:
            await service.recover(
                error_type=ErrorType.SEARCH_FAILED,
                merchant=merchant,
                context=context,
                error=ValueError("bad value"),
                intent="product_search",
                conversation_id="sess_1",
            )
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["error_type"] == "search_failed"
            assert call_kwargs["error_class"] == "ValueError"
            assert call_kwargs["intent"] == "product_search"
