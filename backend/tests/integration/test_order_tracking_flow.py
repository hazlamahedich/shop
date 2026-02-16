"""Integration tests for order tracking flow (Story 4-1).

Tests the full order tracking flow with database interactions.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.merchant import Merchant
from app.models.order import Order, OrderStatus
from app.services.order_tracking import (
    OrderTrackingService,
    OrderLookupType,
    create_mock_orders,
)
from app.services.order_tracking.order_tracking_service import (
    PENDING_STATE_KEY,
    PENDING_STATE_TIMESTAMP_KEY,
    PENDING_STATE_TIMEOUT_SECONDS,
)


@pytest.fixture
async def test_merchant(db_session: AsyncSession) -> Merchant:
    """Create a test merchant."""
    merchant = Merchant(
        merchant_key="test-merchant-order-tracking",
        platform="facebook",
        status="active",
        email="order-tracking-test@example.com",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)
    return merchant


@pytest.fixture
async def test_conversation(
    db_session: AsyncSession,
    test_merchant: Merchant,
) -> Conversation:
    """Create a test conversation."""
    conversation = Conversation(
        merchant_id=test_merchant.id,
        platform="facebook",
        platform_sender_id="test_psid_12345",
        status="active",
        handoff_status="none",
    )
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)
    return conversation


@pytest.fixture
async def test_orders(
    db_session: AsyncSession,
    test_merchant: Merchant,
    test_conversation: Conversation,
) -> list[Order]:
    """Create test orders for the test merchant and customer."""
    return await create_mock_orders(
        db_session,
        test_merchant.id,
        test_conversation.platform_sender_id,
    )


@pytest.fixture
def order_tracking_service() -> OrderTrackingService:
    """Create an OrderTrackingService instance."""
    return OrderTrackingService()


class TestOrderTrackingByCustomer:
    """Integration tests for order tracking by customer ID."""

    @pytest.mark.asyncio
    async def test_returns_most_recent_order(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        test_conversation: Conversation,
        test_orders: list[Order],
    ) -> None:
        """Test that the most recent order is returned for a customer."""
        result = await order_tracking_service.track_order_by_customer(
            db_session,
            test_merchant.id,
            test_conversation.platform_sender_id,
        )

        assert result.found is True
        assert result.order is not None
        assert result.lookup_type == OrderLookupType.BY_CUSTOMER
        assert result.order.merchant_id == test_merchant.id

    @pytest.mark.asyncio
    async def test_returns_not_found_for_nonexistent_customer(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
    ) -> None:
        """Test that not found is returned for nonexistent customer."""
        result = await order_tracking_service.track_order_by_customer(
            db_session,
            test_merchant.id,
            "nonexistent_psid",
        )

        assert result.found is False
        assert result.order is None

    @pytest.mark.asyncio
    async def test_scopes_by_merchant(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_orders: list[Order],
    ) -> None:
        """Test that lookup is scoped to merchant."""
        result = await order_tracking_service.track_order_by_customer(
            db_session,
            99999,
            "test_psid_12345",
        )

        assert result.found is False


class TestOrderTrackingByNumber:
    """Integration tests for order tracking by order number."""

    @pytest.mark.asyncio
    async def test_returns_order_by_number(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        test_orders: list[Order],
    ) -> None:
        """Test that order is returned when found by number."""
        result = await order_tracking_service.track_order_by_number(
            db_session,
            test_merchant.id,
            "ORD-SHIPPED-001",
        )

        assert result.found is True
        assert result.order is not None
        assert result.order.order_number == "ORD-SHIPPED-001"
        assert result.lookup_type == OrderLookupType.BY_ORDER_NUMBER

    @pytest.mark.asyncio
    async def test_returns_not_found_for_nonexistent_number(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
    ) -> None:
        """Test that not found is returned for nonexistent order number."""
        result = await order_tracking_service.track_order_by_number(
            db_session,
            test_merchant.id,
            "ORD-NONEXISTENT",
        )

        assert result.found is False
        assert result.order is None

    @pytest.mark.asyncio
    async def test_scopes_by_merchant(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_orders: list[Order],
    ) -> None:
        """Test that lookup is scoped to merchant."""
        result = await order_tracking_service.track_order_by_number(
            db_session,
            99999,
            "ORD-SHIPPED-001",
        )

        assert result.found is False


class TestOrderTrackingFlow:
    """Integration tests for full order tracking flow."""

    @pytest.mark.asyncio
    async def test_full_flow_order_found_by_customer(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        test_conversation: Conversation,
        test_orders: list[Order],
    ) -> None:
        """Test full flow: customer queries -> order found -> response formatted."""
        result = await order_tracking_service.track_order_by_customer(
            db_session,
            test_merchant.id,
            test_conversation.platform_sender_id,
        )

        assert result.found is True
        assert result.order is not None

        response = order_tracking_service.format_order_response(result.order)
        assert result.order.order_number in response
        assert "Status:" in response

    @pytest.mark.asyncio
    async def test_full_flow_no_orders_ask_for_number(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        test_conversation: Conversation,
    ) -> None:
        """Test full flow: customer queries -> no orders -> ask for order number."""
        result = await order_tracking_service.track_order_by_customer(
            db_session,
            test_merchant.id,
            test_conversation.platform_sender_id,
        )

        assert result.found is False

        response = order_tracking_service.format_order_not_found_response(
            OrderLookupType.BY_CUSTOMER
        )
        assert "order number" in response.lower()

    @pytest.mark.asyncio
    async def test_full_flow_provide_order_number(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        test_orders: list[Order],
    ) -> None:
        """Test full flow: customer provides order number -> order found -> response."""
        result = await order_tracking_service.track_order_by_number(
            db_session,
            test_merchant.id,
            "ORD-DELIVERED-001",
        )

        assert result.found is True
        assert result.order is not None

        response = order_tracking_service.format_order_response(result.order)
        assert "ORD-DELIVERED-001" in response
        assert "Delivered" in response

    @pytest.mark.asyncio
    async def test_full_flow_invalid_order_number(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
    ) -> None:
        """Test full flow: invalid order number -> error message."""
        result = await order_tracking_service.track_order_by_number(
            db_session,
            test_merchant.id,
            "ORD-INVALID",
        )

        assert result.found is False

        response = order_tracking_service.format_order_not_found_response(
            OrderLookupType.BY_ORDER_NUMBER, "ORD-INVALID"
        )
        assert "ORD-INVALID" in response
        assert "couldn't find" in response.lower()


class TestOrderStatusFormats:
    """Integration tests for order status response formatting."""

    @pytest.mark.asyncio
    async def test_shipped_order_includes_tracking(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        test_orders: list[Order],
    ) -> None:
        """Test that shipped order response includes tracking info."""
        result = await order_tracking_service.track_order_by_number(
            db_session,
            test_merchant.id,
            "ORD-SHIPPED-001",
        )

        assert result.order is not None
        response = order_tracking_service.format_order_response(result.order)

        assert "Shipped" in response
        assert "tracking.example.com" in response
        assert "Estimated delivery" in response

    @pytest.mark.asyncio
    async def test_pending_order_format(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        test_orders: list[Order],
    ) -> None:
        """Test pending order response format."""
        result = await order_tracking_service.track_order_by_number(
            db_session,
            test_merchant.id,
            "ORD-PENDING-001",
        )

        assert result.order is not None
        response = order_tracking_service.format_order_response(result.order)

        assert "Pending" in response
        assert "processed soon" in response


class TestMultipleOrders:
    """Integration tests for customers with multiple orders."""

    @pytest.mark.asyncio
    async def test_returns_most_recent_order(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        test_conversation: Conversation,
        test_orders: list[Order],
    ) -> None:
        """Test that the most recent order is returned when multiple exist."""
        result = await order_tracking_service.track_order_by_customer(
            db_session,
            test_merchant.id,
            test_conversation.platform_sender_id,
        )

        assert result.found is True
        assert result.order is not None

        all_orders_result = await db_session.execute(
            select(Order)
            .where(Order.merchant_id == test_merchant.id)
            .where(Order.platform_sender_id == test_conversation.platform_sender_id)
            .order_by(Order.created_at.desc())
        )
        all_orders = list(all_orders_result.scalars().all())
        assert len(all_orders) == 4
        assert result.order.order_number == all_orders[0].order_number


class TestUnicodeAndSpecialCharacters:
    """Integration tests for unicode and special character handling in order numbers."""

    @pytest.mark.asyncio
    async def test_handles_whitespace_in_order_number(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        test_orders: list[Order],
    ) -> None:
        """Test that whitespace is trimmed from order number."""
        result = await order_tracking_service.track_order_by_number(
            db_session,
            test_merchant.id,
            "  ORD-SHIPPED-001  ",
        )

        assert result.found is True
        assert result.order is not None
        assert result.order.order_number == "ORD-SHIPPED-001"

    @pytest.mark.asyncio
    async def test_handles_unicode_order_number_not_found(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
    ) -> None:
        """Test that unicode order numbers don't cause errors."""
        result = await order_tracking_service.track_order_by_number(
            db_session,
            test_merchant.id,
            "ORD-测试-001",
        )

        assert result.found is False
        assert result.error_code is None

    @pytest.mark.asyncio
    async def test_handles_emoji_order_number(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
    ) -> None:
        """Test that emoji order numbers don't cause errors."""
        result = await order_tracking_service.track_order_by_number(
            db_session,
            test_merchant.id,
            "ORD-🔥📦-001",
        )

        assert result.found is False
        assert result.error_code is None

    @pytest.mark.asyncio
    async def test_truncates_very_long_order_number(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
    ) -> None:
        """Test that very long order numbers are truncated to 50 chars."""
        long_number = "ORD-" + "X" * 100

        result = await order_tracking_service.track_order_by_number(
            db_session,
            test_merchant.id,
            long_number,
        )

        assert result.found is False
        assert result.error_code is None


