"""Tests for Shopify integration service.

Tests co-located with service per project standards.
"""

from __future__ import annotations

import pytest
from app.services.shopify import (
    ShopifyService,
    validate_shop_domain,
)


def test_validate_shop_domain_valid() -> None:
    """Test shop domain validation with valid domains."""
    assert validate_shop_domain("mystore.myshopify.com") is True
    assert validate_shop_domain("my-store-123.myshopify.com") is True
    assert validate_shop_domain("mystore123.myshopify.com") is True


def test_validate_shop_domain_invalid() -> None:
    """Test shop domain validation with invalid domains."""
    assert validate_shop_domain("mystore.com") is False
    assert validate_shop_domain(".myshopify.com") is False
    assert validate_shop_domain("-store.myshopify.com") is False
    assert validate_shop_domain("store@myshopify.com") is False
    assert validate_shop_domain("my.shopify.com") is False


@pytest.mark.asyncio
async def test_shopify_service_initialization(db_session, merchant) -> None:
    """Test ShopifyService initialization."""
    from app.services.shopify import ShopifyService

    service = ShopifyService(db_session, is_testing=True)

    assert service.db == db_session
    assert service.is_testing is True


@pytest.mark.asyncio
async def test_generate_oauth_url_invalid_domain(db_session, merchant) -> None:
    """Test OAuth URL generation fails with invalid domain."""
    from app.services.shopify import ShopifyService
    from app.core.errors import APIError, ErrorCode

    service = ShopifyService(db_session, is_testing=True)

    with pytest.raises(APIError) as exc_info:
        await service.generate_oauth_url(merchant_id=merchant.id, shop_domain="invalid.com")

    assert exc_info.value.code == ErrorCode.SHOPIFY_SHOP_DOMAIN_INVALID


@pytest.mark.asyncio
async def test_generate_oauth_url_valid_domain(db_session, merchant, monkeypatch) -> None:
    """Test OAuth URL generation with valid domain."""
    from app.services.shopify import ShopifyService
    from app.core.config import settings

    # Mock config
    def mock_settings():
        return {
            "SHOPIFY_API_KEY": "test_api_key",
            "SHOPIFY_REDIRECT_URI": "https://example.com/callback",
            "IS_TESTING": True,
        }

    # Patch the shopify_oauth module where settings is used
    monkeypatch.setattr("app.services.shopify_oauth.settings", mock_settings)

    service = ShopifyService(db_session, is_testing=True)

    auth_url, state = await service.generate_oauth_url(
        merchant_id=merchant.id,
        shop_domain="test-store.myshopify.com"
    )

    assert "test-store.myshopify.com" in auth_url
    assert "test_api_key" in auth_url
    assert "read_products" in auth_url
    assert state is not None


@pytest.mark.asyncio
async def test_exchange_code_for_token_testing_mode(db_session, merchant) -> None:
    """Test token exchange in testing mode."""
    from app.services.shopify import ShopifyService

    service = ShopifyService(db_session, is_testing=True)

    token_data = await service.exchange_code_for_token(
        shop_domain="test.myshopify.com",
        code="test_code"
    )

    assert token_data["access_token"] == "test_admin_token"
    assert "read_products" in token_data["scope"]
    assert token_data["associated_user"]["account_owner"] is True


@pytest.mark.asyncio
async def test_create_shopify_integration(db_session, merchant) -> None:
    """Test Shopify integration creation."""
    from app.services.shopify import ShopifyService
    from app.models.shopify_integration import ShopifyIntegration
    from sqlalchemy import select

    service = ShopifyService(db_session, is_testing=True)

    integration = await service.create_shopify_integration(
        merchant_id=merchant.id,
        shop_domain="test-store.myshopify.com",
        shop_name="Test Store",
        admin_token="admin_token",
        storefront_token="storefront_token",
        scopes=["read_products", "write_orders"]
    )

    assert integration.id is not None
    assert integration.merchant_id == merchant.id
    assert integration.shop_domain == "test-store.myshopify.com"
    assert integration.shop_name == "Test Store"
    assert integration.status == "active"

    # Verify tokens are encrypted (not plain text)
    assert integration.admin_token_encrypted != "admin_token"
    assert integration.storefront_token_encrypted != "storefront_token"


