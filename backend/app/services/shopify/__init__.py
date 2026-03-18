"""Shopify integration services.

Provides product search, Storefront API client, OAuth flow,
order processing, and related services for Shopify integration.
"""

# New product search services (Story 2-2)
# Admin API and polling services (Story 4-4)
from app.services.shopify.admin_client import (
    ShopifyAdminClient,
    ShopifyAPIError,
    ShopifyAuthError,
    ShopifyRateLimitError,
)
from app.services.shopify.order_polling_service import (
    OrderPollingService,
    PollingResult,
    PollingStatus,
)

# Order processing services (Story 4-2)
from app.services.shopify.order_processor import (
    ShopifyOrderProcessor,
    map_shopify_status_to_order_status,
    parse_shopify_order,
    resolve_customer_psid,
    upsert_order,
)
from app.services.shopify.product_mapper import ProductMapper
from app.services.shopify.product_search_service import ProductSearchService
from app.services.shopify.storefront_client import ShopifyStorefrontClient

# Legacy OAuth and service components (from original shopify.py → shopify_oauth.py)
# These are imported to maintain backward compatibility with integrations API
from app.services.shopify_oauth import (
    REQUIRED_SCOPES,
    ShopifyService,
    get_shopify_service,
    validate_shop_domain,
)

__all__ = [
    # New product search services
    "ShopifyStorefrontClient",
    "ProductSearchService",
    "ProductMapper",
    # Order processing services (Story 4-2)
    "ShopifyOrderProcessor",
    "parse_shopify_order",
    "resolve_customer_psid",
    "upsert_order",
    "map_shopify_status_to_order_status",
    # Admin API and polling services (Story 4-4)
    "ShopifyAdminClient",
    "ShopifyAPIError",
    "ShopifyAuthError",
    "ShopifyRateLimitError",
    "OrderPollingService",
    "PollingResult",
    "PollingStatus",
    # Legacy OAuth and service components
    "ShopifyService",
    "get_shopify_service",
    "REQUIRED_SCOPES",
    "validate_shop_domain",
]
