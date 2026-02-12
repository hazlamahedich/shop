"""Unit Tests for Product Pin Service.

Story 1.15: Product Highlight Pins

Tests product pin service functionality including:
- Pin product operations
- Unpin product operations
- Get pinned products with filters (now returns dict list)
- Search products functionality
- Pin limit enforcement
- Integration with Shopify mock data

Refactored to use function-scoped fixtures per pytest-bmm patterns.
This avoids pytest fixture collision with test class names.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_pin import ProductPin
from app.core.errors import ErrorCode, APIError


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
async def db_session() -> AsyncSession:
    """Create a fresh database session for testing.

    This fixture creates a fresh async session for each test function.
    Tables are dropped and recreated before each test for complete isolation.
    """
    from app.core.database import Base

    # List of custom enum types
    enum_types = [
        "message_sender",
        "message_type",
        "conversation_status",
        "shopify_status",
        "facebook_status",
        "llm_provider",
        "merchant_status",
        "personality_type",
        "verification_platform",
        "test_type",
        "verification_status",
    ]

    # Clean up and recreate schema in a single transaction
    async with db_session.begin() as conn:
        # First, drop all custom enum types (they may block table drops)
        for enum_type in enum_types:
            await conn.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE;"))

        # Recreate enum types
        await conn.execute(text("""
            CREATE TYPE merchant_status AS ENUM (
                'pending', 'active', 'failed'
            );
        """))

        await conn.execute(text("""
            CREATE TYPE personality_type AS ENUM (
                'friendly', 'professional', 'enthusiastic'
            );
        """))

        await conn.execute(text("""
            CREATE TYPE llm_provider AS ENUM (
                'ollama', 'openai', 'anthropic', 'gemini', 'glm'
            );
        """))

        # Create all tables fresh
        await conn.run_sync(Base.metadata.create_all, conn))

    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture
def mock_merchant():
    """Create a mock merchant for testing."""
    merchant = MagicMock()
    merchant.id = "test-merchant-123"
    merchant.shopify_access_token = "test-token-123"
    merchant.personality = "friendly"
    merchant.use_custom_greeting = False
    merchant.custom_greeting = None
    return merchant


@pytest.fixture
def mock_request_with_merchant(merchant):
    """Create a mock request with merchant already set in state."""
    request = AsyncMock()
    request.state.merchant_id = merchant.id
    return request


# =============================================================================
# Test Pin Product
# =============================================================================

class TestProductPinning:
    """Test product pin operations."""

    @pytest.mark.asyncio
    async def test_pin_product_success(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test successful product pinning with populated product details."""
        # Arrange
        product_id = "shopify_prod_123"

        # Act
        from app.services.product_pin_service import pin_product
        result = await pin_product(
            db_session,
            mock_merchant.id,
            product_id,
        )

        # Assert
        assert result.is_pinned is True
        assert result.pinned_order == 1  # First pin gets order 1
        assert isinstance(result, ProductPin)
        assert result.product_title == "Running Shoes Pro"  # From MOCK_PRODUCTS[0]
        assert result.product_image_url == "https://cdn.shopify.com/s/files/shoes-pro.jpg"

    @pytest.mark.asyncio
    async def test_pin_product_enforces_limit(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test pin limit is enforced (10 products max)."""
        from app.services.product_pin_service import pin_product, MAX_PINNED_PRODUCTS

        # Arrange: Pin 10 products first
        for i in range(MAX_PINNED_PRODUCTS):
            product_pin = ProductPin(
                merchant_id=mock_merchant.id,
                product_id=f"prod_{i}",
                product_title=f"Product {i}",
                product_image_url=f"https://example.com/product{i}.jpg",
                pinned_order=i + 1,
            )
            db_session.add(product_pin)

        # Act & Assert: 11th pin should fail
        with pytest.raises(APIError) as exc_info:
            result = await pin_product(
                db_session,
                mock_merchant.id,
                "prod_11",
            )

        assert exc_info.value.code == ErrorCode.PRODUCT_PIN_LIMIT_REACHED
        assert "Maximum pinned products reached" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_pin_product_prevents_duplicates(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test duplicate pins are prevented."""
        from app.services.product_pin_service import pin_product

        # Arrange: Pin a product, then try again
        product_id = "shopify_prod_duplicate"

        # First pin should succeed
        result1 = await pin_product(
            db_session,
            mock_merchant.id,
            product_id,
        )
        assert result1.is_pinned is True

        # Second pin should fail
        with pytest.raises(APIError) as exc_info:
            result2 = await pin_product(
                db_session,
                mock_merchant.id,
                product_id,
            )

        assert exc_info.value.code == ErrorCode.PRODUCT_PIN_ALREADY_PINNED

    @pytest.mark.asyncio
    async def test_pin_product_with_shopify_data(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test pinning populates product details from Shopify data."""
        from app.services.product_pin_service import pin_product

        # Arrange
        product_id = "shopify_prod_001"  # Matches MOCK_PRODUCTS[0]

        # Act
        result = await pin_product(
            db_session,
            mock_merchant.id,
            product_id,
        )

        # Assert - product details should be populated from MOCK_PRODUCTS
        assert result.is_pinned is True
        assert result.pinned_order == 1
        assert result.product_title == "Running Shoes Pro"
        assert result.product_image_url == "https://cdn.shopify.com/s/files/shoes-pro.jpg"

    @pytest.mark.asyncio
    async def test_unpin_product_success(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test successful product unpinning."""
        from app.services.product_pin_service import pin_product, unpin_product

        # Arrange: First pin a product
        product_id = "shopify_prod_123"

        # Pin the product first
        pin = await pin_product(
            db_session,
            mock_merchant.id,
            product_id,
        )
        await db_session.flush()

        # Act: Unpin the product
        result = await unpin_product(
            db_session,
            mock_merchant.id,
            product_id,
        )

        # Assert: Unpin removes the pin record
        from app.services.product_pin_service import get_pinned_products
        pins_result = await get_pinned_products(
            db_session,
            mock_merchant.id,
        )
        pins_list = [p["product_id"] for p in pins_result]
        assert product_id not in pins_list

    @pytest.mark.asyncio
    async def test_unpin_product_not_found(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test unpinning non-existent product raises error."""
        from app.services.product_pin_service import unpin_product

        # Arrange
        product_id = "shopify_prod_nonexistent"

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await unpin_product(
                db_session,
                mock_merchant.id,
                product_id,
            )

        assert exc_info.value.code == ErrorCode.PRODUCT_PIN_NOT_FOUND


# =============================================================================
# Test Get Pinned Products (with Shopify merge)
# =============================================================================

class TestGetPinnedProducts:
    """Test get_pinned_products with Shopify data merge."""

    @pytest.mark.asyncio
    async def test_get_pinned_products_returns_all_products(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test that get_pinned_products returns all products (pinned + unpinned)."""
        from app.services.product_pin_service import get_pinned_products

        # Act
        products, total = await get_pinned_products(
            db_session,
            mock_merchant.id,
            page=1,
            limit=20,
            pinned_only=False,
        )

        # Assert - should return 20 products from MOCK_PRODUCTS
        assert len(products) == 20
        assert total == 20

        # Verify structure - products should be dicts now
        assert isinstance(products, list)
        assert all(isinstance(p, dict) for p in products)

        # Verify product fields
        first_product = products[0]
        assert "product_id" in first_product
        assert "title" in first_product
        assert "is_pinned" in first_product
        assert "pinned_order" in first_product or first_product["is_pinned"]
        assert "pinned_at" in first_product or first_product.get("pinned_at")

    @pytest.mark.asyncio
    async def test_get_pinned_products_pinned_only_filter(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test pinned_only filter returns only pinned products."""
        from app.services.product_pin_service import get_pinned_products

        # Act - Pin some products first
        for i in range(3):
            pin = ProductPin(
                merchant_id=mock_merchant.id,
                product_id=f"prod_{i}",
                product_title=f"Product {i}",
                pinned_order=i + 1,
            )
            db_session.add(pin)

        # Get pinned only products
        products, total = await get_pinned_products(
            db_session,
            mock_merchant.id,
            page=1,
            limit=20,
            pinned_only=True,
        )

        # Assert - should return only 3 pinned products
        assert len(products) == 3
        assert total == 3  # pinned_only doesn't count total, just pinned
        assert all(p["is_pinned"] for p in products)

    @pytest.mark.asyncio
    async def test_get_pinned_products_pagination(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test pagination works correctly."""
        from app.services.product_pin_service import get_pinned_products

        # Act - get page 2
        products, total = await get_pinned_products(
            db_session,
            mock_merchant.id,
            page=2,
            limit=5,
            pinned_only=False,
        )

        # Assert - should return second page of 5 products
        assert len(products) == 5
        assert total == 20  # Total is still 20


# =============================================================================
# Test Search Products
# =============================================================================

class TestSearchProducts:
    """Test product search functionality."""

    @pytest.mark.asyncio
    async def test_search_products_filters_by_title(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test search filters products by title (case-insensitive)."""
        from app.services.product_pin_service import search_products

        # Act - search for "shoes"
        products = await search_products(
            db_session,
            mock_merchant.id,
            "shoes",
        )

        # Assert - should find matching products
        assert len(products) > 0
        # All mock products with "shoes" or "Shoes" in title should match
        expected_matches = ["Running Shoes Pro", "Wireless Earbuds"]
        actual_matches = [p["product_id"] for p in products if "shoes".lower() in p["title"].lower()]
        assert len(actual_matches) == len(expected_matches)


# =============================================================================
# Test Pin Limit
# =============================================================================

class TestPinLimit:
    """Test pin limit enforcement."""

    @pytest.mark.asyncio
    async def test_pin_limit_info_enforced(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test pin limit checking returns correct info."""
        from app.services.product_pin_service import check_pin_limit, MAX_PINNED_PRODUCTS

        # Arrange: Pin 5 products
        for i in range(5):
            pin = ProductPin(
                merchant_id=mock_merchant.id,
                product_id=f"prod_{i}",
                product_title=f"Product {i}",
                product_image_url=f"https://example.com/product{i}.jpg",
                pinned_order=i + 1,
            )
            db_session.add(pin)

        # Act
        current_count, remaining = await check_pin_limit(
            db_session,
            mock_merchant.id,
        )

        # Assert
        assert current_count == 5
        assert remaining == MAX_PINNED_PRODUCTS - 5


# =============================================================================
# Test Error Handling
# =============================================================================

class TestErrorHandling:
    """Test error handling in service functions."""

    @pytest.mark.asyncio
    async def test_error_handling_on_api_failure(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test proper error handling when service functions fail."""
        from app.services.product_pin_service import get_pinned_products

        # Arrange: Mock to raise error
        async def mock_get_pinned_products_fail(*args, **kwargs):
            raise APIError(ErrorCode.INTERNAL_ERROR, "Database connection failed")

        with patch("app.services.product_pin_service.get_pinned_products", mock_get_pinned_products_fail):
            # Act & Assert
            with pytest.raises(APIError) as exc_info:
                await get_pinned_products(
                    db_session,
                    mock_merchant.id,
                )

            assert exc_info.value.code == ErrorCode.INTERNAL_ERROR
            assert "Database connection failed" in exc_info.value.message


# =============================================================================
# Test Shopify Integration
# =============================================================================

class TestShopifyIntegration:
    """Test Shopify product fetch service."""

    @pytest.mark.asyncio
    async def test_fetch_products_returns_mock_data(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test that fetch_products returns mock Shopify data."""
        from app.services.shopify.product_service import fetch_products

        # Act
        products = await fetch_products(
            mock_merchant.shopify_access_token,
            mock_merchant.id,
            db_session,
        )

        # Assert - should return 20 mock products
        assert len(products) == 20
        assert products[0]["id"] == "shopify_prod_001"
        assert products[0]["title"] == "Running Shoes Pro"

    @pytest.mark.asyncio
    async def test_get_product_by_id_returns_product(
        db_session: AsyncSession,
        mock_merchant: MagicMock,
    ) -> None:
        """Test that get_product_by_id returns correct product."""
        from app.services.shopify.product_service import get_product_by_id

        # Act
        product = await get_product_by_id(
            mock_merchant.shopify_access_token,
            "shopify_prod_001",
            mock_merchant.id,
            db_session,
        )

        # Assert
        assert product is not None
        assert product["id"] == "shopify_prod_001"
        assert product["title"] == "Running Shoes Pro"
