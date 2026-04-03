"""Unit tests for RecommendationHandler (Story 11-6).

Tests handler routing, mode guard, context integration, empty set fallback,
and explanation building.
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
def general_merchant():
    merchant = MagicMock()
    merchant.id = 2
    merchant.business_name = "General Store"
    merchant.onboarding_mode = "general"
    merchant.personality = PersonalityType.PROFESSIONAL
    return merchant


@pytest.fixture
def mock_llm():
    service = AsyncMock()
    service.chat = AsyncMock(return_value="LLM response")
    return service


@pytest.fixture
def context():
    return ConversationContext(
        session_id="test-session-123",
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=[],
        shopping_state=SessionShoppingState(),
    )


class TestModeGuard:
    @pytest.mark.asyncio
    async def test_general_mode_returns_fallback(
        self, handler, mock_db, general_merchant, mock_llm, context
    ):
        result = await handler.handle(
            mock_db, general_merchant, mock_llm, "recommend me something", context
        )
        assert result.intent == "product_recommendation"
        assert result.products == [] or result.products is None

    @pytest.mark.asyncio
    async def test_ecommerce_mode_does_not_return_fallback_early(
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
                    mock_db, ecommerce_merchant, mock_llm, "what do you recommend?", context
                )
        assert result.intent == "product_recommendation"


class TestProductFetchFailure:
    @pytest.mark.asyncio
    async def test_fetch_failure_returns_error_response(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        with patch.object(
            handler, "_fetch_products", new_callable=AsyncMock, side_effect=Exception("API down")
        ):
            result = await handler.handle(
                mock_db, ecommerce_merchant, mock_llm, "recommend me something", context
            )
        assert result.fallback is True
        assert result.intent == "product_recommendation"


class TestEmptySetFallback:
    @pytest.mark.asyncio
    async def test_all_products_excluded_returns_fallback(
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
                handler, "_load_context_data", new_callable=AsyncMock, return_value=context_data
            ):
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "recommend something", context
                )
        assert result.intent == "product_recommendation"
        assert result.metadata.get("empty_recommendation") is True


class TestSuccessfulRecommendation:
    @pytest.mark.asyncio
    async def test_returns_products_in_response(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        products = [
            _make_product("1", "Nike Shoes", 99.99, "shoes", ["nike"]),
            _make_product("2", "Adidas Shoes", 79.99, "shoes", ["adidas"]),
        ]
        context_data = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [],
            "constraints": {"brand": "Nike"},
        }
        with patch.object(
            handler, "_fetch_products", new_callable=AsyncMock, return_value=products
        ):
            with patch.object(
                handler, "_load_context_data", new_callable=AsyncMock, return_value=context_data
            ):
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "recommend me Nike shoes", context
                )
        assert result.intent == "product_recommendation"
        assert len(result.products) > 0
        assert result.products[0].get("context_aware") is True

    @pytest.mark.asyncio
    async def test_response_contains_metadata(
        self, handler, mock_db, ecommerce_merchant, mock_llm, context
    ):
        products = [_make_product("1", "Shoes", 50.0)]
        context_data = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [],
            "constraints": {},
        }
        with patch.object(
            handler, "_fetch_products", new_callable=AsyncMock, return_value=products
        ):
            with patch.object(
                handler, "_load_context_data", new_callable=AsyncMock, return_value=context_data
            ):
                result = await handler.handle(
                    mock_db, ecommerce_merchant, mock_llm, "recommend", context
                )
        assert result.metadata.get("context_aware") is True
        assert result.metadata.get("total_candidates") is not None


class TestBuildExplanation:
    def test_brand_match_explanation(self, handler, ecommerce_merchant):
        from app.services.recommendation.schemas import RecommendationScore

        rec = RecommendationScore(
            product=_make_product("1", "Nike Shoes", 99.99, tags=["nike"]),
            total_score=0.85,
            preference_score=0.4,
            budget_score=0.5,
            reason="brand_match:Nike",
            novelty_score=0.9,
        )
        explanation = handler._build_explanation(rec, ecommerce_merchant)
        assert "Nike" in explanation

    def test_multi_match_explanation(self, handler, ecommerce_merchant):
        from app.services.recommendation.schemas import RecommendationScore

        rec = RecommendationScore(
            product=_make_product("1", "Nike Shoes", 89.99, tags=["nike"]),
            total_score=0.95,
            preference_score=0.6,
            budget_score=0.5,
            reason="brand_match:Nike||budget_match:$100",
            novelty_score=0.9,
        )
        explanation = handler._build_explanation(rec, ecommerce_merchant)
        assert len(explanation) > 0

    def test_default_explanation_for_empty_reason(self, handler, ecommerce_merchant):
        from app.services.recommendation.schemas import RecommendationScore

        rec = RecommendationScore(
            product=_make_product("1", "Shoes", 50.0),
            total_score=0.5,
            preference_score=0.3,
            budget_score=0.5,
            reason="default",
            novelty_score=0.8,
        )
        explanation = handler._build_explanation(rec, ecommerce_merchant)
        assert len(explanation) > 0

    def test_professional_personality_explanation(self, handler):
        merchant = MagicMock()
        merchant.personality = PersonalityType.PROFESSIONAL
        from app.services.recommendation.schemas import RecommendationScore

        rec = RecommendationScore(
            product=_make_product("1", "Shoes", 50.0),
            total_score=0.7,
            preference_score=0.4,
            budget_score=0.5,
            reason="brand_match:Nike",
            novelty_score=0.8,
        )
        explanation = handler._build_explanation(rec, merchant)
        assert "Nike" in explanation


class TestFormatProducts:
    def test_formats_product_with_variants(self, handler, ecommerce_merchant):
        from app.services.recommendation.schemas import RecommendationScore

        variant = ProductVariant(
            id="var-1", product_id="1", title="Size 10", price=99.99, available_for_sale=True
        )
        product = _make_product("1", "Nike Shoes", 99.99, variants=[variant])
        image = MagicMock()
        image.url = "https://example.com/image.jpg"
        product.images = [image]

        rec = RecommendationScore(
            product=product,
            total_score=0.9,
            preference_score=0.5,
            budget_score=0.5,
            reason="brand_match:Nike",
        )
        formatted = handler._format_products([rec], ecommerce_merchant)
        assert len(formatted) == 1
        assert formatted[0]["title"] == "Nike Shoes"
        assert formatted[0]["variant_id"] == "var-1"
        assert formatted[0]["context_aware"] is True

    def test_formats_product_without_variants(self, handler, ecommerce_merchant):
        from app.services.recommendation.schemas import RecommendationScore

        product = _make_product("1", "Basic Shirt", 29.99)
        rec = RecommendationScore(
            product=product,
            total_score=0.5,
            preference_score=0.3,
            budget_score=0.5,
            reason="default",
        )
        formatted = handler._format_products([rec], ecommerce_merchant)
        assert formatted[0]["variant_id"] is None


class TestGeneralModeFallback:
    def test_returns_conversation_response(self, handler, general_merchant):
        result = handler._general_mode_fallback(general_merchant)
        assert isinstance(result, ConversationResponse)
        assert result.intent == "product_recommendation"
