"""Product search service for Shopify integration.

Orchestrates product search by mapping intent entities to Shopify queries,
fetching from Admin API (no storefront token required), applying filters, and ranking by relevance.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.schemas.shopify import Product, ProductSearchResult
from app.services.intent.classification_schema import ExtractedEntities
from app.services.shopify.product_mapper import ProductMapper
from app.models.shopify_integration import ShopifyIntegration
from app.core.security import decrypt_access_token
from app.core.config import is_testing
from app.services.shopify_admin import ShopifyAdminClient


logger = structlog.get_logger(__name__)


class ProductSearchService:
    """Service for searching products based on classified entities.

    Uses Shopify Admin API for product search (no storefront token required).
    Maps intent classification entities to filters and ranks results by relevance.

    Attributes:
        mapper: Product data mapper
        db: Database session for fetching merchant credentials
    """

    CATEGORY_MATCH_WEIGHT: float = 50.0
    PRICE_PROXIMITY_WEIGHT: float = 30.0
    BASE_SCORE: float = 20.0

    MAX_RESULTS: int = 20
    MAX_DISPLAY_RESULTS: int = 5

    def __init__(
        self,
        product_mapper: Optional[ProductMapper] = None,
        db: Optional[AsyncSession] = None,
    ) -> None:
        """Initialize product search service.

        Args:
            product_mapper: Product data mapper
            db: Database session for fetching merchant credentials
        """
        self.mapper = product_mapper or ProductMapper()
        self.db = db
        self.logger = structlog.get_logger(__name__)

    async def _get_admin_client_for_merchant(
        self, merchant_id: int
    ) -> Optional[ShopifyAdminClient]:
        """Get Shopify Admin client for a specific merchant.

        Uses the admin token from ShopifyIntegration (no storefront token needed).

        Args:
            merchant_id: Merchant ID to fetch credentials for

        Returns:
            ShopifyAdminClient or None if no integration
        """
        if not self.db:
            self.logger.warning("no_db_session", merchant_id=merchant_id)
            return None

        result = await self.db.execute(
            select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant_id)
        )
        integration = result.scalars().first()

        if (
            not integration
            or integration.status != "active"
            or not integration.admin_token_encrypted
        ):
            self.logger.info(
                "no_shopify_admin_integration",
                merchant_id=merchant_id,
                has_integration=integration is not None,
            )
            return None

        admin_token = decrypt_access_token(integration.admin_token_encrypted)

        self.logger.info(
            "using_shopify_admin_api",
            merchant_id=merchant_id,
            shop_domain=integration.shop_domain,
        )

        return ShopifyAdminClient(
            shop_domain=integration.shop_domain,
            access_token=admin_token,
            is_testing=is_testing(),
        )

    async def search_products(
        self,
        entities: ExtractedEntities,
        merchant_id: Optional[int] = None,
    ) -> ProductSearchResult:
        """Search for products matching the extracted entities.

        Uses Shopify Admin API to fetch products and filters them locally.

        Args:
            entities: Extracted entities from intent classification
            merchant_id: Merchant ID for fetching Shopify credentials

        Returns:
            Product search result with ranked products

        Raises:
            APIError: If search fails
        """
        import time

        start_time = time.time()

        search_params = self.mapper.map_entities_to_search_params(entities)

        self.logger.info(
            "product_search_start",
            merchant_id=merchant_id,
            category=search_params.get("category"),
            max_price=search_params.get("max_price"),
            size=search_params.get("size"),
        )

        # Fetch products from Admin API
        admin_client: Optional[ShopifyAdminClient] = None
        if merchant_id:
            admin_client = await self._get_admin_client_for_merchant(merchant_id)

        if admin_client:
            # Fetch all products from Shopify (Admin API)
            raw_products = await admin_client.list_products(limit=self.MAX_RESULTS)
            self.logger.info(
                "admin_api_products_fetched",
                merchant_id=merchant_id,
                count=len(raw_products),
            )
        else:
            # Fallback to mock products
            from app.services.shopify.product_service import fetch_products

            raw_products = await fetch_products(None, merchant_id, self.db) if self.db else []
            self.logger.info(
                "using_fallback_products",
                merchant_id=merchant_id,
                count=len(raw_products),
            )

        # Map to Product objects
        products = self._map_admin_products(raw_products)

        # Apply filters
        products = self._apply_filters(products, search_params)

        # Apply sorting
        products = self._apply_sorting(products, entities)

        # Fetch pinned product IDs for relevance boosting
        pinned_ids = await self._get_pinned_product_ids(merchant_id)
        pinned_orders = await self._get_pinned_product_orders(merchant_id)

        # Rank by relevance (with pinned boost)
        ranked_products = self._rank_products(products, entities, pinned_ids, pinned_orders)

        has_alternatives = self._check_alternatives(ranked_products, entities)

        search_time_ms = (time.time() - start_time) * 1000

        self.logger.info(
            "product_search_complete",
            merchant_id=merchant_id,
            result_count=len(ranked_products),
            search_time_ms=search_time_ms,
        )

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

    def _map_admin_products(self, raw_products: list[dict]) -> list[Product]:
        """Map Admin API products to Product objects.

        The list_products() method already extracts price and availability,
        so we just need to map to Product objects.

        Args:
            raw_products: Raw product dicts from Admin API (already formatted)

        Returns:
            List of Product objects
        """
        from app.schemas.shopify import ProductVariant, CurrencyCode

        products = []
        for p in raw_products:
            # Parse price safely (Product expects float)
            price_str = p.get("price", "0")
            try:
                price = float(price_str) if price_str else 0.0
            except:
                price = 0.0

            # Build image list from image_url
            images = []
            if p.get("image_url"):
                images.append({"url": p["image_url"], "src": p["image_url"]})

            # Build variant with availability info for filter_by_availability
            available = p.get("available", True)
            variants = [
                ProductVariant(
                    id=p.get("variant_id", ""),
                    product_id=str(p.get("id", "")),
                    title="Default",
                    price=price,
                    currency_code=CurrencyCode.USD,
                    available_for_sale=available,
                    selected_options={},
                )
            ]

            products.append(
                Product(
                    id=str(p.get("id", "")),
                    title=p.get("title", ""),
                    description=p.get("description", ""),
                    description_html=p.get("description", ""),
                    product_type=p.get("product_type", ""),
                    vendor=p.get("vendor", ""),
                    tags=p.get("tags", []) if isinstance(p.get("tags"), list) else [],
                    price=price,
                    currency_code=CurrencyCode.USD,
                    images=images,
                    variants=variants,
                    total_inventory=p.get("inventory_quantity", 0),
                    tracks_inventory=True,
                )
            )
        return products

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

    def _apply_sorting(
        self,
        products: list[Product],
        entities: ExtractedEntities,
    ) -> list[Product]:
        """Apply sorting based on constraints.

        Args:
            products: List of products to sort
            entities: Extracted entities with sort constraints

        Returns:
            Sorted list of products
        """
        constraints = entities.constraints or {}
        sort_by = constraints.get("sort_by")
        sort_order = constraints.get("sort_order", "asc")

        if sort_by == "price":
            reverse = sort_order == "desc"
            products = sorted(products, key=lambda p: p.price or 0, reverse=reverse)

        return products

    def _rank_products(
        self,
        products: list[Product],
        entities: ExtractedEntities,
        pinned_ids: Optional[set[str]] = None,
        pinned_orders: Optional[dict[str, int]] = None,
    ) -> list[Product]:
        """Rank products by relevance to search entities.

        Args:
            products: List of products from Shopify
            entities: Original search entities
            pinned_ids: Set of pinned product IDs (for boosting)
            pinned_orders: Dict mapping product_id to pinned_order (1-10)

        Returns:
            Products with relevance scores, sorted by score
        """
        pinned_ids = pinned_ids or set()
        pinned_orders = pinned_orders or {}

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

            # Pinned product boost (dynamic based on order)
            # Order 1 gets 3.0x boost, order 10 gets 1.5x boost
            product_id_str = str(product.id)
            if product_id_str in pinned_ids:
                order = pinned_orders.get(product_id_str, 10)
                # Calculate boost: 3.0 for order 1, decreasing to 1.5 for order 10
                boost_factor = 3.0 - (order - 1) * 0.167  # (3.0 - 1.5) / 9 = 0.167
                score = score * boost_factor

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

        if len(products) < 3 and (entities.budget or entities.size or entities.color):
            return True

        return False

    async def _get_pinned_product_ids(self, merchant_id: int) -> set[str]:
        """Fetch pinned product IDs for a merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            Set of pinned product IDs as strings
        """
        if not self.db:
            return set()

        try:
            from app.services.product_pin_service import get_pinned_product_ids

            pinned_ids = await get_pinned_product_ids(self.db, merchant_id)
            return {str(pid) for pid in pinned_ids}
        except Exception as e:
            self.logger.warning(
                "get_pinned_ids_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            return set()

    async def _get_pinned_product_orders(self, merchant_id: int) -> dict[str, int]:
        """Fetch pinned product orders for a merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            Dict mapping product_id to pinned_order
        """
        if not self.db:
            return {}

        try:
            from app.models.product_pin import ProductPin

            result = await self.db.execute(
                select(ProductPin.product_id, ProductPin.pinned_order).where(
                    ProductPin.merchant_id == merchant_id
                )
            )
            pins = result.all()
            return {str(pin.product_id): pin.pinned_order for pin in pins}
        except Exception as e:
            self.logger.warning(
                "get_pinned_orders_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            return {}
