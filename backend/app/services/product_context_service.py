"""Product context service for enriching system prompts with store data.

Provides product categories, pinned products, and order context to LLM system prompts
so the bot knows what the store actually sells and can help with order tracking.
"""

from __future__ import annotations

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.product_pin import ProductPin
from app.models.order import Order
from app.services.shopify.product_service import fetch_products


logger = structlog.get_logger(__name__)


async def get_product_context(
    db: AsyncSession,
    merchant_id: int,
    max_pinned: int = 5,
    max_products: int = 15,
) -> dict:
    """Get product context for system prompt enrichment.

    Args:
        db: Database session
        merchant_id: Merchant ID
        max_pinned: Maximum number of pinned products to include
        max_products: Maximum number of products to include in full list

    Returns:
        Dictionary with:
        - categories: List of unique product types/categories
        - pinned_products: List of pinned product titles with prices
        - products: List of all products (for price-based queries)
        - price_range: Min and max prices from products
    """
    context = {
        "categories": [],
        "pinned_products": [],
        "products": [],
        "price_range": None,
    }

    try:
        # Fetch pinned products from database
        pinned_result = await db.execute(
            select(ProductPin)
            .where(ProductPin.merchant_id == merchant_id)
            .order_by(ProductPin.pinned_order)
            .limit(max_pinned)
        )
        pinned_pins = pinned_result.scalars().all()

        # Fetch all products to get categories and price range
        all_products = await fetch_products("", merchant_id, db)

        # Extract unique categories
        categories = set()
        prices = []
        for product in all_products:
            if product.get("product_type"):
                categories.add(product["product_type"])
            if product.get("price"):
                try:
                    prices.append(float(product["price"]))
                except (ValueError, TypeError):
                    pass

        context["categories"] = sorted(list(categories))[:10]  # Limit to 10 categories

        # Calculate price range
        if prices:
            context["price_range"] = {
                "min": min(prices),
                "max": max(prices),
            }

        # Build pinned products list with details
        pinned_map = {p.product_id: p for p in pinned_pins}
        for product in all_products:
            if product["id"] in pinned_map and len(context["pinned_products"]) < max_pinned:
                pinned_info = {
                    "title": product["title"],
                }
                if product.get("price"):
                    pinned_info["price"] = product["price"]
                if product.get("product_type"):
                    pinned_info["category"] = product["product_type"]
                context["pinned_products"].append(pinned_info)

        # Build full products list (sorted by price for variety)
        sorted_products = sorted(all_products, key=lambda p: float(p.get("price", 0) or 0))
        for product in sorted_products[:max_products]:
            product_info = {
                "title": product["title"],
            }
            if product.get("price"):
                product_info["price"] = product["price"]
            if product.get("product_type"):
                product_info["category"] = product["product_type"]
            context["products"].append(product_info)

        logger.debug(
            "product_context_fetched",
            merchant_id=merchant_id,
            categories_count=len(context["categories"]),
            pinned_count=len(context["pinned_products"]),
            products_count=len(context["products"]),
            has_price_range=context["price_range"] is not None,
        )

    except Exception as e:
        logger.warning(
            "product_context_fetch_failed",
            merchant_id=merchant_id,
            error=str(e),
        )

    return context


def format_product_context_for_prompt(context: dict) -> str:
    """Format product context for inclusion in system prompt.

    Args:
        context: Product context dictionary from get_product_context

    Returns:
        Formatted string for system prompt
    """
    parts = []

    if context.get("categories"):
        categories_str = ", ".join(context["categories"])
        parts.append(f"Product Categories: {categories_str}")

    # Include products list with prices (for price-based queries)
    if context.get("products"):
        product_lines = []
        for product in context["products"]:
            line = f"- {product['title']}"
            if product.get("price"):
                line += f" (${product['price']})"
            product_lines.append(line)
        parts.append("Available Products:\n" + "\n".join(product_lines))

    # Also highlight featured/pinned products if any
    if context.get("pinned_products"):
        pinned_lines = []
        for product in context["pinned_products"]:
            line = f"- {product['title']}"
            if product.get("price"):
                line += f" (${product['price']})"
            pinned_lines.append(line)
        parts.append("Featured Products:\n" + "\n".join(pinned_lines))

    if context.get("price_range"):
        pr = context["price_range"]
        parts.append(f"Price Range: ${pr['min']:.2f} - ${pr['max']:.2f}")

    return "\n\n".join(parts) if parts else ""


