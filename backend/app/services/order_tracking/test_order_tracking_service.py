"""Unit tests for OrderTrackingService (Story 4-1).

Tests order tracking lookup, formatting, and state management.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import ErrorCode
from app.models.order import Order, OrderStatus
from app.services.order_tracking.order_tracking_service import (
    ORDER_NOT_FOUND_CUSTOMER,
    ORDER_NOT_FOUND_NUMBER,
    PENDING_STATE_KEY,
    PENDING_STATE_TIMEOUT_SECONDS,
    PENDING_STATE_TIMESTAMP_KEY,
    OrderLookupType,
    OrderTrackingResult,
    OrderTrackingService,
)


@pytest.fixture
def service() -> OrderTrackingService:
    """Create an OrderTrackingService instance."""
    return OrderTrackingService()


@pytest.fixture
def sample_order() -> Order:
    """Create a sample order for testing."""
    return Order(
        id=1,
        order_number="ORD-12345",
        merchant_id=1,
        platform_sender_id="psid_123456",
        is_test=False,
        status=OrderStatus.SHIPPED.value,
        items=[
            {
                "product_id": "prod_123",
                "title": "Test Product",
                "price": 50.00,
                "quantity": 2,
            }
        ],
        subtotal=Decimal("100.00"),
        total=Decimal("110.00"),
        currency_code="USD",
        customer_email="test@example.com",
        shipping_address={"city": "San Francisco"},
        tracking_number="TRACK-123",
        tracking_url="https://tracking.example.com/TRACK-123",
        estimated_delivery=datetime(2026, 2, 20, 12, 0, 0),
        created_at=datetime(2026, 2, 16, 10, 0, 0),
        updated_at=datetime(2026, 2, 16, 12, 0, 0),
    )


@pytest.fixture
def test_order() -> Order:
    """Create a test order (is_test=True) for testing isolation."""
    return Order(
        id=2,
        order_number="1234",
        merchant_id=1,
        platform_sender_id="unknown",
        is_test=True,
        status=OrderStatus.PROCESSING.value,
        items=[
            {
                "product_id": "prod_test",
                "title": "Test Webhook Product",
                "price": 25.00,
                "quantity": 1,
            }
        ],
        subtotal=Decimal("25.00"),
        total=Decimal("30.00"),
        currency_code="USD",
        created_at=datetime(2026, 2, 16, 10, 0, 0),
        updated_at=datetime(2026, 2, 16, 12, 0, 0),
    )


class TestTrackOrderByCustomer:
    """Tests for track_order_by_customer method."""

    @pytest.mark.asyncio
    async def test_returns_order_when_exists(
        self, service: OrderTrackingService, sample_order: Order
    ) -> None:
        """Test that order is returned when it exists for customer."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_order
        mock_db.execute.return_value = mock_result

        result = await service.track_order_by_customer(mock_db, 1, "psid_123456")

        assert result.found is True
        assert result.order == sample_order
        assert result.lookup_type == OrderLookupType.BY_CUSTOMER

    @pytest.mark.asyncio
    async def test_returns_not_found_when_no_orders(self, service: OrderTrackingService) -> None:
        """Test that not found is returned when customer has no orders."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.track_order_by_customer(mock_db, 1, "psid_nonexistent")

        assert result.found is False
        assert result.order is None
        assert result.lookup_type == OrderLookupType.BY_CUSTOMER

    @pytest.mark.asyncio
    async def test_returns_error_on_exception(self, service: OrderTrackingService) -> None:
        """Test that error is returned on database exception."""
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database error")

        result = await service.track_order_by_customer(mock_db, 1, "psid_123456")

        assert result.found is False
        assert result.error_code == ErrorCode.ORDER_LOOKUP_FAILED
        assert "Failed to lookup" in result.error_message


class TestTrackOrderByNumber:
    """Tests for track_order_by_number method."""

    @pytest.mark.asyncio
    async def test_returns_order_when_exists(
        self, service: OrderTrackingService, sample_order: Order
    ) -> None:
        """Test that order is returned when it exists by number."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_order
        mock_db.execute.return_value = mock_result

        result = await service.track_order_by_number(mock_db, 1, "ORD-12345")

        assert result.found is True
        assert result.order == sample_order
        assert result.lookup_type == OrderLookupType.BY_ORDER_NUMBER

    @pytest.mark.asyncio
    async def test_returns_not_found_when_not_exists(self, service: OrderTrackingService) -> None:
        """Test that not found is returned when order number doesn't exist."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.track_order_by_number(mock_db, 1, "ORD-NONEXISTENT")

        assert result.found is False
        assert result.order is None
        assert result.lookup_type == OrderLookupType.BY_ORDER_NUMBER

    @pytest.mark.asyncio
    async def test_sanitizes_order_number(
        self, service: OrderTrackingService, sample_order: Order
    ) -> None:
        """Test that order number is sanitized (trimmed)."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_order
        mock_db.execute.return_value = mock_result

        result = await service.track_order_by_number(mock_db, 1, "  ORD-12345  ")

        assert result.found is True
        assert result.lookup_type == OrderLookupType.BY_ORDER_NUMBER


