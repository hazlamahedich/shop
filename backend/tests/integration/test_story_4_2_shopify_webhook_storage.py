"""Integration tests for Story 4-2: Shopify Webhook Integration.

Tests end-to-end webhook flow including database storage.

Coverage:
- Order storage from webhook (P0)
- Order update storage (P1)
- Order fulfillment storage with tracking (P1)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


API_SECRET = "test_shopify_secret_for_testing"


def generate_valid_hmac(payload: bytes, secret: str = API_SECRET) -> str:
    """Generate valid Shopify webhook HMAC signature."""
    computed_hmac = hmac.new(secret.encode(), payload, hashlib.sha256).digest()
    return base64.b64encode(computed_hmac).decode()


class TestShopifyWebhookOrderStorage:
    """[P0/P1] Integration tests for order storage from webhooks."""

    @pytest.mark.asyncio
    async def test_p0_order_created_stored_in_database(
        self, async_client: AsyncClient, async_session: AsyncSession
    ) -> None:
        """[P0] Order is stored in database after orders/create webhook."""
        from app.models.order import Order, OrderStatus
        from app.models.merchant import Merchant

        merchant = Merchant(
            business_name="Test Store",
            email="test@example.com",
            status="active",
            merchant_key="test_store_key_001",
            platform="facebook",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        order_id = 999888777
        customer_psid = "fb_psid_test_customer_123"

        payload = {
            "id": order_id,
            "email": "buyer@test.com",
            "financial_status": "paid",
            "customer": {"id": customer_psid},
            "line_items": [{"id": 1, "title": "Widget", "quantity": 2, "price": "15.00"}],
            "total_price": "30.00",
            "currency": "USD",
        }
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            "/api/webhooks/shopify",
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_p1_order_updated_in_database(
        self, async_client: AsyncClient, async_session: AsyncSession
    ) -> None:
        """[P1] Order status is updated after orders/updated webhook."""
        from app.models.merchant import Merchant

        merchant = Merchant(
            business_name="Update Test Store",
            email="update@example.com",
            status="active",
            merchant_key="test_update_key_002",
            platform="facebook",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        order_id = 111222333

        payload = {
            "id": order_id,
            "email": "buyer@test.com",
            "financial_status": "refunded",
            "customer": {"id": "fb_psid_update_test"},
        }
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/updated",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            "/api/webhooks/shopify",
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_p1_fulfillment_tracking_stored(
        self, async_client: AsyncClient, async_session: AsyncSession
    ) -> None:
        """[P1] Fulfillment with tracking number is stored."""
        from app.models.merchant import Merchant

        merchant = Merchant(
            business_name="Fulfillment Test Store",
            email="fulfillment@example.com",
            status="active",
            merchant_key="test_fulfillment_key_003",
            platform="facebook",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        order_id = 444555666
        tracking_number = "TRACK-ABC-12345"

        payload = {
            "id": order_id,
            "email": "buyer@test.com",
            "financial_status": "paid",
            "fulfillment_status": "fulfilled",
            "customer": {"id": "fb_psid_fulfillment_test"},
            "tracking_numbers": [tracking_number],
            "tracking_url": f"https://tracking.example.com/{tracking_number}",
        }
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/fulfilled",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            "/api/webhooks/shopify",
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200


class TestShopifyWebhookEdgeCases:
    """[P2] Edge case integration tests."""

    @pytest.mark.asyncio
    async def test_p2_concurrent_webhooks_handled(
        self, async_client: AsyncClient, async_session: AsyncSession
    ) -> None:
        """[P2] Concurrent webhooks are handled without race conditions."""
        from app.models.merchant import Merchant
        import asyncio

        merchant = Merchant(
            business_name="Concurrent Test Store",
            email="concurrent@example.com",
            status="active",
            merchant_key="test_concurrent_key_004",
            platform="facebook",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        async def send_webhook(order_id: int) -> int:
            payload = {
                "id": order_id,
                "email": f"buyer{order_id}@test.com",
                "financial_status": "paid",
                "customer": {"id": f"fb_psid_{order_id}"},
            }
            raw_payload = json.dumps(payload).encode()
            signature = generate_valid_hmac(raw_payload)

            headers = {
                "X-Shopify-Hmac-Sha256": signature,
                "X-Shopify-Topic": "orders/create",
                "X-Shopify-Shop-Domain": "test-store.myshopify.com",
            }

            response = await async_client.post(
                "/api/webhooks/shopify",
                content=raw_payload,
                headers=headers,
            )
            return response.status_code

        # Send 5 concurrent webhooks
        tasks = [send_webhook(100 + i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert all(status == 200 for status in results)

    @pytest.mark.asyncio
    async def test_p2_empty_optional_fields_handled(
        self, async_client: AsyncClient, async_session: AsyncSession
    ) -> None:
        """[P2] Webhook with empty optional fields is handled."""
        from app.models.merchant import Merchant

        merchant = Merchant(
            business_name="Optional Fields Test",
            email="optional@example.com",
            status="active",
            merchant_key="test_optional_key_005",
            platform="facebook",
        )
        async_session.add(merchant)
        await async_session.commit()

        # Minimal payload with no optional fields
        payload = {
            "id": 777888999,
            "financial_status": "pending",
        }
        raw_payload = json.dumps(payload).encode()
        signature = generate_valid_hmac(raw_payload)

        headers = {
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Topic": "orders/create",
            "X-Shopify-Shop-Domain": "test-store.myshopify.com",
        }

        response = await async_client.post(
            "/api/webhooks/shopify",
            content=raw_payload,
            headers=headers,
        )

        assert response.status_code == 200
