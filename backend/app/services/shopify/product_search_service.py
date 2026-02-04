"""Product search service for Shopify integration.

Orchestrates product search by mapping intent entities to Shopify queries,
fetching from Storefront API, applying filters, and ranking by relevance.
"""

from __future__ import annotations

from typing import Any, Optional

import structlog

from app.schemas.shopify import Product, ProductSearchResult
from app.services.intent.classification_schema import ExtractedEntities
from app.services.shopify.product_mapper import ProductMapper
from app.services.shopify.storefront_client import ShopifyStorefrontClient


class ProductSearchService:
    """Service for searching products based on classified entities.

    Maps intent classification entities to Shopify Storefront API queries
    and ranks results by relevance.

    Attributes:
        client: Shopify Storefront API client
        mapper: Product data mapper
    """

    # Relevance scoring weights
    CATEGORY_MATCH_WEIGHT: float = 50.0
    PRICE_PROXIMITY_WEIGHT: float = 30.0
    BASE_SCORE: float = 20.0

    # Search constraints
    # Increased from 5 to 20 to prevent false negatives when top results
    # are filtered out by size/availability constraints in post-processing
    MAX_RESULTS: int = 20
    MAX_DISPLAY_RESULTS: int = 5  # Limit final displayed results

    def __init__(
        self,
        storefront_client: Optional[ShopifyStorefrontClient] = None,
        product_mapper: Optional[ProductMapper] = None,
    ) -> None:
        """Initialize product search service.

        Args:
            storefront_client: Shopify Storefront API client
            product_mapper: Product data mapper
        """
        self.client = storefront_client or ShopifyStorefrontClient()
        self.mapper = product_mapper or ProductMapper()
        self.logger = structlog.get_logger(__name__)

    async def search_products(
        self,
        entities: ExtractedEntities,
    ) -> ProductSearchResult:
        """Search for products matching the extracted entities.

        Args:
            entities: Extracted entities from intent classification

        Returns:
            Product search result with ranked products

        Raises:
            APIError: If search fails
        """
        import time

        start_time = time.time()

        # Map entities to search parameters
        search_params = self.mapper.map_entities_to_search_params(entities)

        self.logger.info(
            "product_search_start",
            category=search_params.get("category"),
            max_price=search_params.get("max_price"),
            size=search_params.get("size"),
        )

        # Query Shopify
        raw_products = await self.client.search_products(
            category=search_params.get("category"),
            max_price=search_params.get("max_price"),
            size=search_params.get("size"),
            first=self.MAX_RESULTS,
        )

        # Map to Product schema
        products = self.mapper.map_products(raw_products)

        # Apply filters
        products = self._apply_filters(products, search_params)

        # Rank by relevance
        ranked_products = self._rank_products(products, entities)

        # Calculate alternatives flag
        has_alternatives = self._check_alternatives(ranked_products, entities)

        search_time_ms = (time.time() - start_time) * 1000

        self.logger.info(
            "product_search_complete",
            result_count=len(ranked_products),
            search_time_ms=search_time_ms,
        )

        # Limit displayed results to MAX_DISPLAY_RESULTS but keep total_count accurate
        displayed_products = ranked_products[: self.MAX_DISPLAY_RESULTS]

        return ProductSearchResult(
            products=displayed_products,
            total_count=len(ranked_products),
            search_params={
                "category": search_params.get("category"),
                "maxPrice": search_params.get("max_price"),
                "size": search_params.get("size"),
                "color": search_params.get("color"),
            },
            has_alternatives=has_alternatives,
            search_time_ms=search_time_ms,
        )

    def _apply_filters(
        self,
        products: list[Product],
        search_params: dict[str, Any],
    ) -> list[Product]:
        """Apply search filters to products.

        Args:
            products: List of products to filter
            search_params: Search parameters including filters

        Returns:
            Filtered list of products
        """
        # Apply availability filter (in-stock only)
        products = self.mapper.filter_by_availability(products)

        # Apply budget filter
        if search_params.get("max_price"):
            products = self.mapper.filter_by_budget(
                products,
                budget=search_params["max_price"],
            )

        # Apply size filter
        if search_params.get("size"):
            products = self.mapper.filter_by_size(
                products,
                size=search_params["size"],
            )

        return products

    def _rank_products(
        self,
        products: list[Product],
        entities: ExtractedEntities,
    ) -> list[Product]:
        """Rank products by relevance to search entities.

        Args:
            products: List of products from Shopify
            entities: Original search entities

        Returns:
            Products with relevance scores, sorted by score
        """
        scored_products: list[Product] = []

        for product in products:
            score = self.BASE_SCORE

            # Category match score (highest weight)
            if entities.category:
                category_lower = entities.category.lower()
                # Check in product type
                if category_lower in product.product_type.lower():
                    score += self.CATEGORY_MATCH_WEIGHT
                # Check in tags
                if any(category_lower in tag.lower() for tag in product.tags):
                    score += self.CATEGORY_MATCH_WEIGHT
                # Check in title
                if category_lower in product.title.lower():
                    score += self.CATEGORY_MATCH_WEIGHT * 0.5

            # Price proximity score
            if entities.budget and product.price:
                if product.price <= entities.budget:
                    # Prefer products closer to budget (better value)
                    budget_ratio = product.price / entities.budget
                    score += (1.0 - budget_ratio) * self.PRICE_PROXIMITY_WEIGHT

            product.relevance_score = score
            scored_products.append(product)

        # Sort by relevance score descending
        scored_products.sort(key=lambda p: p.relevance_score, reverse=True)

        return scored_products

    def _check_alternatives(
        self,
        products: list[Product],
        entities: ExtractedEntities,
    ) -> bool:
        """Check if alternative suggestions should be offered.

        Args:
            products: Current search results
            entities: Original search entities

        Returns:
            True if alternatives should be suggested
        """
        # Suggest alternatives if:
        # - No results found
        # - Very few results and constraints exist
        if len(products) == 0:
            return True

        if len(products) < 3 and (
            entities.budget or entities.size or entities.color
        ):
            return True

        return False