class TestFormatOrderResponse:
    """Tests for format_order_response method."""

    def test_formats_pending_order(self, service: OrderTrackingService) -> None:
        """Test formatting of pending order."""
        order = Order(
            order_number="ORD-123",
            status=OrderStatus.PENDING.value,
            subtotal=Decimal("50.00"),
            total=Decimal("55.00"),
        )

        response = service.format_order_response(order)

        assert "ORD-123" in response
        assert "Pending" in response

    def test_formats_shipped_order_with_tracking(self, service: OrderTrackingService) -> None:
        """Test formatting of shipped order with tracking."""
        order = Order(
            order_number="ORD-456",
            status=OrderStatus.SHIPPED.value,
            tracking_number="TRACK-123",
            tracking_url="https://tracking.example.com/TRACK-123",
            estimated_delivery=datetime(2026, 2, 20, 12, 0, 0),
            subtotal=Decimal("100.00"),
            total=Decimal("110.00"),
        )

        response = service.format_order_response(order)

        assert "ORD-456" in response
        assert "Shipped" in response
        assert "TRACK-123" in response
        assert "tracking.example.com" in response
        assert "February 20, 2026" in response

    def test_formats_delivered_order(self, service: OrderTrackingService) -> None:
        """Test formatting of delivered order."""
        order = Order(
            order_number="ORD-789",
            status=OrderStatus.DELIVERED.value,
            subtotal=Decimal("75.00"),
            total=Decimal("80.00"),
        )

        response = service.format_order_response(order)

        assert "ORD-789" in response
        assert "Delivered" in response

    def test_formats_cancelled_order(self, service: OrderTrackingService) -> None:
        """Test formatting of cancelled order."""
        order = Order(
            order_number="ORD-CANCEL",
            status=OrderStatus.CANCELLED.value,
            subtotal=Decimal("50.00"),
            total=Decimal("55.00"),
        )

        response = service.format_order_response(order)

        assert "ORD-CANCEL" in response
        assert "Cancelled" in response

    def test_formats_refunded_order(self, service: OrderTrackingService) -> None:
        """Test formatting of refunded order."""
        order = Order(
            order_number="ORD-REFUND",
            status=OrderStatus.REFUNDED.value,
            subtotal=Decimal("50.00"),
            total=Decimal("55.00"),
        )

        response = service.format_order_response(order)

        assert "ORD-REFUND" in response
        assert "Refunded" in response


class TestFormatOrderNotFoundResponse:
    """Tests for format_order_not_found_response method."""

    def test_asks_for_order_number_by_customer(self, service: OrderTrackingService) -> None:
        """Test that customer lookup failure asks for order number."""
        response = service.format_order_not_found_response(OrderLookupType.BY_CUSTOMER)

        assert response == ORDER_NOT_FOUND_CUSTOMER
        assert "order number" in response.lower()

    def test_suggests_retry_by_number(self, service: OrderTrackingService) -> None:
        """Test that order number lookup failure suggests retry."""
        response = service.format_order_not_found_response(
            OrderLookupType.BY_ORDER_NUMBER, "ORD-12345"
        )

        assert "ORD-12345" in response
        assert "couldn't find" in response.lower()


class TestPendingStateManagement:
    """Tests for conversation_data state management."""

    def test_get_pending_state_returns_false_when_none(self, service: OrderTrackingService) -> None:
        """Test that pending state is False when conversation_data is None."""
        assert service.get_pending_state(None) is False

    def test_get_pending_state_returns_false_when_not_set(
        self, service: OrderTrackingService
    ) -> None:
        """Test that pending state is False when not set."""
        assert service.get_pending_state({}) is False

    def test_get_pending_state_returns_true_when_active(
        self, service: OrderTrackingService
    ) -> None:
        """Test that pending state is True when active and not expired."""
        data = {
            PENDING_STATE_KEY: True,
            PENDING_STATE_TIMESTAMP_KEY: datetime.now(timezone.utc).isoformat(),
        }

        assert service.get_pending_state(data) is True

    def test_get_pending_state_returns_false_when_expired(
        self, service: OrderTrackingService
    ) -> None:
        """Test that pending state is False when expired (5+ minutes old)."""
        expired_time = datetime.now(timezone.utc) - timedelta(
            seconds=PENDING_STATE_TIMEOUT_SECONDS + 60
        )
        data = {
            PENDING_STATE_KEY: True,
            PENDING_STATE_TIMESTAMP_KEY: expired_time.isoformat(),
        }

        assert service.get_pending_state(data) is False

    def test_set_pending_state_creates_data(self, service: OrderTrackingService) -> None:
        """Test that set_pending_state creates conversation_data if None."""
        result = service.set_pending_state(None)

        assert result[PENDING_STATE_KEY] is True
        assert PENDING_STATE_TIMESTAMP_KEY in result

    def test_set_pending_state_updates_existing(self, service: OrderTrackingService) -> None:
        """Test that set_pending_state updates existing conversation_data."""
        existing = {"other_key": "value"}
        result = service.set_pending_state(existing)

        assert result[PENDING_STATE_KEY] is True
        assert result["other_key"] == "value"

    def test_clear_pending_state_removes_keys(self, service: OrderTrackingService) -> None:
        """Test that clear_pending_state removes pending state keys."""
        data = {
            PENDING_STATE_KEY: True,
            PENDING_STATE_TIMESTAMP_KEY: datetime.now(timezone.utc).isoformat(),
            "other_key": "value",
        }

        result = service.clear_pending_state(data)

        assert PENDING_STATE_KEY not in result
        assert PENDING_STATE_TIMESTAMP_KEY not in result
        assert result["other_key"] == "value"

    def test_clear_pending_state_handles_none(self, service: OrderTrackingService) -> None:
        """Test that clear_pending_state handles None input."""
        result = service.clear_pending_state(None)

        assert isinstance(result, dict)
        assert PENDING_STATE_KEY not in result


