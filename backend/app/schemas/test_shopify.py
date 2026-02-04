"""Tests for Shopify product and variant schemas.

Tests Pydantic model validation, camelCase alias conversion,
and data transformation for Shopify Storefront API responses.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.schemas.shopify import (
    CurrencyCode,
    Product,
    ProductImage,
    ProductSearchResult,
    ProductVariant,
    to_camel,
)


class TestToCamel:
    """Tests for snake_case to camelCase conversion."""

    def test_simple_snake_case(self) -> None:
        """Test converting simple snake_case to camelCase."""
        assert to_camel("hello_world") == "helloWorld"
        assert to_camel("product_id") == "productId"
        assert to_camel("available_for_sale") == "availableForSale"

    def test_single_word(self) -> None:
        """Test that single words are unchanged."""
        assert to_camel("hello") == "hello"
        assert to_camel("world") == "world"

    def test_multiple_underscores(self) -> None:
        """Test converting words with multiple underscores."""
        assert to_camel("hello_world_foo_bar") == "helloWorldFooBar"

    def test_leading_underscore(self) -> None:
        """Test handling of leading underscore."""
        assert to_camel("_private") == "_private"

    def test_trailing_underscore(self) -> None:
        """Test handling of trailing underscore."""
        # to_camel doesn't strip trailing underscores - keeps them as-is
        assert to_camel("private_") == "private_"


class TestProductVariant:
    """Tests for ProductVariant schema."""

    def test_create_variant_with_snake_case(self) -> None:
        """Test creating variant with snake_case field names."""
        variant = ProductVariant(
            id="gid://shopify/ProductVariant/123",
            product_id="gid://shopify/Product/456",
            title="Size 8, Red",
            price=99.99,
            currency_code="USD",
            available_for_sale=True,
            selected_options={"Size": "8", "Color": "Red"},
        )

        assert variant.id == "gid://shopify/ProductVariant/123"
        assert variant.product_id == "gid://shopify/Product/456"
        assert variant.price == 99.99
        assert variant.available_for_sale is True
        assert variant.selected_options == {"Size": "8", "Color": "Red"}

    def test_create_variant_with_camel_case_alias(self) -> None:
        """Test creating variant with camelCase field names (API format)."""
        variant_data = {
            "id": "gid://shopify/ProductVariant/123",
            "productId": "gid://shopify/Product/456",
            "title": "Size 8, Red",
            "price": 99.99,
            "currencyCode": "USD",
            "availableForSale": True,
            "selectedOptions": {"Size": "8", "Color": "Red"},
        }

        variant = ProductVariant(**variant_data)

        assert variant.id == "gid://shopify/ProductVariant/123"
        assert variant.product_id == "gid://shopify/Product/456"
        assert variant.currency_code == CurrencyCode.USD

    def test_variant_default_values(self) -> None:
        """Test variant default values."""
        variant = ProductVariant(
            id="gid://shopify/ProductVariant/123",
            product_id="gid://shopify/Product/456",
            title="Size 8",
            price=49.99,
            available_for_sale=False,  # Must be provided as it has no default
        )

        assert variant.currency_code == CurrencyCode.USD
        assert variant.available_for_sale is False
        assert variant.selected_options == {}

    def test_variant_export_to_camel_case(self) -> None:
        """Test exporting variant to camelCase dict (API response)."""
        variant = ProductVariant(
            id="gid://shopify/ProductVariant/123",
            product_id="gid://shopify/Product/456",
            title="Size 8",
            price=49.99,
            available_for_sale=False,
        )

        data = variant.model_dump(by_alias=True, exclude_none=True)

        assert "productId" in data
        assert "availableForSale" in data
        assert "selectedOptions" in data
        assert "product_id" not in data
        assert "available_for_sale" not in data


class TestProductImage:
    """Tests for ProductImage schema."""

    def test_create_image(self) -> None:
        """Test creating product image."""
        image = ProductImage(
            url="https://cdn.shopify.com/s/files/1/product.jpg",
            alt_text="Red running shoe",
            width=800,
            height=600,
        )

        assert image.url == "https://cdn.shopify.com/s/files/1/product.jpg"
        assert image.alt_text == "Red running shoe"
        assert image.width == 800
        assert image.height == 600

    def test_image_with_optional_fields(self) -> None:
        """Test image with only required field."""
        image = ProductImage(url="https://cdn.shopify.com/s/files/1/product.jpg")

        assert image.url == "https://cdn.shopify.com/s/files/1/product.jpg"
        assert image.alt_text is None
        assert image.width is None
        assert image.height is None


class TestProduct:
    """Tests for Product schema."""

    def test_create_product(self) -> None:
        """Test creating product with all fields."""
        variants = [
            ProductVariant(
                id="gid://shopify/ProductVariant/123",
                product_id="gid://shopify/Product/456",
                title="Size 8",
                price=99.99,
                available_for_sale=True,
            )
        ]

        images = [
            ProductImage(
                url="https://cdn.shopify.com/s/files/1/product.jpg",
                alt_text="Product image",
            )
        ]

        product = Product(
            id="gid://shopify/Product/456",
            title="Running Shoes",
            description="Comfortable running shoes",
            product_type="Footwear",
            tags=["running", "shoes", "athletic"],
            vendor="Nike",
            price=99.99,
            currency_code="USD",
            images=images,
            variants=variants,
            relevance_score=85.5,
        )

        assert product.id == "gid://shopify/Product/456"
        assert product.title == "Running Shoes"
        assert product.product_type == "Footwear"
        assert len(product.tags) == 3
        assert len(product.variants) == 1
        assert len(product.images) == 1
        assert product.relevance_score == 85.5

    def test_product_with_defaults(self) -> None:
        """Test product with default values."""
        product = Product(
            id="gid://shopify/Product/456",
            title="Running Shoes",
            product_type="Footwear",
            price=99.99,
        )

        assert product.currency_code == CurrencyCode.USD
        assert product.tags == []
        assert product.variants == []
        assert product.images == []
        assert product.relevance_score == 0.0

    def test_product_export_to_camel_case(self) -> None:
        """Test exporting product to camelCase dict."""
        product = Product(
            id="gid://shopify/Product/456",
            title="Running Shoes",
            product_type="Footwear",
            price=99.99,
        )

        data = product.model_dump(by_alias=True, exclude_none=True)

        assert "productId" in data or "id" in data
        assert "productType" in data
        assert "currencyCode" in data
        assert "relevanceScore" in data

    def test_relevance_score_sorting(self) -> None:
        """Test that products can be sorted by relevance_score."""
        products = [
            Product(
                id=f"gid://shopify/Product/{i}",
                title=f"Product {i}",
                product_type="Test",
                price=10.0 + i,
                relevance_score=float(i),
            )
            for i in [5, 2, 8, 1, 9]
        ]

        # Sort by relevance score descending
        sorted_products = sorted(products, key=lambda p: p.relevance_score, reverse=True)

        assert sorted_products[0].relevance_score == 9.0
        assert sorted_products[-1].relevance_score == 1.0


class TestProductSearchResult:
    """Tests for ProductSearchResult schema."""

    def test_create_search_result(self) -> None:
        """Test creating search result with products."""
        products = [
            Product(
                id="gid://shopify/Product/1",
                title="Product 1",
                product_type="Test",
                price=10.0,
            ),
            Product(
                id="gid://shopify/Product/2",
                title="Product 2",
                product_type="Test",
                price=20.0,
            ),
        ]

        result = ProductSearchResult(
            products=products,
            total_count=2,
            search_params={"category": "shoes", "maxPrice": 100.0},
            has_alternatives=True,
            search_time_ms=150.5,
        )

        assert result.total_count == 2
        assert len(result.products) == 2
        assert result.search_params == {"category": "shoes", "maxPrice": 100.0}
        assert result.has_alternatives is True
        assert result.search_time_ms == 150.5

    def test_search_result_with_defaults(self) -> None:
        """Test search result with default values."""
        result = ProductSearchResult(
            products=[],
            total_count=0,
        )

        assert result.products == []
        assert result.total_count == 0
        assert result.search_params == {}
        assert result.has_alternatives is False
        assert result.search_time_ms is None

    def test_search_result_export(self) -> None:
        """Test exporting search result to camelCase dict."""
        result = ProductSearchResult(
            products=[
                Product(
                    id="gid://shopify/Product/1",
                    title="Product 1",
                    product_type="Test",
                    price=10.0,
                )
            ],
            total_count=1,
            search_params={"maxPrice": 100},
            search_time_ms=150.0,  # Include search_time_ms to test export
        )

        data = result.model_dump(by_alias=True, exclude_none=True)

        assert "totalCount" in data
        assert "searchParams" in data
        assert "hasAlternatives" in data
        assert "searchTimeMs" in data


class TestCurrencyCode:
    """Tests for CurrencyCode enum."""

    def test_supported_currencies(self) -> None:
        """Test all supported currency codes."""
        assert CurrencyCode.USD.value == "USD"
        assert CurrencyCode.EUR.value == "EUR"
        assert CurrencyCode.GBP.value == "GBP"
        assert CurrencyCode.CAD.value == "CAD"
        assert CurrencyCode.AUD.value == "AUD"

    def test_currency_in_variant(self) -> None:
        """Test currency code in product variant."""
        variant = ProductVariant(
            id="gid://shopify/ProductVariant/123",
            product_id="gid://shopify/Product/456",
            title="Test",
            price=99.99,
            currency_code=CurrencyCode.EUR,
            available_for_sale=True,
        )

        assert variant.currency_code == CurrencyCode.EUR
