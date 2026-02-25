"""Tests for Story 4-13: Payment/Cost Data Enhancement."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.shopify.order_processor import parse_shopify_order
from app.schemas.order import OrderResponse, PaymentBreakdown, ProfitData


class TestOrderResponseSchema:
    """Test OrderResponse schema with payment breakdown and profit data."""

    def test_payment_breakdown_creation(self):
        """Test PaymentBreakdown schema."""
        pb = PaymentBreakdown(
            subtotal=Decimal("100.00"),
            total=Decimal("112.50"),
            shipping=Decimal("10.00"),
            tax=Decimal("2.50"),
            discount=Decimal("5.00"),
            discount_codes=None,
            payment_method="Credit Card",
            currency="USD",
        )
        assert pb.subtotal == Decimal("100.00")
        assert pb.total == Decimal("112.50")
        assert pb.shipping == Decimal("10.00")

    def test_profit_data_creation(self):
        """Test ProfitData schema."""
        pd = ProfitData(
            revenue=Decimal("112.50"),
            cogs=Decimal("50.00"),
            margin=Decimal("62.50"),
            margin_percent=55.56,
            cogs_fetched_at=None,
        )
        assert pd.revenue == Decimal("112.50")
        assert pd.cogs == Decimal("50.00")
        assert pd.margin == Decimal("62.50")

    def test_order_response_from_order(self):
        """Test OrderResponse.from_order factory method."""
        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.order_number = "1001"
        mock_order.status = "shipped"
        mock_order.items = [{"title": "Product", "quantity": 1}]
        mock_order.currency_code = "USD"
        mock_order.customer_email = "test@example.com"
        mock_order.customer_first_name = "John"
        mock_order.customer_last_name = "Doe"
        mock_order.tracking_number = "TRACK123"
        mock_order.tracking_url = "https://track.example.com/123"
        mock_order.estimated_delivery = datetime(2026, 2, 28)
        mock_order.subtotal = Decimal("100.00")
        mock_order.total = Decimal("112.50")
        mock_order.total_shipping = Decimal("10.00")
        mock_order.total_tax = Decimal("2.50")
        mock_order.total_discount = None
        mock_order.discount_codes = None
        mock_order.payment_method = "Credit Card"
        mock_order.cogs_total = Decimal("50.00")
        mock_order.cogs_fetched_at = datetime(2026, 2, 25)
        mock_order.created_at = datetime(2026, 2, 20)
        mock_order.updated_at = datetime(2026, 2, 25)

        response = OrderResponse.from_order(mock_order)
        assert response.order_number == "1001"
        assert response.payment_breakdown.subtotal == Decimal("100.00")
        assert response.payment_breakdown.total == Decimal("112.50")
        assert response.profit_data is not None
        assert response.profit_data.margin == Decimal("62.50")


class TestPaymentDataExtraction:
    """Test that parse_shopify_order extracts payment data correctly."""

    def test_discount_codes(self):
        """Test discount codes extraction."""
        payload = {
            "id": 123456789,
            "order_number": 1001,
            "email": "test@example.com",
            "discount_codes": [
                {"code": "SAVE10", "amount": "10.00", "type": "percentage"},
                {"code": "FREESHIP", "amount": "5.00", "type": "fixed_amount"},
            ],
            "financial_status": "paid",
            "customer": {
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+15551234567",
                "email": "john@example.com",
            },
            "shipping_address": {
                "city": "New York",
                "province": "NY",
                "country": "US",
                "country_code": "US",
                "zip": "10001",
            },
        }
        result = parse_shopify_order(payload)
        assert result["discount_codes"] is not None
        assert len(result["discount_codes"]) == 2

    def test_tax_and_shipping(self):
        """Test tax and shipping extraction."""
        payload = {
            "id": 123456789,
            "total_tax": "5.00",
            "shipping_lines": [
                {"price": "12.50"},
            ],
            "financial_status": "paid",
        }
        result = parse_shopify_order(payload)
        assert result["total_tax"] == Decimal("5.00")
        assert result["total_shipping"] == Decimal("12.50")

    def test_customer_identity(self):
        """Test customer identity extraction."""
        payload = {
            "customer": {
                "first_name": "Maria",
                "last_name": "Garcia",
                "phone": "+15559998888",
                "email": "maria@email.com",
            }
        }
        result = parse_shopify_order(payload)
        assert result["customer_first_name"] == "Maria"
        assert result["customer_last_name"] == "Garcia"
        assert result["customer_phone"] == "+15559998888"

    def test_geographic_data(self):
        """Test geographic data extraction."""
        payload = {
            "shipping_address": {
                "city": "Los Angeles",
                "province": "CA",
                "country": "US",
                "country_code": "US",
                "zip": "90001",
            }
        }
        result = parse_shopify_order(payload)
        assert result["shipping_city"] == "Los Angeles"
        assert result["shipping_province"] == "CA"
        assert result["shipping_country"] == "US"
        assert result["shipping_postal_code"] == "90001"

    def test_payment_method(self):
        """Test payment method extraction."""
        payload = {
            "payment_gateway_names": ["credit Card"],
            "transactions": [
                {
                    "gateway": "shopify_payments",
                    "kind": "sale",
                    "status": "success",
                    "credit_card_company": "Visa",
                    "credit_card_number": "**** **** **** 4242",
                }
            ],
        }
        result = parse_shopify_order(payload)
        assert result["payment_method"] == "credit Card"
        assert result["payment_details"]["gateway"] == "shopify_payments"
        assert result["payment_details"]["credit_card_company"] == "Visa"

    def test_cancellation_data(self):
        """Test cancellation data extraction."""
        payload = {
            "cancel_reason": "customer",
            "cancelled_at": "2026-02-25T10:00:00Z",
        }
        result = parse_shopify_order(payload)
        assert result["cancel_reason"] == "customer"
        assert result["cancelled_at"] is not None
        assert result["cancelled_at"].year == 2026

    def test_cogs_tracking(self):
        """Test COGS field extraction."""
        payload = {
            "id": 123456789,
            "subtotal_price": "50.00",
            "line_items": [
                {
                    "id": 111,
                    "variant_id": 222,
                    "price": "25.00",
                    "quantity": 2,
                }
            ],
        }
        result = parse_shopify_order(payload)
        assert result["subtotal"] == Decimal("50.00")


class TestCOGSCache:
    """Test COGS caching service."""

    @pytest.mark.asyncio
    async def test_cache_get_returns_none_on_miss(self):
        """Test that cache miss returns None."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        cache = COGSCache(redis_client=mock_redis)
        result = await cache.get("variant_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test setting and getting cached COGS."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value="10.50")
        cache = COGSCache(redis_client=mock_redis)
        await cache.set("variant_123", Decimal("10.50"))
        result = await cache.get("variant_123")
        assert result == Decimal("10.50")


