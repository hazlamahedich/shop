"""Unit tests for ContextualRecommendationService (Story 11-6).

Tests scoring logic: preference match, budget fit, novelty, diversity,
empty set fallback, and edge cases.
"""

from __future__ import annotations

import pytest

from app.schemas.shopify import Product, ProductVariant
from app.services.recommendation.contextual_recommendation_service import (
    ContextualRecommendationService,
    _ContextConstraints,
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


def _make_variant(size: str | None = None, color: str | None = None) -> ProductVariant:
    opts = {}
    if size:
        opts["Size"] = size
    if color:
        opts["Color"] = color
    return ProductVariant(
        id="var-1",
        product_id="1",
        title="Default",
        price=50.0,
        selected_options=opts,
    )


@pytest.fixture
def service():
    return ContextualRecommendationService()


@pytest.fixture
def sample_products():
    return [
        _make_product("1", "Nike Running Shoes", 99.99, "shoes", ["nike", "running"]),
        _make_product("2", "Adidas Sneakers", 79.99, "shoes", ["adidas", "casual"]),
        _make_product("3", "Blue T-Shirt", 29.99, "shirts", ["blue", "cotton"]),
        _make_product(
            "4",
            "Black Dress",
            149.99,
            "dresses",
            ["black", "formal"],
            variants=[_make_variant(color="black", size="M")],
        ),
        _make_product("5", "Budget Cap", 14.99, "accessories", ["cap", "casual"]),
    ]


class TestEmptyInputs:
    def test_empty_products_returns_empty_result(self, service):
        result = service.generate_recommendations([], {})
        assert result.empty is True
        assert result.recommendations == []
        assert result.total_candidates == 0

    def test_empty_products_fallback_message(self, service):
        result = service.generate_recommendations([], {})
        assert "No products available" in result.fallback_message

    def test_all_products_excluded_returns_empty(self, service, sample_products):
        context_data = {
            "viewed_products": [1, 2, 3, 4, 5],
            "cart_items": [],
            "dismissed_products": [],
        }
        result = service.generate_recommendations(sample_products, context_data)
        assert result.empty is True
        assert result.filtered_out == 5

    def test_all_products_in_cart_returns_empty(self, service, sample_products):
        context_data = {
            "viewed_products": [],
            "cart_items": [1, 2, 3, 4, 5],
            "dismissed_products": [],
        }
        result = service.generate_recommendations(sample_products, context_data)
        assert result.empty is True

    def test_all_products_dismissed_returns_empty(self, service, sample_products):
        context_data = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [1, 2, 3, 4, 5],
        }
        result = service.generate_recommendations(sample_products, context_data)
        assert result.empty is True


class TestPreferenceScoring:
    def test_brand_match_tags(self, service):
        product = _make_product("1", "Test", 50.0, "shoes", ["nike"])
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand="Nike"
        )
        score = service._score_preference_match(product, constraints)
        assert score >= 0.3

    def test_brand_match_title(self, service):
        product = _make_product("1", "Nike Air Max", 50.0, "shoes")
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand="Nike"
        )
        score = service._score_preference_match(product, constraints)
        assert score >= 0.3

    def test_brand_match_product_type(self, service):
        product = _make_product("1", "Test", 50.0, "nike shoes")
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand="Nike"
        )
        score = service._score_preference_match(product, constraints)
        assert score >= 0.3

    def test_no_brand_match(self, service):
        product = _make_product("1", "Generic Item", 50.0, "accessories")
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand="Nike"
        )
        score = service._score_preference_match(product, constraints)
        assert score == 0.0

    def test_color_match_via_variants(self, service):
        variant = _make_variant(color="red")
        product = _make_product("1", "Shirt", 30.0, variants=[variant])
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color="red", size=None, brand=None
        )
        score = service._score_preference_match(product, constraints)
        assert score >= 0.2

    def test_size_match_via_variants(self, service):
        variant = _make_variant(size="10")
        product = _make_product("1", "Shoes", 80.0, variants=[variant])
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size="10", brand=None
        )
        score = service._score_preference_match(product, constraints)
        assert score >= 0.2

    def test_multi_constraint_bonus(self, service):
        variant = _make_variant(size="10")
        product = _make_product("1", "Nike Shoes", 80.0, "shoes", ["nike"], [variant])
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size="10", brand="Nike"
        )
        score = service._score_preference_match(product, constraints)
        assert score >= 0.5

    def test_no_constraints_gives_zero(self, service):
        product = _make_product("1", "Shoes", 50.0)
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand=None
        )
        score = service._score_preference_match(product, constraints)
        assert score == 0.0


