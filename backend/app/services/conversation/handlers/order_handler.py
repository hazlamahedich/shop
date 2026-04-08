"""Order handler for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService
Story 4-13: Cross-device order lookup with email fallback

Story 5-12: Bot Personality Consistency
Task 2.4: Update OrderHandler to use PersonalityAwareResponseFormatter

Handles ORDER_TRACKING intent with OrderTrackingService.
"""

from __future__ import annotations

import re
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.order import Order
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.llm.base_llm_service import BaseLLMService
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import TransitionCategory
from app.services.personality.transition_selector import get_transition_selector

logger = structlog.get_logger(__name__)

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PENDING_CROSS_DEVICE_KEY = "pending_cross_device_lookup"

COMMON_DOMAIN_TYPOS = {
    "gmial": "gmail",
    "gmal": "gmail",
    "gamil": "gmail",
    "gamial": "gmail",
    "hotmal": "hotmail",
    "hotmai": "hotmail",
    "yaho": "yahoo",
    "yaoo": "yahoo",
    "outloo": "outlook",
    "outlok": "outlook",
}

COMMON_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "icloud.com",
    "aol.com",
    "protonmail.com",
    "live.com",
    "msn.com",
    "mail.com",
}


class OrderHandler(BaseHandler):
    """Handler for ORDER_TRACKING intent.

    Looks up orders by customer ID or order number,
    filtering out test orders (is_test=False).

    Story 4-13: Cross-device lookup with email/order number fallback.
    """

    async def handle(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: BaseLLMService,
        message: str,
        context: ConversationContext,
        entities: dict[str, Any] | None = None,
    ) -> ConversationResponse:
        """Handle order tracking intent.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service for this merchant
            message: User's message
            context: Conversation context
            entities: Extracted entities (order_number if provided)

        Returns:
            ConversationResponse with order status
        """
        try:
            return await self._handle_order_tracking(
                db=db,
                merchant=merchant,
                llm_service=llm_service,
                message=message,
                context=context,
                entities=entities,
            )
        except Exception as e:
            logger.error(
                "order_handler_failed",
                merchant_id=merchant.id,
                error=str(e),
                error_type=type(e).__name__,
            )
            from app.services.conversation.error_recovery_service import (
                ErrorType,
                NaturalErrorRecoveryService,
            )

            return await NaturalErrorRecoveryService().recover(
                error_type=ErrorType.ORDER_LOOKUP_FAILED,
                merchant=merchant,
                context=context,
                error=e,
                intent="order_tracking",
                conversation_id=str(context.session_id),
            )

    async def _handle_order_tracking(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: BaseLLMService,
        message: str,
        context: ConversationContext,
        entities: dict[str, Any] | None = None,
    ) -> ConversationResponse:
        """Internal order tracking implementation."""
        from app.services.customer_lookup_service import CustomerLookupService
        from app.services.order_tracking.order_tracking_service import OrderTrackingService

        tracking_service = OrderTrackingService()
        customer_service = CustomerLookupService()

        order_number = None
        if entities:
            order_number = entities.get("order_number")

        # Check both database-persisted conversation_data and in-memory metadata
        # This allows cross-device lookup to work even before consent is granted
        conversation_data = context.conversation_data or {}
        metadata = context.metadata or {}
        pending_lookup = conversation_data.get(PENDING_CROSS_DEVICE_KEY) or metadata.get(
            PENDING_CROSS_DEVICE_KEY
        )

        if pending_lookup and not order_number:
            normalized_email = self._normalize_email(message)
            if normalized_email:
                return await self._handle_cross_device_email_lookup(
                    db=db,
                    merchant=merchant,
                    customer_service=customer_service,
                    tracking_service=tracking_service,
                    email=normalized_email,
                    context=context,
                )

            if self._looks_like_order_number(message):
                order_number = message.strip()

            if not order_number:
                email_from_history = self._extract_email_from_history(context)
                if email_from_history:
                    return await self._handle_cross_device_email_lookup(
                        db=db,
                        merchant=merchant,
                        customer_service=customer_service,
                        tracking_service=tracking_service,
                        email=email_from_history,
                        context=context,
                    )

        if order_number:
            result = await tracking_service.track_order_by_number(
                db=db,
                merchant_id=merchant.id,
                order_number=order_number,
            )
        else:
            platform_sender_id = context.platform_sender_id or context.session_id

            customer_email = None
            if context.conversation_data:
                customer_email = context.conversation_data.get("customer_email")

            if not customer_email:
                customer_email = self._normalize_email(message)

            result = await tracking_service.track_order_by_customer(
                db=db,
                merchant_id=merchant.id,
                platform_sender_id=platform_sender_id,
                customer_email=customer_email,
            )

        if not result.found or not result.order:
            return await self._handle_order_not_found(
                db=db,
                merchant=merchant,
                tracking_service=tracking_service,
                customer_service=customer_service,
                result=result,
                order_number=order_number,
                context=context,
            )

        orders = result.orders if result.orders else [result.order]
        conversation_id = str(context.session_id)

        customer_name = None
        profile = None
        first_order = orders[0]
        if first_order.customer_email:
            profile = await customer_service.find_by_email(
                db=db,
                merchant_id=merchant.id,
                email=first_order.customer_email,
            )
            if profile and profile.first_name:
                customer_name = profile.first_name
            elif first_order.customer_first_name:
                customer_name = first_order.customer_first_name

        if len(orders) == 1:
            order = orders[0]
            product_images = await self._fetch_product_images(db=db, merchant=merchant, order=order)
            raw_response = tracking_service.format_order_response(order, product_images)
            selector = get_transition_selector()
            transition = selector.select(
                TransitionCategory.SHOWING_RESULTS,
                merchant.personality,
                conversation_id=conversation_id,
                mode="ecommerce",
            )
            greeting = f"Hey {customer_name}! " if customer_name else ""
            response_text = f"{greeting}{transition}\n\n{raw_response}"
            order_dict = {
                "order_number": order.order_number,
                "status": order.status,
                "fulfillment_status": order.fulfillment_status,
                "tracking_number": order.tracking_number,
                "tracking_url": order.tracking_url,
                "items": order.items,
            }
        else:
            response_parts = []
            for order in orders:
                product_images = await self._fetch_product_images(
                    db=db, merchant=merchant, order=order
                )
                formatted = tracking_service.format_order_response(order, product_images)
                response_parts.append(formatted)
            raw_text = "\n\n---\n\n".join(response_parts)
            selector = get_transition_selector()
            transition = selector.select(
                TransitionCategory.SHOWING_RESULTS,
                merchant.personality,
                conversation_id=conversation_id,
                mode="ecommerce",
            )
            greeting = f"Hey {customer_name}! " if customer_name else ""
            response_text = f"{greeting}{transition}\n\n{raw_text}"
            order_dict = None

        logger.info(
            "order_tracking_success",
            merchant_id=merchant.id,
            order_count=len(orders),
            order_numbers=[o.order_number for o in orders],
            lookup_type=result.lookup_type.value if result.lookup_type else "unknown",
        )

        conversation_data = context.conversation_data or {}
        updated_data = conversation_data.copy()

        if first_order.customer_email:
            if not profile:
                profile = await customer_service.upsert_customer_profile(
                    db=db,
                    merchant_id=merchant.id,
                    email=first_order.customer_email,
                    phone=first_order.customer_phone,
                    first_name=first_order.customer_first_name,
                    last_name=first_order.customer_last_name,
                )
            try:
                updated_data = await customer_service.link_device_to_profile(
                    db=db,
                    profile=profile,
                    platform_sender_id=context.platform_sender_id or context.session_id,
                    conversation_data=conversation_data,
                )
            except Exception as e:
                logger.warning("device_link_failed_after_order_lookup", error=str(e))
                updated_data["customer_email"] = first_order.customer_email

        return ConversationResponse(
            message=response_text,
            intent="order_tracking",
            confidence=1.0,
            order=order_dict,
            metadata=updated_data,
        )

    async def _handle_cross_device_email_lookup(
        self,
        db: AsyncSession,
        merchant: Merchant,
        customer_service: CustomerLookupService,
        tracking_service,
        email: str,
        context: ConversationContext,
    ) -> ConversationResponse:
        """Handle cross-device lookup by email.

        Story 4-13: Smart cross-device order lookup flow.

        Args:
            db: Database session
            merchant: Merchant configuration
            customer_service: Customer lookup service
            tracking_service: Order tracking service
            email: Customer email to lookup
            context: Conversation context

        Returns:
            ConversationResponse with order status or error
        """
        orders = await tracking_service.track_order_by_customer_email(
            db=db,
            merchant_id=merchant.id,
            email=email,
            limit=5,
        )

        profile = await customer_service.find_by_email(
            db=db,
            merchant_id=merchant.id,
            email=email,
        )

        if not profile and orders:
            first_order = orders[0]
            profile = await customer_service.upsert_customer_profile(
                db=db,
                merchant_id=merchant.id,
                email=email,
                phone=first_order.customer_phone,
                first_name=first_order.customer_first_name,
                last_name=first_order.customer_last_name,
            )

        if not orders and not profile:
            return ConversationResponse(
                message=PersonalityAwareResponseFormatter.format_response(
                    "order_tracking",
                    "not_found",
                    merchant.personality,
                ),
                intent="order_tracking",
                confidence=1.0,
            )

        if not orders:
            customer_name = profile.first_name or "there" if profile else "there"
            welcome_msg = PersonalityAwareResponseFormatter.format_response(
                "order_tracking",
                "welcome_back",
                merchant.personality,
                customer_name=customer_name,
            )
            selector = get_transition_selector()
            browse_phrase = selector.select(
                TransitionCategory.OFFERING_HELP,
                merchant.personality,
                conversation_id=str(context.session_id),
                mode="ecommerce",
            )
            return ConversationResponse(
                message=f"{welcome_msg} But I couldn't find any orders yet. {browse_phrase}",
                intent="order_tracking",
                confidence=1.0,
            )

        customer_name = profile.first_name if profile and profile.first_name else None
        greeting = f"Hey {customer_name}! " if customer_name else ""

        if len(orders) == 1:
            order = orders[0]
            product_images = await self._fetch_product_images(db=db, merchant=merchant, order=order)
            raw_response = tracking_service.format_order_response(order, product_images)
            selector = get_transition_selector()
            transition = selector.select(
                TransitionCategory.SHOWING_RESULTS,
                merchant.personality,
                conversation_id=str(context.session_id),
                mode="ecommerce",
            )
            response_text = f"{greeting}{transition}\n\n{raw_response}"
        else:
            response_parts = []
            for order in orders:
                product_images = await self._fetch_product_images(
                    db=db, merchant=merchant, order=order
                )
                formatted = tracking_service.format_order_response(order, product_images)
                response_parts.append(formatted)
            raw_text = "\n\n---\n\n".join(response_parts)
            selector = get_transition_selector()
            transition = selector.select(
                TransitionCategory.SHOWING_RESULTS,
                merchant.personality,
                conversation_id=str(context.session_id),
                mode="ecommerce",
            )
            response_text = f"{greeting}{transition}\n\n{raw_text}"

        device_link_name = customer_name or "there"
        device_link_msg = PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "device_linked",
            merchant.personality,
            customer_name=device_link_name,
        )

        conversation_data = context.conversation_data or {}
        updated_data = conversation_data.copy()
        if profile:
            try:
                updated_data = await customer_service.link_device_to_profile(
                    db=db,
                    profile=profile,
                    platform_sender_id=context.platform_sender_id or context.session_id,
                    conversation_data=conversation_data,
                )
            except Exception as e:
                logger.warning("device_link_failed", error=str(e))
                updated_data["customer_email"] = email
        else:
            updated_data["customer_email"] = email

        logger.info(
            "cross_device_lookup_success",
            merchant_id=merchant.id,
            email=email,
            profile_id=profile.id if profile else None,
            order_count=len(orders),
        )

        orders_data = [
            {
                "order_number": order.order_number,
                "status": order.status,
                "tracking_number": order.tracking_number,
                "tracking_url": order.tracking_url,
                "items": order.items,
            }
            for order in orders
        ]

        return ConversationResponse(
            message=response_text + device_link_msg,
            intent="order_tracking",
            confidence=1.0,
            order=orders_data[0] if len(orders_data) == 1 else None,
            products=None,
            cart=None,
            checkout_url=None,
            fallback=False,
            fallback_url=None,
            metadata=updated_data,
        )

    async def _handle_order_not_found(
        self,
        db: AsyncSession,
        merchant: Merchant,
        tracking_service,
        customer_service: CustomerLookupService,
        result,
        order_number: str | None,
        context: ConversationContext,
    ) -> ConversationResponse:
        """Handle order not found with cross-device fallback prompt.

        Story 4-13: Prompt for email or order number.

        Args:
            db: Database session
            merchant: Merchant configuration
            tracking_service: Order tracking service
            customer_service: Customer lookup service
            result: Order tracking result
            order_number: Order number if provided
            context: Conversation context

        Returns:
            ConversationResponse with prompt for email/order number
        """
        response_text = tracking_service.format_order_not_found_response(
            lookup_type=result.lookup_type,
            order_number=order_number,
        )

        cross_device_prompt = "\n\n" + PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "prompt_email",
            merchant.personality,
        )

        # Set pending flag in both conversation_data (for persistence) and metadata (for current session)
        conversation_data = context.conversation_data or {}
        conversation_data[PENDING_CROSS_DEVICE_KEY] = True

        metadata = context.metadata or {}
        metadata[PENDING_CROSS_DEVICE_KEY] = True

        return ConversationResponse(
            message=response_text + cross_device_prompt,
            intent="order_tracking",
            confidence=1.0,
            metadata=metadata,
        )

    def _looks_like_order_number(self, message: str) -> bool:
        """Check if message looks like an order number.

        Args:
            message: User message

        Returns:
            True if message looks like an order number
        """
        cleaned = message.strip().lstrip("#")
        if len(cleaned) < 4 or len(cleaned) > 20:
            return False
        return bool(re.match(r"^[A-Za-z0-9\-]+$", cleaned))

    def _normalize_email(self, message: str) -> str | None:
        """Normalize and correct common email typos.

        Handles common mistakes like:
        - Missing @ symbol (usergmail.com -> user@gmail.com)
        - Comma instead of period (gmail,com -> gmail.com)
        - Double dots (gmail..com -> gmail.com)
        - Common domain typos (gmial -> gmail)

        Args:
            message: Raw message that might contain an email

        Returns:
            Normalized email if valid, None otherwise
        """
        import re

        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", message)
        if not email_match:
            return None

        email = email_match.group(0).strip().lower()

        while ".." in email:
            email = email.replace("..", ".")

        email = email.replace(",", ".")

        if "@" not in email:
            email = self._try_insert_at_symbol(email)
            if not email:
                return None

        parts = email.split("@")
        if len(parts) != 2:
            return None

        local, domain = parts

        domain_parts = domain.split(".")
        if len(domain_parts) < 2:
            return None

        domain_name = domain_parts[0]
        if domain_name in self._get_domain_typos():
            domain_parts[0] = self._get_domain_typos()[domain_name]
            domain = ".".join(domain_parts)

        normalized = f"{local}@{domain}"

        if EMAIL_PATTERN.match(normalized):
            return normalized

        return None

    def _try_insert_at_symbol(self, email: str) -> str | None:
        """Try to insert @ before a known email domain.

        Args:
            email: Email string without @ symbol

        Returns:
            Email with @ inserted if a known domain is found, None otherwise
        """
        sorted_domains = sorted(COMMON_EMAIL_DOMAINS, key=len, reverse=True)
        for domain in sorted_domains:
            if email.endswith(domain):
                local_part = email[: -len(domain)]
                if local_part:
                    return f"{local_part}@{domain}"
        for typo, correct in COMMON_DOMAIN_TYPOS.items():
            typo_domain = f"{typo}.com"
            if email.endswith(typo_domain):
                local_part = email[: -len(typo_domain)]
                if local_part:
                    return f"{local_part}@{correct}.com"
        return None

    def _get_domain_typos(self) -> dict[str, str]:
        """Get common domain typo corrections."""
        return COMMON_DOMAIN_TYPOS

    def _extract_email_from_history(self, context: ConversationContext) -> str | None:
        """Scan conversation history for previously provided email.

        Looks through recent messages for any valid email that was provided
        but may not have been processed correctly (e.g., due to typos).

        Args:
            context: Conversation context with message history

        Returns:
            First valid email found in history, None otherwise
        """
        history = context.conversation_history or []

        for msg in reversed(history[-5:]):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                normalized = self._normalize_email(content)
                if normalized:
                    logger.info(
                        "email_extracted_from_history",
                        email=normalized,
                    )
                    return normalized

        return None

    async def _fetch_product_images(
        self,
        db: AsyncSession,
        merchant: Merchant,
        order: Order,
    ) -> dict[str, str]:
        """Fetch product images from Shopify for order items.

        Story 5-13: Product images in order status.

        Args:
            db: Database session
            merchant: Merchant configuration
            order: Order with items

        Returns:
            Dictionary mapping product ID to image URL
        """
        if not order.items:
            return {}

        from app.services.shopify.product_service import get_products_by_ids

        product_ids = []
        for item in order.items:
            product_id = item.get("product_id") or item.get("id")
            if product_id:
                product_ids.append(str(product_id))

        if not product_ids:
            return {}

        try:
            products = await get_products_by_ids(
                access_token="",
                merchant_id=merchant.id,
                product_ids=product_ids,
                db=db,
            )

            product_images = {}
            for product_id, product_data in products.items():
                image_url = product_data.get("image_url") or (
                    product_data.get("images", [{}])[0].get("url")
                    if product_data.get("images")
                    else None
                )
                if image_url:
                    product_images[product_id] = image_url

            return product_images

        except Exception as e:
            logger.error(
                "order_handler_failed",
                merchant_id=merchant.id,
                error=str(e),
                error_type=type(e).__name__,
            )
            from app.services.conversation.error_recovery_service import (
                ErrorType,
                NaturalErrorRecoveryService,
            )

            return await NaturalErrorRecoveryService().recover(
                error_type=ErrorType.ORDER_LOOKUP_FAILED,
                merchant=merchant,
                context=context,
                error=e,
                intent="order_tracking",
                conversation_id=str(context.session_id),
            )
            return {}
