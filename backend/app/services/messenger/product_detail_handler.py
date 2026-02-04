"""Product Detail View Handler.

Handles expanded product details view in Messenger, including
variant selection, stock availability, and add-to-cart actions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.schemas.shopify import CurrencyCode, Product, ProductImage, ProductVariant


logger = structlog.get_logger(__name__)


class ProductDetailHandler:
    """Handler for product detail views in Messenger.

    Provides expanded product information with variant selection,
    stock availability, and add-to-cart functionality.
    """

    def __init__(self) -> None:
        """Initialize product detail handler."""
        self.logger = structlog.get_logger(__name__)

    def format_product_detail(
        self,
        product: Product,
    ) -> Dict[str, Any]:
        """Format product detail view for Messenger.

        Args:
            product: Product from Shopify

        Returns:
            Messenger message payload with product details

        Raises:
            APIError: If formatting fails
        """
        if not product:
            raise APIError(
                ErrorCode.MESSENGER_FORMATTING_FAILED,
                "Cannot format product detail: product is None",
            )

        # Get primary image with fallback
        image_url = self._get_valid_image_url(product)

        # Truncate title if needed
        title = product.title[:80]
        if len(product.title) > 80:
            title += "..."

        # Build detailed subtitle with price and description
        subtitle = self._build_detail_subtitle(product)

        # Build variant list for detail view
        elements = self._build_variant_elements(product)

        # Create detail view payload
        payload = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": title,
                            "image_url": image_url,
                            "subtitle": subtitle,
                            "default_action": {
                                "type": "web_url",
                                "url": f"{self._get_store_url()}/products/{product.id}",
                                "webview_height_ratio": "tall",
                            },
                        },
                    ],
                },
            },
        }

        # Add variant elements if available
        if elements:
            payload["attachment"]["payload"]["elements"].extend(elements)

        self.logger.info(
            "product_detail_formatted",
            product_id=product.id,
            variants_count=len(elements),
        )

        return payload

    def _get_valid_image_url(self, product: Product) -> str:
        """Get a valid image URL with fallback.

        Args:
            product: Product from Shopify

        Returns:
            Valid image URL
        """
        config = settings()
        fallback_url = config.get(
            "MESSENGER_FALLBACK_IMAGE_URL", "https://cdn.example.com/fallback.png"
        )

        if product.images:
            image = product.images[0]
            return image.url

        return fallback_url

    def _build_detail_subtitle(self, product: Product) -> str:
        """Build detailed subtitle with price and description.

        Args:
            product: Product from Shopify

        Returns:
            Subtitle string
        """
        # Price with currency
        currency_symbol = "$" if product.currency_code == CurrencyCode.USD else ""
        price_str = f"{currency_symbol}{product.price:.2f}"

        # Description (truncated if too long)
        description = ""
        if product.description:
            description = product.description[:100]
            if len(product.description) > 100:
                description += "..."

        # Combine price and description
        if description:
            return f"{price_str} - {description}"
        return price_str

    def _build_variant_elements(self, product: Product) -> List[Dict[str, Any]]:
        """Build variant selection elements.

        Args:
            product: Product from Shopify

        Returns:
            List of variant elements for display
        """
        elements = []

        # Group variants by option type (size, color, etc.)
        option_groups: Dict[str, List[ProductVariant]] = {}

        for variant in product.variants:
            if not variant.available_for_sale:
                continue

            for option_name, option_value in variant.selected_options.items():
                if option_name not in option_groups:
                    option_groups[option_name] = []
                option_groups[option_name].append(variant)

        # Create elements for each option group
        for option_name, variants in option_groups.items():
            # Get unique values for this option
            unique_values = sorted(set(v.selected_options.get(option_name, "") for v in variants))

            # Create variant summary
            available_count = len(unique_values)
            if available_count > 1:
                elements.append(
                    {
                        "title": f"Available {option_name}s",
                        "subtitle": f"{available_count} options available",
                    }
                )

        return elements

    def format_variant_selection(
        self,
        product: Product,
        selected_options: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Format variant selection message.

        Args:
            product: Product from Shopify
            selected_options: Currently selected options

        Returns:
            Messenger message payload with variant options
        """
        elements = []

        # Group variants by their options
        for variant in product.variants:
            if not variant.available_for_sale:
                continue

            # Build variant title
            option_parts = []
            for option_name, option_value in variant.selected_options.items():
                option_parts.append(f"{option_name}: {option_value}")

            variant_title = " | ".join(option_parts) if option_parts else variant.title

            # Build element
            element = {
                "title": variant_title,
                "subtitle": f"${variant.price:.2f}" if variant.price else "",
                "buttons": [
                    {
                        "type": "postback",
                        "title": "Add to Cart",
                        "payload": f"ADD_TO_CART:{product.id}:{variant.id}",
                    }
                ],
            }
            elements.append(element)

        return {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements[:10],  # Limit to 10 elements
                },
            },
        }

    def _get_store_url(self) -> str:
        """Get store URL from settings.

        Returns:
            Store URL
        """
        config = settings()
        return config.get("STORE_URL", "https://shop.example.com")

    def select_variant_by_options(
        self,
        product: Product,
        options: Dict[str, str],
    ) -> Optional[ProductVariant]:
        """Select variant matching specified options.

        Args:
            product: Product from Shopify
            options: Selected options (e.g., {"Size": "8", "Color": "Red"})

        Returns:
            Matching variant or None
        """
        for variant in product.variants:
            if not variant.available_for_sale:
                continue

            # Check if all options match
            matches = True
            for option_name, option_value in options.items():
                if variant.selected_options.get(option_name) != option_value:
                    matches = False
                    break

            if matches:
                return variant

        return None

    def get_available_variants(
        self,
        product: Product,
    ) -> List[ProductVariant]:
        """Get list of available variants.

        Args:
            product: Product from Shopify

        Returns:
            List of available variants
        """
        return [v for v in product.variants if v.available_for_sale]

    def get_variant_summary(
        self,
        product: Product,
    ) -> Dict[str, Any]:
        """Get summary of available variants.

        Args:
            product: Product from Shopify

        Returns:
            Dictionary with variant counts by option type
        """
        summary = {}

        for variant in product.variants:
            if not variant.available_for_sale:
                continue

            for option_name, option_value in variant.selected_options.items():
                if option_name not in summary:
                    summary[option_name] = set()
                summary[option_name].add(option_value)

        # Convert sets to counts
        return {option_name: len(values) for option_name, values in summary.items()}
