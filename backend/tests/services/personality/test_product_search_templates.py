"""Tests for product search response templates (Story 5-12).

Tests personality-based formatting for product search responses
including single results, multiple results, no results, and fallbacks.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


@pytest.mark.test_id("5.12-UNIT-001")
@pytest.mark.priority("P0")
class TestProductSearchTemplates:
    """Test product search response templates for each personality."""

    def test_friendly_found_single(self) -> None:
        """5.12-UNIT-001a: Friendly personality should have warm tone with emoji."""
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_single",
            PersonalityType.FRIENDLY,
            business_name="Test Store",
            title="Product A",
            price=" ($10.00)",
        )
        assert "Test Store" in result
        assert "Product A" in result
        assert "😊" in result

    def test_friendly_found_multiple(self) -> None:
        """5.12-UNIT-001b: Friendly personality should have conversational tone."""
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_multiple",
            PersonalityType.FRIENDLY,
            business_name="Test Store",
            products="• Item 1\n• Item 2",
        )
        assert "Sure thing" in result
        assert "👋" in result
        assert "Would you like more details" in result

    def test_friendly_no_results(self) -> None:
        """5.12-UNIT-001c: Friendly personality should handle no results gracefully."""
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "no_results",
            PersonalityType.FRIENDLY,
            query="missing item",
        )
        assert "couldn't find" in result.lower()
        assert "🤔" in result

    def test_professional_found_single(self) -> None:
        """5.12-UNIT-001d: Professional personality should be formal without emojis."""
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_single",
            PersonalityType.PROFESSIONAL,
            business_name="Test Store",
            title="Product A",
            price=" ($10.00)",
        )
        assert "Test Store" in result
        assert "Product A" in result
        assert "😊" not in result
        assert "!" not in result or "!" in "information"

    def test_professional_found_multiple(self) -> None:
        """5.12-UNIT-001e: Professional personality should be business-like."""
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_multiple",
            PersonalityType.PROFESSIONAL,
            business_name="Test Store",
            products="• Item 1\n• Item 2",
        )
        assert "available products" in result.lower()
        assert "👋" not in result
        assert "additional information" in result.lower()

    def test_professional_no_emojis(self) -> None:
        """5.12-UNIT-001f: Professional personality should NOT use emojis (AC2)."""
        for message_key in ["found_single", "found_multiple", "no_results", "fallback"]:
            result = PersonalityAwareResponseFormatter.format_response(
                "product_search",
                message_key,
                PersonalityType.PROFESSIONAL,
                business_name="Test Store",
                products="Item",
                query="test",
                title="Product",
                price="",
            )
            assert not any(
                emoji in result for emoji in ["😊", "👋", "🤔", "🎉", "✨", "🔥", "💫", "🛒", "🛍️"]
            ), f"Professional should not have emojis in {message_key}: {result}"

    def test_enthusiastic_found_single(self) -> None:
        """5.12-UNIT-001g: Enthusiastic personality should be very expressive."""
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_single",
            PersonalityType.ENTHUSIASTIC,
            business_name="Test Store",
            title="Product A",
            price=" ($10.00)",
        )
        assert "YAY" in result or "WOW" in result
        assert "✨" in result or "🔥" in result or "🎉" in result

    def test_enthusiastic_found_multiple(self) -> None:
        """5.12-UNIT-001h: Enthusiastic personality should have high energy (AC4)."""
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_multiple",
            PersonalityType.ENTHUSIASTIC,
            business_name="Test Store",
            products="• Item 1\n• Item 2",
        )
        assert "!!!" in result
        assert any(emoji in result for emoji in ["🔥", "🎉", "✨", "💫"])
