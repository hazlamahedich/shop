"""Tests for cart response templates (Story 5-12).

Tests personality-based formatting for cart operations
including add, remove, view, and clear actions.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


@pytest.mark.test_id("5.12-UNIT-002")
@pytest.mark.priority("P0")
class TestCartTemplates:
    """Test cart response templates for each personality."""

    def test_friendly_cart_add_success(self) -> None:
        """5.12-UNIT-002a: Friendly add success should be casual with emoji."""
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "add_success",
            PersonalityType.FRIENDLY,
            title="Snowboard Pro",
        )
        assert "Added" in result
        assert "Snowboard Pro" in result
        assert "🛒" in result

    def test_friendly_cart_view_empty(self) -> None:
        """5.12-UNIT-002b: Friendly empty cart should be helpful."""
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
        )
        assert "empty" in result.lower()
        assert "😊" in result

    def test_professional_cart_add_success(self) -> None:
        """5.12-UNIT-002c: Professional add success should be formal."""
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "add_success",
            PersonalityType.PROFESSIONAL,
            title="Snowboard Pro",
        )
        assert "has been added" in result
        assert "proceed to checkout" in result.lower()
        assert "🛒" not in result

    def test_enthusiastic_cart_add_success(self) -> None:
        """5.12-UNIT-002d: Enthusiastic add success should be very excited."""
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "add_success",
            PersonalityType.ENTHUSIASTIC,
            title="Snowboard Pro",
        )
        assert "WOOHOO" in result or "!!!" in result
        assert "🛒" in result

    def test_all_cart_messages_have_personality_variants(self) -> None:
        """5.12-UNIT-002e: All cart message keys should have all three personality variants."""
        cart_keys = [
            "view_empty",
            "view_items",
            "add_success",
            "add_needs_selection",
            "remove_success",
            "remove_needs_selection",
            "clear_success",
            "no_items_to_remove",
            "item_not_found",
        ]
        for key in cart_keys:
            for personality in PersonalityType:
                result = PersonalityAwareResponseFormatter.format_response(
                    "cart", key, personality, title="Test", items="Item", subtotal="$10"
                )
                assert result is not None
                assert len(result) > 0