class TestCustomerLookupService:
    """Test customer lookup service for cross-device recognition."""

    @pytest.mark.asyncio
    async def test_find_by_email(self):
        """Test finding customer by email."""
        from app.services.customer_lookup_service import CustomerLookupService

        service = CustomerLookupService()
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.find_by_email(mock_db, 1, "test@example.com")
        assert result is None

    def test_get_personalized_greeting_first_order(self):
        """Test personalized greeting for first order."""
        from app.services.customer_lookup_service import CustomerLookupService
        from app.models.customer_profile import CustomerProfile

        service = CustomerLookupService()
        profile = MagicMock(spec=CustomerProfile)
        profile.first_name = "John"
        profile.total_orders = 1

        greeting = service.get_personalized_greeting(profile)
        assert "John" in greeting
        assert "Welcome back" in greeting

    def test_get_personalized_greeting_repeat_customer(self):
        """Test personalized greeting for repeat customer."""
        from app.services.customer_lookup_service import CustomerLookupService
        from app.models.customer_profile import CustomerProfile

        service = CustomerLookupService()
        profile = MagicMock(spec=CustomerProfile)
        profile.first_name = "Jane"
        profile.total_orders = 5

        greeting = service.get_personalized_greeting(profile)
        assert "Jane" in greeting
        assert "5 orders" in greeting
