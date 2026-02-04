"""Tests for WebhookVerificationService."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.facebook_integration import FacebookIntegration
from app.models.shopify_integration import ShopifyIntegration
from app.models.webhook_verification_log import WebhookVerificationLog
from app.models.merchant import Merchant
from app.services.webhook_verification import WebhookVerificationService
from sqlalchemy import select


@pytest.fixture
async def verification_service(db_session: AsyncSession) -> WebhookVerificationService:
    """Create a webhook verification service fixture with merchant."""
    # Create merchant first
    merchant = Merchant(
        merchant_key="test_merchant_wv_service",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.flush()
    return WebhookVerificationService(merchant_id=merchant.id, db=db_session)


@pytest.mark.asyncio
async def test_get_verification_status_both_connected(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test getting verification status when both platforms are connected."""
    # Create Facebook integration with webhook verified
    fb_integration = FacebookIntegration(
        merchant_id=verification_service.merchant_id,
        page_id="test_page_id",
        page_name="Test Page",
        access_token_encrypted="encrypted_token",
        scopes=["pages_messaging"],
        webhook_verified=True,
        last_webhook_at=datetime.utcnow(),
    )
    db_session.add(fb_integration)

    # Create Shopify integration with webhook subscribed
    shopify_integration = ShopifyIntegration(
        merchant_id=verification_service.merchant_id,
        shop_domain="test.myshopify.com",
        shop_name="Test Shop",
        storefront_token_encrypted="encrypted_storefront_token",
        admin_token_encrypted="encrypted_admin_token",
        scopes=["read_products", "write_orders"],
        webhook_subscribed=True,
        webhook_topic_subscriptions=["orders/create", "orders/updated"],
        last_webhook_at=datetime.utcnow(),
    )
    db_session.add(shopify_integration)
    await db_session.commit()

    status = await verification_service.get_verification_status()

    assert status["overallStatus"] == "ready"
    assert status["canGoLive"] is True
    assert status["facebook"]["connected"] is True
    assert status["shopify"]["connected"] is True
    assert status["facebook"]["lastWebhookAt"] is not None
    assert status["shopify"]["lastWebhookAt"] is not None


