"""Integration tests for product search.

Tests end-to-end product search flow with mocked Shopify API,
including message processing and response formatting.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.messaging import MessengerResponse
from app.services.intent.classification_schema import ClassificationResult, ExtractedEntities, IntentType
from app.services.messaging.message_processor import MessageProcessor
from app.services.shopify import ProductSearchService


@pytest.fixture
def mock_settings() -> dict[str, Any]:
    """Mock settings for testing."""
    return {
        "SHOPIFY_STORE_URL": "https://test-shop.myshopify.com",
        "SHOPIFY_STOREFRONT_ACCESS_TOKEN": "test_token_123",
    }


@pytest.fixture
def sample_shopify_response() -> list[dict[str, Any]]:
    """Sample Shopify products for integration tests."""
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
                            "priceV2": {"amount": "89.99", "currencyCode": "USD"},
                            "availableForSale": True,
                            "selectedOptions": [
                                {"name": "Size", "value": "8"},
                                {"name": "Color", "value": "Red"},
                            ],
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
    ]


class TestProductSearchIntegration:
    """Integration tests for product search."""

    @pytest.mark.asyncio
    async def test_product_search_flow_with_results(
        self,
        mock_settings: dict[str, Any],
        sample_shopify_response: list[dict[str, Any]],
    ) -> None:
        """Test complete product search flow with results."""
        with patch("app.services.shopify.storefront_client.settings", return_value=mock_settings):
            # Create classification with entities
            classification = ClassificationResult(
                intent=IntentType.PRODUCT_SEARCH,
                confidence=0.95,
                entities=ExtractedEntities(category="shoes", budget=100.0),
                raw_message="Show me shoes under $100",
                llm_provider="test",
                model="test-model",
                processing_time_ms=100.0,
            )

            # Create service
            service = ProductSearchService()

            # Mock the storefront client
            with patch.object(
                service.client,
                "search_products",
                new_callable=AsyncMock,
                return_value=sample_shopify_response,
            ):
                result = await service.search_products(classification.entities)

                # Verify results
                assert result.total_count >= 1
                assert len(result.products) >= 1
                assert result.search_params["category"] == "shoes"
                assert result.search_params["maxPrice"] == 100.0
                assert result.search_time_ms is not None

    @pytest.mark.asyncio
    async def test_product_search_flow_no_results(
        self,
        mock_settings: dict[str, Any],
    ) -> None:
        """Test product search flow with no results."""
        with patch("app.services.shopify.storefront_client.settings", return_value=mock_settings):
            classification = ClassificationResult(
                intent=IntentType.PRODUCT_SEARCH,
                confidence=0.90,
                entities=ExtractedEntities(category="nonexistent", budget=1.0),
                raw_message="Show me products for $1",
                llm_provider="test",
                model="test-model",
                processing_time_ms=100.0,
            )

            service = ProductSearchService()

            with patch.object(
                service.client,
                "search_products",
                new_callable=AsyncMock,
                return_value=[],
            ):
                result = await service.search_products(classification.entities)

                # Verify empty result
                assert result.total_count == 0
                assert len(result.products) == 0
                assert result.has_alternatives is True

    @pytest.mark.asyncio
    async def test_message_processor_product_search_route(
        self,
        mock_settings: dict[str, Any],
        sample_shopify_response: list[dict[str, Any]],
    ) -> None:
        """Test message processor routes product search correctly."""
        # Create webhook payload
        from app.schemas.messaging import FacebookWebhookPayload, FacebookEntry

        payload = FacebookWebhookPayload(
            object="page",
            entry=[
                FacebookEntry(
                    id="test_page_id",
                    time=1234567890,
                    messaging=[
                        {
                            "sender": {"id": "test_psid"},
                            "recipient": {"id": "test_page_id"},
                            "message": {"text": "Show me running shoes under $100"},
                            "timestamp": 1234567890,
                        }
                    ],
                )
            ],
        )

        # Mock the intent classifier
        mock_classification = ClassificationResult(
            intent=IntentType.PRODUCT_SEARCH,
            confidence=0.95,
            entities=ExtractedEntities(category="running shoes", budget=100.0),
            raw_message="Show me running shoes under $100",
            llm_provider="test",
            model="test-model",
            processing_time_ms=100.0,
        )

        # Mock ProductSearchService
        with patch("app.services.shopify.storefront_client.settings", return_value=mock_settings):
            processor = MessageProcessor()

            # Mock classifier and product search
            with patch.object(
                processor.classifier,
                "classify",
                new_callable=AsyncMock,
                return_value=mock_classification,
            ):
                with patch.object(
                    processor.context_manager,
                    "get_context",
                    new_callable=AsyncMock,
                    return_value={"psid": "test_psid"},
                ):
                    with patch.object(
                        processor.context_manager,
                        "update_classification",
                        new_callable=AsyncMock,
                    ):
                        # Mock product search service
                        mock_result = MagicMock()
                        mock_result.total_count = 2
                        mock_result.products = sample_shopify_response[:2]
                        mock_result.has_alternatives = False
                        mock_result.search_time_ms = 150.0

                        with patch(
                            "app.services.shopify.ProductSearchService"
                        ) as mock_service_class:
                            mock_service_instance = AsyncMock()
                            mock_service_instance.search_products.return_value = mock_result
                            mock_service_class.return_value = mock_service_instance

                            response = await processor.process_message(payload)

                            # Verify response
                            assert isinstance(response, MessengerResponse)
                            assert response.recipient_id == "test_psid"

    @pytest.mark.asyncio
    async def test_relevance_ranking_integration(
        self,
        mock_settings: dict[str, Any],
        sample_shopify_response: list[dict[str, Any]],
    ) -> None:
        """Test relevance ranking in integration context."""
        with patch("app.services.shopify.storefront_client.settings", return_value=mock_settings):
            entities = ExtractedEntities(category="running", budget=100.0)

            service = ProductSearchService()

            with patch.object(
                service.client,
                "search_products",
                new_callable=AsyncMock,
                return_value=sample_shopify_response,
            ):
                result = await service.search_products(entities)

                # Check that products are sorted by relevance
                scores = [p.relevance_score for p in result.products]
                assert scores == sorted(scores, reverse=True)

                # Running shoes should be highest ranked
                assert "Running" in result.products[0].title

    @pytest.mark.asyncio
    async def test_budget_filtering_integration(
        self,
        mock_settings: dict[str, Any],
        sample_shopify_response: list[dict[str, Any]],
    ) -> None:
        """Test budget filtering in integration context."""
        with patch("app.services.shopify.storefront_client.settings", return_value=mock_settings):
            entities = ExtractedEntities(category="shoes", budget=70.0)

            service = ProductSearchService()

            with patch.object(
                service.client,
                "search_products",
                new_callable=AsyncMock,
                return_value=sample_shopify_response,
            ):
                result = await service.search_products(entities)

                # All products should be within budget
                for product in result.products:
                    assert product.price <= 70.0

    @pytest.mark.asyncio
    async def test_error_handling_integration(
        self,
        mock_settings: dict[str, Any],
    ) -> None:
        """Test error handling in product search integration."""
        from app.core.errors import APIError, ErrorCode

        with patch("app.services.shopify.storefront_client.settings", return_value=mock_settings):
            entities = ExtractedEntities(category="shoes")

            service = ProductSearchService()

            # Mock API error
            with patch.object(
                service.client,
                "search_products",
                new_callable=AsyncMock,
                side_effect=APIError(
                    ErrorCode.SHOPIFY_API_ERROR,
                    "Shopify API unavailable",
                ),
            ):
                with pytest.raises(APIError) as exc_info:
                    await service.search_products(entities)

                assert exc_info.value.code == ErrorCode.SHOPIFY_API_ERROR
