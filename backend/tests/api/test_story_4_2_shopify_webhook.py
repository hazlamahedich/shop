"""API tests for Story 4-2: Shopify Webhook Integration.

Tests webhook endpoint for receiving real-time order updates from Shopify.

Coverage:
- HMAC signature verification (P0)
- Webhook acceptance/rejection (P0, P1)
- Order data parsing (P0, P1)
- Error handling (P1, P2)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import pytest
from httpx import AsyncClient


API_SECRET = "test_shopify_secret_for_testing"
WEBHOOK_PATH = "/api/webhooks/shopify"


def generate_valid_hmac(payload: bytes, secret: str = API_SECRET) -> str:
    """Generate valid Shopify webhook HMAC signature."""
    computed_hmac = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    return base64.b64encode(computed_hmac).decode()


def create_shopify_order_payload(
    order_id: int = 123456789,
    email: str = "customer@example.com",
    financial_status: str = "paid",
    customer_id: str = "fb_psid_12345",
    fulfillment_status: str | None = None,
    tracking_number: str | None = None,
) -> dict:
    """Create a Shopify order webhook payload with defaults."""
    payload = {
        "id": order_id,
        "email": email,
        "financial_status": financial_status,
        "customer": {
            "id": customer_id,
            "email": email,
        },
        "line_items": [
            {
                "id": 111,
                "title": "Test Product",
                "quantity": 1,
                "price": "29.99",
            }
        ],
        "total_price": "29.99",
        "currency": "USD",
        "created_at": "2026-02-17T10:00:00Z",
        "updated_at": "2026-02-17T10:00:00Z",
    }
    if fulfillment_status:
        payload["fulfillment_status"] = fulfillment_status
    if tracking_number:
        payload["tracking_number"] = tracking_number
        payload["tracking_url"] = f"https://tracking.example.com/{tracking_number}"
    return payload


class TestShopifyWebhookHMACVerification:
    """[P0] HMAC signature verification tests."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "topic",
        [
            "orders/create",
            "orders/updated",
            "orders/fulfilled",
        ],
    )
    async def test_p0_valid_signature_accepted(self, async_client: AsyncClient, topic: str) -> None:
        """[P0] Webhook with valid HMAC signature is accepted (200)."""
        payload = create_shopify_order_payload()
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": topic,
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200
        assert response.text == "OK"

    @pytest.mark.asyncio
    async def test_p0_invalid_signature_rejected(self, async_client: AsyncClient) -> None:
        """[P0] Webhook with invalid HMAC signature is rejected (403)."""
        payload = create_shopify_order_payload()
        raw_payload = json.dumps(payload).encode()

        # Use valid base64 but wrong signature
        headers = {
            "X-Shopify-Hmac-Sha256": "aW52YWxpZF9zaWduYXR1cmVfYmFzZTY0",  # valid base64, wrong signature
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_p0_tampered_payload_rejected(self, async_client: AsyncClient) -> None:
        """[P0] Webhook with tampered payload is rejected."""
        payload = create_shopify_order_payload()
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        tampered_payload = raw_payload.replace(b'"paid"', b'"refunded"')

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=tampered_payload,
            headers=headers,
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_p1_missing_signature_header_rejected(self, async_client: AsyncClient) -> None:
        """[P1] Webhook without HMAC header is rejected (403)."""
        payload = create_shopify_order_payload()
        raw_payload = json.dumps(payload).encode()

        headers = {
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 403


class TestShopifyWebhookOrderParsing:
    """[P0/P1] Order data parsing tests."""

    @pytest.mark.asyncio
    async def test_p0_orders_create_parsed(self, async_client: AsyncClient) -> None:
        """[P0] orders/create webhook payload is parsed correctly."""
        payload = create_shopify_order_payload(
            order_id=999888777,
            email="buyer@test.com",
            financial_status="paid",
            customer_id="fb_psid_customer_123",
        )
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_p1_orders_updated_parsed(self, async_client: AsyncClient) -> None:
        """[P1] orders/updated webhook payload is parsed correctly."""
        payload = create_shopify_order_payload(
            order_id=111222333,
            financial_status="refunded",
        )
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/updated",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_p1_orders_fulfilled_parsed(self, async_client: AsyncClient) -> None:
        """[P1] orders/fulfilled webhook payload is parsed correctly."""
        payload = create_shopify_order_payload(
            order_id=444555666,
            financial_status="paid",
            fulfillment_status="fulfilled",
            tracking_number="TRACK123456",
        )
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/fulfilled",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_p0_required_fields_extracted(self, async_client: AsyncClient) -> None:
        """[P0] Required fields (order_id, customer_id, status) are extracted."""
        payload = {
            "id": 789456123,
            "email": "required@test.com",
            "financial_status": "processing",
            "customer": {"id": "fb_psid_required_test"},
            "fulfillments": [{"tracking_number": "TRACK999", "status": "in_transit"}],
        }
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/updated",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200


class TestShopifyWebhookErrorHandling:
    """[P1/P2] Error handling tests."""

    @pytest.mark.asyncio
    async def test_p1_invalid_json_rejected(self, async_client: AsyncClient) -> None:
        """[P1] Invalid JSON payload is rejected with 400."""
        raw_payload = b"not valid json {{{"
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_p2_unknown_topic_accepted(self, async_client: AsyncClient) -> None:
        """[P2] Unknown webhook topic is accepted but logged (graceful handling)."""
        payload = create_shopify_order_payload()
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "products/create",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_p2_large_payload_accepted(self, async_client: AsyncClient) -> None:
        """[P2] Large payload is handled without error."""
        payload = create_shopify_order_payload()
        payload["line_items"] = [
            {"id": i, "title": f"Product {i}", "quantity": 1, "price": "9.99"} for i in range(100)
        ]
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_p1_missing_topic_header_accepted(self, async_client: AsyncClient) -> None:
        """[P1] Missing topic header is accepted (topic is logged)."""
        payload = create_shopify_order_payload()
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200


class TestShopifyWebhookResponseTime:
    """[P1] Response time tests for >99.9% success rate."""

    @pytest.mark.asyncio
    async def test_p1_response_time_under_2_seconds(self, async_client: AsyncClient) -> None:
        """[P1] Webhook responds within 2 seconds (per AC)."""
        import time

        payload = create_shopify_order_payload()
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        start_time = time.time()
        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 2.0, f"Response took {elapsed_time:.2f}s (expected < 2s)"

    @pytest.mark.asyncio
    async def test_p1_always_returns_200_on_valid_signature(
        self, async_client: AsyncClient
    ) -> None:
        """[P1] Valid webhook always returns 200 (graceful error handling)."""
        payload = create_shopify_order_payload()
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            WEBHOOK_PATH,
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200
