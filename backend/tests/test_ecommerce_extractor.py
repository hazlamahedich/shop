"""Story 11-1: Unit tests for EcommerceContextExtractor.

Tests ecommerce-specific context extraction: price constraints,
product IDs, size/color preferences, and context merging.

Acceptance Criteria:
- Price constraints extracted from messages
- Product IDs tracked across turns
- Size and color preferences detected
- Context merging preserves existing data
"""

import pytest

from app.services.context import EcommerceContextExtractor


class TestEcommerceContextExtractor:
    """Test E-commerce mode context extractor."""

    @pytest.mark.asyncio
    async def test_extract_price_constraints(self):
        """Price constraints extracted from dollar amounts in messages. [11.1-EXT-001]"""
        # Given: An ecommerce context extractor
        extractor = EcommerceContextExtractor()

        # When: Message contains "under $100"
        updates = await extractor.extract("Show me shoes under $100", {})
        # Then: Budget max is 100
        assert "constraints" in updates
        assert updates["constraints"]["budget_max"] == 100.0

        # When: Message contains "max $50"
        updates = await extractor.extract("What about max $50?", {})
        # Then: Budget max is 50
        assert updates["constraints"]["budget_max"] == 50.0

    @pytest.mark.asyncio
    async def test_extract_viewed_products(self):
        """Product IDs extracted from # and product- prefix formats. [11.1-EXT-002]"""
        # Given: An ecommerce context extractor
        extractor = EcommerceContextExtractor()

        # When: Message contains "#123"
        updates = await extractor.extract("Tell me about #123", {})
        # Then: Product 123 is tracked
        assert "viewed_products" in updates
        assert 123 in updates["viewed_products"]

        # When: Message contains "product-456"
        updates = await extractor.extract("Add product-456 to cart", {})
        # Then: Product 456 is tracked
        assert 456 in updates["viewed_products"]

    @pytest.mark.asyncio
    async def test_extract_size_color_preferences(self):
        """Size and color preferences extracted from messages. [11.1-EXT-003]"""
        # Given: An ecommerce context extractor
        extractor = EcommerceContextExtractor()

        # When: Message mentions size and color
        updates = await extractor.extract("I need size 10 in red", {})
        # Then: Both size and color extracted
        assert "constraints" in updates
        assert updates["constraints"]["size"] == "10"
        assert updates["constraints"]["color"] == "red"

    @pytest.mark.asyncio
    async def test_merge_with_existing_context(self):
        """Merge preserves existing data while adding new items. [11.1-EXT-004]"""
        # Given: Existing context with products and constraints
        extractor = EcommerceContextExtractor()
        existing = {
            "viewed_products": [123, 456],
            "constraints": {"budget_max": 100},
        }

        # When: Extracting delta for new product
        updates = await extractor.extract("Add #789 to cart", existing)
        # Then: Delta contains only the new product
        assert updates["viewed_products"] == [789]

        # When: Merging delta with existing
        merged = extractor._merge_context(existing, updates)
        # Then: Both old and new products preserved
        assert 123 in merged["viewed_products"]
        assert 789 in merged["viewed_products"]
        assert merged["constraints"]["budget_max"] == 100

    @pytest.mark.asyncio
    async def test_extract_multiple_prices_in_search_history(self):
        """Messages with price mentions are captured in search history. [11.1-EXT-005]"""
        extractor = EcommerceContextExtractor()
        updates = await extractor.extract("I had $200 but now my budget is $75", {})
        assert "search_history" in updates
        assert len(updates["search_history"]) == 1
        assert "$200" in updates["search_history"][0]
        assert "$75" in updates["search_history"][0]
