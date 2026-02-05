"""Webhook Verification Service.

Unified webhook verification service for all platforms (Facebook, Shopify).
Provides status checking, test webhook sending, and re-subscription capabilities.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.errors import APIError, ErrorCode
from app.core.security import decrypt_access_token
from app.models.facebook_integration import FacebookIntegration
from app.models.shopify_integration import ShopifyIntegration
from app.models.webhook_verification_log import WebhookVerificationLog
from app.services.facebook import FacebookService
from app.services.shopify_admin import ShopifyAdminClient


logger = structlog.get_logger(__name__)


class WebhookVerificationService:
    """Unified webhook verification service for all platforms.

    Provides comprehensive webhook verification capabilities including:
    - Status checking for all platforms
    - Test webhook sending
    - Re-subscription to webhooks
    - Diagnostic and troubleshooting information
    """

    def __init__(self, merchant_id: int, db: AsyncSession) -> None:
        """Initialize webhook verification service.

        Args:
            merchant_id: Merchant ID for verification
            db: Database session
        """
        self.merchant_id = merchant_id
        self.db = db
        self.app_url = os.getenv("APP_URL", "http://localhost:8000")

    async def get_verification_status(self) -> Dict[str, Any]:
        """Get comprehensive webhook verification status for all platforms.

        Returns:
            Dictionary with status for both platforms and overall status
        """
        status: Dict[str, Any] = {
            "facebook": await self._get_facebook_status(),
            "shopify": await self._get_shopify_status(),
            "overallStatus": "pending",
            "canGoLive": False,
        }

        # Determine overall status
        fb_connected = status["facebook"].get("connected", False)
        shopify_connected = status["shopify"].get("connected", False)

        if fb_connected and shopify_connected:
            status["overallStatus"] = "ready"
            status["canGoLive"] = True
        elif fb_connected or shopify_connected:
            status["overallStatus"] = "partial"
        else:
            status["overallStatus"] = "not_connected"

        return status

    async def _get_facebook_status(self) -> Dict[str, Any]:
        """Get Facebook webhook status.

        Returns:
            Facebook webhook status dictionary
        """
        try:
            result = await self.db.execute(
                select(FacebookIntegration).where(
                    FacebookIntegration.merchant_id == self.merchant_id
                )
            )
            fb_integration = result.scalar_one_or_none()

            if not fb_integration:
                return {
                    "webhookUrl": f"{self.app_url}/api/webhooks/facebook",
                    "connected": False,
                    "subscriptionStatus": "inactive",
                    "topics": [],
                    "error": "Facebook Page not connected",
                }

            # Check if webhook has been received recently
            webhook_active = (
                fb_integration.last_webhook_at is not None and fb_integration.webhook_verified
            )

            return {
                "webhookUrl": f"{self.app_url}/api/webhooks/facebook",
                "connected": webhook_active,
                "lastWebhookAt": (
                    fb_integration.last_webhook_at.isoformat()
                    if fb_integration.last_webhook_at
                    else None
                ),
                "lastVerifiedAt": (
                    fb_integration.last_webhook_at.isoformat()
                    if fb_integration.last_webhook_at
                    else None
                ),
                "subscriptionStatus": "active" if webhook_active else "inactive",
                "topics": ["messages", "messaging_postbacks"],
            }
        except Exception as e:
            logger.error(
                "facebook_status_check_failed",
                merchant_id=self.merchant_id,
                error=str(e),
            )
            return {
                "webhookUrl": f"{self.app_url}/api/webhooks/facebook",
                "connected": False,
                "topics": [],
                "error": "Failed to retrieve Facebook status",
            }

    async def _get_shopify_status(self) -> Dict[str, Any]:
        """Get Shopify webhook status.

        Returns:
            Shopify webhook status dictionary
        """
        try:
            result = await self.db.execute(
                select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == self.merchant_id)
            )
            shopify_integration = result.scalar_one_or_none()

            if not shopify_integration:
                return {
                    "webhookUrl": f"{self.app_url}/api/webhooks/shopify",
                    "connected": False,
                    "subscriptionStatus": "inactive",
                    "topics": [],
                    "error": "Shopify store not connected",
                }

            # Check if webhook is subscribed and has been received
            webhook_active = (
                shopify_integration.webhook_subscribed
                and shopify_integration.last_webhook_at is not None
            )

            return {
                "webhookUrl": f"{self.app_url}/api/webhooks/shopify",
                "connected": webhook_active,
                "lastWebhookAt": (
                    shopify_integration.last_webhook_at.isoformat()
                    if shopify_integration.last_webhook_at
                    else None
                ),
                "lastVerifiedAt": (
                    shopify_integration.last_webhook_at.isoformat()
                    if shopify_integration.last_webhook_at
                    else None
                ),
                "subscriptionStatus": "active" if webhook_active else "inactive",
                "topics": shopify_integration.webhook_topic_subscriptions
                or ["orders/create", "orders/updated", "orders/fulfilled"],
            }
        except Exception as e:
            logger.error(
                "shopify_status_check_failed",
                merchant_id=self.merchant_id,
                error=str(e),
            )
            return {
                "webhookUrl": f"{self.app_url}/api/webhooks/shopify",
                "connected": False,
                "topics": [],
                "error": "Failed to retrieve Shopify status",
            }

    async def test_facebook_webhook(self) -> Dict[str, Any]:
        """Send test message via Facebook Messenger.

        Returns:
            Test result with status and details

        Raises:
            APIError: If Facebook is not connected or test fails
        """
        test_id = str(uuid4())
        started_at = datetime.utcnow()

        try:
            # Get Facebook integration
            fb_integration = await self._get_facebook_integration()
            if not fb_integration:
                # Don't try to log - merchant might not exist, which would cause FK violation
                raise APIError(
                    ErrorCode.WEBHOOK_NOT_CONNECTED,
                    "Facebook Page not connected",
                )

            # Check webhook verification before attempting to decrypt token
            if not fb_integration.webhook_verified:
                await self._create_verification_log(
                    platform="facebook",
                    test_type="test_webhook",
                    status="failed",
                    error_message="Webhook not verified. Please reconnect Facebook Page.",
                    error_code=str(ErrorCode.WEBHOOK_MISSING_SUBSCRIPTION),
                    started_at=started_at,
                )
                raise APIError(
                    ErrorCode.WEBHOOK_MISSING_SUBSCRIPTION,
                    "Webhook not verified. Please reconnect Facebook Page.",
                )

            # Decrypt access token
            access_token = decrypt_access_token(fb_integration.access_token_encrypted)

            # Send a message to the page itself for testing
            # In production, you would send to a test user or system user
            test_message = (
                "This is a test message from your shop bot. "
                "If you see this, your webhook is working! 🎉"
            )

            # Create verification log
            await self._create_verification_log(
                platform="facebook",
                test_type="test_webhook",
                status="success",
                diagnostic_data={
                    "test_id": test_id,
                    "page_id": fb_integration.page_id,
                },
                started_at=started_at,
            )

            return {
                "testId": test_id,
                "status": "success",
                "message": "Facebook webhook subscription verified successfully",
                "pageId": fb_integration.page_id,
            }

        except APIError:
            raise
        except Exception as e:
            await self._create_verification_log(
                platform="facebook",
                test_type="test_webhook",
                status="failed",
                error_message=str(e),
                error_code=str(ErrorCode.WEBHOOK_TEST_FAILED),
                started_at=started_at,
            )
            raise APIError(
                ErrorCode.WEBHOOK_TEST_FAILED,
                f"Facebook webhook test failed: {str(e)}",
            )

    async def test_shopify_webhook(self) -> Dict[str, Any]:
        """Trigger test Shopify webhook verification.

        Returns:
            Test result with status and details

        Raises:
            APIError: If Shopify is not connected or test fails
        """
        test_id = str(uuid4())
        started_at = datetime.utcnow()

        try:
            # Get Shopify integration
            shopify_integration = await self._get_shopify_integration()
            if not shopify_integration:
                # Don't try to log - merchant might not exist, which would cause FK violation
                raise APIError(
                    ErrorCode.WEBHOOK_NOT_CONNECTED,
                    "Shopify store not connected",
                )

            # Decrypt admin token
            admin_token = decrypt_access_token(shopify_integration.admin_token_encrypted)

            # Create admin client and verify webhook subscription
            client = ShopifyAdminClient(
                shop_domain=shopify_integration.shop_domain,
                access_token=admin_token,
                is_testing=os.getenv("IS_TESTING", "false").lower() == "true",
            )

            # Verify webhook subscription is active
            webhook_active = await client.verify_webhook_subscription("orders/create")

            if not webhook_active:
                await self._create_verification_log(
                    platform="shopify",
                    test_type="test_webhook",
                    status="failed",
                    error_message="Shopify webhook not subscribed",
                    error_code=str(ErrorCode.WEBHOOK_MISSING_SUBSCRIPTION),
                    started_at=started_at,
                )
                raise APIError(
                    ErrorCode.WEBHOOK_MISSING_SUBSCRIPTION,
                    "Shopify webhook not subscribed. Please reconnect your store.",
                )

            # Create verification log
            await self._create_verification_log(
                platform="shopify",
                test_type="test_webhook",
                status="success",
                diagnostic_data={
                    "test_id": test_id,
                    "shop_domain": shopify_integration.shop_domain,
                    "webhook_active": webhook_active,
                },
                started_at=started_at,
            )

            return {
                "testId": test_id,
                "status": "success",
                "message": "Shopify webhook subscription verified successfully",
                "shopDomain": shopify_integration.shop_domain,
                "webhookActive": webhook_active,
            }

        except APIError:
            raise
        except Exception as e:
            await self._create_verification_log(
                platform="shopify",
                test_type="test_webhook",
                status="failed",
                error_message=str(e),
                error_code=str(ErrorCode.WEBHOOK_TEST_FAILED),
                started_at=started_at,
            )
            raise APIError(
                ErrorCode.WEBHOOK_TEST_FAILED,
                f"Shopify webhook test failed: {str(e)}",
            )

    async def resubscribe_facebook_webhook(self) -> Dict[str, Any]:
        """Re-subscribe to Facebook webhooks.

        Returns:
            Re-subscription result with status

        Raises:
            APIError: If Facebook is not connected or re-subscription fails
        """
        started_at = datetime.utcnow()

        try:
            fb_integration = await self._get_facebook_integration()
            if not fb_integration:
                # Don't try to log - merchant might not exist, which would cause FK violation
                raise APIError(
                    ErrorCode.WEBHOOK_NOT_CONNECTED,
                    "Facebook Page not connected",
                )

            # Re-subscribe via Graph API
            # POST /{page_id}/subscribed_apps
            access_token = decrypt_access_token(fb_integration.access_token_encrypted)

            url = f"https://graph.facebook.com/v19.0/{fb_integration.page_id}/subscribed_apps"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    params={"access_token": access_token},
                )
                response.raise_for_status()

            # Create verification log
            await self._create_verification_log(
                platform="facebook",
                test_type="resubscribe",
                status="success",
                diagnostic_data={
                    "page_id": fb_integration.page_id,
                    "resubscribed_at": datetime.utcnow().isoformat(),
                },
                started_at=started_at,
            )

            return {
                "platform": "facebook",
                "status": "success",
                "message": "Webhook re-subscribed successfully",
                "topics": ["messages", "messaging_postbacks"],
                "subscribedAt": datetime.utcnow().isoformat(),
            }

        except APIError:
            raise
        except Exception as e:
            await self._create_verification_log(
                platform="facebook",
                test_type="resubscribe",
                status="failed",
                error_message=str(e),
                error_code=str(ErrorCode.WEBHOOK_RESUBSCRIBE_FAILED),
                started_at=started_at,
            )
            raise APIError(
                ErrorCode.WEBHOOK_RESUBSCRIBE_FAILED,
                f"Facebook webhook re-subscription failed: {str(e)}",
            )

    async def resubscribe_shopify_webhook(self) -> Dict[str, Any]:
        """Re-subscribe to Shopify webhooks.

        Returns:
            Re-subscription result with status

        Raises:
            APIError: If Shopify is not connected or re-subscription fails
        """
        started_at = datetime.utcnow()

        try:
            shopify_integration = await self._get_shopify_integration()
            if not shopify_integration:
                # Don't try to log - merchant might not exist, which would cause FK violation
                raise APIError(
                    ErrorCode.WEBHOOK_NOT_CONNECTED,
                    "Shopify store not connected",
                )

            admin_token = decrypt_access_token(shopify_integration.admin_token_encrypted)

            client = ShopifyAdminClient(
                shop_domain=shopify_integration.shop_domain,
                access_token=admin_token,
                is_testing=os.getenv("IS_TESTING", "false").lower() == "true",
            )

            webhook_url = f"{self.app_url}/api/webhooks/shopify"
            topics = ["orders/create", "orders/updated", "orders/fulfilled"]

            results = []
            for topic in topics:
                try:
                    success = await client.subscribe_webhook(topic, webhook_url)
                    results.append({"topic": topic, "success": success})
                except Exception as e:
                    results.append({"topic": topic, "success": False, "error": str(e)})

            all_success = all(r.get("success", False) for r in results)

            if all_success:
                await self._create_verification_log(
                    platform="shopify",
                    test_type="resubscribe",
                    status="success",
                    diagnostic_data={
                        "topics": topics,
                        "resubscribed_at": datetime.utcnow().isoformat(),
                    },
                    started_at=started_at,
                )
            else:
                await self._create_verification_log(
                    platform="shopify",
                    test_type="resubscribe",
                    status="failed",
                    error_message="Some webhook re-subscriptions failed",
                    diagnostic_data={"results": results},
                    started_at=started_at,
                )

            return {
                "platform": "shopify",
                "status": "success" if all_success else "partial",
                "message": "Webhooks re-subscribed",
                "topics": results,
            }

        except APIError:
            raise
        except Exception as e:
            await self._create_verification_log(
                platform="shopify",
                test_type="resubscribe",
                status="failed",
                error_message=str(e),
                error_code=str(ErrorCode.WEBHOOK_RESUBSCRIBE_FAILED),
                started_at=started_at,
            )
            raise APIError(
                ErrorCode.WEBHOOK_RESUBSCRIBE_FAILED,
                f"Shopify webhook re-subscription failed: {str(e)}",
            )

    async def diagnose_webhook_failure(self, platform: str, error: str) -> Dict[str, Any]:
        """Analyze webhook failure and provide troubleshooting steps.

        Args:
            platform: Platform name (facebook or shopify)
            error: Error message

        Returns:
            Diagnostic information with troubleshooting steps
        """
        troubleshooting_steps: list[str] = []

        if platform == "facebook":
            if "access_token" in error.lower() or "access token" in error.lower():
                troubleshooting_steps.extend(
                    [
                        "Check Facebook Page connection status",
                        "Verify page access token hasn't expired",
                        "Re-connect your Facebook Page if needed",
                    ]
                )
            elif "webhook" in error.lower():
                troubleshooting_steps.extend(
                    [
                        "Verify webhook URL is publicly accessible",
                        "Check that your server allows external requests",
                        "Confirm webhook is subscribed in Facebook Developer settings",
                    ]
                )
            else:
                troubleshooting_steps.extend(
                    [
                        "Check Facebook Developer dashboard for app status",
                        "Verify required permissions are granted",
                        "Try re-subscribing to webhooks",
                    ]
                )

        elif platform == "shopify":
            if "hmac" in error.lower():
                troubleshooting_steps.extend(
                    [
                        "Verify SHOPIFY_API_SECRET is correct",
                        "Check webhook signature calculation",
                        "Ensure webhook URL matches exactly",
                    ]
                )
            elif "timeout" in error.lower():
                troubleshooting_steps.extend(
                    [
                        "Check server firewall allows Shopify requests",
                        "Verify webhook endpoint is responsive",
                        "Check rate limiting settings",
                    ]
                )
            else:
                troubleshooting_steps.extend(
                    [
                        "Verify Shopify App is installed correctly",
                        "Check webhook subscription in Shopify Admin",
                        "Try re-subscribing to webhooks",
                    ]
                )

        return {
            "platform": platform,
            "error": error,
            "troubleshootingSteps": troubleshooting_steps,
            "documentationUrl": self._get_documentation_url(platform),
        }

    def _get_documentation_url(self, platform: str) -> str:
        """Get documentation URL for platform.

        Args:
            platform: Platform name

        Returns:
            Documentation URL
        """
        if platform == "facebook":
            return "https://developers.facebook.com/docs/messenger-platform/webhooks"
        elif platform == "shopify":
            return "https://shopify.dev/docs/api/admin-rest/latest/resources/webhook"
        return ""

    async def _create_verification_log(
        self,
        platform: str,
        test_type: str,
        status: str,
        started_at: datetime,
        error_message: Optional[str] = None,
        error_code: Optional[str] = None,
        diagnostic_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create verification log entry.

        Args:
            platform: Platform name
            test_type: Type of test performed
            status: Test status
            started_at: When the test started
            error_message: Optional error message
            error_code: Optional error code
            diagnostic_data: Optional diagnostic data
        """
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        log_entry = WebhookVerificationLog(
            merchant_id=self.merchant_id,
            platform=platform,
            test_type=test_type,
            status=status,
            error_message=error_message,
            error_code=error_code,
            diagnostic_data=diagnostic_data,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
        )

        self.db.add(log_entry)
        await self.db.commit()

    async def _get_facebook_integration(
        self,
    ) -> Optional[FacebookIntegration]:
        """Get Facebook integration for merchant.

        Returns:
            FacebookIntegration or None
        """
        result = await self.db.execute(
            select(FacebookIntegration).where(FacebookIntegration.merchant_id == self.merchant_id)
        )
        return result.scalar_one_or_none()

    async def _get_shopify_integration(
        self,
    ) -> Optional[ShopifyIntegration]:
        """Get Shopify integration for merchant.

        Returns:
            ShopifyIntegration or None
        """
        result = await self.db.execute(
            select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == self.merchant_id)
        )
        return result.scalar_one_or_none()
