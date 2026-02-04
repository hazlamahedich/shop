"""Tests for ProductMapper.

Tests entity to Shopify filter mapping, product data transformation,
and variant filtering logic.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.schemas.shopify import CurrencyCode, Product, ProductVariant
from app.services.shopify.product_mapper import ProductMapper
from app.services.intent.classification_schema import ExtractedEntities


class TestProductMapper:
    """Tests for ProductMapper."""

    @pytest.fixture
    def mapper(self) -> ProductMapper:
        """Create a ProductMapper instance."""
        return ProductMapper()

    @pytest.fixture
    def sample_shopify_product(self) -> dict[str, Any]:
        """Sample Shopify product data."""
        return {
            "id": "gid://shopify/Product/1",
            "title": "Running Shoes",
            "description": "Comfortable running shoes",
            "productType": "Footwear",
            "tags": ["running", "shoes", "athletic"],
            "vendor": "Nike",
            "priceRangeV2": {
                "minVariantPrice": {
                    "amount": "99.99",
                    "currencyCode": "USD",
                }
            },
            "images": {
                "edges": [
                    {
                        "node": {
                            "url": "https://cdn.shopify.com/s/files/1/product.jpg",
                            "altText": "Red running shoe",
                            "width": 800,
                            "height": 600,
                        }
                    }
                ]
            },
            "variants": {
                "edges": [
                    {
                        "node": {
                            "id": "gid://shopify/ProductVariant/1",
                            "productId": "gid://shopify/Product/1",
                            "title": "Size 8 / Red",
                            "priceV2": {
                                "amount": "99.99",
                                "currencyCode": "USD",
                            },
                            "availableForSale": True,
                            "selectedOptions": [
                                {"name": "Size", "value": "8"},
                                {"name": "Color", "value": "Red"},
                            ],
                            "weight": 250.0,
                            "weightUnit": "g",
                        }
                    },
                    {
                        "node": {
                            "id": "gid://shopify/ProductVariant/2",
                            "productId": "gid://shopify/Product/1",
                            "title": "Size 9 / Red",
                            "priceV2": {
                                "amount": "99.99",
                                "currencyCode": "USD",
                            },
                            "availableForSale": False,  # Out of stock
                            "selectedOptions": [
                                {"name": "Size", "value": "9"},
                                {"name": "Color", "value": "Red"},
                            ],
                            "weight": 255.0,
                            "weightUnit": "g",
                        }
                    },
                ]
            },
        }

    def test_map_category_exact_match(self, mapper: ProductMapper) -> None:
        """Test category mapping with exact match."""
        result = mapper.map_category("shoes")

        # Category should be passed through as-is
        assert result == "shoes"

    def test_map_category_case_insensitive(self, mapper: ProductMapper) -> None:
        """Test category mapping is case-insensitive."""
        result1 = mapper.map_category("SHOES")
        result2 = mapper.map_category("Shoes")
        result3 = mapper.map_category("shoes")

        # All should return the same lowercased value
        assert result1.lower() == result2.lower() == result3.lower()

    def test_map_category_none(self, mapper: ProductMapper) -> None:
        """Test category mapping with None."""
        result = mapper.map_category(None)

        assert result is None

    def test_map_single_product(
        self,
        mapper: ProductMapper,
        sample_shopify_product: dict[str, Any],
    ) -> None:
        """Test mapping a single product from Shopify format."""
        products = mapper.map_products([sample_shopify_product])

        assert len(products) == 1

        product = products[0]
        assert product.id == "gid://shopify/Product/1"
        assert product.title == "Running Shoes"
        assert product.product_type == "Footwear"
        assert product.vendor == "Nike"
        assert product.price == 99.99
        assert product.currency_code == CurrencyCode.USD

        # Check tags
        assert len(product.tags) == 3
        assert "running" in product.tags

        # Check images
        assert len(product.images) == 1
        assert product.images[0].url == "https://cdn.shopify.com/s/files/1/product.jpg"

        # Check variants
        assert len(product.variants) == 2
        assert product.variants[0].id == "gid://shopify/ProductVariant/1"

    def test_map_product_variants(
        self,
        mapper: ProductMapper,
        sample_shopify_product: dict[str, Any],
    ) -> None:
        """Test product variant mapping."""
        products = mapper.map_products([sample_shopify_product])

        product = products[0]

        # Check first variant (in stock)
        variant1 = product.variants[0]
        assert variant1.id == "gid://shopify/ProductVariant/1"
        assert variant1.title == "Size 8 / Red"
        assert variant1.price == 99.99
        assert variant1.available_for_sale is True
        assert variant1.selected_options == {"Size": "8", "Color": "Red"}

        # Check second variant (out of stock)
        variant2 = product.variants[1]
        assert variant2.id == "gid://shopify/ProductVariant/2"
        assert variant2.available_for_sale is False

    def test_map_products_empty_list(self, mapper: ProductMapper) -> None:
        """Test mapping empty product list."""
        products = mapper.map_products([])

        assert products == []

    def test_map_multiple_products(
        self,
        mapper: ProductMapper,
        sample_shopify_product: dict[str, Any],
    ) -> None:
        """Test mapping multiple products."""
        # Create a second product
        product2 = sample_shopify_product.copy()
        product2["id"] = "gid://shopify/Product/2"
        product2["title"] = "Walking Shoes"

        products = mapper.map_products([sample_shopify_product, product2])

        assert len(products) == 2
        assert products[0].id == "gid://shopify/Product/1"
        assert products[1].id == "gid://shopify/Product/2"

    def test_filter_products_by_budget(
        self,
        mapper: ProductMapper,
    ) -> None:
        """Test filtering products by budget constraint."""
        # Create products with prices: 50, 75, 100, 125, 150
        prices = [50.0, 75.0, 100.0, 125.0, 150.0]
        products = [
            Product(
                id=f"gid://shopify/Product/{i}",
                title=f"Product {i}",
                product_type="Test",
                price=price,
                variants=[
                    ProductVariant(
                        id=f"gid://shopify/ProductVariant/{i}",
                        product_id=f"gid://shopify/Product/{i}",
                        title=f"Variant {i}",
                        price=price,
                        available_for_sale=True,
                        selected_options={},
                    )
                ],
            )
            for i, price in enumerate(prices, start=1)
        ]

        filtered = mapper.filter_by_budget(products, budget=100.0)

        # Only products <= $100 should remain (50, 75, 100)
        assert len(filtered) == 3
        assert all(p.price <= 100.0 for p in filtered)

    def test_filter_products_by_size(
        self,
        mapper: ProductMapper,
    ) -> None:
        """Test filtering products by size variant."""
        # Create products with different size variants
        products = [
            Product(
                id="gid://shopify/Product/1",
                title="Shoes with Size 8",
                product_type="Footwear",
                price=100.0,
                variants=[
                    ProductVariant(
                        id="gid://shopify/ProductVariant/1",
                        product_id="gid://shopify/Product/1",
                        title="Size 8",
                        price=100.0,
                        available_for_sale=True,
                        selected_options={"Size": "8"},
                    )
                ],
            ),
            Product(
                id="gid://shopify/Product/2",
                title="Shoes with Size 9",
                product_type="Footwear",
                price=100.0,
                variants=[
                    ProductVariant(
                        id="gid://shopify/ProductVariant/2",
                        product_id="gid://shopify/Product/2",
                        title="Size 9",
                        price=100.0,
                        available_for_sale=True,
                        selected_options={"Size": "9"},
                    )
                ],
            ),
            Product(
                id="gid://shopify/Product/3",
                title="Shoes with Size 10",
                product_type="Footwear",
                price=100.0,
                variants=[
                    ProductVariant(
                        id="gid://shopify/ProductVariant/3",
                        product_id="gid://shopify/Product/3",
                        title="Size 10",
                        price=100.0,
                        available_for_sale=True,
                        selected_options={"Size": "10"},
                    )
                ],
            ),
        ]

        # Filter for size 8
        filtered = mapper.filter_by_size(products, size="8")

        # Only product with size 8 variant should match
        assert len(filtered) == 1
        assert filtered[0].id == "gid://shopify/Product/1"

    def test_filter_by_size_no_match(self, mapper: ProductMapper) -> None:
        """Test size filtering with no matching products."""
        products = [
            Product(
                id="gid://shopify/Product/1",
                title="Shoes Size 9",
                product_type="Footwear",
                price=100.0,
                variants=[
                    ProductVariant(
                        id="gid://shopify/ProductVariant/1",
                        product_id="gid://shopify/Product/1",
                        title="Size 9",
                        price=100.0,
                        available_for_sale=True,
                        selected_options={"Size": "9"},
                    )
                ],
            )
        ]

        filtered = mapper.filter_by_size(products, size="8")

        # No products should match
        assert len(filtered) == 0

    def test_filter_by_availability(self, mapper: ProductMapper) -> None:
        """Test filtering products by availability."""
        products = [
            Product(
                id="gid://shopify/Product/1",
                title="In Stock Product",
                product_type="Test",
                price=100.0,
                variants=[
                    ProductVariant(
                        id="gid://shopify/ProductVariant/1",
                        product_id="gid://shopify/Product/1",
                        title="In Stock",
                        price=100.0,
                        available_for_sale=True,
                        selected_options={},
                    )
                ],
            ),
            Product(
                id="gid://shopify/Product/2",
                title="Out of Stock Product",
                product_type="Test",
                price=100.0,
                variants=[
                    ProductVariant(
                        id="gid://shopify/ProductVariant/2",
                        product_id="gid://shopify/Product/2",
                        title="Out of Stock",
                        price=100.0,
                        available_for_sale=False,
                        selected_options={},
                    )
                ],
            ),
        ]

        filtered = mapper.filter_by_availability(products)

        # Only in-stock products should remain
        assert len(filtered) == 1
        assert filtered[0].id == "gid://shopify/Product/1"

    def test_map_entities_to_search_params(self, mapper: ProductMapper) -> None:
        """Test mapping extracted entities to search parameters."""
        entities = ExtractedEntities(
            category="shoes",
            budget=100.0,
            size="8",
            color="red",
        )

        params = mapper.map_entities_to_search_params(entities)

        assert params["category"] == "shoes"
        assert params["max_price"] == 100.0
        assert params["size"] == "8"
        assert params["color"] == "red"

    def test_map_entities_with_none_values(self, mapper: ProductMapper) -> None:
        """Test mapping entities with None values."""
        entities = ExtractedEntities(
            category=None,
            budget=None,
            size=None,
        )

        params = mapper.map_entities_to_search_params(entities)

        # Should have keys but None values
        assert params.get("category") is None
        assert params.get("max_price") is None
        assert params.get("size") is None