class TestBudgetScoring:
    def test_within_budget_range(self, service):
        product = _make_product("1", price=75.0)
        constraints = _ContextConstraints(
            budget_min=50.0, budget_max=100.0, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score >= 0.7

    def test_outside_budget_range(self, service):
        product = _make_product("1", price=150.0)
        constraints = _ContextConstraints(
            budget_min=50.0, budget_max=100.0, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score == 0.0

    def test_within_budget_max_only(self, service):
        product = _make_product("1", price=50.0)
        constraints = _ContextConstraints(
            budget_min=None, budget_max=100.0, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score >= 0.7

    def test_over_budget_max(self, service):
        product = _make_product("1", price=150.0)
        constraints = _ContextConstraints(
            budget_min=None, budget_max=100.0, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score < 0.5

    def test_above_budget_min(self, service):
        product = _make_product("1", price=75.0)
        constraints = _ContextConstraints(
            budget_min=50.0, budget_max=None, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score >= 0.7

    def test_below_budget_min(self, service):
        product = _make_product("1", price=25.0)
        constraints = _ContextConstraints(
            budget_min=50.0, budget_max=None, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score < 0.5

    def test_no_budget_constraints(self, service):
        product = _make_product("1", price=50.0)
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score == 0.5

    def test_exact_budget_boundary(self, service):
        product = _make_product("1", price=100.0)
        constraints = _ContextConstraints(
            budget_min=50.0, budget_max=100.0, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score > 0.0
        assert score <= 1.0

    def test_budget_center_scores_highest(self, service):
        product = _make_product("1", price=75.0)
        constraints = _ContextConstraints(
            budget_min=50.0, budget_max=100.0, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score >= 0.9


class TestNoveltyScoring:
    def test_novel_product(self, service):
        score = service._score_novelty(
            _make_product("1"), viewed_products=set(), dismissed_products=set()
        )
        assert score == 1.0

    def test_viewed_product(self, service):
        score = service._score_novelty(
            _make_product("1"), viewed_products={1}, dismissed_products=set()
        )
        assert score == 0.2

    def test_dismissed_product(self, service):
        score = service._score_novelty(
            _make_product("1"), viewed_products=set(), dismissed_products={1}
        )
        assert score == 0.0

    def test_dismissed_takes_precedence(self, service):
        score = service._score_novelty(
            _make_product("1"), viewed_products={1}, dismissed_products={1}
        )
        assert score == 0.0


class TestDiversityScoring:
    def test_diversity_penalty_applied(self, service, sample_products):
        context_data = {"viewed_products": [], "cart_items": [], "dismissed_products": []}
        result = service.generate_recommendations(sample_products, context_data, max_results=5)
        shoes_recs = [r for r in result.recommendations if r.product.product_type == "shoes"]
        if len(shoes_recs) > 1:
            first_shoes = shoes_recs[0]
            second_shoes = shoes_recs[1]
            assert first_shoes.diversity_score >= second_shoes.diversity_score

    def test_single_category_products(self, service):
        products = [
            _make_product("1", "Shoe A", 50.0, "shoes"),
            _make_product("2", "Shoe B", 60.0, "shoes"),
            _make_product("3", "Shoe C", 70.0, "shoes"),
        ]
        context_data = {"viewed_products": [], "cart_items": [], "dismissed_products": []}
        result = service.generate_recommendations(products, context_data)
        assert not result.empty
        for rec in result.recommendations:
            assert rec.total_score > 0


class TestReasonGeneration:
    def test_brand_reason(self, service):
        product = _make_product("1", "Nike Shoes", 99.99, tags=["nike"])
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand="Nike"
        )
        reason = service._generate_reason(product, constraints, 1.0)
        assert "brand_match:Nike" in reason

    def test_budget_reason(self, service):
        product = _make_product("1", "Shoes", 50.0)
        constraints = _ContextConstraints(
            budget_min=None, budget_max=100.0, color=None, size=None, brand=None
        )
        reason = service._generate_reason(product, constraints, 1.0)
        assert "budget_match" in reason

    def test_novelty_reason(self, service):
        product = _make_product("1", "Shoes", 50.0)
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand=None
        )
        reason = service._generate_reason(product, constraints, 1.0)
        assert "novelty:new" in reason

    def test_default_reason(self, service):
        product = _make_product("1", "Shoes", 150.0)
        constraints = _ContextConstraints(
            budget_min=None, budget_max=100.0, color=None, size=None, brand=None
        )
        reason = service._generate_reason(product, constraints, 0.5)
        assert "category_match" in reason


class TestGenerateRecommendations:
    def test_max_results_respected(self, service, sample_products):
        context_data = {"viewed_products": [], "cart_items": [], "dismissed_products": []}
        result = service.generate_recommendations(sample_products, context_data, max_results=3)
        assert len(result.recommendations) <= 3

    def test_result_not_empty(self, service, sample_products):
        context_data = {"viewed_products": [], "cart_items": [], "dismissed_products": []}
        result = service.generate_recommendations(sample_products, context_data)
        assert not result.empty
        assert len(result.recommendations) > 0

    def test_total_candidates_counted(self, service, sample_products):
        context_data = {"viewed_products": [1], "cart_items": [], "dismissed_products": []}
        result = service.generate_recommendations(sample_products, context_data)
        assert result.total_candidates == 4
        assert result.filtered_out == 1

    def test_none_context_fields(self, service, sample_products):
        context_data = {
            "viewed_products": None,
            "cart_items": None,
            "dismissed_products": None,
            "constraints": None,
        }
        result = service.generate_recommendations(sample_products, context_data)
        assert result.empty is False

    def test_context_data_with_constraints(self, service, sample_products):
        context_data = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [],
            "constraints": {"brand": "Nike", "budget_max": 100.0},
        }
        result = service.generate_recommendations(sample_products, context_data)
        assert result.empty is False
        if result.recommendations:
            top = result.recommendations[0]
            assert top.product.id == "1"

    def test_shopping_state_param_ignored_gracefully(self, service, sample_products):
        shopping_state = {"last_cart_item_count": 3, "dismissed_product_ids": [1]}
        result = service.generate_recommendations(
            sample_products,
            {"viewed_products": [], "cart_items": [], "dismissed_products": []},
            shopping_state=shopping_state,
        )
        assert result.empty is False

    def test_product_id_hash_fallback(self, service):
        product = Product(
            id="gid://shopify/Product/abc", title="Test", product_type="shoes", price=50.0, tags=[]
        )
        pid = service._product_id(product)
        assert isinstance(pid, int)

    def test_get_product_type_fallback(self, service):
        product = _make_product("1", "Test", 50.0, product_type="")
        ptype = service._get_product_type(product)
        assert ptype == "unknown"
