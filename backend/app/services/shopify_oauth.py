"""Shopify integration service.

Handles OAuth flow, token management, and API client operations.
"""

from __future__ import annotations

import re
from typing import Optional, Any
from urllib.parse import urlencode

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shopify_integration import ShopifyIntegration
from app.models.merchant import Merchant
from app.core.security import (
    encrypt_access_token,
    decrypt_access_token,
    generate_oauth_state,
)
from app.core.errors import APIError, ErrorCode
from app.core.config import settings

# Shopify API endpoints
SHOPIFY_OAUTH_DIALOG_URL = "https://{shop}/admin/oauth/authorize"
SHOPIFY_TOKEN_EXCHANGE_URL = "https://{shop}/admin/oauth/access_token"

# Required OAuth scopes for Shopify (read-only for chatbot)
REQUIRED_SCOPES = [
    "read_products",
    "write_products",  # Required for creating Storefront access tokens
    "read_inventory",
    "read_orders",
    "read_fulfillments",
    "read_customers",
]

# Optional scopes that enhance functionality but aren't required
OPTIONAL_SCOPES = [
    "read_all_orders",  # Access orders older than 60 days (requires Shopify approval)
]

logger = structlog.get_logger(__name__)


def validate_shop_domain(shop_domain: str) -> bool:
    """Validate Shopify store domain format.

    Args:
        shop_domain: Store domain to validate

    Returns:
        True if valid Shopify domain format

    Examples:
        >>> validate_shop_domain("mystore.myshopify.com")
        True
        >>> validate_shop_domain("mystore.com")
        False
    """
    pattern = r"^[a-zA-Z0-9][a-zA-Z0-9\-]*\.myshopify\.com$"
    return re.match(pattern, shop_domain) is not None


