"""Shopify Store Provider Implementation.

Sprint Change Proposal 2026-02-13: Make Shopify Optional Integration

This provider wraps the existing Shopify services (StorefrontClient, CartService,
CheckoutService) into the ECommerceProvider interface.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import structlog

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.services.ecommerce.base import (
    Cart,
    CartItem,
    CurrencyCode,
    ECommerceProvider,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    ProductVariant,
    StoreNotConnectedError,
)
from app.services.shopify_oauth import ShopifyService
from app.services.shopify.storefront_client import ShopifyStorefrontClient

logger = structlog.get_logger(__name__)


# Mapping from Shopify order status to our OrderStatus enum
SHOPIFY_ORDER_STATUS_MAP = {
    "pending": OrderStatus.PENDING,
    "confirmed": OrderStatus.CONFIRMED,
    "processing": OrderStatus.PROCESSING,
    "shipped": OrderStatus.SHIPPED,
    "delivered": OrderStatus.DELIVERED,
    "cancelled": OrderStatus.CANCELLED,
    "refunded": OrderStatus.REFUNDED,
    # Shopify-specific statuses
    "open": OrderStatus.PROCESSING,
    "closed": OrderStatus.DELIVERED,
    "any": OrderStatus.PROCESSING,
}


class ShopifyStoreProvider(ECommerceProvider):
    """Shopify e-commerce provider implementation.

    This provider wraps the existing Shopify services into the
    ECommerceProvider interface, allowing the system to interact
    with Shopify stores uniformly.

    The provider requires a merchant with an active Shopify integration
    to function. Use get_provider_for_merchant() to create instances.

    Example:
        # Create provider for merchant
        provider = ShopifyStoreProvider(merchant_id=123)

        # Check if connected
        if provider.is_connected():
            products = await provider.search_products("shoes")
    """

    def __init__(
        self,
        merchant_id: int,
        db_session: Optional[Any] = None,
    ) -> None:
        """Initialize Shopify provider for a specific merchant.

        Args:
            merchant_id: ID of the merchant with Shopify integration
            db_session: Optional database session (created if not provided)
        """
        self._merchant_id = merchant_id
        self._db_session = db_session
        self._storefront_client: Optional[ShopifyStorefrontClient] = None
        self._shop_domain: Optional[str] = None
        self._access_token: Optional[str] = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure the provider is initialized with Shopify credentials.

        Raises:
            StoreNotConnectedError: If Shopify not connected for merchant
        """
        if self._initialized:
            return

        try:
            # Get database session if not provided
            if self._db_session is None:
                from app.core.database import async_session_factory

                async with async_session_factory() as session:
                    await self._init_with_session(session)
            else:
                await self._init_with_session(self._db_session)

        except Exception as e:
            logger.error(
                "shopify_provider_init_failed",
                merchant_id=self._merchant_id,
                error=str(e),
            )
            raise StoreNotConnectedError(
                message=f"Failed to initialize Shopify provider: {str(e)}",
                provider="shopify",
            ) from e

    async def _init_with_session(self, session: Any) -> None:
        """Initialize provider with database session.

        Args:
            session: Database session
        """
        from app.services.shopify_oauth import ShopifyService

        shopify_service = ShopifyService(session)
        integration = await shopify_service.get_shopify_integration(self._merchant_id)

        if not integration:
            raise StoreNotConnectedError(
                message="Shopify store not connected for this merchant",
                provider="shopify",
            )

        self._shop_domain = integration.shop_domain
        self._access_token = await shopify_service.get_storefront_token(self._merchant_id)

        # Create storefront client
        store_url = f"https://{self._shop_domain}"
        self._storefront_client = ShopifyStorefrontClient(
            access_token=self._access_token,
            store_url=store_url,
        )

        self._initialized = True
        logger.info(
            "shopify_provider_initialized",
            merchant_id=self._merchant_id,
            shop_domain=self._shop_domain,
        )

    @property
    def provider_name(self) -> str:
        """Return provider identifier.

        Returns:
            "shopify"
        """
        return "shopify"

    def is_connected(self) -> bool:
        """Check if Shopify is connected for this merchant.

        Returns:
            True if initialized and has valid credentials
        """
        return self._initialized and self._access_token is not None

    async def _check_connection(self) -> None:
        """Check connection and raise if not connected.

        Raises:
            StoreNotConnectedError: If not connected
        """
        await self._ensure_initialized()
        if not self.is_connected():
            raise StoreNotConnectedError(
                message="Shopify store not connected",
                provider="shopify",
            )

    # ==================== Product Operations ====================

    async def search_products(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        **kwargs: Any,
    ) -> list[Product]:
        """Search for products in Shopify store.

        Args:
            query: Search query
            limit: Maximum results
            category: Category filter
            max_price: Maximum price
            min_price: Minimum price

        Returns:
            List of matching products
        """
        await self._check_connection()

        # Use the existing storefront client
        raw_products = await self._storefront_client.search_products(
            category=category,
            max_price=max_price,
            first=limit,
        )

        # Filter by query and convert to our Product model
        products = []
        query_lower = query.lower()

        for raw in raw_products:
            # Check if matches query
            title = raw.get("title", "")
            description = raw.get("description", "")
            tags = raw.get("tags", [])

            if (
                query_lower in title.lower()
                or query_lower in description.lower()
                or any(query_lower in tag.lower() for tag in tags)
            ):
                product = self._convert_shopify_product(raw)
                products.append(product)

                if len(products) >= limit:
                    break

        return products

    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get a product by ID from Shopify.

        Args:
            product_id: Shopify product ID (gid://shopify/Product/xxx)

        Returns:
            Product if found, None otherwise
        """
        await self._check_connection()

        # Search for the specific product
        # Note: In production, we'd use a getProduct query
        products = await self.search_products(product_id.split("/")[-1], limit=1)

        for product in products:
            if product.id == product_id:
                return product

        return None

    async def get_product_variants(self, product_id: str) -> list[ProductVariant]:
        """Get variants for a product.

        Args:
            product_id: Product ID

        Returns:
            List of variants
        """
        product = await self.get_product(product_id)
        if product:
            return product.variants
        return []

    # ==================== Cart Operations ====================

    async def create_cart(self) -> Cart:
        """Create a new cart.

        Note: We use the existing Redis-based CartService for local cart
        management. Shopify cart creation happens at checkout time.

        Returns:
            Empty Cart with generated ID
        """
        await self._check_connection()

        # Create a local cart ID
        import uuid

        cart_id = f"local_cart_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        return Cart(
            id=cart_id,
            items=[],
            subtotal=0.0,
            currency_code=CurrencyCode.USD,
            item_count=0,
            created_at=now,
            updated_at=now,
        )

    async def get_cart(self, cart_id: str) -> Optional[Cart]:
        """Get a cart by ID.

        Note: Uses the existing CartService.

        Args:
            cart_id: Cart ID

        Returns:
            Cart if found
        """
        await self._check_connection()

        # The actual cart is managed by CartService in Redis
        # This is a placeholder that would integrate with CartService
        logger.warning("get_cart_not_implemented", cart_id=cart_id)
        return None

    async def add_to_cart(
        self,
        cart_id: str,
        variant_id: str,
        quantity: int = 1,
    ) -> Cart:
        """Add item to cart.

        Note: Uses the existing CartService.

        Args:
            cart_id: Cart ID
            variant_id: Variant to add
            quantity: Quantity

        Returns:
            Updated cart
        """
        await self._check_connection()

        # The actual cart is managed by CartService in Redis
        logger.warning("add_to_cart_not_implemented", cart_id=cart_id, variant_id=variant_id)
        raise NotImplementedError("Use CartService directly for cart operations")

    async def update_cart_item(
        self,
        cart_id: str,
        variant_id: str,
        quantity: int,
    ) -> Cart:
        """Update cart item quantity.

        Args:
            cart_id: Cart ID
            variant_id: Variant to update
            quantity: New quantity

        Returns:
            Updated cart
        """
        await self._check_connection()
        logger.warning("update_cart_item_not_implemented", cart_id=cart_id)
        raise NotImplementedError("Use CartService directly for cart operations")

    async def remove_from_cart(
        self,
        cart_id: str,
        variant_id: str,
    ) -> Cart:
        """Remove item from cart.

        Args:
            cart_id: Cart ID
            variant_id: Variant to remove

        Returns:
            Updated cart
        """
        await self._check_connection()
        logger.warning("remove_from_cart_not_implemented", cart_id=cart_id)
        raise NotImplementedError("Use CartService directly for cart operations")

    # ==================== Checkout Operations ====================

    async def create_checkout_url(
        self,
        cart_id: str,
        custom_attributes: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """Create Shopify checkout URL.

        This method integrates with the existing CheckoutService and
        ShopifyStorefrontClient to create checkout URLs.

        Args:
            cart_id: Cart ID (from local CartService)
            custom_attributes: Custom attributes for checkout

        Returns:
            Shopify checkout URL
        """
        await self._check_connection()

        # The actual checkout creation is handled by CheckoutService
        # which uses ShopifyStorefrontClient.create_checkout_url()
        logger.warning(
            "create_checkout_url_not_implemented",
            cart_id=cart_id,
            message="Use CheckoutService directly for checkout operations",
        )
        raise NotImplementedError("Use CheckoutService directly for checkout operations")

    # ==================== Order Operations ====================

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID.

        Args:
            order_id: Shopify order ID

        Returns:
            Order if found
        """
        await self._check_connection()

        # Order retrieval would use Shopify Admin API
        # This is a placeholder for the full implementation
        logger.warning("get_order_not_implemented", order_id=order_id)
        return None

    async def get_order_by_checkout_token(self, checkout_token: str) -> Optional[Order]:
        """Get order by checkout token.

        Args:
            checkout_token: Checkout token from URL

        Returns:
            Order if found
        """
        await self._check_connection()
        logger.warning("get_order_by_checkout_token_not_implemented")
        return None

    async def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        tracking_number: Optional[str] = None,
        tracking_url: Optional[str] = None,
    ) -> Order:
        """Update order status.

        Note: Order updates typically come from Shopify webhooks,
        not direct API calls.

        Args:
            order_id: Order ID
            status: New status
            tracking_number: Tracking number
            tracking_url: Tracking URL

        Returns:
            Updated order
        """
        await self._check_connection()
        logger.warning("update_order_status_not_implemented", order_id=order_id)
        raise NotImplementedError("Order status updates handled via webhooks")

    # ==================== Helper Methods ====================

    def _convert_shopify_product(self, raw: dict[str, Any]) -> Product:
        """Convert a Shopify product response to our Product model.

        Args:
            raw: Raw Shopify product data

        Returns:
            Product model instance
        """
        # Extract price range
        price_range = raw.get("priceRangeV2", {})
        min_price = float(price_range.get("minVariantPrice", {}).get("amount", 0))
        max_price = float(price_range.get("maxVariantPrice", {}).get("amount", min_price))
        currency = price_range.get("minVariantPrice", {}).get("currencyCode", "USD")

        # Extract image
        images = raw.get("images", {}).get("edges", [])
        image_url = images[0]["node"]["url"] if images else None

        # Extract variants
        variants = []
        raw_variants = raw.get("variants", {}).get("edges", [])
        for edge in raw_variants:
            node = edge["node"]
            variant = ProductVariant(
                id=node.get("id", ""),
                title=node.get("title", ""),
                price=float(node.get("priceV2", {}).get("amount", 0)),
                currency_code=CurrencyCode(node.get("priceV2", {}).get("currencyCode", "USD")),
                available=node.get("availableForSale", True),
                sku=node.get("sku"),
                options=node.get("selectedOptions", []),
            )
            variants.append(variant)

        return Product(
            id=raw.get("id", ""),
            title=raw.get("title", ""),
            description=raw.get("description"),
            product_type=raw.get("productType"),
            vendor=raw.get("vendor"),
            tags=raw.get("tags", []),
            image_url=image_url,
            price_min=min_price,
            price_max=max_price,
            currency_code=CurrencyCode(currency),
            variants=variants,
            available=True,  # Shopify product availability
        )

    async def close(self) -> None:
        """Close the Shopify client."""
        if self._storefront_client:
            await self._storefront_client.close()
            self._storefront_client = None
