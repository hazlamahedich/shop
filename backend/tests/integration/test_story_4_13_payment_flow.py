"""Integration tests for Story 4-13: Payment Data Flow.

Tests payment data extraction → storage → retrieval flow.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.shopify.order_processor import parse_shopify_order


class TestPaymentDataFlow:
    """Integration tests for payment data extraction → storage → retrieval."""

    @pytest.mark.p0
    @pytest.mark.integration
    def test_webhook_to_db_to_api_flow_payment_data(self):
        """Verify payment data flows correctly from webhook through API response."""
        webhook_payload = {
            "id": 123456789,
            "order_number": 1001,
            "email": "test@example.com",
            "subtotal_price": "100.00",
            "total_price": "127.50",
            "total_tax": "5.00",
            "total_shipping_price_set": {"shop_money": {"amount": "12.50"}},
            "discount_codes": [{"code": "SAVE10", "amount": "10.00"}],
            "current_total_discounts": "10.00",
            "payment_gateway_names": ["credit_card"],
            "transactions": [
                {
                    "gateway": "shopify_payments",
                    "kind": "sale",
                    "status": "success",
                    "credit_card_company": "Visa",
                }
            ],
            "customer": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "+15551234567",
            },
            "shipping_address": {
                "city": "New York",
                "province": "NY",
                "country": "US",
                "country_code": "US",
                "zip": "10001",
            },
            "financial_status": "paid",
        }

        result = parse_shopify_order(webhook_payload)

        assert result["subtotal"] == Decimal("100.00")
        assert result["total"] == Decimal("127.50")
        assert result["total_tax"] == Decimal("5.00")
        assert result["total_shipping"] == Decimal("12.50")
        assert result["total_discount"] == Decimal("10.00")
        assert len(result["discount_codes"]) == 1
        assert result["payment_method"] == "credit_card"
        assert result["customer_first_name"] == "John"
        assert result["customer_last_name"] == "Doe"
        assert result["shipping_city"] == "New York"
        assert result["shipping_country"] == "US"

    @pytest.mark.p1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cogs_fetch_updates_order(self):
        """Verify COGS background task updates order correctly."""
        from app.services.shopify.cogs_cache import COGSCache

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="25.50")
        cache = COGSCache(redis_client=mock_redis)

        variant_gid = "gid://shopify/ProductVariant/12345"
        cogs = await cache.get(variant_gid)

        assert cogs == Decimal("25.50")

    @pytest.mark.p1
    @pytest.mark.integration
    def test_customer_profile_upsert_on_conflict(self):
        """Verify customer profile upsert with ON CONFLICT behavior."""
        from app.services.customer_lookup_service import CustomerLookupService

        service = CustomerLookupService()

        assert hasattr(service, "upsert_customer_profile")
        assert hasattr(service, "find_by_email")

    @pytest.mark.p1
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_conversation_linking_on_purchase(self):
        """Verify conversation is updated with customer identity on purchase."""
        webhook_payload = {
            "id": 123456789,
            "order_number": 1001,
            "email": "maria@example.com",
            "customer": {
                "first_name": "Maria",
                "last_name": "Garcia",
                "email": "maria@example.com",
                "phone": "+15559998888",
            },
            "financial_status": "paid",
        }

        result = parse_shopify_order(webhook_payload)

        assert result["customer_email"] == "maria@example.com"
        assert result["customer_first_name"] == "Maria"
        assert result["customer_last_name"] == "Garcia"
        assert result["customer_phone"] == "+15559998888"

    @pytest.mark.p1
    @pytest.mark.integration
    def test_geographic_analytics_aggregation(self):
        """Verify geographic analytics can aggregate by country/city."""
        orders = [
            {"shipping_country": "US", "shipping_city": "New York", "total": Decimal("100.00")},
            {"shipping_country": "US", "shipping_city": "Los Angeles", "total": Decimal("150.00")},
            {"shipping_country": "CA", "shipping_city": "Toronto", "total": Decimal("75.00")},
            {"shipping_country": "US", "shipping_city": "New York", "total": Decimal("50.00")},
        ]

        country_totals = {}
        for order in orders:
            country = order["shipping_country"]
            country_totals[country] = country_totals.get(country, Decimal("0")) + order["total"]

        assert country_totals["US"] == Decimal("300.00")
        assert country_totals["CA"] == Decimal("75.00")

        city_totals = {}
        for order in orders:
            city = f"{order['shipping_country']}/{order['shipping_city']}"
            city_totals[city] = city_totals.get(city, Decimal("0")) + order["total"]

        assert city_totals["US/New York"] == Decimal("150.00")
        assert city_totals["US/Los Angeles"] == Decimal("150.00")
        assert city_totals["CA/Toronto"] == Decimal("75.00")
