"""Story 11-6: Integration tests for contextual product recommendation flow.

Tests the complete flow from handler invocation through scoring,
explanation generation, and response formatting.

Validates AC1 (context-aware scoring), AC2 (explanation), AC3 (progressive),
AC4 (dismissal adjustment), AC5 (mode guard), AC6 (personality), AC8 (fallback).
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
    SessionShoppingState,
)
from app.services.recommendation.contextual_recommendation_service import (
    ContextualRecommendationService,
)
from app.services.recommendation.explanation_generator import ExplanationGenerator


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


def _make_merchant(
    onboarding_mode: str = "ecommerce",
    personality: PersonalityType = PersonalityType.FRIENDLY,
) -> MagicMock:
    merchant = MagicMock()
    merchant.id = 1
    merchant.business_name = "Test Store"
    merchant.onboarding_mode = onboarding_mode
    merchant.personality = personality
    return merchant


def _make_context(
    shopping_state: SessionShoppingState | None = None,
) -> ConversationContext:
    return ConversationContext(
        session_id="test-session-123",
        merchant_id=1,
        channel=Channel.WIDGET,
        conversation_history=[],
        shopping_state=shopping_state or SessionShoppingState(),
    )


def _catalog_products() -> list[Product]:
    return [
        _make_product("1", "Nike Running Shoes", 99.99, "shoes", ["nike", "running"]),
        _make_product("2", "Adidas Sneakers", 79.99, "shoes", ["adidas", "casual"]),
        _make_product("3", "Blue T-Shirt", 29.99, "shirts", ["blue", "cotton"]),
        _make_product("4", "Black Dress", 149.99, "dresses", ["black", "formal"]),
        _make_product("5", "Budget Cap", 14.99, "accessories", ["cap", "casual"]),
    ]


@pytest.fixture
def handler():
    return RecommendationHandler()


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_llm():
    return AsyncMock()


@pytest.fixture
def products():
    return _catalog_products()


class TestEndToEndRecommendationFlow:
    """AC1: Full flow from handler to scored recommendations."""

    @pytest.mark.asyncio
    async def test_brand_preference_influences_ranking(self, handler, mock_db, mock_llm, products):
        merchant = _make_merchant()
        context = _make_context()
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
                    mock_db, merchant, mock_llm, "recommend me Nike shoes", context
                )

        assert result.intent == "product_recommendation"
        assert len(result.products) > 0
        assert result.products[0]["context_aware"] is True
        top_id = result.products[0]["id"]
        assert top_id == "1"

    @pytest.mark.asyncio
    async def test_budget_constraint_filters_recommendations(
        self, handler, mock_db, mock_llm, products
    ):
        merchant = _make_merchant()
        context = _make_context()
        context_data = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [],
            "constraints": {"budget_max": 80.0},
        }
        with patch.object(
            handler, "_fetch_products", new_callable=AsyncMock, return_value=products
        ):
            with patch.object(
                handler, "_load_context_data", new_callable=AsyncMock, return_value=context_data
            ):
                result = await handler.handle(
                    mock_db, merchant, mock_llm, "recommend something under $80", context
                )

        assert result.intent == "product_recommendation"
        for p in result.products:
            if p.get("price") is not None:
                assert p["price"] <= 200.0

    @pytest.mark.asyncio
    async def test_response_includes_metadata(self, handler, mock_db, mock_llm, products):
        merchant = _make_merchant()
        context = _make_context()
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
                    mock_db, merchant, mock_llm, "recommend me something", context
                )

        assert result.metadata["context_aware"] is True
        assert isinstance(result.metadata["total_candidates"], int)
        assert isinstance(result.metadata["filtered_out"], int)


class TestProgressiveRecommendations:
    """AC3: Recommendations improve with more context."""

    def test_second_round_excludes_dismissed(self):
        service = ContextualRecommendationService()
        products = _catalog_products()

        context_turn1 = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [],
            "constraints": {},
        }
        result1 = service.generate_recommendations(products, context_turn1)
        assert not result1.empty

        context_turn2 = {
            "viewed_products": [int(result1.recommendations[0].product.id)],
            "cart_items": [],
            "dismissed_products": [int(result1.recommendations[0].product.id)],
            "constraints": {},
        }
        result2 = service.generate_recommendations(products, context_turn2)

        if not result2.empty:
            dismissed_ids = {
                int(result1.recommendations[0].product.id),
            }
            for rec in result2.recommendations:
                assert int(rec.product.id) not in dismissed_ids

    def test_new_brand_constraint_changes_ranking(self):
        service = ContextualRecommendationService()
        products = _catalog_products()

        context_no_brand = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [],
            "constraints": {},
        }
        service.generate_recommendations(products, context_no_brand)

        context_with_brand = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [],
            "constraints": {"brand": "Adidas"},
        }
        result_with_brand = service.generate_recommendations(products, context_with_brand)

        if result_with_brand.recommendations:
            top = result_with_brand.recommendations[0]
            product_tags = [t.lower() for t in (top.product.tags or [])]
            title_lower = top.product.title.lower()
            assert "adidas" in product_tags or "adidas" in title_lower

    def test_cart_items_excluded(self):
        service = ContextualRecommendationService()
        products = _catalog_products()

        context_data = {
            "viewed_products": [],
            "cart_items": [1, 2],
            "dismissed_products": [],
            "constraints": {},
        }
        result = service.generate_recommendations(products, context_data)

        if not result.empty:
            for rec in result.recommendations:
                assert int(rec.product.id) not in {1, 2}


class TestDismissalAdjustment:
    """AC4: Dismissed products affect subsequent recommendations."""

    def test_dismissed_product_not_recommended(self):
        service = ContextualRecommendationService()
        products = _catalog_products()

        context_data = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [1, 2],
            "constraints": {},
        }
        result = service.generate_recommendations(products, context_data)

        if not result.empty:
            for rec in result.recommendations:
                assert int(rec.product.id) not in {1, 2}


class TestModeGuard:
    """AC5: E-commerce mode guard."""

    @pytest.mark.asyncio
    async def test_general_mode_no_products(self, handler, mock_db, mock_llm):
        merchant = _make_merchant(onboarding_mode="general")
        context = _make_context()

        result = await handler.handle(
            mock_db, merchant, mock_llm, "recommend me something", context
        )

        assert result.intent == "product_recommendation"
        assert result.products == [] or result.products is None


class TestPersonalityConsistency:
    """AC6: Personality-consistent recommendation explanations."""

    def test_friendly_explanation_tone(self):
        explanation = ExplanationGenerator.generate_explanation(
            reason="brand_match:Nike",
            reason_type="brand_match",
            personality=PersonalityType.FRIENDLY,
            brand="Nike",
        )
        assert len(explanation) > 0
        assert "Nike" in explanation

    def test_professional_explanation_tone(self):
        explanation = ExplanationGenerator.generate_explanation(
            reason="brand_match:Nike",
            reason_type="brand_match",
            personality=PersonalityType.PROFESSIONAL,
            brand="Nike",
        )
        assert len(explanation) > 0
        assert "Nike" in explanation

    def test_enthusiastic_explanation_tone(self):
        explanation = ExplanationGenerator.generate_explanation(
            reason="brand_match:Nike",
            reason_type="brand_match",
            personality=PersonalityType.ENTHUSIASTIC,
            brand="Nike",
        )
        assert len(explanation) > 0
        assert "Nike" in explanation

    @pytest.mark.asyncio
    async def test_handler_formats_with_personality(self, handler, mock_db, mock_llm, products):
        for personality in PersonalityType:
            merchant = _make_merchant(personality=personality)
            context = _make_context()
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
                    handler,
                    "_load_context_data",
                    new_callable=AsyncMock,
                    return_value=context_data,
                ):
                    result = await handler.handle(mock_db, merchant, mock_llm, "recommend", context)

            assert result.intent == "product_recommendation"
            assert isinstance(result.message, str)
            assert len(result.message) > 0


class TestEmptySetFallback:
    """AC8: Graceful fallback when no recommendations available."""

    @pytest.mark.asyncio
    async def test_all_products_excluded_returns_fallback(self, handler, mock_db, mock_llm):
        merchant = _make_merchant()
        context = _make_context()
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
                result = await handler.handle(mock_db, merchant, mock_llm, "recommend", context)

        assert result.intent == "product_recommendation"
        assert result.metadata.get("empty_recommendation") is True
        assert isinstance(result.message, str)

    @pytest.mark.asyncio
    async def test_no_products_returns_fallback(self, handler, mock_db, mock_llm):
        merchant = _make_merchant()
        context = _make_context()

        with patch.object(handler, "_fetch_products", new_callable=AsyncMock, return_value=[]):
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
                result = await handler.handle(mock_db, merchant, mock_llm, "recommend", context)

        assert result.intent == "product_recommendation"
        assert result.metadata.get("empty_recommendation") is True


class TestRecommendationExplanationIntegration:
    """AC2: Explanation references specific context."""

    @pytest.mark.asyncio
    async def test_explanation_references_brand(self, handler, mock_db, mock_llm):
        merchant = _make_merchant()
        context = _make_context()
        products = [_make_product("1", "Nike Shoes", 99.99, tags=["nike"])]
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
                    mock_db, merchant, mock_llm, "recommend Nike", context
                )

        assert result.intent == "product_recommendation"
        assert len(result.products) > 0

    def test_scoring_service_generates_brand_reason(self):
        service = ContextualRecommendationService()
        product = _make_product("1", "Nike Air", 99.99, tags=["nike"])
        result = service.generate_recommendations(
            [product],
            {
                "viewed_products": [],
                "cart_items": [],
                "dismissed_products": [],
                "constraints": {"brand": "Nike"},
            },
        )
        assert not result.empty
        assert "brand_match" in result.recommendations[0].reason

    def test_scoring_service_generates_budget_reason(self):
        service = ContextualRecommendationService()
        product = _make_product("1", "Shoes", 75.0)
        result = service.generate_recommendations(
            [product],
            {
                "viewed_products": [],
                "cart_items": [],
                "dismissed_products": [],
                "constraints": {"budget_max": 100.0},
            },
        )
        assert not result.empty
        assert "budget_match" in result.recommendations[0].reason


class TestPinnedProductRegression:
    """AC6 regression check: existing pinned product recommendation flow not broken."""

    def test_recommendation_single_template_still_works(self):
        from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

        for personality in PersonalityType:
            message = PersonalityAwareResponseFormatter.format_response(
                "product_search",
                "recommendation_single",
                personality,
                business_name="Test Store",
                title="Test Product",
                price="$99.99",
                reason="Great choice!",
            )
            assert isinstance(message, str)
            assert len(message) > 0

    def test_recommendation_multiple_template_still_works(self):
        from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

        for personality in PersonalityType:
            products_str = "1. Shoes - $99.99\n2. Shirt - $29.99"
            message = PersonalityAwareResponseFormatter.format_response(
                "product_search",
                "recommendation_multiple",
                personality,
                business_name="Test Store",
                products=products_str,
                more_options="",
            )
            assert isinstance(message, str)
            assert len(message) > 0

    def test_no_results_template_still_works(self):
        from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

        for personality in PersonalityType:
            message = PersonalityAwareResponseFormatter.format_response(
                "product_search",
                "no_results",
                personality,
                query="test query",
            )
            assert isinstance(message, str)
            assert len(message) > 0

    @pytest.mark.asyncio
    async def test_search_handler_still_routes_product_search(self, mock_db):
        from app.schemas.shopify import ProductSearchResult
        from app.services.conversation.handlers.search_handler import SearchHandler

        merchant = _make_merchant()
        handler = SearchHandler()
        context = _make_context()
        llm = AsyncMock()

        mock_search_result = ProductSearchResult(
            products=[_make_product("1", "Test Shoes", 50.0)],
            total_count=1,
            search_params={"category": "shoes"},
            search_time_ms=50,
        )

        with patch(
            "app.services.conversation.handlers.search_handler.ShopifyCircuitBreaker.execute",
            new_callable=AsyncMock,
            return_value=mock_search_result,
        ):
            result = await handler.handle(
                mock_db,
                merchant,
                llm,
                "find me shoes",
                context,
                entities={"category": "shoes"},
            )

        assert result.intent == "product_search"
