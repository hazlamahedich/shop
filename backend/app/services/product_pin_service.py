"""Product pin service for managing merchant's pinned products.

Story 1.15: Product Highlight Pins

Provides CRUD operations for product pinning with limit enforcement,
search functionality, and integration with Shopify product data.
"""

from __future__ import annotations

import os
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.product_pin import ProductPin
from app.models.merchant import Merchant
import structlog


logger = structlog.get_logger(__name__)

# Configurable pin limit from environment variable
MAX_PINNED_PRODUCTS = int(os.getenv("MAX_PINNED_PRODUCTS", "10"))


async def pin_product(
    db: AsyncSession,
    merchant_id: str,
    product_id: str,
) -> ProductPin:
    """Pin a product for a merchant.

    Args:
        db: Database session
        merchant_id: Merchant ID
        product_id: Shopify product ID to pin

    Returns:
        The created ProductPin record

    Raises:
        APIError: If pin limit reached, product already pinned,
                 or product doesn't exist

    AC 2: Pin and Unpin Products
    AC 5: Pin Limits and Validation
    """
    # Check if product already pinned
    existing = await db.execute(
        select(ProductPin).where(
            and_(
                ProductPin.merchant_id == merchant_id,
                ProductPin.product_id == product_id,
            )
        )
    )
    if existing.scalars().first():
        raise APIError(
            ErrorCode.PRODUCT_PIN_ALREADY_PINNED,
            f"Product {product_id} is already pinned",
        )

    # Check pin limit
    pinned_count = await db.execute(
        select(func.count(ProductPin.id)).where(ProductPin.merchant_id == merchant_id)
    )
    if pinned_count.scalars().one() >= MAX_PINNED_PRODUCTS:
        raise APIError(
            ErrorCode.PRODUCT_PIN_LIMIT_REACHED,
            f"Maximum pinned products reached ({MAX_PINNED_PRODUCTS}). Unpin a product first.",
        )

    # Fetch product details from Shopify to populate title and image
    # NOTE: Shopify integration deferred (AC 6), using mock data
    from app.services.shopify.product_service import MOCK_PRODUCTS

    # Find product in mock data by ID
    product = None
    for p in MOCK_PRODUCTS:
        if p["id"] == product_id:
            product = p
            break

    product_title = product["title"] if product else product_id
    product_image_url = product.get("image_url") if product else None

    # Get next pinned_order value
    max_order = await db.execute(
        select(func.coalesce(func.max(ProductPin.pinned_order), 0)).where(
            ProductPin.merchant_id == merchant_id
        )
    )
    next_order = (max_order.scalars().one() or 0) + 1

    # Create new pin with fetched product details
    new_pin = ProductPin(
        merchant_id=merchant_id,
        product_id=product_id,
        product_title=product_title,  # Populated from Shopify product data
        product_image_url=product_image_url,  # Populated from Shopify product data
        pinned_order=next_order,
    )
    db.add(new_pin)
    await db.flush()

    logger.info(
        "product_pinned",
        merchant_id=merchant_id,
        product_id=product_id,
        product_title=product_title,
        pinned_order=next_order,
    )

    return new_pin


async def unpin_product(
    db: AsyncSession,
    merchant_id: str,
    product_id: str,
) -> None:
    """Unpin a product for a merchant.

    Args:
        db: Database session
        merchant_id: Merchant ID
        product_id: Shopify product ID to unpin

    Note:
        This function is idempotent - if the product is not pinned,
        it will simply return without error (no-op).

    AC 2: Pin and Unpin Products
    """
    # Find existing pin
    existing = await db.execute(
        select(ProductPin).where(
            and_(
                ProductPin.merchant_id == merchant_id,
                ProductPin.product_id == product_id,
            )
        )
    )
    pin = existing.scalars().first()

    # If pin doesn't exist, that's fine - it's already unpinned (idempotent)
    if not pin:
        logger.info(
            "product_already_unpinned",
            merchant_id=merchant_id,
            product_id=product_id,
        )
        return

    # Delete the pin
    await db.delete(pin)

    logger.info(
        "product_unpinned",
        merchant_id=merchant_id,
        product_id=product_id,
    )


