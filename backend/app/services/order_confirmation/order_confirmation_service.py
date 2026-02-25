"""Order Confirmation Service (Story 2.9).

Story 5-12: Bot Personality Consistency
Task 3.1: Update OrderConfirmationService to use PersonalityAwareResponseFormatter

Processes Shopify order webhooks, sends confirmation messages to shoppers,
and clears cart after successful payment.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import structlog
import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.merchant import Merchant, PersonalityType
from app.schemas.order_confirmation import (
    ConfirmationStatus,
    OrderConfirmationRequest,
    OrderConfirmationResult,
    OrderReference,
)
from app.services.cart import CartService
from app.services.messenger.send_service import MessengerSendService
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


class OrderConfirmationService:
    """Service for processing Shopify order confirmations.

    Order Confirmation Flow:
    1. Extract PSID from order attributes (primary) or reverse lookup (fallback)
    2. Check idempotency (prevent duplicate confirmations)
    3. Clear checkout_token and cart from Redis
    4. Store order reference for tracking
    5. Send confirmation message via Messenger

    Idempotency:
    - Uses Redis key: order_reference:{psid}:{order_id}
    - If exists, skips confirmation (already processed)
    """

    ORDER_REFERENCE_TTL_DAYS = 365

    def __init__(
        self,
        redis_client: Optional[Any] = None,
        cart_service: Optional[CartService] = None,
        send_service: Optional[MessengerSendService] = None,
        db: Optional[AsyncSession] = None,
    ) -> None:
        """Initialize order confirmation service.

        Args:
            redis_client: Redis client instance
            cart_service: Cart service for clearing carts
            send_service: Messenger send service
            db: Database session for fetching merchant personality
        """
        if redis_client is None:
            from app.core.config import settings

            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            self.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            self.redis = redis_client

        self.cart_service = cart_service or CartService(self.redis)
        self.send_service = send_service or MessengerSendService()
        self.db = db
        self.logger = structlog.get_logger(__name__)

    def _get_order_reference_key(self, psid: str, order_id: str) -> str:
        """Generate Redis key for order reference.

        Args:
            psid: Facebook Page-Scoped ID
            order_id: Shopify order ID

        Returns:
            Redis key for order reference storage
        """
        return f"order_reference:{psid}:{order_id}"

    def _get_idempotency_key(self, psid: str, order_id: str) -> str:
        """Generate Redis key for idempotency check.

        Args:
            psid: Facebook Page-Scoped ID
            order_id: Shopify order ID

        Returns:
            Redis key for idempotency check
        """
        return f"order_confirmation:{psid}:{order_id}"

    async def _get_psid_from_order(self, order_payload: Dict[str, Any]) -> Optional[str]:
        """Extract PSID from order attributes.

        Args:
            order_payload: Shopify order webhook payload

        Returns:
            PSID if found, None otherwise
        """
        # 1. Try note_attributes (Standard Shopify REST Admin API)
        note_attrs = order_payload.get("note_attributes", [])
        if note_attrs:
            for attr in note_attrs:
                if attr.get("name") == "psid":
                    psid = attr.get("value")
                    if psid:
                        self.logger.info("psid_extracted_from_note_attributes")
                        return psid

        # 2. Try attributes (GraphQL / Plus)
        attrs = order_payload.get("attributes", [])
        if attrs:
            for attr in attrs:
                if attr.get("key") == "psid":
                    psid = attr.get("value")
                    if psid:
                        self.logger.info("psid_extracted_from_attributes")
                        return psid

        # 3. Fallback: Reverse lookup via checkout_token is not currently needed
        # Primary strategy (custom attributes) covers the standard flow

        self.logger.warning("psid_not_found_in_order_attributes")
        return None

    async def _check_idempotency(
        self, psid: str, order_id: str
    ) -> Optional[OrderConfirmationResult]:
        """Check if order has already been confirmed.

        Args:
            psid: Facebook Page-Scoped ID
            order_id: Shopify order ID

        Returns:
            Previous confirmation result if already processed, None otherwise
        """
        idempotency_key = self._get_idempotency_key(psid, order_id)
        existing = await self.redis.get(idempotency_key)

        if existing and isinstance(existing, str):
            self.logger.info(
                "order_already_confirmed",
                psid=psid,
                order_id=order_id,
            )
            data = json.loads(existing)
            return OrderConfirmationResult(**data)

        return None

    async def _mark_confirmed(
        self,
        psid: str,
        order_id: str,
        result: OrderConfirmationResult,
    ) -> None:
        """Mark order as confirmed in Redis (idempotency).

        Args:
            psid: Facebook Page-Scoped ID
            order_id: Shopify order ID
            result: Confirmation result to store
        """
        idempotency_key = self._get_idempotency_key(psid, order_id)
        ttl_seconds = self.ORDER_REFERENCE_TTL_DAYS * 24 * 60 * 60

        await self.redis.setex(
            idempotency_key,
            ttl_seconds,
            result.model_dump_json(exclude_none=True),
        )

    async def _store_order_reference(self, psid: str, order: OrderConfirmationRequest) -> None:
        """Store order reference for tracking (operational data tier).

        Args:
            psid: Facebook Page-Scoped ID
            order: Order confirmation request
        """
        reference_key = self._get_order_reference_key(psid, order.order_id)
        ttl_seconds = self.ORDER_REFERENCE_TTL_DAYS * 24 * 60 * 60

        order_reference = OrderReference(
            order_id=order.order_id,
            order_number=order.order_number,
            order_url=order.order_url,
            psid=psid,
            financial_status=order.financial_status,
            created_at=order.created_at,
            confirmed_at=datetime.now(timezone.utc).isoformat(),
        )

        await self.redis.setex(
            reference_key,
            ttl_seconds,
            order_reference.model_dump_json(exclude_none=True),
        )

        self.logger.info(
            "order_reference_stored",
            psid=psid,
            order_id=order.order_id,
            order_number=order.order_number,
        )

    async def _clear_cart_data(self, psid: str, order_id: str) -> None:
        """Clear checkout token and cart for shopper.

        Args:
            psid: Facebook Page-Scoped ID
            order_id: Shopify order ID (for logging)
        """
        try:
            # Clear checkout token
            checkout_token_key = f"checkout_token:{psid}"
            await self.redis.delete(checkout_token_key)
            self.logger.info("checkout_token_cleared", psid=psid, order_id=order_id)

            # Clear cart via CartService
            await self.cart_service.clear_cart(psid)
            self.logger.info("cart_cleared_after_confirmation", psid=psid, order_id=order_id)

        except Exception as e:
            self.logger.error(
                "cart_clearing_failed",
                psid=psid,
                order_id=order_id,
                error=str(e),
            )
            # Continue anyway - confirmation is more important
            raise

    async def _calculate_estimated_delivery(self, created_at: str) -> str:
        """Calculate estimated delivery date.

        Args:
            created_at: Order creation timestamp (ISO-8601)

        Returns:
            Estimated delivery date (Feb 10 format)
        """
        try:
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            # Default: 5 business days for delivery
            est_delivery = created_dt.replace(day=min(created_dt.day + 5, 28))
            return est_delivery.strftime("%b %d")
        except Exception:
            # Fallback to simple string
            return "Feb 10"

    async def _send_confirmation_message(
        self,
        psid: str,
        order_number: int,
        created_at: str,
        personality: PersonalityType = PersonalityType.FRIENDLY,
    ) -> None:
        """Send order confirmation message via Messenger.

        Story 5-12: Uses PersonalityAwareResponseFormatter for personality-based messages.

        Args:
            psid: Facebook Page-Scoped ID
            order_number: Shopify order number
            created_at: Order creation timestamp
            personality: Merchant's personality type for message formatting
        """
        delivery_date = await self._calculate_estimated_delivery(created_at)

        message = PersonalityAwareResponseFormatter.format_response(
            "order_confirmation",
            "confirmed",
            personality,
            order_number=order_number,
            delivery_date=delivery_date,
        )

        await self.send_service.send_message(
            recipient_id=psid,
            message_payload={"text": message},
            tag="order_update",
        )

        self.logger.info(
            "confirmation_message_sent",
            psid=psid,
            order_number=order_number,
        )

    async def _get_merchant_personality(
        self,
        db: AsyncSession,
        merchant_id: int,
    ) -> PersonalityType:
        """Fetch merchant personality from database.

        Args:
            db: Database session
            merchant_id: Merchant ID

        Returns:
            PersonalityType (defaults to FRIENDLY if not found)
        """
        try:
            result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
            merchant = result.scalars().first()
            if merchant and merchant.personality:
                return merchant.personality
        except Exception as e:
            self.logger.warning(
                "failed_to_fetch_merchant_personality",
                merchant_id=merchant_id,
                error=str(e),
            )
        return PersonalityType.FRIENDLY

    async def process_order_confirmation(
        self,
        order_payload: Dict[str, Any],
        db: Optional[AsyncSession] = None,
        merchant_id: Optional[int] = None,
    ) -> OrderConfirmationResult:
        """Process order confirmation from Shopify webhook.

        Story 5-12: Added personality support via merchant_id parameter.

        Args:
            order_payload: Shopify orders/create webhook payload
            db: Optional database session for fetching merchant personality
            merchant_id: Optional merchant ID for personality lookup

        Returns:
            Order confirmation result

        Raises:
            APIError: If critical processing fails
        """
        # Parse order request
        try:
            order = OrderConfirmationRequest(
                order_id=order_payload.get("id", ""),
                order_number=int(order_payload.get("order_number", 0)),
                order_url=order_payload.get("order_url", ""),
                financial_status=order_payload.get("financial_status", ""),
                customer_email=order_payload.get("email"),
                created_at=order_payload.get("created_at", ""),
                note_attributes=order_payload.get("note_attributes", []),
                attributes=order_payload.get("attributes", []),
            )
        except Exception as e:
            self.logger.error("order_payload_parse_failed", error=str(e))
            return OrderConfirmationResult(
                status=ConfirmationStatus.FAILED,
                order_id="",
                order_number=0,
                message="Failed to parse order payload",
            )

        # Extract PSID from order attributes
        psid = await self._get_psid_from_order(order_payload)

        if not psid:
            self.logger.warning(
                "order_confirmation_skipped_no_psid",
                order_id=order.order_id,
            )
            return OrderConfirmationResult(
                status=ConfirmationStatus.SKIPPED,
                order_id=order.order_id,
                order_number=order.order_number,
                psid=None,
                message="Order confirmed but PSID not found - skipping confirmation message",
            )

        # Check idempotency
        existing = await self._check_idempotency(psid, order.order_id)
        if existing:
            return existing

        # Check financial status (only confirm paid orders)
        if order.financial_status != "paid":
            self.logger.info(
                "order_not_paid_skipping_confirmation",
                order_id=order.order_id,
                financial_status=order.financial_status,
            )
            return OrderConfirmationResult(
                status=ConfirmationStatus.SKIPPED,
                order_id=order.order_id,
                order_number=order.order_number,
                psid=psid,
                message=f"Order not paid (status: {order.financial_status}) - skipping confirmation",
            )

        # Process confirmation
        try:
            # Clear cart data
            await self._clear_cart_data(psid, order.order_id)

            # Store order reference
            await self._store_order_reference(psid, order)

            # Get merchant personality for message formatting
            personality = PersonalityType.FRIENDLY
            if db and merchant_id:
                personality = await self._get_merchant_personality(db, merchant_id)

            # Send confirmation message
            await self._send_confirmation_message(
                psid=psid,
                order_number=order.order_number,
                created_at=order.created_at,
                personality=personality,
            )

            # Create result
            result = OrderConfirmationResult(
                status=ConfirmationStatus.CONFIRMED,
                order_id=order.order_id,
                order_number=order.order_number,
                psid=psid,
                message=f"Order #{order.order_number} confirmed!",
                cart_cleared=True,
                confirmed_at=datetime.now(timezone.utc).isoformat(),
            )

            # Mark as confirmed (idempotency)
            await self._mark_confirmed(psid, order.order_id, result)

            self.logger.info(
                "order_confirmation_success",
                psid=psid,
                order_id=order.order_id,
                order_number=order.order_number,
            )

            return result

        except APIError:
            raise
        except Exception as e:
            self.logger.error(
                "order_confirmation_failed",
                psid=psid,
                order_id=order.order_id,
                error=str(e),
            )
            raise APIError(
                ErrorCode.WEBHOOK_UNKNOWN_ERROR,
                f"Order confirmation processing failed: {str(e)}",
            )