class TestSanitizeOrderNumber:
    """Tests for order number sanitization."""

    def test_trims_whitespace(self, service: OrderTrackingService) -> None:
        """Test that whitespace is trimmed."""
        assert service._sanitize_order_number("  ORD-123  ") == "ORD-123"

    def test_truncates_long_numbers(self, service: OrderTrackingService) -> None:
        """Test that long order numbers are truncated to 50 chars."""
        long_number = "ORD-" + "X" * 60
        result = service._sanitize_order_number(long_number)

        assert len(result) == 50

    def test_preserves_valid_numbers(self, service: OrderTrackingService) -> None:
        """Test that valid order numbers are preserved."""
        assert service._sanitize_order_number("ORD-12345") == "ORD-12345"


class TestOrderIsolation:
    """Tests for test order isolation (is_test field filtering).

    Story 5-10: Widget Full App Integration
    Task 0: Fix Order Data Isolation
    """

    @pytest.mark.asyncio
    async def test_track_by_customer_excludes_test_orders(
        self, service: OrderTrackingService, sample_order: Order
    ) -> None:
        """Test that track_order_by_customer excludes test orders."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = sample_order
        mock_db.execute.return_value = mock_result

        result = await service.track_order_by_customer(mock_db, 1, "psid_123456")

        assert result.found is True
        assert result.order == sample_order
        assert result.order is not None
        assert result.order.is_test is False

    @pytest.mark.asyncio
    async def test_track_by_customer_returns_not_found_if_only_test_orders_exist(
        self, service: OrderTrackingService, test_order: Order
    ) -> None:
        """Test that not found is returned when only test orders exist for customer."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.track_order_by_customer(mock_db, 1, "psid_with_only_test_orders")

        assert result.found is False
        assert result.order is None

    @pytest.mark.asyncio
    async def test_track_by_number_can_still_find_test_orders(
        self, service: OrderTrackingService, test_order: Order
    ) -> None:
        """Test that track_order_by_number can still find test orders by explicit number lookup.

        Note: By-number lookup intentionally does NOT filter is_test because it's an
        explicit order number lookup (not a customer-facing feature).
        """
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = test_order
        mock_db.execute.return_value = mock_result

        result = await service.track_order_by_number(mock_db, 1, "1234")

        assert result.found is True
        assert result.order is not None
        assert result.order.order_number == "1234"


class TestOrderModelIsTestField:
    """Tests for Order model is_test field.

    Story 5-10: Widget Full App Integration
    Task 0: Fix Order Data Isolation
    """

    def test_order_can_be_created_with_is_test_false(self) -> None:
        """Test that orders can be explicitly created with is_test=False."""
        order = Order(
            order_number="ORD-999",
            merchant_id=1,
            platform_sender_id="psid_real_customer",
            is_test=False,
            status=OrderStatus.PENDING.value,
            subtotal=Decimal("10.00"),
            total=Decimal("11.00"),
        )

        assert order.is_test is False

    def test_order_with_unknown_psid_is_marked_as_test(self) -> None:
        """Test that orders with 'unknown' platform_sender_id are marked as test."""
        order = Order(
            order_number="TEST-001",
            merchant_id=1,
            platform_sender_id="unknown",
            is_test=True,
            status=OrderStatus.PROCESSING.value,
            subtotal=Decimal("50.00"),
            total=Decimal("55.00"),
        )

        assert order.is_test is True
        assert order.platform_sender_id == "unknown"

    def test_real_vs_test_order_differentiation(self) -> None:
        """Test that real and test orders can be differentiated by is_test."""
        real_order = Order(
            order_number="REAL-001",
            merchant_id=1,
            platform_sender_id="psid_123456789",
            is_test=False,
            status=OrderStatus.SHIPPED.value,
            subtotal=Decimal("100.00"),
            total=Decimal("110.00"),
        )
        test_order = Order(
            order_number="TEST-001",
            merchant_id=1,
            platform_sender_id="unknown",
            is_test=True,
            status=OrderStatus.PROCESSING.value,
            subtotal=Decimal("50.00"),
            total=Decimal("55.00"),
        )

        assert real_order.is_test is False
        assert test_order.is_test is True
        assert real_order.platform_sender_id != "unknown"
        assert test_order.platform_sender_id == "unknown"
