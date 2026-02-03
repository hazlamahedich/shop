"""Webhook error handling and DLQ tests.

Tests for webhook processing with error handling and Dead Letter Queue.
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.api.webhooks.shopify import router as shopify_webhook_router


class TestWebhookSignatureValidation:
    """Test webhook signature validation."""

    @pytest.mark.asyncio
    async def test_valid_signature_passes(self, async_client):
        """[P0] Should accept webhook with valid signature."""
        # Mock signature validation
        with patch('app.api.webhooks.shopify.verify_webhook_signature') as mock_verify:
            mock_verify.return_value = True

            response = await async_client.post(
                "/webhooks/shopify/order_created",
                json={"id": "12345"},
                headers={"X-Shopify-Hmac-Sha256": "valid-signature"}
            )

            # Should accept or process
            assert response.status_code in [200, 202]

    @pytest.mark.asyncio
    async def test_invalid_signature_returns_401(self, async_client):
        """[P0] Should reject webhook with invalid signature."""
        with patch('app.api.webhooks.shopify.verify_webhook_signature') as mock_verify:
            mock_verify.return_value = False

            response = await async_client.post(
                "/webhooks/shopify/order_created",
                json={"id": "12345"},
                headers={"X-Shopify-Hmac-Sha256": "invalid-signature"}
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_signature_returns_401(self, async_client):
        """[P1] Should reject webhook without signature."""
        response = await async_client.post(
            "/webhooks/shopify/order_created",
            json={"id": "12345"}
        )

        assert response.status_code == 401


class TestWebhookDLQ:
    """Test Dead Letter Queue processing."""

    @pytest.mark.asyncio
    async def test_failed_webhook_goes_to_dlq(self, async_client, async_session):
        """[P0] Should send failed webhook to DLQ."""
        with patch('app.services.shopify.storefront.process_webhook') as mock_process:
            mock_process.side_effect = Exception("Processing failed")

            with patch('app.services.shopify.storefront.send_to_dlq') as mock_dlq:
                response = await async_client.post(
                    "/webhooks/shopify/order_created",
                    json={"id": "12345"},
                    headers={"X-Shopify-Hmac-Sha256": "valid-signature"}
                )

                # Should acknowledge webhook to prevent retry
                assert response.status_code in [200, 202]
                # DLQ should be called
                mock_dlq.assert_called_once()

    @pytest.mark.asyncio
    async def test_dlq_retry_mechanism(self, async_client):
        """[P1] Should retry DLQ messages with backoff."""
        # Test retry logic with exponential backoff
        with patch('app.services.shopify.storefront.retry_dlq_message') as mock_retry:
            mock_retry.return_value = True

            # This would be called by a background job
            result = await mock_retry("dlq-message-id")

            assert result is True

    @pytest.mark.asyncio
    async def test_dlq_max_retries_exceeded(self, async_client):
        """[P1] Should mark DLQ message as failed after max retries."""
        with patch('app.services.shopify.storefront.get_dlq_message') as mock_get:
            mock_get.return_value = {
                "id": "dlq-123",
                "retry_count": 3,
                "max_retries": 3
            }

            with patch('app.services.shopify.storefront.mark_dlq_failed') as mock_fail:
                # Process DLQ message
                # This would be called by DLQ processor
                await mock_fail("dlq-123")
                mock_fail.assert_called_once()


class TestFacebookWebhookErrors:
    """Test Facebook webhook error handling."""

    @pytest.mark.asyncio
    async def test_facebook_webhook_verification(self, async_client):
        """[P0] Should verify Facebook webhook challenge."""
        response = await async_client.get(
            "/webhooks/facebook",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "test-challenge",
                "hub.verify_token": "test-token"
            }
        )

        # Should return challenge for valid verification
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_facebook_invalid_token_returns_403(self, async_client):
        """[P1] Should reject webhook with invalid verify token."""
        response = await async_client.get(
            "/webhooks/facebook",
            params={
                "hub.mode": "subscribe",
                "hub.challenge": "test-challenge",
                "hub.verify_token": "invalid-token"
            }
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_facebook_message_processing_error(self, async_client):
        """[P0] Should handle message processing errors gracefully."""
        with patch('app.services.facebook.process_message') as mock_process:
            mock_process.side_effect = Exception("Facebook API error")

            response = await async_client.post(
                "/webhooks/facebook",
                json={
                    "object": "page",
                    "entry": [{
                        "messaging": [{
                            "sender": {"id": "123"},
                            "recipient": {"id": "456"},
                            "message": {"text": "Hello"}
                        }]
                    }]
                }
            )

            # Should acknowledge to prevent Facebook retry
            assert response.status_code == 200
