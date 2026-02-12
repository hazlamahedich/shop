"""Product pin API endpoints.

Story 1.15: Product Highlight Pins

Provides endpoints for:
- Getting products with pin status
- Pinning a product
- Unpinning a product
- Reordering pinned products
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.product_pin import ProductPin
from app.schemas.product_pins import (
    ProductPinRequest,
    ProductPinResponse,
    ProductPinDetailEnvelope,
    ProductListResponse,
    ProductPinEnvelope,
    ReorderPinsRequest,
    ProductPinItem,
    PaginationMeta,
)
from app.api.helpers import create_meta, get_merchant_id, verify_merchant_exists


logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get(
    "/product-pins",
    response_model=ProductPinEnvelope,
)
async def get_product_pins(
    request: Request,
    db: AsyncSession = Depends(get_db),
    search: str | None = Query(default=None),
    pinned_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> ProductPinEnvelope:
    """Get merchant's products with pin status.

    Returns paginated list of products from Shopify with
    pin status indicators for the merchant's pinned products.

    AC 1: Pin Products List Management

    Query Parameters:
        search: Optional search query for filtering products
        pinned_only: If true, return only pinned products
        page: Page number for pagination (default: 1)
        limit: Items per page (default: 20)

    Args:
        request: FastAPI request with merchant authentication
        db: Database session
        search: Optional search query
        pinned_only: Filter to only pinned products
        page: Page number (1-indexed)
        limit: Items per page

    Returns:
        ProductPinEnvelope with products list and pagination

    Raises:
        APIError: If authentication fails or merchant not found
    """
    merchant_id = get_merchant_id(request)

    merchant = await verify_merchant_exists(merchant_id, db)

    # Get products merged from Shopify and pin status
    # Now includes ALL products (pinned + unpinned) from mock Shopify data
    from app.services.product_pin_service import (
        get_pinned_products,
        check_pin_limit,
    )

    # Fetch all products with pin status (now returns list of dicts)
    # Pass search query for filtering products
    products, total = await get_pinned_products(
        db, merchant_id, page=page, limit=limit, pinned_only=pinned_only, search=search
    )

    # Get pin limit info
    current_count, remaining = await check_pin_limit(db, merchant_id)

    logger.info(
        "product_pins_retrieved",
        merchant_id=merchant_id,
        page=page,
        limit=limit,
        pinned_only=pinned_only,
        count=len(products),
    )

    return ProductPinEnvelope(
        data=ProductListResponse(
            products=[
                ProductPinItem(
                    product_id=p["product_id"],
                    title=p["title"],
                    image_url=p.get("image_url"),
                    is_pinned=p["is_pinned"],
                    pinned_order=p.get("pinned_order"),
                    pinned_at=p.get("pinned_at"),
                )
                for p in products
            ],
            pagination=PaginationMeta(
                page=page,
                limit=limit,
                total=total,
                has_more=(page * limit) < total,
            ),
            pin_limit=10,
            pinned_count=current_count,
        ),
        meta=create_meta(),
    )


@router.post(
    "/product-pins",
    response_model=ProductPinDetailEnvelope,
)
async def pin_product(
    request: Request,
    pin_data: ProductPinRequest,
    db: AsyncSession = Depends(get_db),
) -> ProductPinDetailEnvelope:
    """Pin a product (adds to pinned products).

    AC 2: Pin and Unpin Products

    Allows merchant to pin a product for prioritized
    bot recommendations. Maximum of 10 products can be pinned.

    Args:
        request: FastAPI request with merchant authentication
        pin_data: Product pin request data
        db: Database session

    Returns:
        ProductPinDetailEnvelope with updated pin status

    Raises:
        APIError: If authentication fails, merchant not found,
                 validation fails, or pin limit reached

    NOTE: CSRF protection is provided by CSRFMiddleware (see main.py:164).
    All PUT requests automatically require valid CSRF tokens unless path
    is in BYPASS_PATHS. The /api/v1/merchant/product-pins path
    is NOT in bypass list, so it is protected by default.
    """
    merchant_id = get_merchant_id(request)

    merchant = await verify_merchant_exists(merchant_id, db)

    product_id = pin_data.product_id

    logger.info(
        "pinning_product",
        merchant_id=merchant_id,
        product_id=product_id,
    )

    from app.services.product_pin_service import pin_product

    new_pin = await pin_product(db, merchant_id, product_id)

    # Commit the transaction
    await db.commit()

    return ProductPinDetailEnvelope(
        data=ProductPinResponse(
            product_id=new_pin.product_id,
            is_pinned=True,
            pinned_order=new_pin.pinned_order,
            pinned_at=new_pin.pinned_at.isoformat(),
        ),
        meta=create_meta(),
    )


@router.delete(
    "/product-pins/{product_id}",
    response_model=ProductPinDetailEnvelope,
)
async def unpin_product_endpoint(
    request: Request,
    product_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProductPinDetailEnvelope:
    """Unpin a product (removes from pinned products).

    AC 2: Pin and Unpin Products

    Allows merchant to unpin a product, removing it from
    prioritized recommendations.

    Args:
        request: FastAPI request with merchant authentication
        product_id: Shopify product ID to unpin
        db: Database session

    Returns:
        ProductPinDetailEnvelope with updated pin status

    Raises:
        APIError: If authentication fails, merchant not found,
                 or product pin not found

    NOTE: CSRF protection is provided by CSRFMiddleware (see main.py:164).
    All DELETE requests automatically require valid CSRF tokens unless path
    is in BYPASS_PATHS. The /api/v1/merchant/product-pins path
    is NOT in bypass list, so it is protected by default.
    """
    merchant_id = get_merchant_id(request)

    merchant = await verify_merchant_exists(merchant_id, db)

    logger.info(
        "unpinning_product",
        merchant_id=merchant_id,
        product_id=product_id,
    )

    from app.services.product_pin_service import unpin_product

    await unpin_product(db, merchant_id, product_id)

    # Commit the transaction
    await db.commit()

    return ProductPinDetailEnvelope(
        data=ProductPinResponse(
            product_id=product_id,
            is_pinned=False,
            pinned_order=None,
            pinned_at=None,
        ),
        meta=create_meta(),
    )


@router.post(
    "/product-pins/reorder",
    response_model=ProductPinDetailEnvelope,
)
async def reorder_pinned_products(
    request: Request,
    reorder_data: ReorderPinsRequest,
    db: AsyncSession = Depends(get_db),
) -> ProductPinDetailEnvelope:
    """Reorder pinned products by updating pinned_order.

    AC 1: Pin Products List Management

    Allows merchant to customize the priority order of their
    pinned products (1-10).

    Args:
        request: FastAPI request with merchant authentication
        reorder_data: Product order data
        db: Database session

    Returns:
        ProductPinDetailEnvelope with success confirmation

    Raises:
        APIError: If authentication fails, merchant not found,
                 or validation fails

    NOTE: CSRF protection is provided by CSRFMiddleware (see main.py:164).
    All POST requests automatically require valid CSRF tokens unless path
    is in BYPASS_PATHS. The /api/v1/merchant/product-pins/reorder path
    is NOT in bypass list, so it is protected by default.
    """
    merchant_id = get_merchant_id(request)

    merchant = await verify_merchant_exists(merchant_id, db)

    logger.info(
        "reordering_pinned_products",
        merchant_id=merchant_id,
        count=len(reorder_data.product_orders),
    )

    # Validate max 10 products can be reordered
    if len(reorder_data.product_orders) > 10:
        from app.services.product_pin_service import MAX_PINNED_PRODUCTS
        raise APIError(
            ErrorCode.PRODUCT_PIN_LIMIT_REACHED,
            f"Cannot reorder more than {MAX_PINNED_PRODUCTS} products",
        )

    # Update pinned_order for each product
    from app.services.product_pin_service import get_pinned_products

    products, _ = await get_pinned_products(db, merchant_id)

    # Create mapping of product_id to current pin
    pin_map = {p.product_id: p for p in products}

    # Update pinned_order values
    for item in reorder_data.product_orders:
        product_id = item["product_id"]
        new_order = item["order"]

        if product_id not in pin_map:
            raise APIError(
                ErrorCode.PRODUCT_PIN_NOT_FOUND,
                f"Product {product_id} is not pinned",
            )

        pin = pin_map[product_id]
        pin.pinned_order = new_order

    # Save all changes
    db.add_all(list(pin_map.values()))
    await db.commit()

    logger.info(
        "pinned_products_reordered",
        merchant_id=merchant_id,
    )

    return ProductPinDetailEnvelope(
        data=ProductPinResponse(
            product_id="",
            is_pinned=True,
            pinned_order=0,
            pinned_at=None,
        ),
        meta=create_meta(),
    )


# Import PaginationMeta from schemas
from app.schemas.product_pins import PaginationMeta