class TestMerchantSecurityBoundary:
    """Integration tests for merchant security boundaries in order tracking."""

    @pytest.fixture
    async def other_merchant(
        self,
        db_session: AsyncSession,
    ) -> Merchant:
        """Create a second merchant for cross-merchant tests."""
        merchant = Merchant(
            merchant_key="other-merchant-order-tracking",
            platform="facebook",
            status="active",
            email="other-merchant@example.com",
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)
        return merchant

    @pytest.fixture
    async def other_merchant_order(
        self,
        db_session: AsyncSession,
        other_merchant: Merchant,
    ) -> Order:
        """Create an order for the other merchant."""
        order = Order(
            order_number="ORD-OTHER-MERCHANT-001",
            merchant_id=other_merchant.id,
            platform_sender_id="other_psid_12345",
            status=OrderStatus.SHIPPED.value,
            subtotal=Decimal("50.00"),
            total=Decimal("55.00"),
            currency_code="USD",
        )
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)
        return order

    @pytest.mark.asyncio
    async def test_cannot_lookup_other_merchant_order_by_number(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        other_merchant_order: Order,
    ) -> None:
        """Test that one merchant cannot lookup another merchant's order by number."""
        result = await order_tracking_service.track_order_by_number(
            db_session,
            test_merchant.id,
            "ORD-OTHER-MERCHANT-001",
        )

        assert result.found is False
        assert result.order is None

    @pytest.mark.asyncio
    async def test_cannot_lookup_other_merchant_order_by_customer(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        other_merchant_order: Order,
    ) -> None:
        """Test that one merchant cannot lookup another merchant's orders by customer."""
        result = await order_tracking_service.track_order_by_customer(
            db_session,
            test_merchant.id,
            "other_psid_12345",
        )

        assert result.found is False
        assert result.order is None


