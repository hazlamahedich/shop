"""Messenger Product Formatter Service.

Formats Shopify products for Facebook Messenger display using
Generic Template structured messages.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Union

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.schemas.shopify import Product, ProductSearchResult

import structlog


class MessengerProductFormatter:
    """Format Shopify products for Facebook Messenger display.

    Uses Facebook Messenger Generic Template for structured product cards
    with images, titles, prices, and Add to Cart buttons.

    Attributes:
        MAX_TITLE_LENGTH: Maximum title length for Messenger (80 chars)
        MIN_IMAGE_DIMENSION: Minimum image dimension in pixels
        MAX_IMAGE_SIZE_BYTES: Maximum image file size in bytes
        FALLBACK_IMAGE_URL: Default image URL when product has no image
    """

    MAX_TITLE_LENGTH = 80
    MIN_IMAGE_DIMENSION = 400
    MAX_IMAGE_SIZE_BYTES = 524288  # 500KB

    def __init__(self) -> None:
        """Initialize Messenger Product Formatter."""
        self.logger = structlog.get_logger(__name__)
        config = settings()

        # Get fallback image from config or use default
        self.FALLBACK_IMAGE_URL = config.get(
            "MESSENGER_FALLBACK_IMAGE_URL",
            "https://cdn.shopify.com/s/files/1/0533/2089/files/fallback-product.png",
        )

        # Get store URL for default action
        self.STORE_URL = config.get("STORE_URL", "https://shop.example.com")

    def format_product_results(
        self,
        search_result: ProductSearchResult,
    ) -> Dict[str, Any]:
        """Format product search results for Messenger Generic Template.

        Args:
            search_result: Product search result from Story 2.2

        Returns:
            Messenger Generic Template payload with product cards

        Raises:
            APIError: If no products can be formatted for display
        """
        elements: List[Dict[str, Any]] = []

        for product in search_result.products:
            try:
                element = self._format_product_card(product)
                if element:
                    elements.append(element)
            except Exception as e:
                self.logger.warning(
                    "product_format_failed",
                    product_id=product.id,
                    error=str(e),
                )
                # Skip this product, continue with others
                continue

        if not elements:
            raise APIError(
                ErrorCode.MESSAGE_SEND_FAILED,
                "No products could be formatted for display",
            )

        return {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements,
                },
            },
        }

    def _format_product_card(self, product: Product) -> Dict[str, Any]:
        """Format a single product as a Generic Template element.

        Args:
            product: Product from Shopify

        Returns:
            Generic Template element dict with product info

        Raises:
            ValueError: If product data is invalid
        """
        if not product.title:
            raise ValueError(f"Product {product.id} has no title")

        # Get primary image with fallback
        image_url = self._get_valid_image_url(product)

        # Truncate title if needed
        title = self._truncate_title(product.title)

        # Build subtitle with price and variant summary
        subtitle = self._build_subtitle(product)

        # Get default variant for add-to-cart button
        default_variant = self._select_default_variant(product)

        # Build button payload
        button_payload = self._build_button_payload(
            product.id,
            default_variant.id if default_variant else product.id,
        )

        # Build element
        element: Dict[str, Any] = {
            "title": title,
            "image_url": image_url,
            "subtitle": subtitle,
            "default_action": {
                "type": "web_url",
                "url": f"{self.STORE_URL}/products/{self._extract_product_id(product.id)}",
                "webview_height_ratio": "tall",
            },
            "buttons": [
                {
                    "type": "postback",
                    "title": "Add to Cart",
                    "payload": button_payload,
                }
            ],
        }

        return element

    def _get_valid_image_url(self, product: Product) -> str:
        """Get a valid image URL with fallback.

        Args:
            product: Product from Shopify

        Returns:
            Valid image URL (uses fallback if product has no image)
        """
        if product.images:
            image = product.images[0]
            # In production, would validate dimensions here
            # For now, trust Shopify CDN
            return image.url

        # Fallback placeholder
        return self.FALLBACK_IMAGE_URL

    def _truncate_title(self, title: str) -> str:
        """Truncate title to max length.

        Args:
            title: Full product title

        Returns:
            Truncated title with ellipsis if needed
        """
        if len(title) <= self.MAX_TITLE_LENGTH:
            return title

        return title[: self.MAX_TITLE_LENGTH] + "..."

    def _build_subtitle(self, product: Product) -> str:
        """Build subtitle with price and variant info.

        Args:
            product: Product from Shopify

        Returns:
            Subtitle string with price and variant summary
        """
        # Price with currency
        price_str = f"${product.price:.2f}"

        # Variant summary
        if product.variants:
            # Count unique sizes and colors
            sizes: Set[str] = set()
            colors: Set[str] = set()

            for variant in product.variants:
                for option_name, option_value in variant.selected_options.items():
                    option_lower = option_name.lower()
                    if option_lower == "size":
                        sizes.add(option_value)
                    elif option_lower == "color":
                        colors.add(option_value)

            parts: List[str] = [price_str]
            if sizes:
                parts.append(f"{len(sizes)} sizes")
            if colors:
                parts.append(f"{len(colors)} colors")

            return " - ".join(parts)

        return price_str

    def _select_default_variant(self, product: Product) -> Optional[Product]:
        """Select default variant based on availability.

        Args:
            product: Product from Shopify

        Returns:
            Default variant (first available variant, or first variant)
        """
        if not product.variants:
            return None

        # Prefer first available variant
        for variant in product.variants:
            if variant.available_for_sale:
                return variant

        # Fallback to first variant
        return product.variants[0]

    def _build_button_payload(self, product_id: str, variant_id: str) -> str:
        """Build button payload for Add to Cart action.

        Args:
            product_id: Shopify product ID
            variant_id: Shopify variant ID

        Returns:
            Payload string for postback button
        """
        return f"ADD_TO_CART:{product_id}:{variant_id}"

    def _extract_product_id(self, gid: str) -> str:
        """Extract numeric product ID from GID.

        Args:
            gid: Shopify GID (e.g., "gid://shopify/Product/123")

        Returns:
            Numeric product ID as string
        """
        parts = gid.split("/")
        return parts[-1] if parts else gid
