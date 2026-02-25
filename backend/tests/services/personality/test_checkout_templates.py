"""Tests for checkout response templates (Story 5-12).

Tests personality-based formatting for checkout flows
including ready state and empty cart scenarios.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


@pytest.mark.test_id("5.12-UNIT-003")
@pytest.mark.priority("P0")
class TestCheckoutTemplates:
    """Test checkout response templates for each personality."""

    def test_friendly_checkout_ready(self) -> None:
        """5.12-UNIT-003a: Friendly checkout should be encouraging."""
        result = PersonalityAwareResponseFormatter.format_response(
            "checkout",
            "ready",
            PersonalityType.FRIENDLY,
            checkout_url="https://example.com/checkout",
        )
        assert "Ready to checkout" in result
        assert "🛒" in result
        assert "https://example.com/checkout" in result

    def test_friendly_empty_cart(self) -> None:
        """5.12-UNIT-003b: Friendly empty cart checkout should be gentle."""
        result = PersonalityAwareResponseFormatter.format_response(
            "checkout",
            "empty_cart",
            PersonalityType.FRIENDLY,
        )
        assert "empty" in result.lower()
        assert "😊" in result

    def test_professional_checkout_ready(self) -> None:
        """5.12-UNIT-003c: Professional checkout should be direct."""
        result = PersonalityAwareResponseFormatter.format_response(
            "checkout",
            "ready",
            PersonalityType.PROFESSIONAL,
            checkout_url="https://example.com/checkout",
        )
        assert "Ready for checkout" in result or "complete your order" in result.lower()
        assert "🛒" not in result
