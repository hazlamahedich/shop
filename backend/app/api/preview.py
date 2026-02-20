"""Bot preview mode API endpoints (Story 1.13).

Provides endpoints for merchants to test their bot configuration
in a sandbox environment before exposing it to real customers.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.api.helpers import create_meta, get_merchant_id, verify_merchant_exists
from app.schemas.preview import (
    PreviewMessageRequest,
    PreviewSessionResponse,
    PreviewResetResponse,
    PreviewMessageEnvelope,
    PreviewSessionEnvelope,
    PreviewResetEnvelope,
)
from app.services.preview.preview_service import PreviewService


# Maximum age for preview sessions before cleanup (1 hour)
PREVIEW_SESSION_MAX_AGE_SECONDS = 3600


logger = structlog.get_logger(__name__)

router = APIRouter()


@router.post(
    "/preview/conversation",
    response_model=PreviewSessionEnvelope,
)
async def create_preview_conversation(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> PreviewSessionEnvelope:
    """
    Create a new preview conversation session.

    Initializes a sandbox environment where merchants can test their
    bot configuration without affecting real conversations or incurring
    LLM costs.

    NOTE: CSRF protection is provided by CSRFMiddleware (see main.py:164).
    All POST requests automatically require valid CSRF tokens unless the path
    is in BYPASS_PATHS. The /api/v1/preview/conversation path is NOT in
    the bypass list, so it is protected by default.

    NOTE: Authentication in DEBUG mode uses X-Merchant-Id header for
    convenience. In production, proper JWT authentication should be used.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        PreviewSessionEnvelope with session info and starter prompts

    Raises:
        APIError: If authentication fails or merchant not found
    """
    merchant_id = get_merchant_id(request)
    merchant = await verify_merchant_exists(merchant_id, db)

    preview_service = PreviewService(db=db)
    session_data = preview_service.create_session(merchant)

    logger.info(
        "preview_conversation_created",
        merchant_id=merchant_id,
        session_id=session_data["preview_session_id"],
    )

    return PreviewSessionEnvelope(
        data=PreviewSessionResponse(**session_data),
        meta=create_meta(),
    )


@router.post(
    "/preview/message",
    response_model=PreviewMessageEnvelope,
)
async def send_preview_message(
    request: Request,
    message_request: PreviewMessageRequest,
    db: AsyncSession = Depends(get_db),
) -> PreviewMessageEnvelope:
    """
    Send a message in preview mode and get bot response.

    Processes a merchant's test message through the bot configuration
    and returns the bot's response with confidence scoring.

    NOTE: CSRF protection is provided by CSRFMiddleware (see main.py:164).
    All POST requests automatically require valid CSRF tokens unless the path
    is in BYPASS_PATHS. The /api/v1/preview/message path is NOT in
    the bypass list, so it is protected by default.

    NOTE: Authentication in DEBUG mode uses X-Merchant-Id header for
    convenience. In production, proper JWT authentication should be used.

    Args:
        request: FastAPI request with merchant authentication
        message_request: Message with preview session ID
        db: Database session

    Returns:
        PreviewMessageEnvelope with bot response and confidence metadata

    Raises:
        APIError: If session not found, message invalid, or generation fails
    """
    merchant_id = get_merchant_id(request)
    merchant = await verify_merchant_exists(merchant_id, db)

    # Validate message format
    if not message_request.message or not message_request.message.strip():
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Message cannot be empty",
        )

    preview_service = PreviewService(db=db)

    # Verify session exists
    session = preview_service.get_session(message_request.preview_session_id)
    if not session:
        raise APIError(
            ErrorCode.NOT_FOUND,
            f"Preview session {message_request.preview_session_id} not found or has expired",
        )

    try:
        # Send message and get bot response
        response = await preview_service.send_message(
            session_id=message_request.preview_session_id,
            message=message_request.message,
            merchant=merchant,
        )

        logger.info(
            "preview_message_sent",
            merchant_id=merchant_id,
            session_id=message_request.preview_session_id,
            confidence=response.confidence,
        )

        return PreviewMessageEnvelope(
            data=response,
            meta=create_meta(),
        )

    except ValueError as e:
        # Session not found error
        raise APIError(
            ErrorCode.NOT_FOUND,
            str(e),
        )
    except APIError:
        # Re-raise APIError as-is
        raise
    except Exception as e:
        logger.error(
            "preview_message_failed",
            merchant_id=merchant_id,
            session_id=message_request.preview_session_id,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise APIError(
            ErrorCode.LLM_PROVIDER_ERROR,
            f"Failed to generate bot response: {str(e)}",
        )


@router.delete(
    "/preview/conversation/{preview_session_id}",
    response_model=PreviewResetEnvelope,
)
async def reset_preview_conversation(
    request: Request,
    preview_session_id: str,
    db: AsyncSession = Depends(get_db),
) -> PreviewResetEnvelope:
    """
    Reset or delete a preview conversation.

    Clears all messages from the current preview session, allowing
    the merchant to start fresh with a new test conversation.

    NOTE: CSRF protection is provided by CSRFMiddleware (see main.py:164).
    All DELETE requests automatically require valid CSRF tokens unless the path
    is in BYPASS_PATHS. The /api/v1/preview/conversation path is NOT in
    the bypass list, so it is protected by default.

    NOTE: Authentication in DEBUG mode uses X-Merchant-Id header for
    convenience. In production, proper JWT authentication should be used.

    Args:
        request: FastAPI request with merchant authentication
        preview_session_id: The preview session ID to reset
        db: Database session

    Returns:
        PreviewResetEnvelope with reset status

    Raises:
        APIError: If session not found or reset fails
    """
    merchant_id = get_merchant_id(request)
    # Verify merchant exists but don't need the merchant object for reset
    await verify_merchant_exists(merchant_id, db)

    preview_service = PreviewService(db=db)

    # Try to reset the session (clears messages)
    reset_success = preview_service.reset_session(preview_session_id)

    if not reset_success:
        # If reset fails, the session might not exist
        raise APIError(
            ErrorCode.NOT_FOUND,
            f"Preview session {preview_session_id} not found",
        )

    logger.info(
        "preview_conversation_reset",
        merchant_id=merchant_id,
        session_id=preview_session_id,
    )

    return PreviewResetEnvelope(
        data=PreviewResetResponse(
            cleared=True,
            message="Preview conversation reset successfully",
        ),
        meta=create_meta(),
    )


@router.post(
    "/preview/cleanup",
    response_model=dict,
)
async def cleanup_old_preview_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Clean up old preview sessions from memory.

    This endpoint removes preview sessions that have exceeded the maximum age
    to prevent memory leaks. Can be called periodically by a background task.

    NOTE: This endpoint is authenticated to prevent abuse.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        Dictionary with cleanup results
    """
    # Verify authentication but don't need merchant object
    merchant_id = get_merchant_id(request)
    await verify_merchant_exists(merchant_id, db)

    preview_service = PreviewService(db=db)
    removed_count = preview_service.cleanup_old_sessions(
        max_age_seconds=PREVIEW_SESSION_MAX_AGE_SECONDS
    )

    logger.info(
        "preview_sessions_cleanup_completed",
        merchant_id=merchant_id,
        removed_count=removed_count,
    )

    return {
        "removed_count": removed_count,
        "message": f"Cleaned up {removed_count} old preview session(s)",
    }


