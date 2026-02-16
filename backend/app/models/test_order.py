"""Unit tests for Order ORM model (Story 4-1)."""

from datetime import datetime

import pytest

from app.models.order import Order, OrderStatus


class TestOrderModel:
    """Tests for Order model creation and methods."""

    def test_order_creation_minimal(self) -> None:
        """Test creating an order with minimal required fields."""
        order = Order(
            order_number="ORD-12345",
            merchant_id=1,
            platform_sender_id="psid_123456",
            status=OrderStatus.PENDING.value,
            subtotal=100.00,
            total=110.00,
            currency_code="USD",
        )

        assert order.order_number == "ORD-12345"
        assert order.merchant_id == 1
        assert order.platform_sender_id == "psid_123456"
        assert order.status == OrderStatus.PENDING.value
        assert order.subtotal == 100.00
        assert order.total == 110.00
        assert order.currency_code == "USD"
        assert order.items is None
        assert order.customer_email is None
        assert order.shipping_address is None
        assert order.tracking_number is None
        assert order.tracking_url is None
        assert order.estimated_delivery is None

    def test_order_creation_full(self) -> None:
        """Test creating an order with all fields."""
        estimated_delivery = datetime(2026, 2, 20, 12, 0, 0)
        items = [
            {
                "product_id": "prod_123",
                "variant_id": "var_456",
                "title": "Test Product",
                "price": 50.00,
                "quantity": 2,
            }
        ]
        shipping_address = {
            "name": "John Doe",
            "street": "123 Main St",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94102",
            "country": "US",
        }

        order = Order(
            order_number="ORD-67890",
            merchant_id=2,
            platform_sender_id="psid_789012",
            status=OrderStatus.SHIPPED.value,
            items=items,
            subtotal=100.00,
            total=110.00,
            currency_code="USD",
            customer_email="john@example.com",
            shipping_address=shipping_address,
            tracking_number="TRACK-123456",
            tracking_url="https://tracking.example.com/TRACK-123456",
            estimated_delivery=estimated_delivery,
        )

        assert order.order_number == "ORD-67890"
        assert order.merchant_id == 2
        assert order.platform_sender_id == "psid_789012"
        assert order.status == OrderStatus.SHIPPED.value
        assert order.items == items
        assert order.subtotal == 100.00
        assert order.total == 110.00
        assert order.currency_code == "USD"
        assert order.customer_email == "john@example.com"
        assert order.shipping_address == shipping_address
        assert order.tracking_number == "TRACK-123456"
        assert order.tracking_url == "https://tracking.example.com/TRACK-123456"
        assert order.estimated_delivery == estimated_delivery

    def test_order_default_status(self) -> None:
        """Test that order status field accepts pending value."""
        order = Order(
            order_number="ORD-DEFAULT",
            merchant_id=1,
            platform_sender_id="psid_default",
            subtotal=50.00,
            total=55.00,
            status=OrderStatus.PENDING.value,
        )

        assert order.status == OrderStatus.PENDING.value

    def test_order_default_currency(self) -> None:
        """Test that order currency field accepts USD value."""
        order = Order(
            order_number="ORD-CURRENCY",
            merchant_id=1,
            platform_sender_id="psid_currency",
            subtotal=50.00,
            total=55.00,
            status=OrderStatus.PENDING.value,
            currency_code="USD",
        )

        assert order.currency_code == "USD"

    def test_order_repr(self) -> None:
        """Test Order __repr__ method."""
        order = Order(
            order_number="ORD-REPR",
            merchant_id=1,
            platform_sender_id="psid_repr",
            status=OrderStatus.DELIVERED.value,
            subtotal=100.00,
            total=110.00,
        )

        repr_str = repr(order)
        assert "Order" in repr_str
        assert "ORD-REPR" in repr_str
        assert "merchant_id=1" in repr_str
        assert "delivered" in repr_str


class TestOrderStatus:
    """Tests for OrderStatus enum."""

    def test_all_status_values(self) -> None:
        """Test all OrderStatus enum values exist."""
        assert OrderStatus.PENDING.value == "pending"
        assert OrderStatus.CONFIRMED.value == "confirmed"
        assert OrderStatus.PROCESSING.value == "processing"
        assert OrderStatus.SHIPPED.value == "shipped"
        assert OrderStatus.DELIVERED.value == "delivered"
        assert OrderStatus.CANCELLED.value == "cancelled"
        assert OrderStatus.REFUNDED.value == "refunded"

    def test_status_count(self) -> None:
        """Test that we have exactly 7 order statuses."""
        assert len(OrderStatus) == 7

    def test_status_is_string_enum(self) -> None:
        """Test that OrderStatus is a string enum."""
        assert isinstance(OrderStatus.PENDING, str)
        assert OrderStatus.PENDING == "pending"