@pytest.mark.asyncio
async def test_get_verification_status_partial_connection(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test getting verification status with only one platform connected."""
    # Create only Facebook integration
    fb_integration = FacebookIntegration(
        merchant_id=verification_service.merchant_id,
        page_id="test_page_id",
        page_name="Test Page",
        access_token_encrypted="encrypted_token",
        scopes=["pages_messaging"],
        webhook_verified=True,
        last_webhook_at=datetime.utcnow(),
    )
    db_session.add(fb_integration)
    await db_session.commit()

    status = await verification_service.get_verification_status()

    assert status["overallStatus"] == "partial"
    assert status["canGoLive"] is False
    assert status["facebook"]["connected"] is True
    assert status["shopify"]["connected"] is False
    assert "Shopify store not connected" in status["shopify"]["error"]


@pytest.mark.asyncio
async def test_get_verification_status_none_connected(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test getting verification status when no platforms are connected."""
    status = await verification_service.get_verification_status()

    assert status["overallStatus"] == "not_connected"
    assert status["canGoLive"] is False
    assert status["facebook"]["connected"] is False
    assert status["shopify"]["connected"] is False


@pytest.mark.asyncio
async def test_get_facebook_status_webhook_not_verified(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test Facebook status when webhook is not verified."""
    fb_integration = FacebookIntegration(
        merchant_id=verification_service.merchant_id,
        page_id="test_page_id",
        page_name="Test Page",
        access_token_encrypted="encrypted_token",
        scopes=["pages_messaging"],
        webhook_verified=False,
        last_webhook_at=None,
    )
    db_session.add(fb_integration)
    await db_session.commit()

    status = await verification_service.get_verification_status()

    assert status["facebook"]["connected"] is False
    assert status["facebook"]["subscriptionStatus"] == "inactive"


@pytest.mark.asyncio
async def test_get_shopify_status_webhook_not_subscribed(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test Shopify status when webhook is not subscribed."""
    shopify_integration = ShopifyIntegration(
        merchant_id=verification_service.merchant_id,
        shop_domain="test.myshopify.com",
        shop_name="Test Shop",
        storefront_token_encrypted="encrypted_storefront_token",
        admin_token_encrypted="encrypted_admin_token",
        scopes=["read_products"],
        webhook_subscribed=False,
        last_webhook_at=None,
    )
    db_session.add(shopify_integration)
    await db_session.commit()

    status = await verification_service.get_verification_status()

    assert status["shopify"]["connected"] is False
    assert status["shopify"]["subscriptionStatus"] == "inactive"


@pytest.mark.asyncio
async def test_test_facebook_webhook_not_connected(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test Facebook webhook when not connected."""
    merchant_id = verification_service.merchant_id
    with pytest.raises(APIError) as exc_info:
        await verification_service.test_facebook_webhook()

    assert exc_info.value.code == ErrorCode.WEBHOOK_NOT_CONNECTED
    assert "Facebook Page not connected" in str(exc_info.value.message)

    # Note: No log is created when merchant is not connected (to avoid FK errors)
    # Logs are only created for actual test failures, not "not connected" errors


@pytest.mark.asyncio
async def test_test_facebook_webhook_not_verified(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test Facebook webhook when integration exists but webhook not verified."""
    fb_integration = FacebookIntegration(
        merchant_id=verification_service.merchant_id,
        page_id="test_page_id",
        page_name="Test Page",
        access_token_encrypted="encrypted_token",
        scopes=["pages_messaging"],
        webhook_verified=False,
    )
    db_session.add(fb_integration)
    await db_session.commit()

    with pytest.raises(APIError) as exc_info:
        await verification_service.test_facebook_webhook()

    assert exc_info.value.code == ErrorCode.WEBHOOK_MISSING_SUBSCRIPTION


@pytest.mark.asyncio
async def test_test_facebook_webhook_success(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test successful Facebook webhook test."""
    merchant_id = verification_service.merchant_id
    fb_integration = FacebookIntegration(
        merchant_id=merchant_id,
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
    ) as mock_decrypt:
        mock_decrypt.return_value = "decrypted_token"

        result = await verification_service.test_facebook_webhook()

        assert result["status"] == "success"
        assert "testId" in result
        assert result["pageId"] == "test_page_id"

    # Verify log was created
    result = await db_session.execute(
        select(WebhookVerificationLog).where(
            WebhookVerificationLog.merchant_id == merchant_id,
            WebhookVerificationLog.platform == "facebook",
            WebhookVerificationLog.test_type == "test_webhook",
            WebhookVerificationLog.status == "success",
        )
    )
    log = result.scalar_one_or_none()
    assert log is not None


@pytest.mark.asyncio
async def test_test_shopify_webhook_not_connected(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test Shopify webhook when not connected."""
    with pytest.raises(APIError) as exc_info:
        await verification_service.test_shopify_webhook()

    assert exc_info.value.code == ErrorCode.WEBHOOK_NOT_CONNECTED


@pytest.mark.asyncio
async def test_test_shopify_webhook_success(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test successful Shopify webhook test."""
    shopify_integration = ShopifyIntegration(
        merchant_id=verification_service.merchant_id,
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
        ) as mock_decrypt:
            mock_decrypt.return_value = "decrypted_token"

            result = await verification_service.test_shopify_webhook()

            assert result["status"] == "success"
            assert "testId" in result
            assert result["shopDomain"] == "test.myshopify.com"
            assert result["webhookActive"] is True


@pytest.mark.asyncio
async def test_resubscribe_facebook_webhook_not_connected(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test Facebook webhook re-subscribe when not connected."""
    with pytest.raises(APIError) as exc_info:
        await verification_service.resubscribe_facebook_webhook()

    assert exc_info.value.code == ErrorCode.WEBHOOK_NOT_CONNECTED


@pytest.mark.asyncio
async def test_resubscribe_facebook_webhook_success(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test successful Facebook webhook re-subscription."""
    fb_integration = FacebookIntegration(
        merchant_id=verification_service.merchant_id,
        page_id="test_page_id",
        page_name="Test Page",
        access_token_encrypted="encrypted_token",
        scopes=["pages_messaging"],
        webhook_verified=True,
    )
    db_session.add(fb_integration)
    await db_session.commit()

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        with patch(
            "app.services.webhook_verification.decrypt_access_token"
        ) as mock_decrypt:
            mock_decrypt.return_value = "decrypted_token"

            result = await verification_service.resubscribe_facebook_webhook()

            assert result["platform"] == "facebook"
            assert result["status"] == "success"
            assert "subscribedAt" in result


@pytest.mark.asyncio
async def test_resubscribe_shopify_webhook_not_connected(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test Shopify webhook re-subscribe when not connected."""
    with pytest.raises(APIError) as exc_info:
        await verification_service.resubscribe_shopify_webhook()

    assert exc_info.value.code == ErrorCode.WEBHOOK_NOT_CONNECTED


@pytest.mark.asyncio
async def test_resubscribe_shopify_webhook_success(
    db_session: AsyncSession,
    verification_service: WebhookVerificationService,
) -> None:
    """Test successful Shopify webhook re-subscription."""
    shopify_integration = ShopifyIntegration(
        merchant_id=verification_service.merchant_id,
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
        ) as mock_decrypt:
            mock_decrypt.return_value = "decrypted_token"

            result = await verification_service.resubscribe_shopify_webhook()

            assert result["platform"] == "shopify"
            assert result["status"] == "success"
            assert "topics" in result


@pytest.mark.asyncio
async def test_diagnose_webhook_failure_facebook(
    verification_service: WebhookVerificationService,
) -> None:
    """Test diagnosing Facebook webhook failure."""
    result = await verification_service.diagnose_webhook_failure(
        "facebook", "Invalid access token"
    )

    assert result["platform"] == "facebook"
    assert result["error"] == "Invalid access token"
    assert len(result["troubleshootingSteps"]) > 0
    # Check that any step contains access_token related guidance
    steps_lower = " ".join(result["troubleshootingSteps"]).lower()
    assert "access_token" in steps_lower or "token" in steps_lower
    assert result["documentationUrl"] != ""


@pytest.mark.asyncio
async def test_diagnose_webhook_failure_shopify_hmac(
    verification_service: WebhookVerificationService,
) -> None:
    """Test diagnosing Shopify webhook HMAC failure."""
    result = await verification_service.diagnose_webhook_failure(
        "shopify", "HMAC verification failed"
    )

    assert result["platform"] == "shopify"
    assert result["error"] == "HMAC verification failed"
    assert len(result["troubleshootingSteps"]) > 0
    # Check that any step contains hmac related guidance
    steps_lower = " ".join(result["troubleshootingSteps"]).lower()
    assert "hmac" in steps_lower or "signature" in steps_lower or "secret" in steps_lower


@pytest.mark.asyncio
async def test_diagnose_webhook_failure_shopify_timeout(
    verification_service: WebhookVerificationService,
) -> None:
    """Test diagnosing Shopify webhook timeout failure."""
    result = await verification_service.diagnose_webhook_failure(
        "shopify", "Connection timeout"
    )

    assert result["platform"] == "shopify"
    assert len(result["troubleshootingSteps"]) > 0
    # Check that any step contains timeout related guidance
    steps_lower = " ".join(result["troubleshootingSteps"]).lower()
    assert "timeout" in steps_lower or "firewall" in steps_lower or "responsive" in steps_lower


@pytest.mark.asyncio
async def test_get_documentation_url_facebook(
    verification_service: WebhookVerificationService,
) -> None:
    """Test getting Facebook documentation URL."""
    url = verification_service._get_documentation_url("facebook")
    assert "facebook" in url
    assert "developers.facebook.com" in url


@pytest.mark.asyncio
async def test_get_documentation_url_shopify(
    verification_service: WebhookVerificationService,
) -> None:
    """Test getting Shopify documentation URL."""
    url = verification_service._get_documentation_url("shopify")
    assert "shopify.dev" in url


@pytest.mark.asyncio
async def test_get_documentation_url_unknown(
    verification_service: WebhookVerificationService,
) -> None:
    """Test getting documentation URL for unknown platform."""
    url = verification_service._get_documentation_url("unknown")
    assert url == ""
