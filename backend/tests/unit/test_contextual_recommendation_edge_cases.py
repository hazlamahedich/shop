"""Unit tests for ContextualRecommendationService edge cases (Story 11-6, AC1).

Covers scoring edge cases: None price, GID-format product IDs,
empty tags, missing product_type, zero-price products, and boundary conditions.
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


class TestGidFormatProductIds:
    def test_gid_product_id_hash_fallback(self, service):
        product = Product(
            id="gid://shopify/Product/12345",
            title="Test",
            product_type="shoes",
            price=50.0,
            tags=[],
        )
        pid = service._product_id(product)
        assert isinstance(pid, int)

    def test_gid_product_not_in_viewed_set(self, service):
        product = Product(
            id="gid://shopify/Product/999",
            title="GID Product",
            product_type="shoes",
            price=50.0,
            tags=[],
        )
        context_data = {
            "viewed_products": [999],
            "cart_items": [],
            "dismissed_products": [],
        }
        result = service.generate_recommendations([product], context_data)
        assert result.total_candidates <= 1

    def test_non_numeric_product_id_hashed(self, service):
        product = Product(
            id="abc-def-ghi",
            title="Non-numeric ID",
            product_type="accessories",
            price=25.0,
            tags=[],
        )
        pid = service._product_id(product)
        assert isinstance(pid, int)
        assert pid != 0


class TestNonePriceBudget:
    def test_none_price_returns_mid_budget_score(self, service):
        product = _make_product("1", price=0.0)
        product.price = None  # type: ignore[assignment]
        constraints = _ContextConstraints(
            budget_min=50.0, budget_max=100.0, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score == 0.5

    def test_none_price_no_constraints(self, service):
        product = _make_product("1", price=0.0)
        product.price = None  # type: ignore[assignment]
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score == 0.5

    def test_none_price_with_budget_max_only(self, service):
        product = _make_product("1", price=0.0)
        product.price = None  # type: ignore[assignment]
        constraints = _ContextConstraints(
            budget_min=None, budget_max=100.0, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score == 0.5

    def test_zero_price_within_range(self, service):
        product = _make_product("1", price=0.0)
        constraints = _ContextConstraints(
            budget_min=0.0, budget_max=50.0, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score >= 0.5


class TestEmptyTagsAndMissingAttributes:
    def test_empty_tags_no_brand_match(self, service):
        product = _make_product("1", "Generic Item", 50.0, "accessories", [])
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand="Nike"
        )
        score = service._score_preference_match(product, constraints)
        assert score == 0.0

    def test_none_tags_no_crash(self, service):
        product = _make_product("1", "Item", 50.0, "shoes")
        product.tags = None  # type: ignore[assignment]
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand="Nike"
        )
        score = service._score_preference_match(product, constraints)
        assert isinstance(score, float)
        assert score >= 0.0

    def test_empty_product_type_returns_unknown(self, service):
        product = _make_product("1", "Item", 50.0, product_type="")
        ptype = service._get_product_type(product)
        assert ptype == "unknown"

    def test_none_product_type_returns_unknown(self, service):
        product = _make_product("1", "Item", 50.0)
        product.product_type = None  # type: ignore[assignment]
        ptype = service._get_product_type(product)
        assert ptype == "unknown"

    def test_empty_variants_no_color_match(self, service):
        product = _make_product("1", "Shirt", 30.0, variants=[])
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color="red", size=None, brand=None
        )
        score = service._score_preference_match(product, constraints)
        assert score == 0.0

    def test_empty_variants_no_size_match(self, service):
        product = _make_product("1", "Shoes", 80.0, variants=[])
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size="10", brand=None
        )
        score = service._score_preference_match(product, constraints)
        assert score == 0.0


class TestScoringBoundaryConditions:
    def test_budget_exact_min_boundary(self, service):
        product = _make_product("1", price=50.0)
        constraints = _ContextConstraints(
            budget_min=50.0, budget_max=100.0, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score >= 0.5

    def test_budget_just_over_max(self, service):
        product = _make_product("1", price=100.01)
        constraints = _ContextConstraints(
            budget_min=50.0, budget_max=100.0, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score == 0.0

    def test_budget_just_under_min(self, service):
        product = _make_product("1", price=49.99)
        constraints = _ContextConstraints(
            budget_min=50.0, budget_max=None, color=None, size=None, brand=None
        )
        score = service._score_budget_fit(product, constraints)
        assert score < 0.5

    def test_preference_score_capped_at_one(self, service):
        variant = _make_variant(size="10", color="red")
        product = _make_product(
            "1", "Nike Red Shoes", 80.0, "nike shoes", ["nike", "red"], [variant]
        )
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color="red", size="10", brand="Nike"
        )
        score = service._score_preference_match(product, constraints)
        assert score <= 1.0

    def test_single_product_recommendation(self, service):
        product = _make_product("1", "Only One", 50.0)
        context_data = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [],
        }
        result = service.generate_recommendations([product], context_data)
        assert not result.empty
        assert len(result.recommendations) == 1

    def test_max_results_one(self, service):
        products = [_make_product(str(i), f"Product {i}", 50.0) for i in range(1, 6)]
        context_data = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [],
        }
        result = service.generate_recommendations(products, context_data, max_results=1)
        assert len(result.recommendations) <= 1


class TestReasonEdgeCases:
    def test_reason_with_all_match_types(self, service):
        variant = _make_variant(color="blue")
        product = _make_product("1", "Nike Blue", 80.0, "sneakers", ["nike"], [variant])
        constraints = _ContextConstraints(
            budget_min=None, budget_max=100.0, color="blue", size=None, brand="Nike"
        )
        reason = service._generate_reason(product, constraints, 1.0)
        assert "brand_match" in reason
        assert "budget_match" in reason
        assert "feature_match" in reason or "novelty" in reason

    def test_reason_with_none_product_type(self, service):
        product = _make_product("1", "Item", 50.0)
        product.product_type = None  # type: ignore[assignment]
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand=None
        )
        reason = service._generate_reason(product, constraints, 0.5)
        assert isinstance(reason, str)
        assert len(reason) > 0

    def test_reason_for_dismissed_product(self, service):
        product = _make_product("1", "Dismissed", 50.0)
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand=None
        )
        reason = service._generate_reason(product, constraints, 0.0)
        assert isinstance(reason, str)

    def test_reason_with_very_high_novelty(self, service):
        product = _make_product("1", "New Arrival", 50.0, "new")
        constraints = _ContextConstraints(
            budget_min=None, budget_max=None, color=None, size=None, brand=None
        )
        reason = service._generate_reason(product, constraints, 1.0)
        assert "novelty:new" in reason


class TestMixedExclusionSets:
    def test_partial_exclusion_still_returns(self, service):
        products = [_make_product(str(i), f"Product {i}", 50.0) for i in range(1, 6)]
        context_data = {
            "viewed_products": [1, 2],
            "cart_items": [3],
            "dismissed_products": [],
        }
        result = service.generate_recommendations(products, context_data)
        assert not result.empty
        assert result.total_candidates == 2
        assert result.filtered_out == 3

    def test_overlapping_exclusion_sets(self, service):
        products = [_make_product(str(i), f"Product {i}", 50.0) for i in range(1, 4)]
        context_data = {
            "viewed_products": [1],
            "cart_items": [1],
            "dismissed_products": [1],
        }
        result = service.generate_recommendations(products, context_data)
        assert not result.empty
        assert result.total_candidates == 2

    def test_empty_context_dict(self, service):
        product = _make_product("1", "Item", 50.0)
        result = service.generate_recommendations([product], {})
        assert not result.empty
        assert len(result.recommendations) == 1

    def test_extra_context_keys_ignored(self, service):
        products = [_make_product("1", "Item", 50.0)]
        context_data = {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [],
            "constraints": {},
            "unknown_key": "ignored",
            "another_key": 42,
        }
        result = service.generate_recommendations(products, context_data)
        assert not result.empty
