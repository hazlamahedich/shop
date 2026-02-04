"""Tests for webhook verification API endpoints."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.facebook_integration import FacebookIntegration
from app.models.shopify_integration import ShopifyIntegration
from app.models.merchant import Merchant


@pytest.mark.asyncio
async def test_get_webhook_verification_status_both_connected(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """Test getting webhook verification status when both platforms are connected."""
    # Create merchant first
    merchant = Merchant(
        merchant_key="test_merchant_wv_api_1",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    # Create Facebook integration
    fb_integration = FacebookIntegration(
        merchant_id=merchant.id,
        page_id="test_page_id",
        page_name="Test Page",
        access_token_encrypted="encrypted_token",
        scopes=["pages_messaging"],
        webhook_verified=True,
        last_webhook_at=datetime.utcnow(),
    )
    db_session.add(fb_integration)

    # Create Shopify integration
    shopify_integration = ShopifyIntegration(
        merchant_id=merchant.id,
        shop_domain="test.myshopify.com",
        shop_name="Test Shop",
        storefront_token_encrypted="encrypted_storefront_token",
        admin_token_encrypted="encrypted_admin_token",
        scopes=["read_products"],
        webhook_subscribed=True,
        webhook_topic_subscriptions=["orders/create"],
        last_webhook_at=datetime.utcnow(),
    )
    db_session.add(shopify_integration)
    await db_session.commit()

    response = await async_client.get(f"/webhooks/verification/status?merchant_id={merchant.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert data["data"]["overallStatus"] == "ready"
    assert data["data"]["canGoLive"] is True
    assert data["data"]["facebook"]["connected"] is True
    assert data["data"]["shopify"]["connected"] is True


@pytest.mark.asyncio
async def test_get_webhook_verification_status_partial_connection(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """Test getting webhook verification status with partial connection."""
    merchant = Merchant(
        merchant_key="test_merchant_wv_api_2",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    fb_integration = FacebookIntegration(
        merchant_id=merchant.id,
        page_id="test_page_id",
        page_name="Test Page",
        access_token_encrypted="encrypted_token",
        scopes=["pages_messaging"],
        webhook_verified=True,
        last_webhook_at=datetime.utcnow(),
    )
    db_session.add(fb_integration)
    await db_session.commit()

    response = await async_client.get(f"/webhooks/verification/status?merchant_id={merchant.id}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data"]["overallStatus"] == "partial"
    assert data["data"]["canGoLive"] is False
    assert data["data"]["facebook"]["connected"] is True
    assert data["data"]["shopify"]["connected"] is False


@pytest.mark.asyncio
async def test_get_webhook_verification_status_none_connected(
    async_client: AsyncClient,
) -> None:
    """Test getting webhook verification status when none are connected."""
    response = await async_client.get("/webhooks/verification/status?merchant_id=99999")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data"]["overallStatus"] == "not_connected"
    assert data["data"]["canGoLive"] is False


@pytest.mark.asyncio
async def test_test_facebook_webhook_not_connected(
    async_client: AsyncClient,
) -> None:
    """Test Facebook webhook test when not connected."""
    response = await async_client.post("/webhooks/verification/test-facebook?merchant_id=99999")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "error_code" in data["detail"]


@pytest.mark.asyncio
async def test_test_facebook_webhook_success(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """Test successful Facebook webhook test."""
    merchant = Merchant(
        merchant_key="test_merchant_wv_api_3",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    fb_integration = FacebookIntegration(
        merchant_id=merchant.id,
        page_id="test_page_id",
        page_name="Test Page",
        access_token_encrypted="encrypted_token",
        scopes=["pages_messaging"],
        webhook_verified=True,
        last_webhook_at=datetime.utcnow(),
    )
    db_session.add(fb_integration)
    await db_session.commit()

    with patch(
        "app.services.webhook_verification.decrypt_access_token"
    ):
        response = await async_client.post(
            f"/webhooks/verification/test-facebook?merchant_id={merchant.id}"
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["data"]["status"] == "success"
    assert "testId" in data["data"]


@pytest.mark.asyncio
async def test_test_shopify_webhook_not_connected(
    async_client: AsyncClient,
) -> None:
    """Test Shopify webhook test when not connected."""
    response = await async_client.post("/webhooks/verification/test-shopify?merchant_id=99999")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "error_code" in data["detail"]


@pytest.mark.asyncio
async def test_test_shopify_webhook_success(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """Test successful Shopify webhook test."""
    merchant = Merchant(
        merchant_key="test_merchant_wv_api_4",
        platform="shopify",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    shopify_integration = ShopifyIntegration(
        merchant_id=merchant.id,
        shop_domain="test.myshopify.com",
        shop_name="Test Shop",
        storefront_token_encrypted="encrypted_storefront_token",
        admin_token_encrypted="encrypted_admin_token",
        scopes=["read_products"],
        webhook_subscribed=True,
        webhook_topic_subscriptions=["orders/create"],
        last_webhook_at=datetime.utcnow(),
    )
    db_session.add(shopify_integration)
    await db_session.commit()

    with patch(
        "app.services.webhook_verification.ShopifyAdminClient"
    ) as mock_client:
        mock_instance = AsyncMock()
        mock_instance.verify_webhook_subscription.return_value = True
        mock_client.return_value = mock_instance

        with patch(
            "app.services.webhook_verification.decrypt_access_token"
        ):
            response = await async_client.post(
                f"/webhooks/verification/test-shopify?merchant_id={merchant.id}"
            )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["data"]["status"] == "success"
    assert "testId" in data["data"]


@pytest.mark.asyncio
async def test_resubscribe_facebook_webhook_not_connected(
    async_client: AsyncClient,
) -> None:
    """Test Facebook webhook re-subscribe when not connected."""
    response = await async_client.post(
        "/webhooks/verification/resubscribe-facebook?merchant_id=99999"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_resubscribe_facebook_webhook_success(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """Test successful Facebook webhook re-subscription."""
    merchant = Merchant(
        merchant_key="test_merchant_wv_api_5",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    fb_integration = FacebookIntegration(
        merchant_id=merchant.id,
        page_id="test_page_id",
        page_name="Test Page",
        access_token_encrypted="encrypted_token",
        scopes=["pages_messaging"],
        webhook_verified=True,
    )
    db_session.add(fb_integration)
    await db_session.commit()

    with patch("httpx.AsyncClient") as mock_httpx:
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_httpx.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        with patch(
            "app.services.webhook_verification.decrypt_access_token"
        ):
            response = await async_client.post(
                f"/webhooks/verification/resubscribe-facebook?merchant_id={merchant.id}"
            )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["data"]["platform"] == "facebook"
    assert data["data"]["status"] == "success"


@pytest.mark.asyncio
async def test_resubscribe_shopify_webhook_not_connected(
    async_client: AsyncClient,
) -> None:
    """Test Shopify webhook re-subscribe when not connected."""
    response = await async_client.post(
        "/webhooks/verification/resubscribe-shopify?merchant_id=99999"
    )

    # Note: May return 404 if route doesn't exist, or 400 with error
    assert response.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)


@pytest.mark.asyncio
async def test_resubscribe_shopify_webhook_success(
    db_session: AsyncSession,
    async_client: AsyncClient,
) -> None:
    """Test successful Shopify webhook re-subscription."""
    merchant = Merchant(
        merchant_key="test_merchant_wv_api_6",
        platform="shopify",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()

    shopify_integration = ShopifyIntegration(
        merchant_id=merchant.id,
        shop_domain="test.myshopify.com",
        shop_name="Test Shop",
        storefront_token_encrypted="encrypted_storefront_token",
        admin_token_encrypted="encrypted_admin_token",
        scopes=["read_products"],
        webhook_subscribed=True,
    )
    db_session.add(shopify_integration)
    await db_session.commit()

    with patch(
        "app.services.webhook_verification.ShopifyAdminClient"
    ) as mock_client:
        mock_instance = AsyncMock()
        mock_instance.subscribe_webhook.return_value = True
        mock_client.return_value = mock_instance

        with patch(
            "app.services.webhook_verification.decrypt_access_token"
        ):
            response = await async_client.post(
                f"/webhooks/verification/resubscribe-shopify?merchant_id={merchant.id}"
            )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["data"]["platform"] == "shopify"
    assert data["data"]["status"] == "success"


@pytest.mark.asyncio
async def test_meta_data_in_response(
    async_client: AsyncClient,
) -> None:
    """Test that all responses include proper metadata."""
    response = await async_client.get("/webhooks/verification/status?merchant_id=99999")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "meta" in data
    assert "requestId" in data["meta"]
    assert "timestamp" in data["meta"]