async def get_pinned_products(
    db: AsyncSession,
    merchant_id: int | str,
    page: int = 1,
    limit: int = 20,
    pinned_only: bool = False,
    search: str | None = None,
) -> tuple[list[dict], int]:
    """Get merchant's products with pin status (pinned + unpinned).

    Args:
        db: Database session
        merchant_id: Merchant ID (int or str)
        page: Page number (1-indexed)
        limit: Items per page (default 20)
        pinned_only: If True, return only pinned products
        search: Optional search query to filter products by title

    Returns:
        Tuple of (products list with pin status, total count)

    AC 1: Pin Products List Management
    AC 3: Product Search and Filter

    NOTE: Returns list of dicts with product data merged from Shopify
          and pin status from database, NOT ProductPin ORM objects.
    """
    from app.services.shopify.product_service import fetch_products, get_product_by_id
    from app.models.merchant import Merchant

    merchant_id_int = int(merchant_id) if isinstance(merchant_id, str) else merchant_id

    # Fetch merchant to get access token
    merchant_result = await db.execute(select(Merchant).where(Merchant.id == merchant_id_int))
    merchant = merchant_result.scalars().first()

    # Check if merchant has Shopify connection (stored in config JSONB)
    shopify_access_token = None
    if merchant and merchant.config:
        shopify_access_token = merchant.config.get("shopify_access_token")

    # Fetch all products from Shopify (mock data for now)
    # NOTE: Shopify integration deferred per Story 1.15 AC 6
    # Always use mock products for development/testing
    all_products = await fetch_products(shopify_access_token or "", merchant_id_int, db)

    # Store original product count for pagination (before search filter)
    original_product_count = len(all_products)

    # Apply search filter if provided (case-insensitive title search)
    if search and search.strip():
        search_lower = search.lower().strip()
        all_products = [p for p in all_products if search_lower in p["title"].lower()]
        logger.info(
            "search_filter_applied",
            merchant_id=merchant_id_int,
            search_query=search,
            filtered_count=len(all_products),
        )

    # Fetch pinned products from database
    pinned_result = await db.execute(
        select(ProductPin).where(ProductPin.merchant_id == merchant_id_int)
    )
    pinned_pins = pinned_result.scalars().all()

    # Create lookup map for pinned products
    pinned_map = {p.product_id: p for p in pinned_pins}

    # Merge Shopify products with pin status
    merged_products = []
    for product in all_products:
        product_id = product["id"]
        is_pinned = product_id in pinned_map
        pin_data = pinned_map.get(product_id)

        merged_products.append(
            {
                "product_id": product_id,
                "title": product["title"],
                "image_url": product.get("image_url"),
                "is_pinned": is_pinned,
                "pinned_order": pin_data.pinned_order if is_pinned else None,
                "pinned_at": pin_data.pinned_at.isoformat() if is_pinned else None,
            }
        )

    # If pinned_only filter, show only pinned products
    if pinned_only:
        filtered_products = [p for p in merged_products if p["is_pinned"]]
        total = len(pinned_map)
    else:
        filtered_products = merged_products
        # When search is applied, total should reflect filtered count
        # Otherwise, use the original product count (before filter)
        if search and search.strip():
            total = len(merged_products)
        else:
            total = original_product_count

    # Apply pagination
    offset = (page - 1) * limit
    paginated = filtered_products[offset : offset + limit]

    logger.info(
        "products_retrieved",
        merchant_id=merchant_id,
        page=page,
        limit=limit,
        pinned_only=pinned_only,
        search=search,
        total=total,
        returned=len(paginated),
    )

    return paginated, total


async def search_products(
    db: AsyncSession,
    merchant_id: str,
    query: str,
) -> list[ProductPin]:
    """Search products by title (case-insensitive).

    Args:
        db: Database session
        merchant_id: Merchant ID
        query: Search query string

    Returns:
        List of matching ProductPin records

    AC 3: Product Search and Filter
    """
    if not query or not query.strip():
        return await get_pinned_products(db, merchant_id)

    # Case-insensitive search using ilike
    search_pattern = f"%{query.lower()}%"

    results = await db.execute(
        select(ProductPin).where(
            and_(
                ProductPin.merchant_id == merchant_id,
                ProductPin.product_title.ilike(search_pattern),
            )
        )
    )
    products = results.scalars().all()

    logger.info(
        "product_search",
        merchant_id=merchant_id,
        query=query,
        count=len(products),
    )

    return list(products)


async def check_pin_limit(
    db: AsyncSession,
    merchant_id: str,
) -> tuple[int, int]:
    """Check if merchant can pin more products.

    Args:
        db: Database session
        merchant_id: Merchant ID

    Returns:
        Tuple of (current_count, remaining_slots)

    AC 5: Pin Limits and Validation
    """
    # Get current pinned count
    result = await db.execute(
        select(func.count(ProductPin.id)).where(ProductPin.merchant_id == merchant_id)
    )
    count = result.scalars().one()

    remaining = max(0, MAX_PINNED_PRODUCTS - count)

    return count, remaining


async def get_pinned_product_ids(
    db: AsyncSession,
    merchant_id: str,
) -> list[str]:
    """Get list of pinned product IDs for a merchant.

    Used by bot recommendation service to boost pinned products.

    Args:
        db: Database session
        merchant_id: Merchant ID

    Returns:
        List of product IDs that are pinned

    AC 4: Integration with Bot Recommendation Engine
    """
    result = await db.execute(
        select(ProductPin.product_id).where(
            and_(
                ProductPin.merchant_id == merchant_id,
            )
        )
    )
    return list(result.scalars().all())
