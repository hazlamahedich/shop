"""Unit tests for Shopify order processor.

Story 4-2: Shopify Webhook Integration
Task 7: Unit tests for order_processor.py

Tests:
- parse_shopify_order extracts all required fields
- resolve_customer_psid from note_attributes, custom_attributes
- map_shopify_status_to_order_status mapping
- upsert_order creates/updates orders with idempotency
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.services.shopify.order_processor import (
    map_shopify_status_to_order_status,
    parse_shopify_order,
    resolve_customer_psid,
    upsert_order,
)
from app.services.shopify.dlq_retry_worker import (
    DLQRetryWorker,
    BACKOFF_DELAYS,
    MAX_RETRY_ATTEMPTS,
)


def create_shopify_payload(
    order_id: int = 123456789,
    order_number: int = 1001,
    email: str = "customer@example.com",
    financial_status: str = "paid",
    fulfillment_status: str | None = None,
    tracking_number: str | None = None,
    note_attributes: list | None = None,
    custom_attributes: list | None = None,
    updated_at: str = "2026-02-17T10:00:00Z",
) -> dict:
    """Create a Shopify order webhook payload for testing."""
    payload = {
        "id": order_id,
        "order_number": order_number,
        "name": f"#{order_number}",
        "email": email,
        "financial_status": financial_status,
        "customer": {
            "id": 987654321,
            "email": email,
            "first_name": "John",
            "last_name": "Doe",
        },
        "line_items": [
            {
                "id": 111,
                "title": "Test Product",
                "quantity": 2,
                "price": "29.99",
                "variant_id": 222,
                "product_id": 333,
            }
        ],
        "subtotal_price": "59.98",
        "total_price": "64.98",
        "current_subtotal_price": "59.98",
        "current_total_price": "64.98",
        "currency": "USD",
        "shipping_address": {
            "first_name": "John",
            "last_name": "Doe",
            "address1": "123 Main St",
            "city": "San Francisco",
            "province": "CA",
            "country": "US",
            "zip": "94102",
        },
        "created_at": "2026-02-17T09:00:00Z",
        "updated_at": updated_at,
    }

    if fulfillment_status:
        payload["fulfillment_status"] = fulfillment_status

    if tracking_number:
        payload["tracking_numbers"] = [tracking_number]
        payload["tracking_number"] = tracking_number
        payload["tracking_url"] = f"https://tracking.example.com/{tracking_number}"
        payload["fulfillments"] = [
            {
                "id": 999,
                "tracking_number": tracking_number,
                "tracking_url": f"https://tracking.example.com/{tracking_number}",
            }
        ]

    if note_attributes is not None:
        payload["note_attributes"] = note_attributes

    if custom_attributes is not None:
        payload["custom_attributes"] = custom_attributes

    return payload


class TestParseShopifyOrder:
    """Tests for parse_shopify_order function."""

    def test_parse_extracts_all_required_fields(self) -> None:
        """Test that parse_shopify_order extracts all required fields."""
        payload = create_shopify_payload(
            order_id=123456789,
            order_number=1001,
            email="test@example.com",
            financial_status="paid",
            tracking_number="TRACK123",
        )

        result = parse_shopify_order(payload)

        assert result["shopify_order_id"] == "gid://shopify/Order/123456789"
        assert result["shopify_order_key"] == 1001
        assert result["order_number"] == 1001
        assert result["financial_status"] == "paid"
        assert result["customer_email"] == "test@example.com"
        assert result["tracking_number"] == "TRACK123"
        assert result["currency_code"] == "USD"
        assert result["subtotal"] == Decimal("59.98")
        assert result["total"] == Decimal("64.98")
        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "Test Product"
        assert result["shipping_address"]["city"] == "San Francisco"

    def test_parse_handles_missing_optional_fields(self) -> None:
        """Test parsing payload with missing optional fields."""
        payload = {
            "id": 123,
            "email": "minimal@example.com",
        }

        result = parse_shopify_order(payload)

        assert result["shopify_order_id"] == "gid://shopify/Order/123"
        assert result["financial_status"] is None
        assert result["fulfillment_status"] is None
        assert result["tracking_number"] is None
        assert result["subtotal"] == Decimal("0")
        assert result["total"] == Decimal("0")

    def test_parse_extracts_tracking_from_fulfillments_with_tracking_number(
        self,
    ) -> None:
        """Test tracking URL extraction from fulfillments when tracking number is present."""
        payload = create_shopify_payload(tracking_number="FULFILL123")
        payload["tracking_url"] = None
        payload["fulfillments"] = [
            {
                "tracking_number": "FULFILL123",
                "tracking_url": "https://track.co/FULFILL123",
            }
        ]

        result = parse_shopify_order(payload)

        assert result["tracking_number"] == "FULFILL123"
        assert result["tracking_url"] == "https://track.co/FULFILL123"

    def test_parse_converts_updated_at_timestamp(self) -> None:
        """Test Shopify timestamp conversion to datetime."""
        payload = create_shopify_payload(updated_at="2026-02-17T15:30:00Z")

        result = parse_shopify_order(payload)

        assert result["shopify_updated_at"] is not None
        assert result["shopify_updated_at"].year == 2026
        assert result["shopify_updated_at"].month == 2
        assert result["shopify_updated_at"].day == 17

    def test_parse_handles_order_number_from_name(self) -> None:
        """Test order_number fallback to name field."""
        payload = {"id": 123, "name": "#1001"}

        result = parse_shopify_order(payload)

        assert result["order_number"] == "#1001"


class TestMapShopifyStatusToOrderStatus:
    """Tests for Shopify status to OrderStatus mapping."""

    @pytest.mark.parametrize(
        "financial,fulfillment,expected",
        [
            ("pending", None, OrderStatus.PENDING),
            ("authorized", None, OrderStatus.CONFIRMED),
            ("paid", None, OrderStatus.PROCESSING),
            ("paid", "fulfilled", OrderStatus.SHIPPED),
            ("cancelled", None, OrderStatus.CANCELLED),
            ("refunded", None, OrderStatus.REFUNDED),
            ("void", None, OrderStatus.CANCELLED),
            ("partially_paid", None, OrderStatus.PROCESSING),
            ("partially_paid", "fulfilled", OrderStatus.SHIPPED),
        ],
    )
    def test_status_mapping(
        self, financial: str, fulfillment: str | None, expected: OrderStatus
    ) -> None:
        """Test Shopify financial/fulfillment status maps to correct OrderStatus."""
        result = map_shopify_status_to_order_status(financial, fulfillment)
        assert result == expected

    def test_status_mapping_case_insensitive(self) -> None:
        """Test status mapping is case insensitive."""
        assert map_shopify_status_to_order_status("PAID", None) == OrderStatus.PROCESSING
        assert map_shopify_status_to_order_status("Paid", "FULFILLED") == OrderStatus.SHIPPED

    def test_status_mapping_defaults_to_processing(self) -> None:
        """Test unknown status defaults to PROCESSING."""
        result = map_shopify_status_to_order_status("unknown_status", None)
        assert result == OrderStatus.PROCESSING

    def test_status_mapping_empty_financial_defaults_to_pending(self) -> None:
        """Test empty financial status defaults to PENDING."""
        result = map_shopify_status_to_order_status(None, None)
        assert result == OrderStatus.PENDING


class TestResolveCustomerPsid:
    """Tests for customer PSID resolution."""

    @pytest.mark.asyncio
    async def test_resolve_from_note_attributes(self) -> None:
        """Test PSID resolution from note_attributes."""
        payload = create_shopify_payload(
            note_attributes=[{"name": "messenger_psid", "value": "1234567890123456"}]
        )

        mock_db = AsyncMock(spec=AsyncSession)

        result = await resolve_customer_psid(payload, mock_db, merchant_id=1)

        assert result == "1234567890123456"

    @pytest.mark.asyncio
    async def test_resolve_from_custom_attributes(self) -> None:
        """Test PSID resolution from custom_attributes."""
        payload = create_shopify_payload(
            custom_attributes=[{"name": "messenger_psid", "value": "9876543210987654"}]
        )

        mock_db = AsyncMock(spec=AsyncSession)

        result = await resolve_customer_psid(payload, mock_db, merchant_id=1)

        assert result == "9876543210987654"

    @pytest.mark.asyncio
    async def test_resolve_returns_none_when_not_in_attributes(self) -> None:
        """Test PSID resolution returns None when no messenger_psid in attributes."""
        payload = create_shopify_payload(email="notfound@example.com")
        payload.pop("note_attributes", None)
        payload.pop("custom_attributes", None)

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await resolve_customer_psid(payload, mock_db, merchant_id=1)

        assert result is None

    @pytest.mark.asyncio
    async def test_resolve_note_attributes_takes_precedence(self) -> None:
        """Test note_attributes takes precedence over other methods."""
        payload = create_shopify_payload(
            email="lookup@example.com",
            note_attributes=[{"name": "messenger_psid", "value": "note_psid"}],
        )

        mock_db = AsyncMock(spec=AsyncSession)

        result = await resolve_customer_psid(payload, mock_db, merchant_id=1)

        assert result == "note_psid"

    @pytest.mark.asyncio
    async def test_resolve_handles_empty_psid_value(self) -> None:
        """Test PSID resolution handles empty value gracefully."""
        payload = create_shopify_payload(note_attributes=[{"name": "messenger_psid", "value": ""}])

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await resolve_customer_psid(payload, mock_db, merchant_id=1)

        assert result is None


class TestUpsertOrder:
    """Tests for order upsert with idempotency."""

    @pytest.mark.asyncio
    async def test_upsert_creates_new_order(self) -> None:
        """Test upsert_order creates a new order when none exists."""
        payload = create_shopify_payload()
        order_data = parse_shopify_order(payload)

        mock_order = MagicMock()
        mock_order.id = 1
        mock_order.shopify_order_id = order_data["shopify_order_id"]
        mock_order.status = OrderStatus.PROCESSING.value

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with (
            patch("app.services.shopify.order_processor.select") as mock_select,
            patch("app.services.shopify.order_processor.Order") as MockOrder,
        ):
            mock_select.return_value.where.return_value = MagicMock()
            MockOrder.return_value = mock_order

            result = await upsert_order(
                mock_db, order_data, merchant_id=1, platform_sender_id="psid123"
            )

            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_order(self) -> None:
        """Test upsert_order updates existing order (idempotency)."""
        payload = create_shopify_payload(
            financial_status="paid",
            fulfillment_status="fulfilled",
            tracking_number="TRACK999",
        )
        order_data = parse_shopify_order(payload)

        mock_existing = MagicMock()
        mock_existing.shopify_order_id = order_data["shopify_order_id"]
        mock_existing.shopify_updated_at = datetime(2026, 2, 17, 9, 0, 0, tzinfo=timezone.utc)
        mock_existing.status = OrderStatus.PROCESSING.value
        mock_existing.fulfillment_status = None
        mock_existing.tracking_number = None
        mock_existing.tracking_url = None
        mock_existing.items = None
        mock_existing.subtotal = Decimal("0")
        mock_existing.total = Decimal("0")
        mock_existing.platform_sender_id = "psid123"
        mock_existing.id = 1

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_existing

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("app.services.shopify.order_processor.select") as mock_select:
            mock_select.return_value.where.return_value = MagicMock()

            result = await upsert_order(
                mock_db, order_data, merchant_id=1, platform_sender_id="psid123"
            )

            assert result.fulfillment_status == "fulfilled"
            assert result.tracking_number == "TRACK999"
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_preserves_psid_on_update(self) -> None:
        """Test upsert preserves existing PSID when new PSID is None."""
        payload = create_shopify_payload()
        order_data = parse_shopify_order(payload)

        mock_existing = MagicMock()
        mock_existing.shopify_order_id = order_data["shopify_order_id"]
        mock_existing.shopify_updated_at = datetime(2026, 2, 17, 9, 0, 0, tzinfo=timezone.utc)
        mock_existing.status = OrderStatus.PROCESSING.value
        mock_existing.fulfillment_status = None
        mock_existing.tracking_number = None
        mock_existing.tracking_url = None
        mock_existing.items = None
        mock_existing.subtotal = Decimal("0")
        mock_existing.total = Decimal("0")
        mock_existing.platform_sender_id = "existing_psid"
        mock_existing.id = 1

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_existing

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("app.services.shopify.order_processor.select") as mock_select:
            mock_select.return_value.where.return_value = MagicMock()

            result = await upsert_order(mock_db, order_data, merchant_id=1, platform_sender_id=None)

            assert result.platform_sender_id == "existing_psid"

    @pytest.mark.asyncio
    async def test_upsert_skips_older_webhook(self) -> None:
        """Test upsert skips update when incoming webhook is older."""
        payload = create_shopify_payload(updated_at="2026-02-17T09:00:00Z")
        order_data = parse_shopify_order(payload)

        mock_existing = MagicMock()
        mock_existing.shopify_order_id = order_data["shopify_order_id"]
        mock_existing.shopify_updated_at = datetime(2026, 2, 17, 10, 0, 0, tzinfo=timezone.utc)
        mock_existing.status = OrderStatus.SHIPPED.value
        mock_existing.id = 1

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_existing

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        with patch("app.services.shopify.order_processor.select") as mock_select:
            mock_select.return_value.where.return_value = MagicMock()

            result = await upsert_order(mock_db, order_data, merchant_id=1)

            assert result.status == OrderStatus.SHIPPED.value
            mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_rolls_back_on_error(self) -> None:
        """Test upsert rolls back transaction on error."""
        order_data = {"shopify_order_id": "gid://shopify/Order/123"}

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute.side_effect = Exception("Database error")
        mock_db.rollback = AsyncMock()

        with pytest.raises(Exception):
            await upsert_order(mock_db, order_data, merchant_id=1)

        mock_db.rollback.assert_called_once()


class TestDLQRetryWorker:
    """Tests for DLQ retry worker."""

    def test_backoff_delays_are_correct(self) -> None:
        """Test exponential backoff delays are 1m, 5m, 15m."""
        assert BACKOFF_DELAYS == [60, 300, 900]

    def test_max_retry_attempts_is_three(self) -> None:
        """Test max retry attempts is 3."""
        assert MAX_RETRY_ATTEMPTS == 3

    def test_should_retry_returns_true_for_old_entry(self) -> None:
        """Test should_retry returns True for DLQ entry older than backoff."""
        worker = DLQRetryWorker()
        from datetime import timedelta

        old_timestamp = (datetime.utcnow() - timedelta(minutes=2)).isoformat()
        retry_data = {
            "attempts": 0,
            "timestamp": old_timestamp,
        }

        should_retry, retry_after = worker._should_retry(retry_data)

        assert should_retry is True
        assert retry_after == 0

    def test_should_retry_returns_false_after_max_attempts(self) -> None:
        """Test should_retry returns False after max attempts."""
        worker = DLQRetryWorker()
        retry_data = {
            "attempts": 3,
            "timestamp": datetime.utcnow().isoformat(),
        }

        should_retry, retry_after = worker._should_retry(retry_data)

        assert should_retry is False

    def test_should_retry_applies_backoff_delay(self) -> None:
        """Test should_retry applies backoff delay for recent failures."""
        worker = DLQRetryWorker()
        retry_data = {
            "attempts": 1,
            "timestamp": datetime.utcnow().isoformat(),
        }

        should_retry, retry_after = worker._should_retry(retry_data)

        assert should_retry is True
        assert retry_after > 0

    def test_get_dlq_metrics_returns_expected_structure(self) -> None:
        """Test get_dlq_metrics returns expected structure."""
        worker = DLQRetryWorker()

        with patch.object(worker, "get_dlq_size", return_value=5):
            metrics = worker.get_dlq_metrics()

            assert "dlq_size" in metrics
            assert "dlq_healthy" in metrics
            assert "max_retries" in metrics
            assert "backoff_delays_seconds" in metrics
            assert metrics["dlq_size"] == 5
            assert metrics["max_retries"] == 3

    def test_should_retry_missing_timestamp(self) -> None:
        """Test should_retry handles missing timestamp gracefully."""
        worker = DLQRetryWorker()
        retry_data = {"attempts": 0}

        should_retry, retry_after = worker._should_retry(retry_data)

        assert should_retry is True
        assert retry_after == 0
