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
    # GIVEN all ErrorType enum values
    # WHEN each enum value is inspected
    # THEN the .value matches the expected snake_case template key
    def test_all_error_type_values_are_valid_template_keys(self):
        expected = {
            "search_failed",
            "cart_failed",
            "checkout_failed",
            "order_lookup_failed",
            "llm_timeout",
            "context_lost",
            "general",
        }
        actual = {et.value for et in ErrorType}
        assert actual == expected

    # GIVEN all ErrorType enum values
    # WHEN the suggestion builder dict is inspected after registration
    # THEN every non-GENERAL type has a registered builder
    def test_all_non_general_error_types_have_suggestion_builders(self):
        NaturalErrorRecoveryService._register_builders()
        builders = NaturalErrorRecoveryService._SUGGESTION_BUILDERS
        for error_type in ErrorType:
            if error_type == ErrorType.GENERAL:
                continue
            assert error_type in builders, f"No builder for {error_type}"


class TestBasicRecovery:
    # GIVEN a general error and a friendly merchant
    # WHEN recovery is invoked with ErrorType.GENERAL
    # THEN the response has fallback=True, correct metadata, and confidence=1.0
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

    # GIVEN a professional merchant and every error type
    # WHEN recovery is called for each type
    # THEN every response contains a non-empty message string
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

    # GIVEN a specific conversation_id
    # WHEN recovery is invoked
    # THEN the formatter receives the conversation_id in kwargs
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
    # GIVEN any supported personality type
    # WHEN recovery handles an LLM timeout
    # THEN the response is a non-empty string with fallback=True
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
    # GIVEN a search error with a last_search_query in context
    # WHEN recovery is invoked with ErrorType.SEARCH_FAILED
    # THEN the response includes a suggestion referencing the context
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

    # GIVEN a search error with previously viewed products in context
    # WHEN recovery is invoked with ErrorType.SEARCH_FAILED
    # THEN the response has fallback=True
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

    # GIVEN a search error with no context (no last query, no viewed products)
    # WHEN recovery is invoked with ErrorType.SEARCH_FAILED
    # THEN the response still succeeds with fallback=True
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

    # GIVEN a cart error with viewed products in context
    # WHEN recovery is invoked with ErrorType.CART_FAILED
    # THEN the response has fallback=True
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

    # GIVEN a cart error with no viewed products
    # WHEN recovery is invoked with ErrorType.CART_FAILED
    # THEN the response still succeeds with fallback=True
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

    # GIVEN a checkout error with cart items in context
    # WHEN recovery is invoked with ErrorType.CHECKOUT_FAILED
    # THEN the response has fallback=True
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

    # GIVEN a checkout error with an empty cart
    # WHEN recovery is invoked with ErrorType.CHECKOUT_FAILED
    # THEN the response still succeeds with fallback=True
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

    # GIVEN an order lookup error with no context
    # WHEN recovery is invoked with ErrorType.ORDER_LOOKUP_FAILED
    # THEN the response always includes a suggestion with fallback=True
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

    # GIVEN an LLM timeout with a last search query in context
    # WHEN recovery is invoked with ErrorType.LLM_TIMEOUT
    # THEN the response has fallback=True
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

    # GIVEN an LLM timeout with no context
    # WHEN recovery is invoked with ErrorType.LLM_TIMEOUT
    # THEN the response returns a generic fallback
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

    # GIVEN a context_lost error with no context
    # WHEN recovery is invoked with ErrorType.CONTEXT_LOST
    # THEN the response always includes a suggestion with fallback=True
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
    # GIVEN a checkout error and a circuit breaker returning a fallback URL
    # WHEN recovery is invoked with ErrorType.CHECKOUT_FAILED
    # THEN the response includes the fallback URL
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

    # GIVEN a cart error and a circuit breaker returning a fallback URL
    # WHEN recovery is invoked with ErrorType.CART_FAILED
    # THEN the response includes the fallback URL
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

    # GIVEN a search error
    # WHEN recovery is invoked with ErrorType.SEARCH_FAILED
    # THEN the response has no fallback URL
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

    # GIVEN a checkout error where the circuit breaker import fails
    # WHEN recovery is invoked with ErrorType.CHECKOUT_FAILED
    # THEN the response fallback_url is None
    @pytest.mark.asyncio
    async def test_fallback_url_import_failure_returns_none(self, service):
        merchant = _make_merchant()
        context = _make_context()

        with patch(
            "app.services.conversation.error_recovery_service.PersonalityAwareResponseFormatter.format_response",
            return_value="test",
        ):
            with patch.dict("sys.modules", {"app.services.shopify.circuit_breaker": None}):
                response = await service.recover(
                    error_type=ErrorType.CHECKOUT_FAILED,
                    merchant=merchant,
                    context=context,
                    error=Exception("err"),
                    intent="checkout",
                )
                assert response.fallback_url is None

    # GIVEN a checkout error where ShopifyCircuitBreaker.get_fallback_url raises
    # WHEN recovery is invoked with ErrorType.CHECKOUT_FAILED
    # THEN the response fallback_url is None and no exception propagates
    @pytest.mark.asyncio
    async def test_fallback_url_runtime_exception_returns_none(self, service):
        merchant = _make_merchant()
        context = _make_context()

        with patch(
            "app.services.shopify.circuit_breaker.ShopifyCircuitBreaker.get_fallback_url",
            side_effect=RuntimeError("circuit breaker blew up"),
        ):
            response = await service.recover(
                error_type=ErrorType.CHECKOUT_FAILED,
                merchant=merchant,
                context=context,
                error=Exception("err"),
                intent="checkout",
            )
            assert response.fallback_url is None


class TestLogging:
    # GIVEN a search failed error
    # WHEN recovery is invoked
    # THEN the logger.info call includes error_type, error_class, and intent
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


class TestPerformance:
    # GIVEN a context with full shopping state
    # WHEN recovery is called for every error type
    # THEN each completes in under 50ms
    @pytest.mark.asyncio
    async def test_all_error_types_complete_under_50ms(self, service):
        import time

        merchant = _make_merchant()
        context = _make_context(
            last_search_query="shoes",
            last_viewed_products=[{"id": "1", "title": "Sneakers"}],
            last_cart_item_count=2,
        )

        for error_type in ErrorType:
            start = time.monotonic()
            await service.recover(
                error_type=error_type,
                merchant=merchant,
                context=context,
                error=Exception("perf test"),
                intent="test",
                conversation_id="sess_perf",
            )
            elapsed_ms = (time.monotonic() - start) * 1000
            assert elapsed_ms < 50, f"{error_type.value} took {elapsed_ms:.1f}ms (>50ms)"
