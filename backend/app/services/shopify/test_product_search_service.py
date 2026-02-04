"""Tests for ProductSearchService.

Tests product search orchestration, relevance ranking, and
integration with Storefront client and mapper.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.shopify import Product, ProductSearchResult
from app.services.intent.classification_schema import ExtractedEntities, IntentType
from app.services.shopify.product_mapper import ProductMapper
from app.services.shopify.product_search_service import ProductSearchService
from app.services.shopify.storefront_client import ShopifyStorefrontClient


@pytest.fixture
def mock_settings() -> dict[str, Any]:
    """Mock settings for testing."""
    return {
        "SHOPIFY_STORE_URL": "https://test-shop.myshopify.com",
        "SHOPIFY_STOREFRONT_ACCESS_TOKEN": "test_token_123",
    }


@pytest.fixture
def sample_shopify_products() -> list[dict[str, Any]]:
    """Sample Shopify products for testing."""
    return [
        {
            "id": "gid://shopify/Product/1",
            "title": "Nike Running Shoes",
            "description": "Professional running shoes",
            "productType": "Footwear",
            "tags": ["running", "shoes", "nike"],
            "vendor": "Nike",
            "priceRangeV2": {
                "minVariantPrice": {"amount": "89.99", "currencyCode": "USD"}
            },
            "images": {"edges": []},
            "variants": {
                "edges": [
                    {
                        "node": {
                            "id": "gid://shopify/ProductVariant/1",
                            "productId": "gid://shopify/Product/1",
                            "title": "Size 8",
                            "priceV2": {"amount": "89.99", "currencyCode": "USD"},
                            "availableForSale": True,
                            "selectedOptions": [{"name": "Size", "value": "8"}],
                        }
                    }
                ]
            },
        },
        {
            "id": "gid://shopify/Product/2",
            "title": "Adidas Walking Shoes",
            "description": "Comfortable walking shoes",
            "productType": "Footwear",
            "tags": ["walking", "shoes", "adidas"],
            "vendor": "Adidas",
            "priceRangeV2": {
                "minVariantPrice": {"amount": "69.99", "currencyCode": "USD"}
            },
            "images": {"edges": []},
            "variants": {
                "edges": [
                    {
                        "node": {
                            "id": "gid://shopify/ProductVariant/2",
                            "productId": "gid://shopify/Product/2",
                            "title": "Size 9",
                            "priceV2": {"amount": "69.99", "currencyCode": "USD"},
                            "availableForSale": True,
                            "selectedOptions": [{"name": "Size", "value": "9"}],
                        }
                    }
                ]
            },
        },
        {
            "id": "gid://shopify/Product/3",
            "title": "Nike Basketball Shoes",
            "description": "High-top basketball shoes",
            "productType": "Footwear",
            "tags": ["basketball", "shoes", "nike"],
            "vendor": "Nike",
            "priceRangeV2": {
                "minVariantPrice": {"amount": "129.99", "currencyCode": "USD"}
            },
            "images": {"edges": []},
            "variants": {
                "edges": [
                    {
                        "node": {
                            "id": "gid://shopify/ProductVariant/3",
                            "productId": "gid://shopify/Product/3",
                            "title": "Size 10",
                            "priceV2": {"amount": "129.99", "currencyCode": "USD"},
                            "availableForSale": True,
                            "selectedOptions": [{"name": "Size", "value": "10"}],
                        }
                    }
                ]
            },
        },
    ]


class TestProductSearchService:
    """Tests for ProductSearchService."""

    @pytest.fixture
    def service(self, mock_settings: dict[str, Any]) -> ProductSearchService:
        """Create a ProductSearchService with mocked dependencies."""
        with patch("app.services.shopify.storefront_client.settings", return_value=mock_settings):
            return ProductSearchService()

    def test_init_with_defaults(self, mock_settings: dict[str, Any]) -> None:
        """Test service initialization with default dependencies."""
        with patch("app.services.shopify.storefront_client.settings", return_value=mock_settings):
            service = ProductSearchService()

            assert service.client is not None
            assert service.mapper is not None

    def test_init_with_custom_dependencies(self) -> None:
        """Test service initialization with custom dependencies."""
        mock_client = MagicMock(spec=ShopifyStorefrontClient)
        mock_mapper = MagicMock(spec=ProductMapper)

        service = ProductSearchService(
            storefront_client=mock_client,
            product_mapper=mock_mapper,
        )

        assert service.client == mock_client
        assert service.mapper == mock_mapper

    @pytest.mark.asyncio
    async def test_search_products_with_category(
        self,
        service: ProductSearchService,
        sample_shopify_products: list[dict[str, Any]],
    ) -> None:
        """Test product search with category filter."""
        entities = ExtractedEntities(category="shoes")

        with patch.object(
            service.client,
            "search_products",
            new_callable=AsyncMock,
            return_value=sample_shopify_products,
        ):
            result = await service.search_products(entities)

            assert isinstance(result, ProductSearchResult)
            assert result.total_count == 3
            assert len(result.products) == 3
            assert result.search_params["category"] == "shoes"

    @pytest.mark.asyncio
    async def test_search_products_with_budget(
        self,
        service: ProductSearchService,
        sample_shopify_products: list[dict[str, Any]],
    ) -> None:
        """Test product search with budget constraint."""
        entities = ExtractedEntities(category="shoes", budget=100.0)

        with patch.object(
            service.client,
            "search_products",
            new_callable=AsyncMock,
            return_value=sample_shopify_products,
        ):
            result = await service.search_products(entities)

            # Only products <= $100 should be returned
            assert result.total_count >= 0
            assert all(p.price <= 100.0 for p in result.products)
            assert result.search_params["maxPrice"] == 100.0

    @pytest.mark.asyncio
    async def test_search_products_with_size(
        self,
        service: ProductSearchService,
        sample_shopify_products: list[dict[str, Any]],
    ) -> None:
        """Test product search with size constraint."""
        entities = ExtractedEntities(category="shoes", size="8")

        with patch.object(
            service.client,
            "search_products",
            new_callable=AsyncMock,
            return_value=sample_shopify_products,
        ):
            result = await service.search_products(entities)

            # Results should be filtered to size 8
            assert result.search_params["size"] == "8"

    @pytest.mark.asyncio
    async def test_search_products_no_results(
        self,
        service: ProductSearchService,
    ) -> None:
        """Test search with no matching products."""
        entities = ExtractedEntities(category="nonexistent", budget=1.0)

        with patch.object(
            service.client,
            "search_products",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await service.search_products(entities)

            assert result.total_count == 0
            assert len(result.products) == 0
            # When there are no results, has_alternatives should be True
            # to suggest the user broaden their search
            assert result.has_alternatives is True

    @pytest.mark.asyncio
    async def test_search_products_relevance_ranking(
        self,
        service: ProductSearchService,
        sample_shopify_products: list[dict[str, Any]],
    ) -> None:
        """Test that products are ranked by relevance."""
        entities = ExtractedEntities(category="running shoes", budget=150.0)

        with patch.object(
            service.client,
            "search_products",
            new_callable=AsyncMock,
            return_value=sample_shopify_products,
        ):
            result = await service.search_products(entities)

            # Products should be sorted by relevance score
            scores = [p.relevance_score for p in result.products]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_search_products_relevance_category_boost(
        self,
        service: ProductSearchService,
        sample_shopify_products: list[dict[str, Any]],
    ) -> None:
        """Test that category match gives highest relevance boost."""
        entities = ExtractedEntities(category="running")

        with patch.object(
            service.client,
            "search_products",
            new_callable=AsyncMock,
            return_value=sample_shopify_products,
        ):
            result = await service.search_products(entities)

            # "Nike Running Shoes" should rank highest due to "running" tag
            # while "Nike Basketball Shoes" has Nike brand but not running
            assert result.products[0].title == "Nike Running Shoes"
            assert result.products[0].relevance_score > 0

    @pytest.mark.asyncio
    async def test_search_products_relevance_price_proximity(
        self,
        service: ProductSearchService,
    ) -> None:
        """Test that price proximity affects relevance score."""
        entities = ExtractedEntities(budget=90.0)

        products = [
            {
                "id": "gid://shopify/Product/1",
                "title": "Expensive Shoes",
                "productType": "Footwear",
                "tags": [],
                "priceRangeV2": {"minVariantPrice": {"amount": "150.00", "currencyCode": "USD"}},
                "images": {"edges": []},
                "variants": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/ProductVariant/1",
                                "productId": "gid://shopify/Product/1",
                                "title": "Size 8",
                                "priceV2": {"amount": "150.00", "currencyCode": "USD"},
                                "availableForSale": True,
                                "selectedOptions": [],
                            }
                        }
                    ]
                },
            },
            {
                "id": "gid://shopify/Product/2",
                "title": "Close to Budget",
                "productType": "Footwear",
                "tags": [],
                "priceRangeV2": {"minVariantPrice": {"amount": "85.00", "currencyCode": "USD"}},
                "images": {"edges": []},
                "variants": {
                    "edges": [
                        {
                            "node": {
                                "id": "gid://shopify/ProductVariant/2",
                                "productId": "gid://shopify/Product/2",
                                "title": "Size 8",
                                "priceV2": {"amount": "85.00", "currencyCode": "USD"},
                                "availableForSale": True,
                                "selectedOptions": [],
                            }
                        }
                    ]
                },
            },
        ]

        with patch.object(
            service.client,
            "search_products",
            new_callable=AsyncMock,
            return_value=products,
        ):
            result = await service.search_products(entities)

            # Product closer to budget should rank higher (and pass budget filter)
            # Expensive shoes (150) > budget (90) so it should be filtered out
            assert len(result.products) >= 1
            assert result.products[0].title == "Close to Budget"

    @pytest.mark.asyncio
    async def test_rank_products(
        self,
        service: ProductSearchService,
    ) -> None:
        """Test product ranking algorithm."""
        products = [
            Product(
                id="gid://shopify/Product/1",
                title="Running Shoes",
                product_type="Footwear",
                price=80.0,
                tags=["running", "shoes"],
            ),
            Product(
                id="gid://shopify/Product/2",
                title="Basketball Shoes",
                product_type="Footwear",
                price=120.0,
                tags=["basketball", "shoes"],
            ),
        ]

        entities = ExtractedEntities(category="running", budget=100.0)

        ranked = service._rank_products(products, entities)

        # Running shoes should rank higher due to category match
        assert ranked[0].title == "Running Shoes"
        assert ranked[0].relevance_score > ranked[1].relevance_score

    @pytest.mark.asyncio
    async def test_search_with_all_constraints(
        self,
        service: ProductSearchService,
        sample_shopify_products: list[dict[str, Any]],
    ) -> None:
        """Test search with category, budget, and size constraints."""
        entities = ExtractedEntities(
            category="shoes",
            budget=100.0,
            size="8",
            color="red",
        )

        with patch.object(
            service.client,
            "search_products",
            new_callable=AsyncMock,
            return_value=sample_shopify_products,
        ):
            result = await service.search_products(entities)

            # All search params should be included
            assert result.search_params["category"] == "shoes"
            assert result.search_params["maxPrice"] == 100.0
            assert result.search_params["size"] == "8"
            assert result.search_params["color"] == "red"

    @pytest.mark.asyncio
    async def test_search_time_tracking(
        self,
        service: ProductSearchService,
        sample_shopify_products: list[dict[str, Any]],
    ) -> None:
        """Test that search time is tracked."""
        entities = ExtractedEntities(category="shoes")

        with patch.object(
            service.client,
            "search_products",
            new_callable=AsyncMock,
            return_value=sample_shopify_products,
        ):
            result = await service.search_products(entities)

            # Search time should be tracked
            assert result.search_time_ms is not None
            assert result.search_time_ms >= 0


class TestProductSearchServiceErrors:
    """Tests for error handling in ProductSearchService."""

    @pytest.fixture
    def service(self, mock_settings: dict[str, Any]) -> ProductSearchService:
        """Create a ProductSearchService with mocked dependencies."""
        with patch("app.services.shopify.storefront_client.settings", return_value=mock_settings):
            return ProductSearchService()

    @pytest.mark.asyncio
    async def test_client_error_propagation(self, service: ProductSearchService) -> None:
        """Test that client errors are properly propagated."""
        from app.core.errors import APIError

        entities = ExtractedEntities(category="shoes")

        with patch.object(
            service.client,
            "search_products",
            new_callable=AsyncMock,
            side_effect=APIError(
                4000,  # SHOPIFY_API_ERROR
                "Shopify API unavailable",
            ),
        ):
            with pytest.raises(APIError) as exc_info:
                await service.search_products(entities)

            assert exc_info.value.code == 4000
