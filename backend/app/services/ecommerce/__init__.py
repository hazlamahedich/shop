"""E-Commerce Platform Abstraction Layer.

Sprint Change Proposal 2026-02-13: Make Shopify Optional Integration

This module provides a pluggable e-commerce architecture that supports:
- No store connected (NullStoreProvider)
- Testing without real credentials (MockStoreProvider)
- Shopify integration (ShopifyStoreProvider)
- Future integrations (WooCommerce, BigCommerce, etc.)

Usage:
    from app.services.ecommerce import get_provider

    provider = get_provider(merchant)
    if provider.is_connected():
        products = await provider.search_products("shoes")
"""

from app.services.ecommerce.base import (
    ECommerceProvider,
    Product,
    ProductVariant,
    Cart,
    CartItem,
    Order,
    OrderItem,
    StoreNotConnectedError,
)
from app.services.ecommerce.null_provider import NullStoreProvider
from app.services.ecommerce.mock_provider import MockStoreProvider
from app.services.ecommerce.provider_factory import (
    get_provider,
    get_provider_for_merchant,
    StoreProvider,
)

__all__ = [
    # Base classes and exceptions
    "ECommerceProvider",
    "StoreNotConnectedError",
    # Data models
    "Product",
    "ProductVariant",
    "Cart",
    "CartItem",
    "Order",
    "OrderItem",
    # Providers
    "NullStoreProvider",
    "MockStoreProvider",
    # Factory functions
    "get_provider",
    "get_provider_for_merchant",
    "StoreProvider",
]
