"""API integration tests for order processing GDPR check.

Story 6-6: GDPR Deletion Processing - AC3

Tests that order processing respects GDPR "do not process" flag:
- GDPR customers have orders skipped for proactive notifications
- CCPA customers have orders skipped
- Manual deletion type allows processing
- Processing resumes after GDPR revocation
- Normal customers process normally
"""

from datetime import UTC, datetime

import pytest

from app.models.deletion_audit_log import DeletionRequestType
from app.services.privacy.gdpr_service import GDPRDeletionService
from app.services.shopify.order_processor import ShopifyOrderProcessor


class TestOrderGDPRCheck:
    """Tests for GDPR check in order processing."""

    @pytest.mark.asyncio
    async def test_order_processing_skip_gdpr_customer(
        self, async_client, async_session, test_merchant
    ):
        """Test that order processing skips GDPR customers for proactive notifications."""
        merchant_id = test_merchant
        customer_id = "gdpr_skip_customer"
        customer_email = "gdpr-customer@example.com"

        # Create GDPR deletion request
        gdpr_service = GDPRDeletionService()
        await gdpr_service.process_deletion_request(
            db=async_session,
            customer_id=customer_id,
            merchant_id=merchant_id,
            request_type=DeletionRequestType.GDPR_FORMAL,
        )
        await async_session.commit()

        # Use note_attributes to provide PSID directly (bypasses conversation lookup)
        order_payload = {
            "id": "1234567890",
            "email": customer_email,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "financial_status": "paid",
            "fulfillment_status": None,
            "total_price": "100.00",
            "subtotal_price": "90.00",
            "total_tax": "10.00",
            "currency": "USD",
            "items": [],
            "customer": {"id": customer_id, "email": customer_email},
            "shipping_address": {},
            "note_attributes": [{"name": "messenger_psid", "value": customer_id}],
        }

        processor = ShopifyOrderProcessor()
        result = await processor.process_order_webhook(
            payload=order_payload,
            shop_domain="test-shop.myshopify.com",
            merchant_id=merchant_id,
            db=async_session,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_order_processing_skip_ccpa_customer(
        self, async_client, async_session, test_merchant
    ):
        """Test that order processing skips CCPA customers."""
        merchant_id = test_merchant
        customer_id = "ccpa_skip_customer"
        customer_email = "ccpa-customer@example.com"

        # Create CCPA deletion request
        gdpr_service = GDPRDeletionService()
        await gdpr_service.process_deletion_request(
            db=async_session,
            customer_id=customer_id,
            merchant_id=merchant_id,
            request_type=DeletionRequestType.CCPA_REQUEST,
        )
        await async_session.commit()

        # Use note_attributes to provide PSID directly
        order_payload = {
            "id": "1234567891",
            "email": customer_email,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "financial_status": "paid",
            "fulfillment_status": None,
            "total_price": "100.00",
            "subtotal_price": "90.00",
            "total_tax": "10.00",
            "currency": "USD",
            "items": [],
            "customer": {"id": customer_id, "email": customer_email},
            "shipping_address": {},
            "note_attributes": [{"name": "messenger_psid", "value": customer_id}],
        }

        processor = ShopifyOrderProcessor()
        result = await processor.process_order_webhook(
            payload=order_payload,
            shop_domain="test-shop.myshopify.com",
            merchant_id=merchant_id,
            db=async_session,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_order_processing_allows_manual_deletion(
        self, async_client, async_session, test_merchant
    ):
        """Test that manual deletion type allows order processing."""
        merchant_id = test_merchant
        customer_id = "manual_deletion_customer"
        customer_email = "manual-customer@example.com"

        # Create manual deletion request
        gdpr_service = GDPRDeletionService()
        await gdpr_service.process_deletion_request(
            db=async_session,
            customer_id=customer_id,
            merchant_id=merchant_id,
            request_type=DeletionRequestType.MANUAL,
        )
        await async_session.commit()

        # Use note_attributes to provide PSID directly
        order_payload = {
            "id": "1234567892",
            "email": customer_email,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "financial_status": "paid",
            "fulfillment_status": None,
            "total_price": "100.00",
            "subtotal_price": "90.00",
            "total_tax": "10.00",
            "currency": "USD",
            "items": [],
            "customer": {"id": customer_id, "email": customer_email},
            "shipping_address": {},
            "note_attributes": [{"name": "messenger_psid", "value": customer_id}],
        }

        processor = ShopifyOrderProcessor()
        result = await processor.process_order_webhook(
            payload=order_payload,
            shop_domain="test-shop.myshopify.com",
            merchant_id=merchant_id,
            db=async_session,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_order_processing_allows_after_revocation(
        self, async_client, async_session, test_merchant
    ):
        """Test that processing resumes after GDPR revocation."""
        merchant_id = test_merchant
        customer_id = "revoked_gdpr_customer"
        customer_email = "revoked-customer@example.com"

        # Create GDPR deletion request
        gdpr_service = GDPRDeletionService()
        await gdpr_service.process_deletion_request(
            db=async_session,
            customer_id=customer_id,
            merchant_id=merchant_id,
            request_type=DeletionRequestType.GDPR_FORMAL,
        )
        await async_session.commit()

        # Revoke the GDPR request
        await gdpr_service.revoke_gdpr_request(async_session, customer_id, merchant_id)
        await async_session.commit()

        # Use note_attributes to provide PSID directly
        order_payload = {
            "id": "1234567893",
            "email": customer_email,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "financial_status": "paid",
            "fulfillment_status": None,
            "total_price": "100.00",
            "subtotal_price": "90.00",
            "total_tax": "10.00",
            "currency": "USD",
            "items": [],
            "customer": {"id": customer_id, "email": customer_email},
            "shipping_address": {},
            "note_attributes": [{"name": "messenger_psid", "value": customer_id}],
        }

        processor = ShopifyOrderProcessor()
        result = await processor.process_order_webhook(
            payload=order_payload,
            shop_domain="test-shop.myshopify.com",
            merchant_id=merchant_id,
            db=async_session,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_order_processing_allows_normal_customer(
        self, async_client, async_session, test_merchant
    ):
        """Test that normal customers without GDPR requests process normally."""
        merchant_id = test_merchant
        customer_id = "normal_customer_no_gdpr"
        customer_email = "normal-customer@example.com"

        # No GDPR request for this customer

        # Use note_attributes to provide PSID directly
        order_payload = {
            "id": "1234567894",
            "email": customer_email,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "financial_status": "paid",
            "fulfillment_status": None,
            "total_price": "100.00",
            "subtotal_price": "90.00",
            "total_tax": "10.00",
            "currency": "USD",
            "items": [],
            "customer": {"id": customer_id, "email": customer_email},
            "shipping_address": {},
            "note_attributes": [{"name": "messenger_psid", "value": customer_id}],
        }

        processor = ShopifyOrderProcessor()
        result = await processor.process_order_webhook(
            payload=order_payload,
            shop_domain="test-shop.myshopify.com",
            merchant_id=merchant_id,
            db=async_session,
        )

        assert result is not None
        assert result.platform_sender_id == customer_id
