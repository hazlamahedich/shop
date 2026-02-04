"""Product mapper for Shopify Storefront API data transformation.

Maps Shopify product data to internal schema and provides filtering
logic for budget, size, and availability constraints.
"""

from __future__ import annotations

from typing import Any, Optional

from app.schemas.shopify import CurrencyCode, Product, ProductImage, ProductVariant
from app.services.intent.classification_schema import ExtractedEntities


class ProductMapper:
    """Maps Shopify product data and applies search constraints.

    Provides methods to:
    - Map Shopify GraphQL responses to Product schema
    - Filter products by budget, size, availability
    - Map extracted entities to search parameters
    """

    def map_category(self, category: Optional[str]) -> Optional[str]:
        """Map category to Shopify product type/tag format.

        Args:
            category: Product category from intent classification

        Returns:
            Category in Shopify-compatible format (case-insensitive)
        """
        if not category:
            return None

        # Return category as-is (Shopify search is case-insensitive)
        return category.strip()

    def map_products(self, raw_products: list[dict[str, Any]]) -> list[Product]:
        """Map Shopify product data to Product schema.

        Args:
            raw_products: List of products from Shopify GraphQL response

        Returns:
            List of mapped Product objects
        """
        products: list[Product] = []

        for raw_product in raw_products:
            try:
                # Extract price range
                price_range = raw_product.get("priceRangeV2", {})
                min_price = price_range.get("minVariantPrice", {})
                price = float(min_price.get("amount", 0.0))
                currency = min_price.get("currencyCode", "USD")

                # Extract images
                images = self._extract_images(raw_product.get("images", {}))

                # Extract variants
                variants = self._extract_variants(
                    raw_product.get("variants", {}),
                    raw_product.get("id", ""),
                )

                product = Product(
                    id=raw_product.get("id", ""),
                    title=raw_product.get("title", ""),
                    description=raw_product.get("description"),
                    description_html=raw_product.get("descriptionHtml"),
                    product_type=raw_product.get("productType", ""),
                    tags=raw_product.get("tags", []),
                    vendor=raw_product.get("vendor"),
                    price=price,
                    currency_code=CurrencyCode(currency),
                    images=images,
                    variants=variants,
                    relevance_score=0.0,  # Will be set by ranking algorithm
                )

                products.append(product)

            except (ValueError, KeyError) as e:
                # Skip malformed products but continue processing
                # Note: In production, log this error
                continue

        return products

    def _extract_images(self, images_data: dict[str, Any]) -> list[ProductImage]:
        """Extract images from Shopify images data.

        Args:
            images_data: Images section from GraphQL response

        Returns:
            List of ProductImage objects
        """
        images: list[ProductImage] = []

        edges = images_data.get("edges", [])
        for edge in edges:
            node = edge.get("node", {})
            image = ProductImage(
                url=node.get("url", ""),
                alt_text=node.get("altText"),
                width=node.get("width"),
                height=node.get("height"),
            )
            images.append(image)

        return images

    def _extract_variants(
        self,
        variants_data: dict[str, Any],
        product_id: str,
    ) -> list[ProductVariant]:
        """Extract variants from Shopify variants data.

        Args:
            variants_data: Variants section from GraphQL response
            product_id: Parent product ID

        Returns:
            List of ProductVariant objects
        """
        variants: list[ProductVariant] = []

        edges = variants_data.get("edges", [])
        for edge in edges:
            node = edge.get("node", {})

            # Extract price
            price_data = node.get("priceV2", {})
            price = float(price_data.get("amount", 0.0))
            currency = price_data.get("currencyCode", "USD")

            # Extract selected options
            selected_options: dict[str, str] = {}
            for option in node.get("selectedOptions", []):
                selected_options[option.get("name", "")] = option.get("value", "")

            variant = ProductVariant(
                id=node.get("id", ""),
                product_id=node.get("productId", product_id),
                title=node.get("title", ""),
                price=price,
                currency_code=CurrencyCode(currency),
                available_for_sale=node.get("availableForSale", False),
                selected_options=selected_options,
                weight=node.get("weight"),
                weight_unit=node.get("weightUnit"),
            )
            variants.append(variant)

        return variants

    def filter_by_budget(
        self,
        products: list[Product],
        budget: Optional[float],
    ) -> list[Product]:
        """Filter products by budget constraint.

        Args:
            products: List of products to filter
            budget: Maximum price filter (None = no filter)

        Returns:
            Products with price <= budget, or all products if budget is None
        """
        if budget is None:
            return products

        return [p for p in products if p.price <= budget]

    def filter_by_size(
        self,
        products: list[Product],
        size: Optional[str],
    ) -> list[Product]:
        """Filter products by size variant.

        Args:
            products: List of products to filter
            size: Size value to match (None = no filter)

        Returns:
            Products with at least one variant matching the size
        """
        if not size:
            return products

        filtered: list[Product] = []
        size_lower = size.lower()

        for product in products:
            # Check if any variant has the specified size
            # Use exact matching on selected option values to avoid
            # false positives like "1" matching "10"
            has_size = any(
                any(
                    size_lower == option_value.lower()
                    for option_value in v.selected_options.values()
                )
                for v in product.variants
            )

            if has_size:
                filtered.append(product)

        return filtered

    def filter_by_availability(
        self,
        products: list[Product],
    ) -> list[Product]:
        """Filter products to only include in-stock items.

        Args:
            products: List of products to filter

        Returns:
            Products with at least one in-stock variant
        """
        filtered: list[Product] = []

        for product in products:
            # Check if any variant is available for sale
            has_stock = any(v.available_for_sale for v in product.variants)

            if has_stock:
                filtered.append(product)

        return filtered

    def map_entities_to_search_params(
        self,
        entities: ExtractedEntities,
    ) -> dict[str, Any]:
        """Map extracted entities to search parameters.

        Args:
            entities: Extracted entities from intent classification

        Returns:
            Dictionary of search parameters
        """
        return {
            "category": self.map_category(entities.category),
            "max_price": entities.budget,
            "size": entities.size,
            "color": entities.color,
            "brand": entities.brand,
        }
