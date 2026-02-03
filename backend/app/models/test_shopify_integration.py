"""Tests for Shopify Integration ORM model.

Tests co-located with model per project standards.
"""

from __future__ import annotations

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_shopify_integration_creation(db_session: AsyncSession, merchant) -> None:
    """Test ShopifyIntegration model creation.

    Args:
        db_session: Async database session fixture
        merchant: Test merchant fixture
    """
    from app.models.shopify_integration import ShopifyIntegration

    integration = ShopifyIntegration(
        merchant_id=merchant.id,
        shop_domain="test-store.myshopify.com",
        shop_name="Test Store",
        storefront_token_encrypted="encrypted_token",
        admin_token_encrypted="encrypted_admin_token",
        scopes=["read_products", "write_orders"],
        status="active",
    )

    db_session.add(integration)
    await db_session.commit()
    await db_session.refresh(integration)

    assert integration.id is not None
    assert integration.merchant_id == merchant.id
    assert integration.shop_domain == "test-store.myshopify.com"
    assert integration.shop_name == "Test Store"
    assert integration.status == "active"
    assert integration.storefront_api_verified is False
    assert integration.admin_api_verified is False
    assert integration.webhook_subscribed is False
    assert isinstance(integration.connected_at, datetime)
    assert isinstance(integration.created_at, datetime)


@pytest.mark.asyncio
async def test_shopify_integration_unique_merchant_id(db_session: AsyncSession, merchant) -> None:
    """Test that merchant_id is unique.

    Args:
        db_session: Async database session fixture
        merchant: Test merchant fixture
    """
    from app.models.shopify_integration import ShopifyIntegration
    from sqlalchemy import select

    integration1 = ShopifyIntegration(
        merchant_id=merchant.id,
        shop_domain="store1.myshopify.com",
        shop_name="Store 1",
        storefront_token_encrypted="token1",
        admin_token_encrypted="admin1",
        scopes=["read_products"],
    )

    integration2 = ShopifyIntegration(
        merchant_id=merchant.id,
        shop_domain="store2.myshopify.com",
        shop_name="Store 2",
        storefront_token_encrypted="token2",
        admin_token_encrypted="admin2",
        scopes=["read_products"],
    )

    db_session.add(integration1)
    await db_session.commit()

    db_session.add(integration2)

    with pytest.raises(Exception):  # IntegrityError
        await db_session.commit()


@pytest.mark.asyncio
async def test_shopify_integration_unique_shop_domain(db_session: AsyncSession, merchant) -> None:
    """Test that shop_domain is unique.

    Args:
        db_session: Async database session fixture
        merchant: Test merchant fixture
    """
    from app.models.shopify_integration import ShopifyIntegration
    from app.models.merchant import Merchant

    # Create a second merchant with required fields
    merchant2 = Merchant(
        id=2,
        merchant_key="test_merchant_key_2",
        platform="facebook"
    )
    db_session.add(merchant2)
    await db_session.commit()

    integration1 = ShopifyIntegration(
        merchant_id=merchant.id,
        shop_domain="store.myshopify.com",
        shop_name="Store 1",
        storefront_token_encrypted="token1",
        admin_token_encrypted="admin1",
        scopes=["read_products"],
    )

    integration2 = ShopifyIntegration(
        merchant_id=merchant2.id,
        shop_domain="store.myshopify.com",
        shop_name="Store 2",
        storefront_token_encrypted="token2",
        admin_token_encrypted="admin2",
        scopes=["read_products"],
    )

    db_session.add(integration1)
    await db_session.commit()

    db_session.add(integration2)

    with pytest.raises(Exception):  # IntegrityError
        await db_session.commit()


@pytest.mark.asyncio
async def test_shopify_integration_webhook_fields(db_session: AsyncSession, merchant) -> None:
    """Test webhook subscription fields.

    Args:
        db_session: Async database session fixture
        merchant: Test merchant fixture
    """
    from app.models.shopify_integration import ShopifyIntegration

    integration = ShopifyIntegration(
        merchant_id=merchant.id,
        shop_domain="test-store.myshopify.com",
        shop_name="Test Store",
        storefront_token_encrypted="token",
        admin_token_encrypted="admin",
        scopes=["read_products"],
        webhook_subscribed=True,
        webhook_topic_subscriptions=["orders/create", "orders/updated"],
        last_webhook_at=datetime.utcnow(),
    )

    db_session.add(integration)
    await db_session.commit()
    await db_session.refresh(integration)

    assert integration.webhook_subscribed is True
    assert integration.webhook_topic_subscriptions == ["orders/create", "orders/updated"]
    assert integration.last_webhook_at is not None


@pytest.mark.asyncio
async def test_shopify_integration_default_values(db_session: AsyncSession, merchant) -> None:
    """Test default field values.

    Args:
        db_session: Async database session fixture
        merchant: Test merchant fixture
    """
    from app.models.shopify_integration import ShopifyIntegration

    integration = ShopifyIntegration(
        merchant_id=merchant.id,
        shop_domain="test-store.myshopify.com",
        shop_name="Test Store",
        storefront_token_encrypted="token",
        admin_token_encrypted="admin",
        scopes=["read_products"],
    )

    db_session.add(integration)
    await db_session.commit()
    await db_session.refresh(integration)

    assert integration.status == "pending"
    assert integration.storefront_api_verified is False
    assert integration.admin_api_verified is False
    assert integration.webhook_subscribed is False
    assert integration.webhook_topic_subscriptions is None
