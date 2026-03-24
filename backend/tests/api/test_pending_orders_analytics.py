"""API tests for Pending Orders widget endpoints.

Tests pending orders GET endpoint, validation errors,
authentication requirements, and sorting/filtering.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import text

from app.models.merchant import PersonalityType
from tests.conftest import auth_headers


# Test merchant data
class TestMerchantData:
    id = 1
    merchant_key = "test-pending-orders"
    platform = "facebook"
    merchant_status = "active"
    personality_type = PersonalityType.FRIENDLY
    bot_name = "TestBot"
    business_name = "Test Business"


@pytest.fixture(autouse=True)
async def setup_test_merchant(async_session):
    """Setup a test merchant before each test."""
    now = datetime.utcnow()
    # Clear existing data for freshness
    await async_session.execute(text("DELETE FROM orders"))
    await async_session.execute(text("DELETE FROM merchants"))

    await async_session.execute(
        text(
            "INSERT INTO merchants "
            "(id, merchant_key, platform, status, personality, bot_name, business_name, created_at, updated_at) "
            "VALUES (:id, :merchant_key, :platform, :status, :personality, :bot_name, :business_name, :created_at, :updated_at)"
        ),
        {
            "id": TestMerchantData.id,
            "merchant_key": TestMerchantData.merchant_key,
            "platform": TestMerchantData.platform,
            "status": TestMerchantData.merchant_status,
            "personality": TestMerchantData.personality_type.value,
            "bot_name": TestMerchantData.bot_name,
            "business_name": TestMerchantData.business_name,
            "created_at": now,
            "updated_at": now,
        },
    )
    # Create a second merchant to test isolation
    await async_session.execute(
        text(
            "INSERT INTO merchants "
            "(id, merchant_key, platform, status, personality, bot_name, business_name, created_at, updated_at) "
            "VALUES (2, 'other-merchant', :platform, :status, :personality, :bot_name, :business_name, :created_at, :updated_at)"
        ),
        {
            "platform": TestMerchantData.platform,
            "status": TestMerchantData.merchant_status,
            "personality": TestMerchantData.personality_type.value,
            "bot_name": TestMerchantData.bot_name,
            "business_name": TestMerchantData.business_name,
            "created_at": now,
            "updated_at": now,
        },
    )
    await async_session.commit()

    yield

    await async_session.execute(text("DELETE FROM orders"))
    await async_session.execute(text("DELETE FROM merchants"))
    await async_session.commit()


async def create_test_orders(async_session):
    """Helper to create test orders."""
    now = datetime.utcnow()

    orders = [
        # Pending order with estimated delivery soonest
        {
            "order_number": "ORD-001",
            "merchant_id": 1,
            "platform_sender_id": "cust1",
            "status": "processing",
            "is_test": False,
            "subtotal": 100.0,
            "total": 100.0,
            "estimated_delivery": now + timedelta(days=2)
        },
        # Pending order with estimated delivery later
        {
            "order_number": "ORD-002",
            "merchant_id": 1,
            "platform_sender_id": "cust2",
            "status": "shipped",
            "is_test": False,
            "subtotal": 50.0,
            "total": 50.0,
            "estimated_delivery": now + timedelta(days=5)
        },
        # Pending order with NO estimated delivery
        {
            "order_number": "ORD-003",
            "merchant_id": 1,
            "platform_sender_id": "cust3",
            "status": "pending",
            "is_test": False,
            "subtotal": 75.0,
            "total": 75.0,
            "estimated_delivery": None
        },
        # Delivered order (should be excluded)
        {
            "order_number": "ORD-004",
            "merchant_id": 1,
            "platform_sender_id": "cust4",
            "status": "delivered",
            "is_test": False,
            "subtotal": 200.0,
            "total": 200.0,
            "estimated_delivery": now - timedelta(days=1)
        },
        # Cancelled order (should be excluded)
        {
            "order_number": "ORD-005",
            "merchant_id": 1,
            "platform_sender_id": "cust5",
            "status": "cancelled",
            "is_test": False,
            "subtotal": 150.0,
            "total": 150.0,
            "estimated_delivery": None
        },
        # Test order (should be excluded)
        {
            "order_number": "test-order",
            "merchant_id": 1,
            "platform_sender_id": "testcust",
            "status": "pending",
            "is_test": True,
            "subtotal": 10.0,
            "total": 10.0,
            "estimated_delivery": now + timedelta(days=1)
        },
        # Other merchant order (should be excluded)
        {
            "order_number": "ORD-006",
            "merchant_id": 2,
            "platform_sender_id": "cust6",
            "status": "pending",
            "is_test": False,
            "subtotal": 0.0,
            "total": 0.0,
            "estimated_delivery": now + timedelta(days=1)
        }
    ]

    for o in orders:
        if "now" not in o:
            o["now"] = now
        await async_session.execute(
            text(
                "INSERT INTO orders (order_number, merchant_id, platform_sender_id, "
                "status, is_test, subtotal, total, estimated_delivery, currency_code, data_tier, created_at, updated_at) "
                "VALUES (:order_number, :merchant_id, :platform_sender_id, :status, "
                ":is_test, :subtotal, :total, :estimated_delivery, 'USD', 'operational', :now, :now)"
            ),
            o
        )


@pytest.mark.asyncio
async def test_get_pending_orders_success(async_client, async_session):
    """Test retrieving pending orders returns correct data sorted by delivery date."""
    await create_test_orders(async_session)
    await async_session.commit()

    response = await async_client.get(
        "/api/v1/analytics/pending-orders?merchant_id=1",
        headers=auth_headers(1)
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["merchantId"] == 1

    # Check ordering (earliest estimated delivery first)
    orders = data["items"]
    assert orders[0]["orderNumber"] == "ORD-001" # 2 days
    assert orders[1]["orderNumber"] == "ORD-002" # 5 days
    assert orders[2]["orderNumber"] == "ORD-003" # null

    # Check that resolved orders are not included
    order_numbers = [o["orderNumber"] for o in orders]
    assert "ORD-004" not in order_numbers # Delivered
    assert "ORD-005" not in order_numbers # Cancelled

    # Verify field population
    assert orders[0]["status"] == "processing"
    assert orders[0]["total"] == 100.0
    assert orders[0]["estimatedDelivery"] is not None
    assert orders[2]["estimatedDelivery"] is None


@pytest.mark.asyncio
async def test_get_pending_orders_empty(async_client):
    """Test retrieving pending orders when none exist returns empty list."""
    response = await async_client.get(
        "/api/v1/analytics/pending-orders?merchant_id=1",
        headers=auth_headers(1)
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_get_pending_orders_pagination(async_client, async_session):
    """Test pagination of pending orders."""
    await create_test_orders(async_session)
    await async_session.commit()

    # Get second page (offset 1, limit 1)
    response = await async_client.get(
        "/api/v1/analytics/pending-orders?merchant_id=1&limit=1&offset=1",
        headers=auth_headers(1)
    )

    assert response.status_code == 200
    data = response.json()
    orders = data["items"]
    assert len(orders) == 1
    # Second order should be ORD-002 based on sorting
    assert orders[0]["orderNumber"] == "ORD-002"


@pytest.mark.asyncio
async def test_get_pending_orders_requires_auth(async_client):
    """Test getting pending orders without authentication returns 401."""
    response = await async_client.get("/api/v1/analytics/pending-orders")

    assert response.status_code == 401