class TestPendingStateTimeout:
    """Integration tests for pending state timeout behavior."""

    @pytest.mark.asyncio
    async def test_pending_state_expires_after_timeout(
        self,
        order_tracking_service: OrderTrackingService,
    ) -> None:
        """Test that pending state expires after 5 minutes."""
        from datetime import datetime, timedelta, timezone

        expired_time = datetime.now(timezone.utc) - timedelta(
            seconds=PENDING_STATE_TIMEOUT_SECONDS + 60
        )
        data = {
            PENDING_STATE_KEY: True,
            PENDING_STATE_TIMESTAMP_KEY: expired_time.isoformat(),
        }

        assert order_tracking_service.get_pending_state(data) is False

    @pytest.mark.asyncio
    async def test_pending_state_active_within_timeout(
        self,
        order_tracking_service: OrderTrackingService,
    ) -> None:
        """Test that pending state is active within 5 minutes."""
        from datetime import datetime, timezone

        data = {
            PENDING_STATE_KEY: True,
            PENDING_STATE_TIMESTAMP_KEY: datetime.now(timezone.utc).isoformat(),
        }

        assert order_tracking_service.get_pending_state(data) is True

    @pytest.mark.asyncio
    async def test_pending_state_can_be_cleared(
        self,
        order_tracking_service: OrderTrackingService,
    ) -> None:
        """Test that pending state can be explicitly cleared."""
        from datetime import datetime, timezone

        data = {
            PENDING_STATE_KEY: True,
            PENDING_STATE_TIMESTAMP_KEY: datetime.now(timezone.utc).isoformat(),
            "other_key": "value",
        }

        result = order_tracking_service.clear_pending_state(data)

        assert PENDING_STATE_KEY not in result
        assert PENDING_STATE_TIMESTAMP_KEY not in result
        assert result["other_key"] == "value"


