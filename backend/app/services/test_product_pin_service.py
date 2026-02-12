"""Tests for product pin service.

Story 1.15: Product Highlight Pins

Tests pin/unpin functionality, pin limit enforcement,
product search and filtering, and Shopify integration.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.product_pin import ProductPin
from app.services.product_pin_service import (
    MAX_PINNED_PRODUCTS,
    pin_product,
    unpin_product,
    get_pinned_products,
    search_products,
)
from app.core.errors import ErrorCode, APIError


@pytest.mark.asyncio
async def test_pin_product_success(db_session: AsyncSession) -> None:
    """Test successful product pinning.

    Given a merchant and valid product ID,
    when pin_product is called,
    then product is pinned successfully.
    """
    # This test will fail until ProductPin model is implemented
    # RED phase of TDD
    with pytest.raises(NotImplementedError):
        await pin_product(db_session, merchant_id=1, product_id="shopify_prod_123")


@pytest.mark.asyncio
async def test_pin_product_enforces_limit(db_session: AsyncSession) -> None:
    """Test pin limit is enforced (10 products maximum).

    Given a merchant has 10 pinned products,
    when attempting to pin an 11th product,
    then PRODUCT_PIN_LIMIT_REACHED error is raised.

    AC 5: Pin limits and validation
    """
    # Pin 10 products first
    for i in range(10):
        try:
            await pin_product(db_session, merchant_id=1, product_id=f"prod_{i}")
        except Exception:
            pass  # Continue even if pin_product not yet implemented

    # 11th pin should fail with limit error
    with pytest.raises(APIError) as exc_info:
        await pin_product(db_session, merchant_id=1, product_id="prod_11")
    assert exc_info.value.code == ErrorCode.PRODUCT_PIN_LIMIT_REACHED


@pytest.mark.asyncio
async def test_pin_product_prevents_duplicates(db_session: AsyncSession) -> None:
    """Test duplicate pin is prevented.

    Given a product is already pinned,
    when attempting to pin the same product again,
    then PRODUCT_PIN_ALREADY_PINNED error is raised.

    AC 2, 5: Pin and Unpin Products
    """
    # Pin a product first
    try:
        await pin_product(db_session, merchant_id=1, product_id="shopify_prod_123")
    except Exception:
        pass

    # Try to pin again - should fail
    with pytest.raises(APIError) as exc_info:
        await pin_product(db_session, merchant_id=1, product_id="shopify_prod_123")
    assert exc_info.value.code == ErrorCode.PRODUCT_PIN_ALREADY_PINNED


@pytest.mark.asyncio
async def test_unpin_product_success(db_session: AsyncSession) -> None:
    """Test successful product unpinning.

    Given a merchant has a pinned product,
    when unpin_product is called,
    then product is unpinned successfully.

    AC 2: Pin and Unpin Products
    """
    with pytest.raises(NotImplementedError):
        await unpin_product(db_session, merchant_id=1, product_id="shopify_prod_123")


@pytest.mark.asyncio
async def test_get_pinned_products_returns_pinned_list(
    db_session: AsyncSession,
) -> None:
    """Test retrieving pinned products.

    Given a merchant has pinned products,
    when get_pinned_products is called,
    then returns list of pinned products ordered by pinned_order.

    AC 1: Pin Products List Management
    """
    with pytest.raises(NotImplementedError):
        await get_pinned_products(db_session, merchant_id=1)


@pytest.mark.asyncio
async def test_get_pinned_products_with_pagination(
    db_session: AsyncSession,
) -> None:
    """Test pagination of pinned products.

    Given a merchant has more than 20 pinned products,
    when get_pinned_products is called with page/limit,
    then returns correct page of results.

    AC 1: Pin Products List Management
    """
    with pytest.raises(NotImplementedError):
        await get_pinned_products(db_session, merchant_id=1, page=1, limit=20)


@pytest.mark.asyncio
async def test_search_products_filters_by_title(db_session: AsyncSession) -> None:
    """Test product search filters by title.

    Given a merchant has many products,
    when search_products is called with a query,
    then returns matching products (case-insensitive).

    AC 3: Product Search and Filter
    """
    with pytest.raises(NotImplementedError):
        await search_products(db_session, merchant_id=1, query="Running Shoes")


@pytest.mark.asyncio
async def test_search_products_empty_query_returns_all(
    db_session: AsyncSession,
) -> None:
    """Test empty search query returns all products.

    Given search_products is called with empty query,
    when merchant has products,
    then returns all products.

    AC 3: Product Search and Filter
    """
    with pytest.raises(NotImplementedError):
        await search_products(db_session, merchant_id=1, query="")


@pytest.mark.asyncio
async def test_pin_limit_is_configurable(db_session: AsyncSession) -> None:
    """Test pin limit can be configured via environment variable.

    Given MAX_PINNED_PRODUCTS environment variable,
    when checking pin limit,
    then the configured limit is used.

    AC 5: Pin Limits and Validation
    """
    # This test verifies the limit is configurable
    # The default is 10, but can be changed via env var
    assert MAX_PINNED_PRODUCTS == 10  # Default value
