"""Integration tests for Product Display (Story 2.3).

Tests end-to-end flow from product search to Messenger display
using mocked Facebook Send API.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

from app.schemas.shopify import (
    CurrencyCode,
    Product,
    ProductImage,
    ProductSearchResult,
    ProductVariant,
)
from app.services.messenger import MessengerProductFormatter, MessengerSendService


@pytest.fixture
def mock_settings() -> dict[str, Any]:
    """Mock settings for testing."""
    return {
        "FACEBOOK_PAGE_ACCESS_TOKEN": "test_token_123",
        "FACEBOOK_API_VERSION": "v19.0",
        "MESSENGER_FALLBACK_IMAGE_URL": "https://cdn.example.com/fallback.png",
        "STORE_URL": "https://shop.example.com",
    }


@pytest.fixture
def sample_search_result() -> ProductSearchResult:
    """Sample product search result."""
    return ProductSearchResult(
        products=[
            Product(
                id="gid://shopify/Product/1",
                title="Nike Running Shoes",
                description="Professional running shoes for marathon training",
                product_type="Footwear",
                tags=["running", "shoes", "nike"],
                price=89.99,
                currency_code=CurrencyCode.USD,
                images=[
                    ProductImage(url="https://cdn.shopify.com/test.jpg", alt_text="Running shoes")
                ],
                variants=[
                    ProductVariant(
                        id="gid://shopify/ProductVariant/1",
                        product_id="gid://shopify/Product/1",
                        title="Size 8",
                        price=89.99,
                        currency_code=CurrencyCode.USD,
                        available_for_sale=True,
                        selected_options={"Size": "8"},
                    )
                ],
            ),
            Product(
                id="gid://shopify/Product/2",
                title="Adidas Running Shoes",
                description="Lightweight running shoes for daily training",
                product_type="Footwear",
                tags=["running", "shoes", "adidas"],
                price=79.99,
                currency_code=CurrencyCode.USD,
                images=[
                    ProductImage(url="https://cdn.shopify.com/test2.jpg", alt_text="Adidas shoes")
                ],
                variants=[
                    ProductVariant(
                        id="gid://shopify/ProductVariant/2",
                        product_id="gid://shopify/Product/2",
                        title="Size 9",
                        price=79.99,
                        currency_code=CurrencyCode.USD,
                        available_for_sale=True,
                        selected_options={"Size": "9"},
                    )
                ],
            ),
        ],
        total_count=2,
        search_params={"category": "shoes", "maxPrice": 100.0},
    )


class TestProductDisplayIntegration:
    """Integration tests for product display flow."""

    @pytest.mark.asyncio
    async def test_formatter_and_send_integration(
        self,
        mock_settings: dict[str, Any],
        sample_search_result: ProductSearchResult,
    ) -> None:
        """Test formatter and send service working together."""
        with (
            patch("app.services.messenger.product_formatter.settings", return_value=mock_settings),
            patch("app.services.messenger.send_service.settings", return_value=mock_settings),
        ):
            # Format products
            formatter = MessengerProductFormatter()
            message_payload = formatter.format_product_results(sample_search_result)

            # Verify structure
            assert "attachment" in message_payload
            assert message_payload["attachment"]["type"] == "template"

            elements = message_payload["attachment"]["payload"]["elements"]
            assert len(elements) == 2

            # Send to Facebook
            with respx.mock:
                request = respx.post(
                    "https://graph.facebook.com/v19.0/me/messages"
                ).mock(
                    return_value=httpx.Response(
                        200,
                        json={"message_id": "mid.msg_456"},
                    )
                )

                send_service = MessengerSendService()
                response = await send_service.send_message("test_psid", message_payload)
                await send_service.close()

                assert response["message_id"] == "mid.msg_456"
                assert request.called

    @pytest.mark.asyncio
    async def test_send_api_error_handling(
        self,
        mock_settings: dict[str, Any],
        sample_search_result: ProductSearchResult,
    ) -> None:
        """Test handling of Facebook Send API errors."""
        from app.core.errors import APIError

        with (
            patch("app.services.messenger.product_formatter.settings", return_value=mock_settings),
            patch("app.services.messenger.send_service.settings", return_value=mock_settings),
        ):
            formatter = MessengerProductFormatter()
            message_payload = formatter.format_product_results(sample_search_result)

            send_service = MessengerSendService()

            # Mock Facebook error response
            with respx.mock:
                respx.post(
                    "https://graph.facebook.com/v19.0/me/messages"
                ).mock(
                    return_value=httpx.Response(
                        200,
                        json={
                            "error": {
                                "code": 100,
                                "message": "Invalid parameter",
                            }
                        },
                    )
                )

                with pytest.raises(APIError):
                    await send_service.send_message("test_psid", message_payload)

            await send_service.close()


class TestProductDisplayEdgeCases:
    """Tests for edge cases in product display."""

    @pytest.mark.asyncio
    async def test_product_without_images(
        self,
        mock_settings: dict[str, Any],
    ) -> None:
        """Test formatting product without images (uses fallback)."""
        with patch("app.services.messenger.product_formatter.settings", return_value=mock_settings):
            formatter = MessengerProductFormatter()

            product = Product(
                id="gid://shopify/Product/1",
                title="Product Without Image",
                product_type="Test",
                price=10.0,
                currency_code=CurrencyCode.USD,
                images=[],  # No images
                variants=[],
            )

            search_result = ProductSearchResult(
                products=[product],
                total_count=1,
                search_params={},
            )

            message_payload = formatter.format_product_results(search_result)
            element = message_payload["attachment"]["payload"]["elements"][0]

            # Should use fallback image
            assert "fallback" in element["image_url"].lower() or "cdn" in element["image_url"].lower()

    @pytest.mark.asyncio
    async def test_product_with_long_title(
        self,
        mock_settings: dict[str, Any],
    ) -> None:
        """Test that long titles are properly truncated."""
        with patch("app.services.messenger.product_formatter.settings", return_value=mock_settings):
            formatter = MessengerProductFormatter()

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

            search_result = ProductSearchResult(
                products=[product],
                total_count=1,
                search_params={},
            )

            message_payload = formatter.format_product_results(search_result)
            element = message_payload["attachment"]["payload"]["elements"][0]

            # Title should be truncated
            assert len(element["title"]) <= 83  # 80 + "..."

    @pytest.mark.asyncio
    async def test_multiple_products_ordering(
        self,
        mock_settings: dict[str, Any],
    ) -> None:
        """Test that products maintain their order from search results."""
        with patch("app.services.messenger.product_formatter.settings", return_value=mock_settings):
            formatter = MessengerProductFormatter()

            products = [
                Product(
                    id=f"gid://shopify/Product/{i}",
                    title=f"Product {i}",
                    product_type="Test",
                    price=float(i * 10),
                    currency_code=CurrencyCode.USD,
                    images=[ProductImage(url=f"https://example.com/test{i}.jpg")],
                    variants=[],
                    relevance_score=float(i * 10),
                )
                for i in [3, 1, 2]  # Intentionally out of order
            ]

            search_result = ProductSearchResult(
                products=products,
                total_count=3,
                search_params={},
            )

            message_payload = formatter.format_product_results(search_result)
            elements = message_payload["attachment"]["payload"]["elements"]

            # Should maintain order (Product 3, then 1, then 2)
            assert len(elements) == 3
            assert "Product 3" in elements[0]["title"]
            assert "Product 1" in elements[1]["title"]
            assert "Product 2" in elements[2]["title"]

    @pytest.mark.asyncio
    async def test_product_with_variants(
        self,
        mock_settings: dict[str, Any],
    ) -> None:
        """Test subtitle formatting with variants."""
        with patch("app.services.messenger.product_formatter.settings", return_value=mock_settings):
            formatter = MessengerProductFormatter()

            product = Product(
                id="gid://shopify/Product/1",
                title="T-Shirt",
                product_type="Apparel",
                price=25.0,
                currency_code=CurrencyCode.USD,
                images=[ProductImage(url="https://example.com/shirt.jpg")],
                variants=[
                    ProductVariant(
                        id=f"gid://shopify/ProductVariant/{size}",
                        product_id="gid://shopify/Product/1",
                        title=f"Size {size}",
                        price=25.0,
                        currency_code=CurrencyCode.USD,
                        available_for_sale=True,
                        selected_options={"Size": str(size)},
                    )
                    for size in [8, 9, 10, 11]
                ],
            )

            search_result = ProductSearchResult(
                products=[product],
                total_count=1,
                search_params={},
            )

            message_payload = formatter.format_product_results(search_result)
            element = message_payload["attachment"]["payload"]["elements"][0]

            # Subtitle should mention available sizes
            subtitle = element["subtitle"].lower()
            assert "sizes" in subtitle or "size" in subtitle
            assert "$25.00" in subtitle

    @pytest.mark.asyncio
    async def test_add_to_cart_button_payload(
        self,
        mock_settings: dict[str, Any],
        sample_search_result: ProductSearchResult,
    ) -> None:
        """Test that Add to Cart button has correct payload."""
        with patch("app.services.messenger.product_formatter.settings", return_value=mock_settings):
            formatter = MessengerProductFormatter()
            message_payload = formatter.format_product_results(sample_search_result)

            elements = message_payload["attachment"]["payload"]["elements"]

            for element in elements:
                buttons = element["buttons"]
                assert len(buttons) >= 1

                button = buttons[0]
                assert button["type"] == "postback"
                assert button["title"] == "Add to Cart"

                payload = button["payload"]
                assert "ADD_TO_CART" in payload
                assert "gid://shopify/Product/" in payload
