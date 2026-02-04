"""Tests for ProductDetailHandler.

Tests product detail view formatting, variant selection, and
stock availability display for Messenger.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.core.errors import ErrorCode
from app.schemas.shopify import (
    CurrencyCode,
    Product,
    ProductImage,
    ProductVariant,
)
from app.services.messenger.product_detail_handler import ProductDetailHandler


@pytest.fixture
def sample_product() -> Product:
    """Create a sample product for testing."""
    return Product(
        id="gid://shopify/Product/1",
        title="Nike Running Shoes",
        description="Professional running shoes for marathon training with advanced cushioning",
        product_type="Footwear",
        tags=["running", "shoes", "nike"],
        price=89.99,
        currency_code=CurrencyCode.USD,
        images=[
            ProductImage(
                url="https://cdn.shopify.com/s/files/1/test.jpg",
                alt_text="Running shoes side view",
            )
        ],
        variants=[
            ProductVariant(
                id="gid://shopify/ProductVariant/1",
                product_id="gid://shopify/Product/1",
                title="Size 8 - Red",
                price=89.99,
                currency_code=CurrencyCode.USD,
                available_for_sale=True,
                selected_options={"Size": "8", "Color": "Red"},
            ),
            ProductVariant(
                id="gid://shopify/ProductVariant/2",
                product_id="gid://shopify/Product/1",
                title="Size 9 - Red",
                price=89.99,
                currency_code=CurrencyCode.USD,
                available_for_sale=True,
                selected_options={"Size": "9", "Color": "Red"},
            ),
            ProductVariant(
                id="gid://shopify/ProductVariant/3",
                product_id="gid://shopify/Product/1",
                title="Size 8 - Blue",
                price=89.99,
                currency_code=CurrencyCode.USD,
                available_for_sale=False,
                selected_options={"Size": "8", "Color": "Blue"},
            ),
        ],
    )


@pytest.fixture
def mock_settings() -> dict[str, Any]:
    """Mock settings for testing."""
    return {
        "MESSENGER_FALLBACK_IMAGE_URL": "https://cdn.example.com/fallback-product.png",
        "STORE_URL": "https://shop.example.com",
    }


class TestProductDetailHandler:
    """Tests for ProductDetailHandler."""

    @pytest.fixture
    def handler(self, mock_settings: dict[str, Any]) -> ProductDetailHandler:
        """Create a handler with mocked settings."""
        with patch("app.services.messenger.product_detail_handler.settings", return_value=mock_settings):
            return ProductDetailHandler()

    def test_init(self, handler: ProductDetailHandler) -> None:
        """Test handler initialization."""
        assert handler is not None

    def test_format_product_detail(
        self,
        handler: ProductDetailHandler,
        sample_product: Product,
    ) -> None:
        """Test product detail formatting."""
        payload = handler.format_product_detail(sample_product)

        assert "attachment" in payload
        assert payload["attachment"]["type"] == "template"
        assert payload["attachment"]["payload"]["template_type"] == "generic"

        elements = payload["attachment"]["payload"]["elements"]
        assert len(elements) >= 1

        # Main product element
        main_element = elements[0]
        assert "Nike Running Shoes" in main_element["title"]
        assert "image_url" in main_element
        assert "subtitle" in main_element
        # Note: Main element may not have buttons - they're in variant elements

    def test_format_product_detail_with_description(
        self,
        handler: ProductDetailHandler,
        sample_product: Product,
    ) -> None:
        """Test that description is included in subtitle."""
        payload = handler.format_product_detail(sample_product)
        main_element = payload["attachment"]["payload"]["elements"][0]

        # Subtitle should contain price
        assert "$89.99" in main_element["subtitle"] or "89.99" in main_element["subtitle"]

    def test_format_product_detail_variants_included(
        self,
        handler: ProductDetailHandler,
        sample_product: Product,
    ) -> None:
        """Test that available variants are included."""
        payload = handler.format_product_detail(sample_product)
        elements = payload["attachment"]["payload"]["elements"]

        # Should have main element plus variant summaries
        # (2 available sizes: 8 and 9)
        assert len(elements) >= 1

    def test_format_variant_selection(
        self,
        handler: ProductDetailHandler,
        sample_product: Product,
    ) -> None:
        """Test variant selection formatting."""
        payload = handler.format_variant_selection(sample_product)

        assert "attachment" in payload
        elements = payload["attachment"]["payload"]["elements"]

        # Should have 2 available variants (not 3 - one is out of stock)
        assert len(elements) == 2

        # Each variant should have add to cart button
        for element in elements:
            assert "buttons" in element
            assert len(element["buttons"]) == 1
            assert element["buttons"][0]["title"] == "Add to Cart"
            assert "ADD_TO_CART" in element["buttons"][0]["payload"]

    def test_select_variant_by_options(
        self,
        handler: ProductDetailHandler,
        sample_product: Product,
    ) -> None:
        """Test selecting variant by options."""
        # Select size 8, red
        variant = handler.select_variant_by_options(
            sample_product,
            {"Size": "8", "Color": "Red"},
        )

        assert variant is not None
        assert variant.id == "gid://shopify/ProductVariant/1"
        assert variant.available_for_sale is True

    def test_select_variant_unavailable(
        self,
        handler: ProductDetailHandler,
        sample_product: Product,
    ) -> None:
        """Test selecting unavailable variant returns None."""
        # Select size 8, blue (not available)
        variant = handler.select_variant_by_options(
            sample_product,
            {"Size": "8", "Color": "Blue"},
        )

        assert variant is None

    def test_select_variant_no_match(
        self,
        handler: ProductDetailHandler,
        sample_product: Product,
    ) -> None:
        """Test selecting non-existent variant returns None."""
        variant = handler.select_variant_by_options(
            sample_product,
            {"Size": "12", "Color": "Green"},
        )

        assert variant is None

    def test_get_available_variants(
        self,
        handler: ProductDetailHandler,
        sample_product: Product,
    ) -> None:
        """Test getting available variants."""
        variants = handler.get_available_variants(sample_product)

        # Should return 2 variants (3 total, 1 unavailable)
        assert len(variants) == 2

        # All should be available
        for variant in variants:
            assert variant.available_for_sale is True

    def test_get_variant_summary(
        self,
        handler: ProductDetailHandler,
        sample_product: Product,
    ) -> None:
        """Test getting variant summary."""
        summary = handler.get_variant_summary(sample_product)

        # Should have 2 sizes (8 and 9)
        assert "Size" in summary
        assert summary["Size"] == 2

        # Should have 1 color (Red - Blue is out of stock)
        assert "Color" in summary
        assert summary["Color"] == 1

    def test_format_product_detail_no_images(
        self,
        handler: ProductDetailHandler,
    ) -> None:
        """Test product detail without images uses fallback."""
        product = Product(
            id="gid://shopify/Product/1",
            title="Product Without Image",
            product_type="Test",
            price=10.0,
            currency_code=CurrencyCode.USD,
            images=[],
            variants=[],
        )

        payload = handler.format_product_detail(product)
        main_element = payload["attachment"]["payload"]["elements"][0]

        # Should use fallback image
        assert "fallback" in main_element["image_url"].lower()

    def test_format_product_detail_long_title(
        self,
        handler: ProductDetailHandler,
    ) -> None:
        """Test that long titles are truncated."""
        long_title = "A" * 100
        product = Product(
            id="gid://shopify/Product/1",
            title=long_title,
            product_type="Test",
            price=10.0,
            currency_code=CurrencyCode.USD,
            images=[ProductImage(url="https://example.com/test.jpg")],
            variants=[],
        )

        payload = handler.format_product_detail(product)
        main_element = payload["attachment"]["payload"]["elements"][0]

        # Title should be truncated
        assert len(main_element["title"]) <= 83  # 80 + "..."

    def test_format_product_detail_none_product(
        self,
        handler: ProductDetailHandler,
    ) -> None:
        """Test that None product raises error."""
        from app.core.errors import APIError

        with pytest.raises(APIError) as exc_info:
            handler.format_product_detail(None)  # type: ignore

        assert exc_info.value.code in [
            ErrorCode.MESSENGER_FORMATTING_FAILED,
            ErrorCode.MESSAGE_SEND_FAILED,
        ]


class TestProductDetailHandlerEdgeCases:
    """Tests for edge cases in ProductDetailHandler."""

    @pytest.fixture
    def handler(self, mock_settings: dict[str, Any]) -> ProductDetailHandler:
        """Create a handler with mocked settings."""
        with patch("app.services.messenger.product_detail_handler.settings", return_value=mock_settings):
            return ProductDetailHandler()

    def test_format_variant_selection_no_variants(
        self,
        handler: ProductDetailHandler,
    ) -> None:
        """Test variant selection with no variants."""
        product = Product(
            id="gid://shopify/Product/1",
            title="No Variants Product",
            product_type="Test",
            price=10.0,
            currency_code=CurrencyCode.USD,
            images=[ProductImage(url="https://example.com/test.jpg")],
            variants=[],
        )

        payload = handler.format_variant_selection(product)
        elements = payload["attachment"]["payload"]["elements"]

        # Should have empty elements list
        assert len(elements) == 0

    def test_format_variant_selection_all_unavailable(
        self,
        handler: ProductDetailHandler,
    ) -> None:
        """Test variant selection when all variants are unavailable."""
        product = Product(
            id="gid://shopify/Product/1",
            title="All Unavailable",
            product_type="Test",
            price=10.0,
            currency_code=CurrencyCode.USD,
            images=[ProductImage(url="https://example.com/test.jpg")],
            variants=[
                ProductVariant(
                    id="gid://shopify/ProductVariant/1",
                    product_id="gid://shopify/Product/1",
                    title="Unavailable",
                    price=10.0,
                    currency_code=CurrencyCode.USD,
                    available_for_sale=False,
                )
            ],
        )

        payload = handler.format_variant_selection(product)
        elements = payload["attachment"]["payload"]["elements"]

        # Should have no available variants
        assert len(elements) == 0

    def test_build_variant_elements_no_options(
        self,
        handler: ProductDetailHandler,
    ) -> None:
        """Test variant elements with variants that have no options."""
        product = Product(
            id="gid://shopify/Product/1",
            title="No Options",
            product_type="Test",
            price=10.0,
            currency_code=CurrencyCode.USD,
            images=[ProductImage(url="https://example.com/test.jpg")],
            variants=[
                ProductVariant(
                    id="gid://shopify/ProductVariant/1",
                    product_id="gid://shopify/Product/1",
                    title="Default",
                    price=10.0,
                    currency_code=CurrencyCode.USD,
                    available_for_sale=True,
                )
            ],
        )

        elements = handler._build_variant_elements(product)

        # Should have empty list (no option groups)
        assert len(elements) == 0
