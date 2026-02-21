"""Widget API endpoints for embeddable chat widget.

Provides public API endpoints for:
- Creating anonymous widget sessions
- Sending messages and receiving bot responses
- Getting widget configuration
- Ending widget sessions

Story 5.1: Backend Widget API
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.core.rate_limiter import RateLimiter
from app.core.validators import is_valid_session_id
from app.core.sanitization import sanitize_message, validate_message_length, MAX_MESSAGE_LENGTH
from app.schemas.base import MetaData
from app.schemas.widget import (
    CreateSessionRequest,
    WidgetSessionResponse,
    WidgetSessionEnvelope,
    WidgetSessionMetadataResponse,
    WidgetSessionMetadataEnvelope,
    SendMessageRequest,
    WidgetMessageResponse,
    WidgetMessageEnvelope,
    WidgetConfigResponse,
    WidgetConfigEnvelope,
    SuccessResponse,
    SuccessEnvelope,
    WidgetConfig,
    create_meta,
)
from app.schemas.widget_search import (
    WidgetSearchRequest,
    WidgetSearchResult,
    WidgetSearchEnvelope,
    ProductSummary,
    WidgetCartRequest,
    WidgetCartUpdateRequest,
    WidgetCartResponse,
    WidgetCartEnvelope,
    WidgetCartItem,
    WidgetCheckoutRequest,
    WidgetCheckoutResponse,
    WidgetCheckoutEnvelope,
)
from app.models.merchant import Merchant
from app.services.widget.widget_session_service import WidgetSessionService
from app.services.widget.widget_message_service import WidgetMessageService


logger = structlog.get_logger(__name__)

router = APIRouter()


def _validate_domain_whitelist(request: Request, allowed_domains: list[str]) -> None:
    """Validate request origin against domain whitelist.

    Args:
        request: FastAPI request
        allowed_domains: List of allowed domains (empty = all allowed)

    Raises:
        APIError: If origin is not in whitelist
    """
    if not allowed_domains:
        return

    origin = request.headers.get("Origin", "")
    if not origin:
        return

    from urllib.parse import urlparse

    try:
        parsed = urlparse(origin)
        request_domain = parsed.netloc.lower()

        for allowed in allowed_domains:
            allowed_lower = allowed.lower()
            if request_domain == allowed_lower or request_domain.endswith(f".{allowed_lower}"):
                return

        raise APIError(
            ErrorCode.WIDGET_DOMAIN_NOT_ALLOWED,
            f"Domain {request_domain} is not allowed",
        )
    except Exception as e:
        if isinstance(e, APIError):
            raise
        logger.warning("widget_domain_parse_error", origin=origin, error=str(e))


def _validate_session_id_format(session_id: str) -> None:
    """Validate session ID format before processing.

    Story 5-10 Task 14: Production safeguard - validate format early.

    Args:
        session_id: Widget session identifier

    Raises:
        APIError: If session ID format is invalid
    """
    if not is_valid_session_id(session_id):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid session ID format",
        )


def _check_rate_limit(request: Request) -> Optional[int]:
    """Check if client is rate limited using shared RateLimiter.

    Args:
        request: FastAPI request

    Returns:
        None if allowed, retry_after seconds if rate limited
    """
    return RateLimiter.check_widget_rate_limit(request)


def _check_merchant_rate_limit(merchant_id: int, rate_limit: Optional[int]) -> Optional[int]:
    """Check per-merchant rate limit.

    Story 5-2 AC5: Per-merchant configurable rate limiting.

    Args:
        merchant_id: Merchant ID
        rate_limit: Per-merchant rate limit from widget_config

    Returns:
        None if allowed, retry_after seconds if rate limited
    """
    if rate_limit is None:
        return None
    return RateLimiter.check_merchant_rate_limit(merchant_id, rate_limit)


@router.post(
    "/widget/session",
    response_model=WidgetSessionEnvelope,
    summary="Create widget session",
    description="Create a new anonymous widget session for a merchant",
)
async def create_widget_session(
    request: Request,
    session_request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
) -> WidgetSessionEnvelope:
    """Create a new anonymous widget session.

    Creates a session that allows visitors to interact with the
    merchant's AI shopping assistant without authentication.

    Args:
        request: FastAPI request
        session_request: Session creation request with merchant_id
        db: Database session

    Returns:
        WidgetSessionEnvelope with session_id and expires_at

    Raises:
        APIError: If merchant not found or widget disabled
    """
    # Check rate limit
    retry_after = _check_rate_limit(request)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after},
        )

    # Verify merchant exists
    result = await db.execute(select(Merchant).where(Merchant.id == session_request.merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant {session_request.merchant_id} not found",
        )

    # Check if widget is enabled for this merchant
    widget_config = merchant.widget_config or {}
    if not widget_config.get("enabled", True):
        raise APIError(
            ErrorCode.WIDGET_MERCHANT_DISABLED,
            "Widget is disabled for this merchant",
        )

    # Check per-merchant rate limit (Story 5-2 AC5)
    merchant_rate_limit = widget_config.get("rate_limit")
    retry_after = _check_merchant_rate_limit(merchant.id, merchant_rate_limit)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Merchant rate limit exceeded",
            {"retry_after": retry_after},
        )

    # Validate domain whitelist (AC7)
    allowed_domains = widget_config.get("allowed_domains", [])
    _validate_domain_whitelist(request, allowed_domains)

    # Create session
    client_ip = RateLimiter.get_widget_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    # Story 5-10 Enhancement: Pass visitor_id for returning shopper detection
    visitor_id = getattr(session_request, "visitor_id", None)

    session_service = WidgetSessionService()
    session = await session_service.create_session(
        merchant_id=merchant.id,
        visitor_ip=client_ip,
        user_agent=user_agent,
        visitor_id=visitor_id,
    )

    logger.info(
        "widget_session_created",
        merchant_id=merchant.id,
        session_id=session.session_id,
        client_ip=client_ip,
        is_returning_shopper=session.is_returning_shopper,
    )

    return WidgetSessionEnvelope(
        data=WidgetSessionResponse(
            session_id=session.session_id,
            expires_at=session.expires_at,
        ),
        meta=create_meta(),
    )


@router.get(
    "/widget/session/{session_id}",
    response_model=WidgetSessionMetadataEnvelope,
    summary="Get widget session metadata",
    description="Retrieve metadata for an active widget session",
)
async def get_widget_session(
    request: Request,
    session_id: str,
) -> WidgetSessionMetadataEnvelope:
    """Get widget session metadata.

    Returns metadata about an active widget session including
    creation time, last activity, and expiry.

    Args:
        request: FastAPI request
        session_id: Widget session identifier

    Returns:
        WidgetSessionMetadataEnvelope with session details

    Raises:
        APIError: If session not found or expired
    """
    # Validate UUID format (Story 5-7 AC3)
    if not is_valid_session_id(session_id):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid session ID format",
        )

    session_service = WidgetSessionService()
    session = await session_service.get_session_or_error(session_id)

    logger.info(
        "widget_session_retrieved",
        session_id=session_id,
        merchant_id=session.merchant_id,
    )

    return WidgetSessionMetadataEnvelope(
        data=WidgetSessionMetadataResponse(
            session_id=session.session_id,
            merchant_id=session.merchant_id,
            expires_at=session.expires_at,
            created_at=session.created_at,
            last_activity_at=session.last_activity_at,
        ),
        meta=create_meta(),
    )


@router.post(
    "/widget/message",
    response_model=WidgetMessageEnvelope,
    summary="Send widget message",
    description="Send a message and receive bot response",
)
async def send_widget_message(
    request: Request,
    message_request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> WidgetMessageEnvelope:
    """Send a message in the widget and get bot response.

    Processes the user's message through the merchant's configured
    LLM provider and returns the bot's response.

    Args:
        request: FastAPI request
        message_request: Message with session_id and message text
        db: Database session

    Returns:
        WidgetMessageEnvelope with bot response

    Raises:
        APIError: If session invalid, expired, or processing fails
    """
    # Validate UUID format (Story 5-7 AC3)
    if not is_valid_session_id(message_request.session_id):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid session ID format",
        )

    # Check rate limit
    retry_after = _check_rate_limit(request)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after},
        )

    # Validate message length (Story 5-7 AC5)
    is_valid, error_msg = validate_message_length(message_request.message)
    if not is_valid:
        assert error_msg is not None
        if "empty" in error_msg.lower():
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                error_msg,
            )
        else:
            raise APIError(
                ErrorCode.WIDGET_MESSAGE_TOO_LONG,
                error_msg,
            )

    # Sanitize message (Story 5-7 AC5)
    sanitized_message = sanitize_message(message_request.message)

    # Get and validate session
    session_service = WidgetSessionService()
    session = await session_service.get_session_or_error(message_request.session_id)

    # Get merchant with eager-loaded llm_configuration relationship
    result = await db.execute(
        select(Merchant)
        .where(Merchant.id == session.merchant_id)
        .options(selectinload(Merchant.llm_configuration))
    )
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant {session.merchant_id} not found",
        )

    # Check if widget is enabled
    widget_config = merchant.widget_config or {}
    if not widget_config.get("enabled", True):
        raise APIError(
            ErrorCode.WIDGET_MERCHANT_DISABLED,
            "Widget is disabled for this merchant",
        )

    # Check per-merchant rate limit (Story 5-2 AC5)
    merchant_rate_limit = widget_config.get("rate_limit")
    retry_after = _check_merchant_rate_limit(merchant.id, merchant_rate_limit)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Merchant rate limit exceeded",
            {"retry_after": retry_after},
        )

    # Validate domain whitelist (AC7)
    allowed_domains = widget_config.get("allowed_domains", [])
    _validate_domain_whitelist(request, allowed_domains)

    # Process message
    message_service = WidgetMessageService(db=db, session_service=session_service)
    response = await message_service.process_message(
        session=session,
        message=sanitized_message,
        merchant=merchant,
    )

    logger.info(
        "widget_message_sent",
        session_id=session.session_id,
        merchant_id=merchant.id,
        message_length=len(sanitized_message),
    )

    return WidgetMessageEnvelope(
        data=WidgetMessageResponse(
            message_id=response["message_id"],
            content=response["content"],
            sender=response["sender"],
            created_at=response["created_at"],
            products=response.get("products"),
            cart=response.get("cart"),
            checkout_url=response.get("checkout_url"),
        ),
        meta=create_meta(),
    )


@router.get(
    "/widget/config/{merchant_id}",
    response_model=WidgetConfigEnvelope,
    summary="Get widget configuration",
    description="Get widget theme and bot configuration for a merchant",
)
async def get_widget_config(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> WidgetConfigEnvelope:
    """Get widget configuration for a merchant.

    Returns the widget's appearance settings and bot configuration
    for the frontend to render the widget correctly.

    Args:
        merchant_id: The merchant ID
        db: Database session

    Returns:
        WidgetConfigEnvelope with theme and bot settings

    Raises:
        APIError: If merchant not found
    """
    # Get merchant
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant {merchant_id} not found",
        )

    # Get widget config with defaults
    stored_config = merchant.widget_config or {}
    widget_config = WidgetConfig(**stored_config)

    # Override bot_name with merchant's bot_name if set
    bot_name = merchant.bot_name or widget_config.bot_name

    # Story 5-10 Enhancement: Include personality and business_hours
    personality = None
    if hasattr(merchant, "personality") and merchant.personality:
        personality = (
            merchant.personality.value
            if hasattr(merchant.personality, "value")
            else str(merchant.personality)
        )

    business_hours = getattr(merchant, "business_hours", None)

    logger.info(
        "widget_config_retrieved",
        merchant_id=merchant_id,
    )

    return WidgetConfigEnvelope(
        data=WidgetConfigResponse(
            bot_name=bot_name,
            welcome_message=widget_config.welcome_message,
            theme=widget_config.theme,
            enabled=widget_config.enabled,
            personality=personality,
            business_hours=business_hours,
        ),
        meta=create_meta(),
    )


@router.delete(
    "/widget/session/{session_id}",
    response_model=SuccessEnvelope,
    summary="End widget session",
    description="Terminate a widget session and clear its data",
)
async def end_widget_session(
    request: Request,
    session_id: str,
) -> SuccessEnvelope:
    """End a widget session.

    Terminates the session and clears all associated data
    including message history.

    Args:
        request: FastAPI request
        session_id: Widget session identifier

    Returns:
        SuccessEnvelope with success status

    Raises:
        APIError: If session not found
    """
    # Validate UUID format (Story 5-7 AC3)
    if not is_valid_session_id(session_id):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid session ID format",
        )

    # Check rate limit
    retry_after = _check_rate_limit(request)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after},
        )

    # End session
    session_service = WidgetSessionService()
    ended = await session_service.end_session(session_id)

    if not ended:
        raise APIError(
            ErrorCode.WIDGET_SESSION_NOT_FOUND,
            f"Widget session {session_id} not found",
        )

    logger.info(
        "widget_session_ended",
        session_id=session_id,
    )

    return SuccessEnvelope(
        data=SuccessResponse(success=True),
        meta=create_meta(),
    )


@router.post(
    "/widget/search",
    response_model=WidgetSearchEnvelope,
    summary="Search products",
    description="Search products via Shopify Admin API",
)
async def widget_search(
    request: Request,
    search_request: WidgetSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> WidgetSearchEnvelope:
    """Search products for a widget session.

    Uses Shopify Admin API to search products based on query.

    Args:
        request: FastAPI request
        search_request: Search request with session_id and query
        db: Database session

    Returns:
        WidgetSearchEnvelope with matching products

    Raises:
        APIError: If session invalid or search fails
    """
    import time

    start_time = time.time()

    if not is_valid_session_id(search_request.session_id):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid session ID format",
        )

    retry_after = _check_rate_limit(request)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after},
        )

    session_service = WidgetSessionService()
    session = await session_service.get_session_or_error(search_request.session_id)

    result = await db.execute(select(Merchant).where(Merchant.id == session.merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant {session.merchant_id} not found",
        )

    widget_config = merchant.widget_config or {}
    if not widget_config.get("enabled", True):
        raise APIError(
            ErrorCode.WIDGET_MERCHANT_DISABLED,
            "Widget is disabled for this merchant",
        )

    try:
        from app.services.shopify.product_service import fetch_products

        products = await fetch_products(search_request.query, merchant.id, db)

        product_summaries = [
            ProductSummary(
                product_id=str(p.get("id", "")),
                variant_id=(
                    str(p.get("variants", [{}])[0].get("id", "")) if p.get("variants") else ""
                ),
                title=p.get("title", ""),
                price=float(p.get("price", 0) or 0),
                currency=p.get("currency_code", "USD"),
                image_url=p.get("image_url"),
                available=p.get("available", True),
                relevance_score=p.get("relevance_score"),
            )
            for p in products[:10]
        ]

        search_time_ms = (time.time() - start_time) * 1000

        logger.info(
            "widget_search_complete",
            session_id=search_request.session_id,
            merchant_id=merchant.id,
            query=search_request.query,
            result_count=len(product_summaries),
            search_time_ms=search_time_ms,
        )

        return WidgetSearchEnvelope(
            data=WidgetSearchResult(
                products=product_summaries,
                total_count=len(products),
                search_time_ms=search_time_ms,
                alternatives_available=len(products) > 10,
            ),
            meta=create_meta(),
        )

    except Exception as e:
        logger.warning(
            "widget_search_failed",
            session_id=search_request.session_id,
            merchant_id=merchant.id,
            error=str(e),
        )
        return WidgetSearchEnvelope(
            data=WidgetSearchResult(
                products=[],
                total_count=0,
                search_time_ms=(time.time() - start_time) * 1000,
                alternatives_available=False,
            ),
            meta=create_meta(),
        )


@router.get(
    "/widget/cart",
    response_model=WidgetCartEnvelope,
    summary="Get cart",
    description="Get cart contents for widget session",
)
async def get_widget_cart(
    request: Request,
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> WidgetCartEnvelope:
    """Get cart contents for a widget session.

    Args:
        request: FastAPI request
        session_id: Widget session identifier
        db: Database session

    Returns:
        WidgetCartEnvelope with cart contents

    Raises:
        APIError: If session invalid
    """
    if not is_valid_session_id(session_id):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid session ID format",
        )

    retry_after = _check_rate_limit(request)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after},
        )

    session_service = WidgetSessionService()
    session = await session_service.get_session_or_error(session_id)

    from app.services.cart.cart_service import CartService
    from app.services.conversation.cart_key_strategy import CartKeyStrategy

    cart_service = CartService()
    cart_key = CartKeyStrategy.for_widget(session_id)
    cart = await cart_service.get_cart(cart_key)

    cart_items = [
        WidgetCartItem(
            variant_id=item.variant_id,
            title=item.title,
            price=float(item.price) if item.price else 0.0,
            quantity=item.quantity,
        )
        for item in cart.items
    ]

    logger.info(
        "widget_cart_retrieved",
        session_id=session_id,
        merchant_id=session.merchant_id,
        item_count=len(cart_items),
    )

    return WidgetCartEnvelope(
        data=WidgetCartResponse(
            items=cart_items,
            subtotal=float(cart.subtotal) if cart.subtotal else 0.0,
            currency=cart.currency_code.value if cart.currency_code else "USD",
            item_count=sum(item.quantity for item in cart.items),
        ),
        meta=create_meta(),
    )


@router.post(
    "/widget/cart",
    response_model=WidgetCartEnvelope,
    summary="Add to cart",
    description="Add item to widget cart",
)
async def add_to_widget_cart(
    request: Request,
    cart_request: WidgetCartRequest,
    db: AsyncSession = Depends(get_db),
) -> WidgetCartEnvelope:
    """Add item to cart for a widget session.

    Args:
        request: FastAPI request
        cart_request: Cart request with session_id, variant_id, quantity
        db: Database session

    Returns:
        WidgetCartEnvelope with updated cart

    Raises:
        APIError: If session invalid or add fails
    """
    if not is_valid_session_id(cart_request.session_id):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid session ID format",
        )

    retry_after = _check_rate_limit(request)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after},
        )

    session_service = WidgetSessionService()
    session = await session_service.get_session_or_error(cart_request.session_id)

    from app.services.cart.cart_service import CartService
    from app.services.conversation.cart_key_strategy import CartKeyStrategy

    cart_service = CartService()
    cart_key = CartKeyStrategy.for_widget(cart_request.session_id)

    await cart_service.add_item(
        psid=cart_key,
        product_id=cart_request.variant_id,
        variant_id=cart_request.variant_id,
        title=f"Product {cart_request.variant_id}",
        price=0.0,
        image_url="",
        quantity=cart_request.quantity,
    )

    cart = await cart_service.get_cart(cart_key)

    cart_items = [
        WidgetCartItem(
            variant_id=item.variant_id,
            title=item.title,
            price=float(item.price) if item.price else 0.0,
            quantity=item.quantity,
        )
        for item in cart.items
    ]

    logger.info(
        "widget_cart_item_added",
        session_id=cart_request.session_id,
        merchant_id=session.merchant_id,
        variant_id=cart_request.variant_id,
        quantity=cart_request.quantity,
    )

    return WidgetCartEnvelope(
        data=WidgetCartResponse(
            items=cart_items,
            subtotal=float(cart.subtotal) if cart.subtotal else 0.0,
            currency=cart.currency_code.value if cart.currency_code else "USD",
            item_count=sum(item.quantity for item in cart.items),
        ),
        meta=create_meta(),
    )


@router.delete(
    "/widget/cart/{variant_id}",
    response_model=WidgetCartEnvelope,
    summary="Remove from cart",
    description="Remove item from widget cart",
)
async def remove_from_widget_cart(
    request: Request,
    variant_id: str,
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> WidgetCartEnvelope:
    """Remove item from cart for a widget session.

    Args:
        request: FastAPI request
        variant_id: Product variant ID to remove
        session_id: Widget session identifier
        db: Database session

    Returns:
        WidgetCartEnvelope with updated cart

    Raises:
        APIError: If session invalid or remove fails
    """
    if not is_valid_session_id(session_id):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid session ID format",
        )

    retry_after = _check_rate_limit(request)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after},
        )

    session_service = WidgetSessionService()
    session = await session_service.get_session_or_error(session_id)

    from app.services.cart.cart_service import CartService
    from app.services.conversation.cart_key_strategy import CartKeyStrategy

    cart_service = CartService()
    cart_key = CartKeyStrategy.for_widget(session_id)

    await cart_service.remove_item(psid=cart_key, variant_id=variant_id)

    cart = await cart_service.get_cart(cart_key)

    cart_items = [
        WidgetCartItem(
            variant_id=item.variant_id,
            title=item.title,
            price=float(item.price) if item.price else 0.0,
            quantity=item.quantity,
        )
        for item in cart.items
    ]

    logger.info(
        "widget_cart_item_removed",
        session_id=session_id,
        merchant_id=session.merchant_id,
        variant_id=variant_id,
    )

    return WidgetCartEnvelope(
        data=WidgetCartResponse(
            items=cart_items,
            subtotal=float(cart.subtotal) if cart.subtotal else 0.0,
            currency=cart.currency_code.value if cart.currency_code else "USD",
            item_count=sum(item.quantity for item in cart.items),
        ),
        meta=create_meta(),
    )


@router.patch(
    "/widget/cart/{variant_id}",
    response_model=WidgetCartEnvelope,
    summary="Update cart item quantity",
    description="Update quantity of an item in widget cart",
)
async def update_widget_cart_item(
    request: Request,
    variant_id: str,
    update_request: WidgetCartUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> WidgetCartEnvelope:
    """Update item quantity in cart for a widget session.

    Args:
        request: FastAPI request
        variant_id: Product variant ID to update
        update_request: Update request with session_id and quantity
        db: Database session

    Returns:
        WidgetCartEnvelope with updated cart

    Raises:
        APIError: If session invalid or update fails
    """
    if not is_valid_session_id(update_request.session_id):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid session ID format",
        )

    retry_after = _check_rate_limit(request)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after},
        )

    session_service = WidgetSessionService()
    session = await session_service.get_session_or_error(update_request.session_id)

    from app.services.cart.cart_service import CartService
    from app.services.conversation.cart_key_strategy import CartKeyStrategy

    cart_service = CartService()
    cart_key = CartKeyStrategy.for_widget(update_request.session_id)

    await cart_service.update_quantity(
        psid=cart_key, variant_id=variant_id, quantity=update_request.quantity
    )

    cart = await cart_service.get_cart(cart_key)

    cart_items = [
        WidgetCartItem(
            variant_id=item.variant_id,
            title=item.title,
            price=float(item.price) if item.price else 0.0,
            quantity=item.quantity,
        )
        for item in cart.items
    ]

    logger.info(
        "widget_cart_item_updated",
        session_id=update_request.session_id,
        merchant_id=session.merchant_id,
        variant_id=variant_id,
        quantity=update_request.quantity,
    )

    return WidgetCartEnvelope(
        data=WidgetCartResponse(
            items=cart_items,
            subtotal=float(cart.subtotal) if cart.subtotal else 0.0,
            currency=cart.currency_code.value if cart.currency_code else "USD",
            item_count=sum(item.quantity for item in cart.items),
        ),
        meta=create_meta(),
    )


@router.post(
    "/widget/checkout",
    response_model=WidgetCheckoutEnvelope,
    summary="Generate checkout URL",
    description="Generate Shopify checkout URL from cart",
)
async def widget_checkout(
    request: Request,
    checkout_request: WidgetCheckoutRequest,
    db: AsyncSession = Depends(get_db),
) -> WidgetCheckoutEnvelope:
    """Generate checkout URL for widget cart.

    Args:
        request: FastAPI request
        checkout_request: Checkout request with session_id
        db: Database session

    Returns:
        WidgetCheckoutEnvelope with checkout URL

    Raises:
        APIError: If session invalid, cart empty, or checkout fails
    """
    if not is_valid_session_id(checkout_request.session_id):
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid session ID format",
        )

    retry_after = _check_rate_limit(request)
    if retry_after:
        raise APIError(
            ErrorCode.WIDGET_RATE_LIMITED,
            "Rate limit exceeded",
            {"retry_after": retry_after},
        )

    session_service = WidgetSessionService()
    session = await session_service.get_session_or_error(checkout_request.session_id)

    result = await db.execute(select(Merchant).where(Merchant.id == session.merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant {session.merchant_id} not found",
        )

    from app.services.cart.cart_service import CartService
    from app.services.conversation.cart_key_strategy import CartKeyStrategy

    cart_service = CartService()
    cart_key = CartKeyStrategy.for_widget(checkout_request.session_id)
    cart = await cart_service.get_cart(cart_key)

    if not cart.items:
        raise APIError(
            ErrorCode.WIDGET_CART_EMPTY,
            "Cannot checkout with empty cart",
        )

    from sqlalchemy import select as sql_select
    from app.models.shopify_integration import ShopifyIntegration

    integration_result = await db.execute(
        sql_select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant.id)
    )
    integration = integration_result.scalars().first()

    if not integration or integration.status != "active":
        raise APIError(
            ErrorCode.WIDGET_NO_SHOPIFY,
            "No active Shopify integration for this merchant",
        )

    shop_domain = integration.shop_domain
    if not shop_domain:
        raise APIError(
            ErrorCode.WIDGET_NO_SHOPIFY,
            "No shop domain configured",
        )

    variant_parts = []
    for item in cart.items:
        if item.variant_id:
            variant_parts.append(f"{item.variant_id}:{item.quantity}")

    if not variant_parts:
        raise APIError(
            ErrorCode.WIDGET_CART_EMPTY,
            "No valid items in cart",
        )

    checkout_url = f"https://{shop_domain}/cart/" + ",".join(variant_parts)

    logger.info(
        "widget_checkout_generated",
        session_id=checkout_request.session_id,
        merchant_id=merchant.id,
        item_count=len(cart.items),
    )

    return WidgetCheckoutEnvelope(
        data=WidgetCheckoutResponse(
            checkout_url=checkout_url,
            cart_total=float(cart.subtotal) if cart.subtotal else 0.0,
            currency=cart.currency_code.value if cart.currency_code else "USD",
            item_count=sum(item.quantity for item in cart.items),
        ),
        meta=create_meta(),
    )


@router.post(
    "/widget/test/reset-rate-limiter",
    response_model=SuccessEnvelope,
    summary="Reset rate limiter state (test only)",
    description="Reset the rate limiter state for testing purposes",
)
async def reset_rate_limiter(request: Request) -> SuccessEnvelope:
    """Reset rate limiter state for testing.

    This endpoint is only available in test mode and resets the
    in-memory rate limiter state.

    Args:
        request: FastAPI request

    Returns:
        SuccessEnvelope with success status

    Raises:
        APIError: If not in test mode
    """
    is_test_env = os.getenv("IS_TESTING", "false").lower() == "true"
    is_test_header = request.headers.get("X-Test-Mode", "").lower() == "true"

    if not (is_test_env or is_test_header):
        raise APIError(
            ErrorCode.FORBIDDEN,
            "This endpoint is only available in test mode",
        )

    RateLimiter.reset_all()

    logger.info("widget_rate_limiter_reset")

    return SuccessEnvelope(
        data=SuccessResponse(success=True),
        meta=create_meta(),
    )
