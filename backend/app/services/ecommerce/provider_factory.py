"""E-Commerce Provider Factory.

Sprint Change Proposal 2026-02-13: Make Shopify Optional Integration

Factory module for instantiating the appropriate e-commerce provider
based on merchant configuration and environment settings.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import TYPE_CHECKING, Optional

import structlog

from app.services.ecommerce.base import ECommerceProvider, StoreNotConnectedError
from app.services.ecommerce.null_provider import NullStoreProvider
from app.services.ecommerce.mock_provider import MockStoreProvider

if TYPE_CHECKING:
    from app.models.merchant import Merchant

logger = structlog.get_logger(__name__)


class StoreProvider(str, Enum):
    """Supported e-commerce store providers.

    Used in the Merchant model to track which store (if any) is connected.
    """

    NONE = "none"  # No store connected
    SHOPIFY = "shopify"  # Shopify integration
    WOOCOMMERCE = "woocommerce"  # Future: WooCommerce integration
    BIGCOMMERCE = "bigcommerce"  # Future: BigCommerce integration
    MOCK = "mock"  # Testing/development mode


# Singleton instances for stateless providers
_null_provider: Optional[NullStoreProvider] = None
_mock_provider: Optional[MockStoreProvider] = None


def get_null_provider() -> NullStoreProvider:
    """Get the singleton NullStoreProvider instance.

    Returns:
        NullStoreProvider instance
    """
    global _null_provider
    if _null_provider is None:
        _null_provider = NullStoreProvider()
    return _null_provider


def get_mock_provider() -> MockStoreProvider:
    """Get the singleton MockStoreProvider instance.

    Returns:
        MockStoreProvider instance
    """
    global _mock_provider
    if _mock_provider is None:
        _mock_provider = MockStoreProvider()
    return _mock_provider


def get_provider(store_provider: StoreProvider = StoreProvider.NONE) -> ECommerceProvider:
    """Get an e-commerce provider instance based on the provider type.

    This is a simple factory function for getting a provider by type.
    For merchant-specific providers, use get_provider_for_merchant().

    Args:
        store_provider: The type of store provider to instantiate

    Returns:
        ECommerceProvider instance

    Example:
        # Get null provider (no store)
        provider = get_provider(StoreProvider.NONE)

        # Get mock provider for testing
        provider = get_provider(StoreProvider.MOCK)
    """
    if store_provider == StoreProvider.NONE:
        return get_null_provider()

    if store_provider == StoreProvider.MOCK:
        return get_mock_provider()

    if store_provider == StoreProvider.SHOPIFY:
        # Import here to avoid circular dependency
        from app.services.ecommerce.shopify_provider import ShopifyStoreProvider

        # Shopify requires credentials, so we return null if not configured
        # The actual Shopify provider is created via get_provider_for_merchant
        logger.warning(
            "shopify_provider_requires_credentials",
            message="Use get_provider_for_merchant() for Shopify providers",
        )
        return get_null_provider()

    # Future providers (WooCommerce, BigCommerce) would go here
    logger.warning(
        "unsupported_provider",
        provider=store_provider.value,
        fallback="null_provider",
    )
    return get_null_provider()


def get_provider_for_merchant(merchant: Optional["Merchant"]) -> ECommerceProvider:
    """Get the appropriate e-commerce provider for a merchant.

    This is the main entry point for getting a provider instance.
    It determines the provider type from the merchant's configuration
    and returns the appropriate provider instance.

    Args:
        merchant: Merchant instance (can be None for unauthenticated requests)

    Returns:
        ECommerceProvider instance:
        - MockStoreProvider if IS_TESTING or MOCK_STORE_ENABLED
        - ShopifyStoreProvider if merchant has Shopify connected
        - NullStoreProvider otherwise

    Example:
        # In an API endpoint
        @router.get("/products")
        async def search_products(
            current_merchant: Merchant = Depends(get_current_merchant),
        ):
            provider = get_provider_for_merchant(current_merchant)
            if not provider.is_connected():
                raise HTTPException(503, "Store not connected")
            products = await provider.search_products("shoes")
            return {"products": products}
    """
    # Check for testing mode first
    is_testing = os.getenv("IS_TESTING", "false").lower() == "true"
    mock_enabled = os.getenv("MOCK_STORE_ENABLED", "false").lower() == "true"

    if is_testing or mock_enabled:
        logger.debug(
            "using_mock_provider",
            is_testing=is_testing,
            mock_enabled=mock_enabled,
        )
        return get_mock_provider()

    # If no merchant, return null provider
    if merchant is None:
        logger.debug("no_merchant_using_null_provider")
        return get_null_provider()

    # Get store provider from merchant
    # This will be added to the Merchant model in a subsequent migration
    store_provider_value = getattr(merchant, "store_provider", None)

    if store_provider_value is None:
        # Check for legacy Shopify integration
        # Merchants with existing ShopifyIntegration records should be migrated
        store_provider_value = StoreProvider.NONE.value
        if _merchant_has_shopify_integration(merchant):
            store_provider_value = StoreProvider.SHOPIFY.value
            logger.debug(
                "merchant_has_legacy_shopify",
                merchant_id=merchant.id,
            )

    store_provider = StoreProvider(store_provider_value)

    if store_provider == StoreProvider.NONE:
        return get_null_provider()

    if store_provider == StoreProvider.SHOPIFY:
        return _get_shopify_provider_for_merchant(merchant)

    # Future: WooCommerce, BigCommerce
    logger.warning(
        "unsupported_store_provider",
        merchant_id=merchant.id,
        store_provider=store_provider.value,
        fallback="null_provider",
    )
    return get_null_provider()


def _merchant_has_shopify_integration(merchant: "Merchant") -> bool:
    """Check if merchant has an existing Shopify integration.

    This is a compatibility check for the migration period.

    Args:
        merchant: Merchant to check

    Returns:
        True if merchant has Shopify integration
    """
    # Check for related ShopifyIntegration record
    # This requires the relationship to be loaded or a separate query
    # For now, we'll use a simple heuristic based on config
    if merchant.config:
        shopify_domain = merchant.config.get("shopify_domain")
        if shopify_domain:
            return True

    return False


def _get_shopify_provider_for_merchant(merchant: "Merchant") -> ECommerceProvider:
    """Get Shopify provider for a merchant with Shopify credentials.

    Args:
        merchant: Merchant with Shopify integration

    Returns:
        ShopifyStoreProvider if credentials available, NullStoreProvider otherwise
    """
    try:
        from app.services.ecommerce.shopify_provider import ShopifyStoreProvider

        return ShopifyStoreProvider(merchant_id=merchant.id)

    except Exception as e:
        logger.error(
            "failed_to_create_shopify_provider",
            merchant_id=merchant.id,
            error=str(e),
        )
        return get_null_provider()


def has_store_connected(merchant: Optional["Merchant"]) -> bool:
    """Check if a merchant has a store connected.

    This is a convenience function for the frontend to determine
    whether to show e-commerce features.

    Args:
        merchant: Merchant to check

    Returns:
        True if merchant has a connected store
    """
    provider = get_provider_for_merchant(merchant)
    return provider.is_connected()


def get_store_provider_type(merchant: Optional["Merchant"]) -> str:
    """Get the store provider type for a merchant.

    Args:
        merchant: Merchant to check

    Returns:
        Store provider type string (e.g., "shopify", "none", "mock")
    """
    provider = get_provider_for_merchant(merchant)
    return provider.provider_name
