"""Null Store Provider - No E-Commerce Store Connected.

Sprint Change Proposal 2026-02-13: Make Shopify Optional Integration

This provider is used when a merchant has not connected an e-commerce store.
It raises StoreNotConnectedError for all e-commerce operations, allowing
the system to gracefully handle the absence of a store.
"""

from __future__ import annotations

from typing import Any, Optional

from app.services.ecommerce.base import (
    Cart,
    ECommerceProvider,
    Order,
    OrderStatus,
    Product,
    ProductVariant,
    StoreNotConnectedError,
)


class NullStoreProvider(ECommerceProvider):
    """Provider for merchants without an e-commerce store.

    This provider implements the Null Object pattern, providing a no-op
    implementation that raises StoreNotConnectedError for all operations.

    Used when:
    - Merchant has not connected any store
    - Store connection was removed/disconnected
    - As a fallback when provider lookup fails

    Example:
        provider = NullStoreProvider()
        assert provider.is_connected() == False
        try:
            await provider.search_products("shoes")
        except StoreNotConnectedError:
            print("Please connect a store to use shopping features")
    """

    def __init__(self, message: Optional[str] = None) -> None:
        """Initialize the null provider.

        Args:
            message: Custom error message (optional)
        """
        self._message = message or (
            "No e-commerce store connected. "
            "Please connect a store in your dashboard to use shopping features."
        )

    @property
    def provider_name(self) -> str:
        """Return provider identifier.

        Returns:
            "none" to indicate no store connected
        """
        return "none"

    def is_connected(self) -> bool:
        """Check if provider has valid credentials.

        Returns:
            Always False for NullStoreProvider
        """
        return False

    def _raise_not_connected(self) -> None:
        """Raise StoreNotConnectedError.

        Raises:
            StoreNotConnectedError: Always raised
        """
        raise StoreNotConnectedError(
            message=self._message,
            provider=self.provider_name,
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
        """Search for products - not available without store.

        Raises:
            StoreNotConnectedError: Always
        """
        self._raise_not_connected()  # type: ignore[return-value]

    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get a product - not available without store.

        Raises:
            StoreNotConnectedError: Always
        """
        self._raise_not_connected()  # type: ignore[return-value]

    async def get_product_variants(self, product_id: str) -> list[ProductVariant]:
        """Get product variants - not available without store.

        Raises:
            StoreNotConnectedError: Always
        """
        self._raise_not_connected()  # type: ignore[return-value]

    # ==================== Cart Operations ====================

    async def create_cart(self) -> Cart:
        """Create a cart - not available without store.

        Raises:
            StoreNotConnectedError: Always
        """
        self._raise_not_connected()  # type: ignore[return-value]

    async def get_cart(self, cart_id: str) -> Optional[Cart]:
        """Get a cart - not available without store.

        Raises:
            StoreNotConnectedError: Always
        """
        self._raise_not_connected()  # type: ignore[return-value]

    async def add_to_cart(
        self,
        cart_id: str,
        variant_id: str,
        quantity: int = 1,
    ) -> Cart:
        """Add to cart - not available without store.

        Raises:
            StoreNotConnectedError: Always
        """
        self._raise_not_connected()  # type: ignore[return-value]

    async def update_cart_item(
        self,
        cart_id: str,
        variant_id: str,
        quantity: int,
    ) -> Cart:
        """Update cart item - not available without store.

        Raises:
            StoreNotConnectedError: Always
        """
        self._raise_not_connected()  # type: ignore[return-value]

    async def remove_from_cart(
        self,
        cart_id: str,
        variant_id: str,
    ) -> Cart:
        """Remove from cart - not available without store.

        Raises:
            StoreNotConnectedError: Always
        """
        self._raise_not_connected()  # type: ignore[return-value]

    # ==================== Checkout Operations ====================

    async def create_checkout_url(
        self,
        cart_id: str,
        custom_attributes: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """Create checkout URL - not available without store.

        Raises:
            StoreNotConnectedError: Always
        """
        self._raise_not_connected()  # type: ignore[return-value]

    # ==================== Order Operations ====================

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order - not available without store.

        Raises:
            StoreNotConnectedError: Always
        """
        self._raise_not_connected()  # type: ignore[return-value]

    async def get_order_by_checkout_token(self, checkout_token: str) -> Optional[Order]:
        """Get order by token - not available without store.

        Raises:
            StoreNotConnectedError: Always
        """
        self._raise_not_connected()  # type: ignore[return-value]

    async def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        tracking_number: Optional[str] = None,
        tracking_url: Optional[str] = None,
    ) -> Order:
        """Update order status - not available without store.

        Raises:
            StoreNotConnectedError: Always
        """
        self._raise_not_connected()  # type: ignore[return-value]
