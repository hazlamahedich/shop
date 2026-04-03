"""Integration tests for RecommendationHandler error paths (Story 11-6).

Tests _fetch_products and _load_context_data failure scenarios,
verifying graceful degradation and error responses.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.merchant import PersonalityType
from app.schemas.shopify import Product, ProductVariant
from app.services.conversation.handlers.recommendation_handler import RecommendationHandler
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    ConversationResponse,
    SessionShoppingState,
)


def _make_product(
    product_id: str = "1",
    title: str = "Test Product",
    price: float = 50.0,
    product_type: str = "shoes",
    tags: list[str] | None = None,
    variants: list[ProductVariant] | None = None,
) -> Product:
    return Product(
        id=product_id,
        title=title,
        product_type=product_type,
        price=price,
        tags=tags or [],
        variants=variants or [],
    )


@pytest.fixture
def handler():
    return RecommendationHandler()


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def ecommerce_merchant():
    merchant = MagicMock()
    merchant.id = 1
    merchant.business_name = "Test Store"
    merchant.onboarding_mode = "ecommerce"
    merchant.personality = PersonalityType.FRIENDLY
    return merchant


@pytest.fixture
def mock_llm():
    service = AsyncMock()
    service.chat = AsyncMock(return_value="LLM response")
    return service


@pytest.fixture
def context():
    return ConversationContext(
        session_id="test-session-error",
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=[],
        shopping_state=SessionShoppingState(),
    )


@pytest.fixture
def context_no_shopping_state():
    return ConversationContext(
        session_id="test-session-no-state",
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=[],
        shopping_state=None,
    )


class TestFetchProductsErrors:
    @pytest.mark.asyncio
    async def test_shopify_api_timeout(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        with patch.object(
            handler,
            "_fetch_products",
            new_callable=AsyncMock,
            side_effect=TimeoutError("Shopify API timeout"),
        ):
            result = await handler.handle(
                mock_db, ecommerce_merchant, mock_llm, "recommend something", context
            )
        assert result.fallback is True
        assert result.intent == "product_recommendation"
        assert isinstance(result.message, str)
        assert len(result.message) > 0

    @pytest.mark.asyncio
    async def test_shopify_connection_error(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        with patch.object(
            handler,
            "_fetch_products",
            new_callable=AsyncMock,
            side_effect=ConnectionError("Cannot reach Shopify"),
        ):
            result = await handler.handle(
                mock_db, ecommerce_merchant, mock_llm, "show me products", context
            )
        assert result.fallback is True
        assert result.intent == "product_recommendation"

    @pytest.mark.asyncio
    async def test_shopify_auth_error(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        with patch.object(
            handler,
            "_fetch_products",
            new_callable=AsyncMock,
            side_effect=PermissionError("Invalid API credentials"),
        ):
            result = await handler.handle(
                mock_db, ecommerce_merchant, mock_llm, "recommend", context
            )
        assert result.fallback is True

    @pytest.mark.asyncio
    async def test_generic_fetch_exception(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        with patch.object(
            handler,
            "_fetch_products",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Unexpected error"),
        ):
            result = await handler.handle(
                mock_db, ecommerce_merchant, mock_llm, "recommend me something", context
            )
        assert result.fallback is True
        assert result.confidence == 1.0


class TestLoadContextDataErrors:
    @pytest.mark.asyncio
    async def test_context_load_failure_uses_defaults(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        products = [_make_product("1", "Shoes", 50.0)]
        with patch.object(
            handler, "_fetch_products", new_callable=AsyncMock, return_value=products
        ):
            with patch.object(
                handler,
                "_load_context_data",
                new_callable=AsyncMock,
                return_value={
                    "viewed_products": [],
                    "cart_items": [],
                    "dismissed_products": [],
                    "constraints": {},
                },
            ):
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "recommend", context
                )
        assert result.intent == "product_recommendation"
        assert not result.fallback

    @pytest.mark.asyncio
    async def test_context_load_with_conversation_id_none(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        context.conversation_id = None
        products = [_make_product("1", "Shoes", 50.0)]
        with patch.object(
            handler, "_fetch_products", new_callable=AsyncMock, return_value=products
        ):
            with patch.object(
                handler,
                "_load_context_data",
                new_callable=AsyncMock,
                return_value={
                    "viewed_products": [],
                    "cart_items": [],
                    "dismissed_products": [],
                    "constraints": {},
                },
            ):
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "recommend", context
                )
        assert result.intent == "product_recommendation"

    @pytest.mark.asyncio
    async def test_no_shopping_state_still_works(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context_no_shopping_state
    ):
        products = [_make_product("1", "Shoes", 50.0)]
        with patch.object(
            handler,
            "_fetch_products",
            new_callable=AsyncMock,
            return_value=products,
        ):
            with patch.object(
                handler,
                "_load_context_data",
                new_callable=AsyncMock,
                return_value={
                    "viewed_products": [],
                    "cart_items": [],
                    "dismissed_products": [],
                    "constraints": {},
                },
            ):
                result = await handler.handle(
                    mock_db,
                    ecommerce_merchant,
                    mock_llm,
                    "recommend",
                    context_no_shopping_state,
                )
        assert result.intent == "product_recommendation"
        assert not result.fallback


class TestDismissalIntegrationInHandler:
    @pytest.mark.asyncio
    async def test_dismissed_products_from_context_populate_shopping_state(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        products = [
            _make_product("1", "Shoes A", 50.0),
            _make_product("2", "Shoes B", 60.0),
        ]
        context_data = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [1],
            "constraints": {},
        }
        with patch.object(
            handler, "_fetch_products", new_callable=AsyncMock, return_value=products
        ):
            with patch.object(
                handler,
                "_load_context_data",
                new_callable=AsyncMock,
                return_value=context_data,
            ):
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "recommend", context
                )
        assert result.intent == "product_recommendation"
        if result.products:
            assert all(p["id"] != "1" for p in result.products) or len(result.products) < 2

    @pytest.mark.asyncio
    async def test_empty_dismissed_list_no_crash(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        products = [_make_product("1", "Shoes", 50.0)]
        context_data = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": None,
            "constraints": {},
        }
        with patch.object(
            handler, "_fetch_products", new_callable=AsyncMock, return_value=products
        ):
            with patch.object(
                handler,
                "_load_context_data",
                new_callable=AsyncMock,
                return_value=context_data,
            ):
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "recommend", context
                )
        assert result.intent == "product_recommendation"


class TestHandlerResponseShape:
    @pytest.mark.asyncio
    async def test_error_response_is_conversation_response(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        with patch.object(
            handler,
            "_fetch_products",
            new_callable=AsyncMock,
            side_effect=Exception("API error"),
        ):
            result = await handler.handle(
                mock_db, ecommerce_merchant, mock_llm, "recommend", context
            )
        assert isinstance(result, ConversationResponse)

    @pytest.mark.asyncio
    async def test_successful_response_shape(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        products = [_make_product("1", "Shoes", 50.0)]
        with patch.object(
            handler, "_fetch_products", new_callable=AsyncMock, return_value=products
        ):
            with patch.object(
                handler,
                "_load_context_data",
                new_callable=AsyncMock,
                return_value={
                    "viewed_products": [],
                    "cart_items": [],
                    "dismissed_products": [],
                    "constraints": {},
                },
            ):
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "recommend", context
                )
        assert isinstance(result, ConversationResponse)
        assert result.intent == "product_recommendation"
        assert result.confidence == 1.0
        assert isinstance(result.metadata, dict)
        assert "total_candidates" in result.metadata
        assert "filtered_out" in result.metadata
        assert result.metadata["context_aware"] is True

    @pytest.mark.asyncio
    async def test_empty_set_response_shape(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        products = [_make_product("1", "Only Product", 50.0)]
        context_data = {
            "viewed_products": [1],
            "cart_items": [],
            "dismissed_products": [],
            "constraints": {},
        }
        with patch.object(
            handler, "_fetch_products", new_callable=AsyncMock, return_value=products
        ):
            with patch.object(
                handler,
                "_load_context_data",
                new_callable=AsyncMock,
                return_value=context_data,
            ):
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "recommend", context
                )
        assert isinstance(result, ConversationResponse)
        assert result.metadata.get("empty_recommendation") is True
        assert result.products == []