@pytest.mark.asyncio
async def test_create_shopify_integration_duplicate(db_session, merchant) -> None:
    """Test duplicate Shopify integration raises error."""
    from app.services.shopify import ShopifyService
    from app.core.errors import APIError, ErrorCode

    service = ShopifyService(db_session, is_testing=True)

    # Create first integration
    await service.create_shopify_integration(
        merchant_id=merchant.id,
        shop_domain="store1.myshopify.com",
        shop_name="Store 1",
        admin_token="token1",
        storefront_token="sf_token1",
        scopes=["read_products"]
    )

    # Try to create duplicate
    with pytest.raises(APIError) as exc_info:
        await service.create_shopify_integration(
            merchant_id=merchant.id,
            shop_domain="store2.myshopify.com",
            shop_name="Store 2",
            admin_token="token2",
            storefront_token="sf_token2",
            scopes=["read_products"]
        )

    assert exc_info.value.code == ErrorCode.SHOPIFY_ALREADY_CONNECTED


@pytest.mark.asyncio
async def test_get_shopify_integration(db_session, merchant) -> None:
    """Test getting Shopify integration."""
    from app.services.shopify import ShopifyService

    service = ShopifyService(db_session, is_testing=True)

    # Create integration
    await service.create_shopify_integration(
        merchant_id=merchant.id,
        shop_domain="test-store.myshopify.com",
        shop_name="Test Store",
        admin_token="admin_token",
        storefront_token="storefront_token",
        scopes=["read_products"]
    )

    # Get integration
    integration = await service.get_shopify_integration(merchant.id)

    assert integration is not None
    assert integration.merchant_id == merchant.id
    assert integration.shop_domain == "test-store.myshopify.com"


@pytest.mark.asyncio
async def test_get_shopify_integration_not_found(db_session) -> None:
    """Test getting non-existent Shopify integration returns None."""
    from app.services.shopify import ShopifyService

    service = ShopifyService(db_session, is_testing=True)

    integration = await service.get_shopify_integration(999)

    assert integration is None


@pytest.mark.asyncio
async def test_get_shop_domain(db_session, merchant) -> None:
    """Test getting shop domain."""
    from app.services.shopify import ShopifyService

    service = ShopifyService(db_session, is_testing=True)

    await service.create_shopify_integration(
        merchant_id=merchant.id,
        shop_domain="test-store.myshopify.com",
        shop_name="Test Store",
        admin_token="admin_token",
        storefront_token="storefront_token",
        scopes=["read_products"]
    )

    domain = await service.get_shop_domain(merchant.id)

    assert domain == "test-store.myshopify.com"


@pytest.mark.asyncio
async def test_get_shop_domain_not_connected(db_session) -> None:
    """Test getting shop domain when not connected raises error."""
    from app.services.shopify import ShopifyService
    from app.core.errors import APIError, ErrorCode

    service = ShopifyService(db_session, is_testing=True)

    with pytest.raises(APIError) as exc_info:
        await service.get_shop_domain(999)

    assert exc_info.value.code == ErrorCode.SHOPIFY_NOT_CONNECTED


@pytest.mark.asyncio
async def test_disconnect_shopify(db_session, merchant) -> None:
    """Test disconnecting Shopify integration."""
    from app.services.shopify import ShopifyService

    service = ShopifyService(db_session, is_testing=True)

    # Create integration
    await service.create_shopify_integration(
        merchant_id=merchant.id,
        shop_domain="test-store.myshopify.com",
        shop_name="Test Store",
        admin_token="admin_token",
        storefront_token="storefront_token",
        scopes=["read_products"]
    )

    # Disconnect
    await service.disconnect_shopify(merchant.id)

    # Verify disconnected
    integration = await service.get_shopify_integration(merchant.id)
    assert integration is None


@pytest.mark.asyncio
async def test_close_service(db_session, merchant) -> None:
    """Test closing the service and its HTTP client."""
    from app.services.shopify import ShopifyService

    service = ShopifyService(db_session, is_testing=True)

    # In testing mode, accessing async_client creates a mock client
    # Test that close() properly cleans up
    _ = service.async_client
    assert service._async_client is not None

    # Close service
    await service.close()
    # After closing, the client should be cleaned up
    # In testing mode, a new client would be created if accessed again
    assert service._async_client is None
