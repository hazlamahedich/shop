"""Shopify integration services.

Provides product search, Storefront API client, OAuth flow,
and related services for Shopify integration.
"""

# New product search services (Story 2-2)
from app.services.shopify.storefront_client import ShopifyStorefrontClient
from app.services.shopify.product_search_service import ProductSearchService
from app.services.shopify.product_mapper import ProductMapper

# Legacy OAuth and service components (from original shopify.py → shopify_oauth.py)
# These are imported to maintain backward compatibility with integrations API
from app.services.shopify_oauth import (
    ShopifyService,
    get_shopify_service,
    REQUIRED_SCOPES,
    validate_shop_domain,
)

__all__ = [
    # New product search services
    "ShopifyStorefrontClient",
    "ProductSearchService",
    "ProductMapper",
    # Legacy OAuth and service components
    "ShopifyService",
    "get_shopify_service",
    "REQUIRED_SCOPES",
    "validate_shop_domain",
]
