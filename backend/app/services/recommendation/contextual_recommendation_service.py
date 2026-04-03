"""Contextual product recommendation service (Story 11-6).

Generates context-aware product recommendations by scoring products
against conversation history: preferences, budget, viewed products,
dismissed products, and cart items.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

from app.schemas.shopify import Product
from app.services.recommendation.schemas import RecommendationResult, RecommendationScore

logger = structlog.get_logger(__name__)


@dataclass
class _ContextConstraints:
    budget_min: float | None
    budget_max: float | None
    color: str | None
    size: str | None
    brand: str | None


class ContextualRecommendationService:
    WEIGHT_PREFERENCE: float = 0.35
    WEIGHT_BUDGET: float = 0.25
    WEIGHT_NOVELTY: float = 0.25
    WEIGHT_DIVERSITY: float = 0.15

    def generate_recommendations(
        self,
        products: list[Product],
        context_data: dict[str, Any],
        shopping_state: dict[str, Any] | None = None,
        max_results: int = 5,
    ) -> RecommendationResult:
        if not products:
            return RecommendationResult(
                empty=True,
                fallback_message="No products available to recommend.",
                total_candidates=0,
                filtered_out=0,
            )

        viewed_products = set(context_data.get("viewed_products") or [])
        cart_items = set(context_data.get("cart_items") or [])
        dismissed_products = set(context_data.get("dismissed_products") or [])
        constraints_raw = context_data.get("constraints") or {}
        constraints = _ContextConstraints(
            budget_min=constraints_raw.get("budget_min"),
            budget_max=constraints_raw.get("budget_max"),
            color=constraints_raw.get("color"),
            size=constraints_raw.get("size"),
            brand=constraints_raw.get("brand"),
        )

        excluded = viewed_products | cart_items | dismissed_products
        candidates = [p for p in products if self._product_id(p) not in excluded]

        if not candidates:
            return RecommendationResult(
                empty=True,
                fallback_message=(
                    "All available products have been viewed or are in your cart. "
                    "Would you like to browse the full catalog?"
                ),
                total_candidates=len(products),
                filtered_out=len(excluded),
            )

        scored: list[RecommendationScore] = []
        for product in candidates:
            pref = self._score_preference_match(product, constraints)
            budget = self._score_budget_fit(product, constraints)
            novelty = self._score_novelty(product, viewed_products, dismissed_products)
            base_total = (
                pref * self.WEIGHT_PREFERENCE
                + budget * self.WEIGHT_BUDGET
                + novelty * self.WEIGHT_NOVELTY
            )
            reason = self._generate_reason(product, constraints, novelty)
            scored.append(
                RecommendationScore(
                    product=product,
                    total_score=base_total,
                    preference_score=pref,
                    budget_score=budget,
                    novelty_score=novelty,
                    diversity_score=0.0,
                    reason=reason,
                )
            )

        scored.sort(key=lambda s: s.total_score, reverse=True)
        top_candidates = scored[: max_results * 3]

        seen_categories: dict[str, int] = {}
        for rec in top_candidates:
            cat = self._get_product_type(rec.product)
            category_count = seen_categories.get(cat, 0)
            diversity_penalty = category_count * 0.1
            rec.diversity_score = max(0.0, 1.0 - diversity_penalty) * self.WEIGHT_DIVERSITY
            rec.total_score += rec.diversity_score
            seen_categories[cat] = category_count + 1

        top_candidates.sort(key=lambda s: s.total_score, reverse=True)
        final = top_candidates[:max_results]

        return RecommendationResult(
            recommendations=final,
            empty=len(final) == 0,
            fallback_message="" if final else "No matching recommendations found.",
            total_candidates=len(candidates),
            filtered_out=len(excluded),
        )

    def _product_id(self, product: Product) -> int:
        try:
            return int(product.id)
        except (ValueError, TypeError):
            return hash(str(product.id))

    def _get_product_type(self, product: Product) -> str:
        return getattr(product, "product_type", None) or "unknown"

    def _score_preference_match(self, product: Product, constraints: _ContextConstraints) -> float:
        score = 0.0
        match_count = 0

        if constraints.brand:
            product_tags = [t.lower() for t in (product.tags or [])]
            product_title_lower = (product.title or "").lower()
            product_type_lower = self._get_product_type(product).lower()
            if (
                constraints.brand.lower() in product_tags
                or constraints.brand.lower() in product_title_lower
                or constraints.brand.lower() in product_type_lower
            ):
                score += 0.4
                match_count += 1

        if constraints.color:
            product_tags = [t.lower() for t in (product.tags or [])]
            variants_text = " ".join(
                " ".join(v.selected_options.values()) for v in (product.variants or [])
            ).lower()
            if (
                constraints.color.lower() in " ".join(product_tags)
                or constraints.color.lower() in variants_text
            ):
                score += 0.3
                match_count += 1

        if constraints.size:
            variants_text = " ".join(
                " ".join(v.selected_options.values()) for v in (product.variants or [])
            ).lower()
            if constraints.size.lower() in variants_text:
                score += 0.3
                match_count += 1

        if match_count > 1:
            score += 0.2 * (match_count - 1)

        return min(score, 1.0)

    def _score_budget_fit(self, product: Product, constraints: _ContextConstraints) -> float:
        price = float(product.price) if product.price else None
        if price is None:
            return 0.5

        if constraints.budget_min is not None and constraints.budget_max is not None:
            if constraints.budget_min <= price <= constraints.budget_max:
                range_span = constraints.budget_max - constraints.budget_min
                if range_span > 0:
                    distance_from_center = abs(
                        price - (constraints.budget_min + constraints.budget_max) / 2
                    )
                    return max(0.0, 1.0 - (distance_from_center / range_span))
                return 1.0
            return 0.0

        if constraints.budget_max is not None:
            if price <= constraints.budget_max:
                return 1.0 - (price / constraints.budget_max) * 0.3
            return max(0.0, 0.3 - (price - constraints.budget_max) / constraints.budget_max)

        if constraints.budget_min is not None:
            if price >= constraints.budget_min:
                return 0.8
            return max(0.0, 0.3)

        return 0.5

    def _score_novelty(
        self,
        product: Product,
        viewed_products: set[int],
        dismissed_products: set[int],
    ) -> float:
        pid = self._product_id(product)
        if pid in dismissed_products:
            return 0.0
        if pid in viewed_products:
            return 0.2
        return 1.0

    def _generate_reason(
        self,
        product: Product,
        constraints: _ContextConstraints,
        novelty: float,
    ) -> str:
        reasons = []
        if constraints.brand:
            product_tags = [t.lower() for t in (product.tags or [])]
            if (
                constraints.brand.lower() in product_tags
                or constraints.brand.lower() in (product.title or "").lower()
            ):
                reasons.append(f"brand_match:{constraints.brand}")
        if constraints.budget_max is not None:
            price = float(product.price) if product.price else None
            if price is not None and price <= constraints.budget_max:
                reasons.append(f"budget_match:${constraints.budget_max:.0f}")
        if constraints.color:
            variants_text = " ".join(
                " ".join(v.selected_options.values()) for v in (product.variants or [])
            ).lower()
            if constraints.color.lower() in variants_text:
                reasons.append(f"feature_match:{constraints.color}")
        if novelty > 0.8:
            reasons.append("novelty:new")
        product_type = self._get_product_type(product)
        if product_type and product_type != "unknown":
            reasons.append(f"category_match:{product_type}")
        return "||".join(reasons) if reasons else "default"
