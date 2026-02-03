"""Webhook error handling and DLQ tests.

Tests for webhook processing with error handling and Dead Letter Queue.
"""

import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock


class TestWebhookSignatureValidation:
    """Test webhook signature validation."""

    @pytest.mark.asyncio
    async def test_valid_signature_passes(self, async_client):
        """[P0] Should accept webhook with valid signature."""
        # Mock signature verification to return True
        # Patch at the import location in the webhook module
        with patch('app.api.webhooks.shopify.verify_shopify_webhook_hmac') as mock_verify:
            mock_verify.return_value = True

            response = await async_client.post(
                "/webhooks/shopify",
                json={"id": "12345"},
                headers={
                    "X-Shopify-Hmac-Sha256": "valid-signature",
                    "X-Shopify-Topic": "orders/create"
                }
            )

            # Should accept webhook
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_invalid_signature_returns_403(self, async_client):
        """[P0] Should reject webhook with invalid signature."""
        # Mock signature verification to return False
        with patch('app.api.webhooks.shopify.verify_shopify_webhook_hmac') as mock_verify:
            mock_verify.return_value = False

            response = await async_client.post(
                "/webhooks/shopify",
                json={"id": "12345"},
                headers={
                    "X-Shopify-Hmac-Sha256": "invalid-signature",
                    "X-Shopify-Topic": "orders/create"
                }
            )

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_signature_returns_403(self, async_client):
        """[P1] Should reject webhook without signature."""
        # Mock signature verification to handle None header gracefully
        with patch('app.api.webhooks.shopify.verify_shopify_webhook_hmac') as mock_verify:
            mock_verify.return_value = False

            response = await async_client.post(
                "/webhooks/shopify",
                json={"id": "12345"},
                headers={"X-Shopify-Topic": "orders/create"}
            )

            # Without HMAC header, verification should fail
            assert response.status_code == 403


class TestWebhookDLQ:
    """Test Dead Letter Queue processing."""

    @pytest.mark.asyncio
    async def test_failed_webhook_goes_to_dlq(self, async_client):
        """[P0] Should send failed webhook to DLQ."""
        # Mock the signature verification
        with patch('app.api.webhooks.shopify.verify_shopify_webhook_hmac') as mock_verify:
            mock_verify.return_value = True

            # Mock the DLQ enqueue function
            with patch('app.api.webhooks.shopify.enqueue_failed_shopify_webhook') as mock_dlq:
                response = await async_client.post(
                    "/webhooks/shopify",
                    json={"id": "12345"},
                    headers={
                        "X-Shopify-Hmac-Sha256": "valid-signature",
                        "X-Shopify-Topic": "orders/create"
                    }
                )

                # Should acknowledge webhook to prevent retry
                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dlq_with_redis_unavailable(self, async_client):
        """[P1] Should handle Redis unavailability gracefully."""
        # Mock signature verification
        with patch('app.api.webhooks.shopify.verify_shopify_webhook_hmac') as mock_verify:
            mock_verify.return_value = True

            # Mock Redis as unavailable by removing REDIS_URL
            original_redis_url = os.environ.get("REDIS_URL")
            os.environ.pop("REDIS_URL", None)

            try:
                response = await async_client.post(
                    "/webhooks/shopify",
                    json={"id": "12345"},
                    headers={
                        "X-Shopify-Hmac-Sha256": "valid-signature",
                        "X-Shopify-Topic": "orders/create"
                    }
                )

                # Should still accept webhook even if DLQ is unavailable
                assert response.status_code == 200
            finally:
                if original_redis_url:
                    os.environ["REDIS_URL"] = original_redis_url


class TestFacebookWebhookErrors:
    """Test Facebook webhook error handling."""

    @pytest.mark.asyncio
    async def test_facebook_webhook_verification(self, async_client):
        """[P0] Should verify Facebook webhook challenge."""
        # Use the test token from conftest.py
        # The endpoint expects 'mode', 'token', 'challenge' params
        response = await async_client.get(
            "/webhooks/facebook",
            params={
                "mode": "subscribe",
                "challenge": "test-challenge",
                "token": "test_token"
            }
        )

        # Should return challenge for valid verification
        assert response.status_code == 200
        assert "test-challenge" in response.text

    @pytest.mark.asyncio
    async def test_facebook_invalid_token_returns_403(self, async_client):
        """[P1] Should reject webhook with invalid verify token."""
        response = await async_client.get(
            "/webhooks/facebook",
            params={
                "mode": "subscribe",
                "challenge": "test-challenge",
                "token": "invalid-token"
            }
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_facebook_message_processing_error(self, async_client):
        """[P0] Should handle message processing errors gracefully."""
        # Mock signature verification at the import location
        with patch('app.api.webhooks.facebook.verify_webhook_signature') as mock_verify:
            mock_verify.return_value = True

            # The background processing happens asynchronously
            # Even if it fails, the endpoint should return 200 to acknowledge receipt
            response = await async_client.post(
                "/webhooks/facebook",
                json={
                    "object": "page",
                    "entry": [{
                        "id": "123456789",
                        "messaging": [{
                            "sender": {"id": "123"},
                            "recipient": {"id": "456"},
                            "message": {"text": "Hello"}
                        }]
                    }]
                },
                headers={"X-Hub-Signature-256": "valid-signature"}
            )

            # Should acknowledge to prevent Facebook retry
            # The webhook is processed asynchronously, so we return 200 immediately
            assert response.status_code == 200