class ShopifyService:
    """Service for Shopify integration operations."""

    def __init__(self, db: AsyncSession, is_testing: bool = False) -> None:
        """Initialize Shopify service.

        Args:
            db: Database session
            is_testing: Whether running in test mode (uses mock client)
        """
        self.db = db
        self.is_testing = is_testing
        self._async_client: Optional[httpx.AsyncClient] = None

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client.

        Returns:
            httpx.AsyncClient: Configured HTTP client
        """
        if self._async_client is None:
            if self.is_testing:
                from httpx import ASGITransport
                from app.main import app

                self._async_client = httpx.AsyncClient(
                    transport=ASGITransport(app=app), base_url="http://test"
                )
            else:
                # Use SSL context with certifi for macOS compatibility
                from app.core.http_client import get_ssl_context

                ssl_context = get_ssl_context()
                self._async_client = httpx.AsyncClient(verify=ssl_context, timeout=30.0)
        return self._async_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    async def generate_oauth_url(self, merchant_id: int, shop_domain: str) -> tuple[str, str]:
        """Generate Shopify OAuth URL with state parameter.

        Args:
            merchant_id: Merchant ID initiating OAuth
            shop_domain: Shopify store domain (e.g., mystore.myshopify.com)

        Returns:
            Tuple of (auth_url, state_token)

        Raises:
            APIError: If shop domain is invalid or configuration is missing
        """
        # Validate shop domain format
        if not validate_shop_domain(shop_domain):
            raise APIError(
                ErrorCode.SHOPIFY_SHOP_DOMAIN_INVALID,
                "Shop domain format invalid. Expected: mystore.myshopify.com",
            )

        # First try to get merchant-specific credentials
        result = await self.db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalars().first()

        api_key = None
        if merchant and merchant.config:
            api_key = merchant.config.get("shopify_api_key")
            if api_key:
                logger.info("using_merchant_shopify_api_key", merchant_id=merchant_id)

        # Fall back to global config if merchant credentials not found
        if not api_key:
            config = settings()
            api_key = config.get("SHOPIFY_API_KEY")

        if not api_key:
            raise APIError(
                ErrorCode.SHOPIFY_ENCRYPTION_KEY_MISSING,
                "Shopify API Key not configured. Please save your Shopify App credentials first.",
            )

        # Get redirect URI - try merchant config first, then global
        redirect_uri = None
        if merchant and merchant.config:
            redirect_uri = merchant.config.get("shopify_redirect_uri")

        if not redirect_uri:
            config = settings()
            redirect_uri = config.get("SHOPIFY_REDIRECT_URI")

        if not redirect_uri:
            # Default redirect URI - backend callback endpoint
            from app.core.config import is_testing

            if is_testing():
                redirect_uri = "http://localhost:8000/api/integrations/shopify/callback"
            else:
                redirect_uri = "http://localhost:8000/api/integrations/shopify/callback"
            logger.info("using_default_redirect_uri", redirect_uri=redirect_uri)

        # Generate state token for CSRF protection (stores merchant_id)
        state = generate_oauth_state(merchant_id)

        # Build OAuth URL - include read_all_orders if merchant has approval
        params = {
            "client_id": api_key,
            "redirect_uri": redirect_uri,
            "scope": ",".join(REQUIRED_SCOPES + ["read_all_orders"]),
            "response_type": "code",
            "state": state,
        }

        query_string = urlencode(params)
        auth_url = f"{SHOPIFY_OAUTH_DIALOG_URL.format(shop=shop_domain)}?{query_string}"
        return auth_url, state

    async def exchange_code_for_token(
        self,
        shop_domain: str,
        code: str,
        merchant_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Exchange authorization code for Admin API access token.

        Args:
            shop_domain: Shopify shop domain
            code: Authorization code from Shopify
            merchant_id: Optional merchant ID for manual credential lookup

        Returns:
            Dict with access_token, scope, and associated_user

        Raises:
            APIError: If token exchange fails
        """
        config = settings()
        api_key = config.get("SHOPIFY_API_KEY")
        api_secret = config.get("SHOPIFY_API_SECRET")
        redirect_uri = config.get("SHOPIFY_REDIRECT_URI")

        # Try to find merchant-specific credentials
        lookup_id = merchant_id
        if not lookup_id:
            # Fallback to finding merchant by shop_domain if merchant_id not provided
            result = await self.db.execute(
                select(ShopifyIntegration).where(ShopifyIntegration.shop_domain == shop_domain)
            )
            integration = result.scalars().first()
            if integration:
                lookup_id = integration.merchant_id

        if lookup_id:
            merchant_result = await self.db.execute(
                select(Merchant).where(Merchant.id == lookup_id)
            )
            merchant = merchant_result.scalars().first()
            if merchant and merchant.config:
                merchant_api_key = merchant.config.get("shopify_api_key")
                merchant_api_secret_encrypted = merchant.config.get("shopify_api_secret_encrypted")
                if merchant_api_key and merchant_api_secret_encrypted:
                    api_key = merchant_api_key
                    api_secret = decrypt_access_token(merchant_api_secret_encrypted)
                    logger.debug(
                        "using_merchant_shopify_credentials",
                        merchant_id=lookup_id,
                    )

        # Exchange code for access token
        params = {
            "client_id": api_key,
            "client_secret": api_secret,
            "code": code,
        }

        try:
            if self.is_testing:
                # Return mock token in test mode
                return {
                    "access_token": "test_admin_token",
                    "scope": ",".join(REQUIRED_SCOPES),
                    "associated_user": {
                        "id": 123456789,
                        "first_name": "Test",
                        "last_name": "User",
                        "email": "test@example.com",
                        "email_verified": True,
                        "account_owner": True,
                    },
                }

            url = SHOPIFY_TOKEN_EXCHANGE_URL.format(shop=shop_domain)
            response = await self.async_client.post(url, params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise APIError(
                ErrorCode.SHOPIFY_TOKEN_EXCHANGE_FAILED,
                f"Failed to exchange authorization code: {e.response.text}",
            )

    async def create_shopify_integration(
        self,
        merchant_id: int,
        shop_domain: str,
        shop_name: str,
        admin_token: str,
        storefront_token: Optional[str],
        scopes: list[str],
    ) -> ShopifyIntegration:
        """Create Shopify integration record.

        Args:
            merchant_id: Merchant ID
            shop_domain: Shopify shop domain
            shop_name: Shopify shop name
            admin_token: Admin API access token (will be encrypted)
            storefront_token: Storefront API access token (will be encrypted, optional)
            scopes: Granted OAuth scopes

        Returns:
            Created ShopifyIntegration record

        Raises:
            APIError: If merchant already has Shopify connected
        """
        # Check if merchant already has Shopify integration
        result = await self.db.execute(
            select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant_id)
        )
        existing = result.scalars().first()

        if existing:
            raise APIError(
                ErrorCode.SHOPIFY_ALREADY_CONNECTED,
                "Shopify store already connected to this merchant",
            )

        # Encrypt access tokens
        encrypted_admin_token = encrypt_access_token(admin_token)
        encrypted_storefront_token = (
            encrypt_access_token(storefront_token) if storefront_token else None
        )

        # Create integration record
        integration = ShopifyIntegration(
            merchant_id=merchant_id,
            shop_domain=shop_domain,
            shop_name=shop_name,
            admin_token_encrypted=encrypted_admin_token,
            storefront_token_encrypted=encrypted_storefront_token,
            scopes=scopes,
            status="active",
        )

        # Sprint Change 2026-02-13: Update merchant's store_provider
        merchant_result = await self.db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = merchant_result.scalars().first()
        if merchant:
            merchant.store_provider = "shopify"

        self.db.add(integration)
        await self.db.commit()
        await self.db.refresh(integration)

        return integration

    async def get_shopify_integration(self, merchant_id: int) -> Optional[ShopifyIntegration]:
        """Get Shopify integration for merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            ShopifyIntegration record or None
        """
        result = await self.db.execute(
            select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant_id)
        )
        return result.scalars().first()

    async def get_admin_token(self, merchant_id: int) -> str:
        """Get decrypted Admin API access token for merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            Decrypted Admin API access token

        Raises:
            APIError: If Shopify not connected
        """
        integration = await self.get_shopify_integration(merchant_id)

        if not integration:
            raise APIError(ErrorCode.SHOPIFY_NOT_CONNECTED, "Shopify store not connected")

        return decrypt_access_token(integration.admin_token_encrypted)

    async def get_storefront_token(self, merchant_id: int) -> str:
        """Get decrypted Storefront API access token for merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            Decrypted Storefront API access token

        Raises:
            APIError: If Shopify not connected
        """
        integration = await self.get_shopify_integration(merchant_id)

        if not integration:
            raise APIError(ErrorCode.SHOPIFY_NOT_CONNECTED, "Shopify store not connected")

        return decrypt_access_token(integration.storefront_token_encrypted)

    async def get_shop_domain(self, merchant_id: int) -> str:
        """Get shop domain for merchant.

        Args:
            merchant_id: Merchant ID

        Returns:
            Shopify shop domain

        Raises:
            APIError: If Shopify not connected
        """
        integration = await self.get_shopify_integration(merchant_id)

        if not integration:
            raise APIError(ErrorCode.SHOPIFY_NOT_CONNECTED, "Shopify store not connected")

        return integration.shop_domain

    async def disconnect_shopify(self, merchant_id: int) -> None:
        """Disconnect Shopify integration for merchant.

        Args:
            merchant_id: Merchant ID

        Raises:
            APIError: If Shopify not connected
        """
        integration = await self.get_shopify_integration(merchant_id)

        if not integration:
            raise APIError(ErrorCode.SHOPIFY_NOT_CONNECTED, "Shopify store not connected")

        await self.db.delete(integration)

        # Sprint Change 2026-02-13: Reset merchant's store_provider to none
        merchant_result = await self.db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = merchant_result.scalars().first()
        if merchant:
            merchant.store_provider = "none"

        await self.db.commit()

    async def save_shopify_credentials(self, merchant_id: int, api_key: str, api_secret: str):
        """Save Shopify API Key and Secret for a merchant."""
        from sqlalchemy.orm.attributes import flag_modified

        result = await self.db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalars().first()

        if not merchant:
            raise APIError(
                ErrorCode.MERCHANT_NOT_FOUND, f"Merchant with id {merchant_id} not found."
            )

        encrypted_secret = encrypt_access_token(api_secret)

        config = merchant.config or {}
        config["shopify_api_key"] = api_key
        config["shopify_api_secret_encrypted"] = encrypted_secret
        merchant.config = config

        # Mark config as modified so SQLAlchemy detects the change
        flag_modified(merchant, "config")

        await self.db.commit()
        await self.db.refresh(merchant)


from fastapi import Depends
from app.core.database import get_db


async def get_shopify_service(db: AsyncSession = Depends(get_db)) -> ShopifyService:
    """Get Shopify service instance.

    Args:
        db: Database session

    Returns:
        ShopifyService instance
    """
    from app.core.config import is_testing

    return ShopifyService(db, is_testing=is_testing())