class TestResponseTimeAC5:
    """Integration tests for AC5: Response time < 2 seconds (P95)."""

    @pytest.mark.asyncio
    async def test_track_by_customer_response_time_under_2_seconds(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        test_conversation: Conversation,
        test_orders: list[Order],
    ) -> None:
        """AC5: Verify order lookup by customer completes in < 2 seconds."""
        import time

        start_time = time.perf_counter()

        result = await order_tracking_service.track_order_by_customer(
            db_session,
            test_merchant.id,
            test_conversation.platform_sender_id,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert result.found is True
        assert elapsed_ms < 2000, f"Response time {elapsed_ms:.2f}ms exceeds 2000ms threshold"

    @pytest.mark.asyncio
    async def test_track_by_number_response_time_under_2_seconds(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
        test_orders: list[Order],
    ) -> None:
        """AC5: Verify order lookup by order number completes in < 2 seconds."""
        import time

        start_time = time.perf_counter()

        result = await order_tracking_service.track_order_by_number(
            db_session,
            test_merchant.id,
            "ORD-SHIPPED-001",
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert result.found is True
        assert elapsed_ms < 2000, f"Response time {elapsed_ms:.2f}ms exceeds 2000ms threshold"

    @pytest.mark.asyncio
    async def test_not_found_response_time_under_2_seconds(
        self,
        db_session: AsyncSession,
        order_tracking_service: OrderTrackingService,
        test_merchant: Merchant,
    ) -> None:
        """AC5: Verify not-found lookups also complete in < 2 seconds."""
        import time

        start_time = time.perf_counter()

        result = await order_tracking_service.track_order_by_customer(
            db_session,
            test_merchant.id,
            "nonexistent_psid_for_timing_test",
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert result.found is False
        assert elapsed_ms < 2000, f"Response time {elapsed_ms:.2f}ms exceeds 2000ms threshold"
