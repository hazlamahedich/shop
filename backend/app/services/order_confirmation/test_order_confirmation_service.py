"""Tests for OrderConfirmationService (Story 2.9).

Tests order confirmation processing, cart clearing, idempotency,
PSID extraction, and confirmation message sending.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import APIError, ErrorCode
from app.services.cart import CartService
from app.services.order_confirmation import OrderConfirmationService
from app.services.messenger.send_service import MessengerSendService


class TestOrderConfirmationService:
    """Test OrderConfirmationService order processing."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client with async methods."""
        mock_client = MagicMock()
        mock_client.get = AsyncMock()
        mock_client.setex = AsyncMock()
        mock_client.delete = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_cart_service(self):
        """Create mock CartService."""
        return AsyncMock(spec=CartService)

    @pytest.fixture
    def mock_send_service(self):
        """Create mock MessengerSendService."""
        return AsyncMock(spec=MessengerSendService)

    @pytest.fixture
    def order_confirmation_service(
        self, mock_redis, mock_cart_service, mock_send_service
    ):
        """Create order confirmation service with mocked dependencies."""
        return OrderConfirmationService(
            redis_client=mock_redis,
            cart_service=mock_cart_service,
            send_service=mock_send_service,
        )

    @pytest.fixture
    def sample_paid_order_payload(self):
        """Create sample paid order webhook payload."""
        return {
            "id": "gid://shopify/Order/123456789",
            "order_number": 1001,
            "order_url": "https://shop.myshopify.com/admin/orders/123456789",
            "financial_status": "paid",
            "email": "customer@example.com",
            "created_at": "2026-02-05T10:00:00Z",
            "note_attributes": [
                {"name": "psid", "value": "test_psid_12345"}
            ],
        }

    @pytest.mark.asyncio
    async def test_order_confirmation_clears_cart(
        self, order_confirmation_service, mock_cart_service, sample_paid_order_payload
    ):
        """Test that order confirmation clears cart (Story 2.9)."""
        # Process order confirmation
        result = await order_confirmation_service.process_order_confirmation(
            sample_paid_order_payload
        )

        # Verify result
        assert result.status == "confirmed"
        assert result.cart_cleared is True

        # Verify cart was cleared
        mock_cart_service.clear_cart.assert_called_once_with("test_psid_12345")

    @pytest.mark.asyncio
    async def test_paid_order_sends_confirmation(
        self, order_confirmation_service, mock_send_service, sample_paid_order_payload
    ):
        """Test that paid order sends confirmation message."""
        # Process order confirmation
        result = await order_confirmation_service.process_order_confirmation(
            sample_paid_order_payload
        )

        # Verify confirmation sent
        assert result.status == "confirmed"
        mock_send_service.send_message.assert_called_once()

        # Verify message content (call_args is args+kwargs combined)
        call_kwargs = mock_send_service.send_message.call_args.kwargs
        assert call_kwargs["recipient_id"] == "test_psid_12345"
        assert "Order #1001" in call_kwargs["message_payload"]["text"]

        # Story 2.9: Verify order_update tag is used for 24-hour rule compliance
        assert call_kwargs["tag"] == "order_update"

    @pytest.mark.asyncio
    async def test_unpaid_order_skips_confirmation(
        self, order_confirmation_service, mock_send_service
    ):
        """Test that unpaid order doesn't send confirmation."""
        unpaid_payload = {
            "id": "gid://shopify/Order/123456789",
            "order_number": 1001,
            "order_url": "https://shop.myshopify.com/admin/orders/123456789",
            "financial_status": "pending",  # Not paid
            "email": "customer@example.com",
            "created_at": "2026-02-05T10:00:00Z",
            "note_attributes": [
                {"name": "psid", "value": "test_psid_12345"}
            ],
        }

        # Process order confirmation
        result = await order_confirmation_service.process_order_confirmation(unpaid_payload)

        # Verify skipped
        assert result.status == "skipped"
        assert "not paid" in result.message.lower()

        # Verify no confirmation sent
        mock_send_service.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_psid_extraction_from_note_attributes(
        self, order_confirmation_service, sample_paid_order_payload
    ):
        """Test PSID extraction from note_attributes (Standard Shopify)."""
        # Process order confirmation
        result = await order_confirmation_service.process_order_confirmation(
            sample_paid_order_payload
        )

        # Verify PSID was extracted
        assert result.psid == "test_psid_12345"
        assert result.status == "confirmed"

    @pytest.mark.asyncio
    async def test_psid_extraction_from_attributes(
        self, order_confirmation_service, sample_paid_order_payload
    ):
        """Test PSID extraction from attributes (GraphQL/Plus)."""
        # Use attributes instead of note_attributes
        sample_paid_order_payload["note_attributes"] = []
        sample_paid_order_payload["attributes"] = [
            {"key": "psid", "value": "test_psid_graphql"}
        ]

        # Process order confirmation
        result = await order_confirmation_service.process_order_confirmation(
            sample_paid_order_payload
        )

        # Verify PSID was extracted
        assert result.psid == "test_psid_graphql"
        assert result.status == "confirmed"

    @pytest.mark.asyncio
    async def test_missing_psid_skips_confirmation(
        self, order_confirmation_service, mock_send_service
    ):
        """Test that missing PSID skips confirmation with warning log."""
        payload_no_psid = {
            "id": "gid://shopify/Order/123456789",
            "order_number": 1001,
            "order_url": "https://shop.myshopify.com/admin/orders/123456789",
            "financial_status": "paid",
            "email": "customer@example.com",
            "created_at": "2026-02-05T10:00:00Z",
            "note_attributes": [],
            "attributes": [],
        }

        # Process order confirmation
        result = await order_confirmation_service.process_order_confirmation(
            payload_no_psid
        )

        # Verify skipped
        assert result.status == "skipped"
        assert "PSID not found" in result.message
        assert result.psid is None

        # Verify no confirmation sent
        mock_send_service.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_idempotent_confirmation(
        self, order_confirmation_service, mock_redis, sample_paid_order_payload
    ):
        """Test that re-processing same order returns cached result (idempotency)."""
        # First confirmation
        result1 = await order_confirmation_service.process_order_confirmation(
            sample_paid_order_payload
        )
        assert result1.status == "confirmed"

        # Simulate idempotency key exists in Redis
        mock_redis.get.return_value = result1.model_dump_json(exclude_none=True)

        # Second confirmation (should return cached)
        result2 = await order_confirmation_service.process_order_confirmation(
            sample_paid_order_payload
        )

        # Verify idempotent result
        assert result2.status == "confirmed"
        assert result2.order_id == result1.order_id

    @pytest.mark.asyncio
    async def test_checkout_token_cleared(
        self, order_confirmation_service, mock_redis, sample_paid_order_payload
    ):
        """Test that checkout token is cleared after confirmation."""
        # Process order confirmation
        result = await order_confirmation_service.process_order_confirmation(
            sample_paid_order_payload
        )

        # Verify checkout token was cleared
        mock_redis.delete.assert_called()
        delete_calls = [str(call) for call in mock_redis.delete.call_args_list]
        assert any("checkout_token:test_psid_12345" in call for call in delete_calls)

    @pytest.mark.asyncio
    async def test_order_reference_stored(
        self, order_confirmation_service, mock_redis, sample_paid_order_payload
    ):
        """Test that order reference is stored for tracking."""
        # Process order confirmation
        result = await order_confirmation_service.process_order_confirmation(
            sample_paid_order_payload
        )

        # Verify order reference was stored
        assert mock_redis.setex.called

        # Find the order reference storage call
        order_ref_calls = [
            call for call in mock_redis.setex.call_args_list
            if "order_reference:" in str(call[0][0])
        ]

        assert len(order_ref_calls) > 0

        # Verify order reference data
        call = order_ref_calls[0]
        key = call[0][0]
        value = json.loads(call[0][2])

        assert key == "order_reference:test_psid_12345:gid://shopify/Order/123456789"
        assert value["order_id"] == "gid://shopify/Order/123456789"
        assert value["order_number"] == 1001
        assert value["psid"] == "test_psid_12345"

    @pytest.mark.asyncio
    async def test_confirmation_message_content(
        self, order_confirmation_service, mock_send_service, sample_paid_order_payload
    ):
        """Test confirmation message contains required elements."""
        # Process order confirmation
        await order_confirmation_service.process_order_confirmation(
            sample_paid_order_payload
        )

        # Get the sent message
        call_kwargs = mock_send_service.send_message.call_args.kwargs
        message_text = call_kwargs["message_payload"]["text"]

        # Verify message contains required elements
        assert "Order confirmed!" in message_text
        assert "Order #1001" in message_text
        assert "Est. delivery:" in message_text
        assert "Track your order" in message_text
        assert "Where's my order?" in message_text

    @pytest.mark.asyncio
    async def test_get_order_reference_key(self, order_confirmation_service):
        """Test Redis key generation for order reference."""
        key = order_confirmation_service._get_order_reference_key("test_psid", "order_123")
        assert key == "order_reference:test_psid:order_123"

    @pytest.mark.asyncio
    async def test_get_idempotency_key(self, order_confirmation_service):
        """Test Redis key generation for idempotency check."""
        key = order_confirmation_service._get_idempotency_key("test_psid", "order_123")
        assert key == "order_confirmation:test_psid:order_123"

    @pytest.mark.asyncio
    async def test_calculate_estimated_delivery(self, order_confirmation_service):
        """Test estimated delivery date calculation."""
        delivery = await order_confirmation_service._calculate_estimated_delivery(
            "2026-02-05T10:00:00Z"
        )
        # Should return format like "Feb 10"
        assert delivery is not None
        assert len(delivery) > 0

    @pytest.mark.asyncio
    async def test_order_confirmation_ttl_365_days(
        self, order_confirmation_service, mock_redis, sample_paid_order_payload
    ):
        """Test that order reference is stored with 365-day TTL."""
        # Process order confirmation
        await order_confirmation_service.process_order_confirmation(
            sample_paid_order_payload
        )

        # Verify TTL is 365 days (31536000 seconds)
        order_ref_calls = [
            call for call in mock_redis.setex.call_args_list
            if "order_reference:" in str(call[0][0])
        ]

        call = order_ref_calls[0]
        ttl = call[0][1]
        assert ttl == 365 * 24 * 60 * 60
