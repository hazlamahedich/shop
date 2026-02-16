"""Mock orders for testing order tracking (Story 4-1).

Provides test data for order tracking functionality.
Real Shopify webhook integration will be added in Story 4-2.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus


class MockOrderFactory:
    """Factory for creating mock orders for testing.

    Creates realistic test orders with various statuses for validating
    order tracking functionality without requiring real Shopify data.
    """

    @staticmethod
    def create_pending_order(
        merchant_id: int,
        platform_sender_id: str,
        order_number: str = "ORD-PENDING-001",
    ) -> Order:
        """Create a pending order.

        Args:
            merchant_id: Merchant ID
            platform_sender_id: Customer's platform sender ID
            order_number: Order number (auto-generated if not provided)

        Returns:
            Order with PENDING status
        """
        return Order(
            order_number=order_number,
            merchant_id=merchant_id,
            platform_sender_id=platform_sender_id,
            status=OrderStatus.PENDING.value,
            items=[
                {
                    "product_id": "prod_001",
                    "variant_id": "var_001",
                    "title": "Premium Widget",
                    "price": 29.99,
                    "quantity": 2,
                }
            ],
            subtotal=Decimal("59.98"),
            total=Decimal("64.98"),
            currency_code="USD",
            customer_email="customer@example.com",
            shipping_address={
                "name": "John Doe",
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94102",
                "country": "US",
            },
            created_at=datetime.utcnow() - timedelta(hours=1),
            updated_at=datetime.utcnow() - timedelta(hours=1),
        )

    @staticmethod
    def create_confirmed_order(
        merchant_id: int,
        platform_sender_id: str,
        order_number: str = "ORD-CONFIRMED-001",
    ) -> Order:
        """Create a confirmed order.

        Args:
            merchant_id: Merchant ID
            platform_sender_id: Customer's platform sender ID
            order_number: Order number (auto-generated if not provided)

        Returns:
            Order with CONFIRMED status
        """
        return Order(
            order_number=order_number,
            merchant_id=merchant_id,
            platform_sender_id=platform_sender_id,
            status=OrderStatus.CONFIRMED.value,
            items=[
                {
                    "product_id": "prod_conf_001",
                    "variant_id": "var_conf_001",
                    "title": "Confirmed Bundle",
                    "price": 79.99,
                    "quantity": 1,
                }
            ],
            subtotal=Decimal("79.99"),
            total=Decimal("84.99"),
            currency_code="USD",
            customer_email="customer@example.com",
            shipping_address={
                "name": "John Doe",
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94102",
                "country": "US",
            },
            created_at=datetime.utcnow() - timedelta(hours=2),
            updated_at=datetime.utcnow() - timedelta(hours=1),
        )

    @staticmethod
    def create_processing_order(
        merchant_id: int,
        platform_sender_id: str,
        order_number: str = "ORD-PROCESSING-001",
    ) -> Order:
        """Create a processing order.

        Args:
            merchant_id: Merchant ID
            platform_sender_id: Customer's platform sender ID
            order_number: Order number (auto-generated if not provided)

        Returns:
            Order with PROCESSING status
        """
        return Order(
            order_number=order_number,
            merchant_id=merchant_id,
            platform_sender_id=platform_sender_id,
            status=OrderStatus.PROCESSING.value,
            items=[
                {
                    "product_id": "prod_002",
                    "variant_id": "var_002",
                    "title": "Deluxe Gadget",
                    "price": 49.99,
                    "quantity": 1,
                }
            ],
            subtotal=Decimal("49.99"),
            total=Decimal("54.99"),
            currency_code="USD",
            customer_email="customer@example.com",
            shipping_address={
                "name": "John Doe",
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94102",
                "country": "US",
            },
            created_at=datetime.utcnow() - timedelta(days=1),
            updated_at=datetime.utcnow() - timedelta(hours=12),
        )

    @staticmethod
    def create_shipped_order(
        merchant_id: int,
        platform_sender_id: str,
        order_number: str = "ORD-SHIPPED-001",
        tracking_number: str = "TRACK-123456",
        tracking_url: str = "https://tracking.example.com/TRACK-123456",
    ) -> Order:
        """Create a shipped order.

        Args:
            merchant_id: Merchant ID
            platform_sender_id: Customer's platform sender ID
            order_number: Order number (auto-generated if not provided)
            tracking_number: Tracking number
            tracking_url: Tracking URL

        Returns:
            Order with SHIPPED status and tracking info
        """
        return Order(
            order_number=order_number,
            merchant_id=merchant_id,
            platform_sender_id=platform_sender_id,
            status=OrderStatus.SHIPPED.value,
            items=[
                {
                    "product_id": "prod_003",
                    "variant_id": "var_003",
                    "title": "Super Accessory",
                    "price": 19.99,
                    "quantity": 3,
                }
            ],
            subtotal=Decimal("59.97"),
            total=Decimal("69.97"),
            currency_code="USD",
            customer_email="customer@example.com",
            shipping_address={
                "name": "John Doe",
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94102",
                "country": "US",
            },
            tracking_number=tracking_number,
            tracking_url=tracking_url,
            estimated_delivery=datetime.utcnow() + timedelta(days=3),
            created_at=datetime.utcnow() - timedelta(days=2),
            updated_at=datetime.utcnow() - timedelta(hours=6),
        )

    @staticmethod
    def create_delivered_order(
        merchant_id: int,
        platform_sender_id: str,
        order_number: str = "ORD-DELIVERED-001",
    ) -> Order:
        """Create a delivered order.

        Args:
            merchant_id: Merchant ID
            platform_sender_id: Customer's platform sender ID
            order_number: Order number (auto-generated if not provided)

        Returns:
            Order with DELIVERED status
        """
        return Order(
            order_number=order_number,
            merchant_id=merchant_id,
            platform_sender_id=platform_sender_id,
            status=OrderStatus.DELIVERED.value,
            items=[
                {
                    "product_id": "prod_004",
                    "variant_id": "var_004",
                    "title": "Mega Bundle",
                    "price": 99.99,
                    "quantity": 1,
                }
            ],
            subtotal=Decimal("99.99"),
            total=Decimal("109.99"),
            currency_code="USD",
            customer_email="customer@example.com",
            shipping_address={
                "name": "John Doe",
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip": "94102",
                "country": "US",
            },
            tracking_number="TRACK-789012",
            tracking_url="https://tracking.example.com/TRACK-789012",
            estimated_delivery=datetime.utcnow() - timedelta(days=1),
            created_at=datetime.utcnow() - timedelta(days=5),
            updated_at=datetime.utcnow() - timedelta(days=1),
        )

    @staticmethod
    def create_cancelled_order(
        merchant_id: int,
        platform_sender_id: str,
        order_number: str = "ORD-CANCELLED-001",
    ) -> Order:
        """Create a cancelled order.

        Args:
            merchant_id: Merchant ID
            platform_sender_id: Customer's platform sender ID
            order_number: Order number (auto-generated if not provided)

        Returns:
            Order with CANCELLED status
        """
        return Order(
            order_number=order_number,
            merchant_id=merchant_id,
            platform_sender_id=platform_sender_id,
            status=OrderStatus.CANCELLED.value,
            items=[
                {
                    "product_id": "prod_005",
                    "variant_id": "var_005",
                    "title": "Cancelled Item",
                    "price": 39.99,
                    "quantity": 1,
                }
            ],
            subtotal=Decimal("39.99"),
            total=Decimal("44.99"),
            currency_code="USD",
            customer_email="customer@example.com",
            created_at=datetime.utcnow() - timedelta(days=3),
            updated_at=datetime.utcnow() - timedelta(days=2),
        )


async def create_mock_orders(
    db: AsyncSession,
    merchant_id: int,
    platform_sender_id: str,
) -> list[Order]:
    """Create a set of mock orders for testing.

    Creates orders with different statuses to test various tracking scenarios.

    Args:
        db: Database session
        merchant_id: Merchant ID
        platform_sender_id: Customer's platform sender ID

    Returns:
        List of created orders
    """
    factory = MockOrderFactory()

    orders = [
        factory.create_pending_order(merchant_id, platform_sender_id),
        factory.create_processing_order(merchant_id, platform_sender_id),
        factory.create_shipped_order(merchant_id, platform_sender_id),
        factory.create_delivered_order(merchant_id, platform_sender_id),
    ]

    for order in orders:
        db.add(order)

    await db.commit()

    for order in orders:
        await db.refresh(order)

    return orders


async def ensure_mock_orders_exist(
    db: AsyncSession,
    merchant_id: int,
    platform_sender_id: str,
) -> list[Order]:
    """Ensure mock orders exist for testing, creating them if needed.

    Checks if orders already exist for the merchant/customer before creating.

    Args:
        db: Database session
        merchant_id: Merchant ID
        platform_sender_id: Customer's platform sender ID

    Returns:
        List of existing or newly created orders
    """
    result = await db.execute(
        select(Order)
        .where(Order.merchant_id == merchant_id)
        .where(Order.platform_sender_id == platform_sender_id)
    )
    existing_orders = list(result.scalars().all())

    if existing_orders:
        return existing_orders

    return await create_mock_orders(db, merchant_id, platform_sender_id)