async def get_product_context_prompt_section(
    db: Optional[AsyncSession],
    merchant_id: int,
) -> str:
    """Get formatted product context section for system prompts.

    Convenience function that combines fetching and formatting.

    Args:
        db: Database session (optional, returns empty string if None)
        merchant_id: Merchant ID

    Returns:
        Formatted product context string, or empty string if unavailable
    """
    if not db:
        return ""

    try:
        context = await get_product_context(db, merchant_id)
        return format_product_context_for_prompt(context)
    except Exception as e:
        logger.warning(
            "product_context_section_failed",
            merchant_id=merchant_id,
            error=str(e),
        )
        return ""


async def get_order_context(
    db: AsyncSession,
    merchant_id: int,
    max_orders: int = 10,
) -> dict:
    """Get order context for system prompt enrichment.

    Args:
        db: Database session
        merchant_id: Merchant ID
        max_orders: Maximum number of recent orders to include

    Returns:
        Dictionary with:
        - recent_orders: List of recent order numbers and statuses
        - total_orders: Total count of orders
    """
    context = {
        "recent_orders": [],
        "total_orders": 0,
    }

    try:
        count_result = await db.execute(select(Order).where(Order.merchant_id == merchant_id))
        all_orders = count_result.scalars().all()
        context["total_orders"] = len(all_orders)

        recent_result = await db.execute(
            select(Order)
            .where(Order.merchant_id == merchant_id)
            .order_by(Order.created_at.desc())
            .limit(max_orders)
        )
        recent_orders = recent_result.scalars().all()

        for order in recent_orders:
            order_info = {
                "order_number": order.order_number,
                "status": order.status,
            }
            if order.tracking_number:
                order_info["tracking_number"] = order.tracking_number
            if order.customer_email:
                order_info["email"] = order.customer_email
            context["recent_orders"].append(order_info)

        logger.debug(
            "order_context_fetched",
            merchant_id=merchant_id,
            total_orders=context["total_orders"],
            recent_count=len(context["recent_orders"]),
        )

    except Exception as e:
        logger.warning(
            "order_context_fetch_failed",
            merchant_id=merchant_id,
            error=str(e),
        )

    return context


def format_order_context_for_prompt(context: dict) -> str:
    """Format order context for inclusion in system prompt.

    Args:
        context: Order context dictionary from get_order_context

    Returns:
        Formatted string for system prompt
    """
    parts = []

    total = context.get("total_orders", 0)
    if total > 0:
        parts.append(f"You have {total} order(s) in the system.")

        recent = context.get("recent_orders", [])
        if recent:
            order_lines = []
            for order in recent[:5]:
                line = f"- Order #{order['order_number']}: {order['status']}"
                if order.get("tracking_number"):
                    line += f" (Tracking: {order['tracking_number']})"
                order_lines.append(line)
            parts.append("Recent Orders:\n" + "\n".join(order_lines))

    return "\n\n".join(parts) if parts else ""


async def get_order_context_prompt_section(
    db: Optional[AsyncSession],
    merchant_id: int,
) -> str:
    """Get formatted order context section for system prompts.

    Args:
        db: Database session (optional, returns empty string if None)
        merchant_id: Merchant ID

    Returns:
        Formatted order context string, or empty string if unavailable
    """
    if not db:
        return ""

    try:
        context = await get_order_context(db, merchant_id)
        return format_order_context_for_prompt(context)
    except Exception as e:
        logger.warning(
            "order_context_section_failed",
            merchant_id=merchant_id,
            error=str(e),
        )
        return ""