@router.get(
    "/preview/products",
)
async def search_preview_products(
    request: Request,
    query: str = "",
    max_price: float | None = None,
    category: str | None = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Search products for preview chat with images and details.

    Used by the preview chat to display product cards with images,
    prices, and inventory when the bot mentions products.

    Args:
        request: FastAPI request with merchant authentication
        query: Optional search query (searches product titles)
        max_price: Optional maximum price filter
        category: Optional category filter
        limit: Maximum number of products to return (default 10)
        db: Database session

    Returns:
        Dictionary with products list including images, prices, inventory
    """
    from app.services.shopify.product_service import fetch_products
    from app.models.shopify_integration import ShopifyIntegration

    merchant_id = get_merchant_id(request)
    merchant = await verify_merchant_exists(merchant_id, db)

    all_products = await fetch_products("", merchant_id, db)

    filtered = all_products

    if query and query.strip():
        query_lower = query.lower().strip()
        filtered = [
            p
            for p in filtered
            if query_lower in (p.get("title") or "").lower()
            or query_lower in (p.get("description") or "").lower()
        ]

    if max_price is not None:
        try:
            max_price_float = float(max_price)
            filtered = [
                p
                for p in filtered
                if p.get("price") and float(p.get("price", 0)) <= max_price_float
            ]
        except (ValueError, TypeError):
            pass

    if category and category.strip():
        category_lower = category.lower().strip()
        filtered = [p for p in filtered if category_lower in (p.get("product_type") or "").lower()]

    filtered.sort(key=lambda p: float(p.get("price") or 0))

    products = filtered[:limit]

    formatted_products = []
    for p in products:
        formatted_products.append(
            {
                "id": p.get("id"),
                "title": p.get("title"),
                "description": p.get("description", "")[:200] if p.get("description") else "",
                "image_url": p.get("image_url"),
                "price": p.get("price"),
                "available": p.get("available", True),
                "inventory_quantity": p.get("inventory_quantity", 0),
                "product_type": p.get("product_type"),
                "vendor": p.get("vendor"),
                "variant_id": p.get("variant_id"),
            }
        )

    shop_domain = None
    result = await db.execute(
        select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant_id)
    )
    integration = result.scalars().first()
    if integration:
        shop_domain = integration.shop_domain

    return {
        "data": {
            "products": formatted_products,
            "total": len(filtered),
            "query": query,
            "filters": {
                "max_price": max_price,
                "category": category,
            },
            "shop_domain": shop_domain,
        },
        "meta": create_meta(),
    }


@router.get(
    "/preview/products/{product_id}",
)
async def get_preview_product(
    request: Request,
    product_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get single product details for preview chat.

    Returns full product information including image, description,
    price, and inventory for the product detail modal.

    Args:
        request: FastAPI request with merchant authentication
        product_id: The product ID to fetch
        db: Database session

    Returns:
        Product details with image, price, inventory
    """
    from app.services.shopify.product_service import fetch_products
    from app.models.shopify_integration import ShopifyIntegration

    merchant_id = get_merchant_id(request)
    await verify_merchant_exists(merchant_id, db)

    all_products = await fetch_products("", merchant_id, db)

    product = None
    for p in all_products:
        if str(p.get("id")) == str(product_id):
            product = p
            break

    if not product:
        raise APIError(
            ErrorCode.NOT_FOUND,
            f"Product {product_id} not found",
        )

    shop_domain = None
    result = await db.execute(
        select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant_id)
    )
    integration = result.scalars().first()
    if integration:
        shop_domain = integration.shop_domain

    return {
        "data": {
            "id": product.get("id"),
            "title": product.get("title"),
            "description": product.get("description", ""),
            "image_url": product.get("image_url"),
            "price": product.get("price"),
            "available": product.get("available", True),
            "inventory_quantity": product.get("inventory_quantity", 0),
            "product_type": product.get("product_type"),
            "vendor": product.get("vendor"),
            "variant_id": product.get("variant_id"),
            "shop_domain": shop_domain,
        },
        "meta": create_meta(),
    }


@router.get(
    "/preview/shop-domain",
)
async def get_preview_shop_domain(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get the Shopify shop domain for checkout redirect.

    Returns the shop domain needed to build cart permalinks for checkout.

    Args:
        request: FastAPI request with merchant authentication
        db: Database session

    Returns:
        Shop domain for checkout
    """
    from app.models.shopify_integration import ShopifyIntegration

    merchant_id = get_merchant_id(request)
    await verify_merchant_exists(merchant_id, db)

    result = await db.execute(
        select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == merchant_id)
    )
    integration = result.scalars().first()

    if not integration:
        raise APIError(
            ErrorCode.NOT_FOUND,
            "No Shopify store connected",
        )

    return {
        "data": {
            "shop_domain": integration.shop_domain,
        },
        "meta": create_meta(),
    }


@router.get(
    "/preview/orders/{order_number}",
)
async def track_preview_order(
    request: Request,
    order_number: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Track an order by order number for preview chat.

    Used by the preview chat bot to look up order status and tracking info.

    Args:
        request: FastAPI request with merchant authentication
        order_number: The order number to look up (e.g., "1001" or "#1001")
        db: Database session

    Returns:
        Order details including status, tracking, and formatted response
    """
    from app.services.order_tracking.order_tracking_service import OrderTrackingService

    merchant_id = get_merchant_id(request)
    await verify_merchant_exists(merchant_id, db)

    tracking_service = OrderTrackingService()
    result = await tracking_service.track_order_by_number(db, merchant_id, order_number)

    if not result.found or not result.order:
        return {
            "data": {
                "found": False,
                "order_number": order_number,
                "message": f"I couldn't find order #{order_number}. Please double-check the number and try again.",
            },
            "meta": create_meta(),
        }

    order = result.order
    return {
        "data": {
            "found": True,
            "order_number": order.order_number,
            "status": order.status,
            "fulfillment_status": order.fulfillment_status,
            "tracking_number": order.tracking_number,
            "tracking_url": order.tracking_url,
            "customer_email": order.customer_email,
            "total": str(order.total),
            "currency": order.currency_code,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "estimated_delivery": order.estimated_delivery.isoformat()
            if order.estimated_delivery
            else None,
            "formatted_response": tracking_service.format_order_response(order),
        },
        "meta": create_meta(),
    }


@router.get(
    "/preview/orders",
)
async def list_preview_orders(
    request: Request,
    email: str | None = None,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List recent orders for preview chat.

    Used by the preview chat bot to show order history.
    Can filter by customer email.

    Args:
        request: FastAPI request with merchant authentication
        email: Optional customer email to filter by
        limit: Maximum number of orders to return (default 5)
        db: Database session

    Returns:
        List of recent orders with basic details
    """
    from app.models.order import Order

    merchant_id = get_merchant_id(request)
    await verify_merchant_exists(merchant_id, db)

    stmt = (
        select(Order)
        .where(Order.merchant_id == merchant_id)
        .order_by(Order.created_at.desc())
        .limit(limit)
    )

    if email:
        stmt = stmt.where(Order.customer_email == email.lower().strip())

    result = await db.execute(stmt)
    orders = result.scalars().all()

    formatted_orders = []
    for order in orders:
        formatted_orders.append(
            {
                "order_number": order.order_number,
                "status": order.status,
                "tracking_number": order.tracking_number,
                "total": str(order.total),
                "currency": order.currency_code,
                "created_at": order.created_at.isoformat() if order.created_at else None,
            }
        )

    return {
        "data": {
            "orders": formatted_orders,
            "total": len(formatted_orders),
        },
        "meta": create_meta(),
    }
