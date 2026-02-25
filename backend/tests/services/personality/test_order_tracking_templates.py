"""Tests for order tracking response templates (Story 5-12).

Tests personality-based formatting for order tracking responses
including welcome back, order found, and device linking scenarios.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


@pytest.mark.test_id("5.12-UNIT-004")
@pytest.mark.priority("P0")
class TestOrderTrackingTemplates:
    """Test order tracking response templates for each personality."""

    def test_friendly_order_found(self) -> None:
        """5.12-UNIT-004a: Friendly order found should be celebratory."""
        result = PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "found",
            PersonalityType.FRIENDLY,
            order_details="Order #1234 - Shipped",
        )
        assert "Great news" in result or "🎉" in result or "📦" in result

    def test_friendly_device_linked(self) -> None:
        """5.12-UNIT-004b: Friendly device linked should welcome the customer."""
        result = PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "device_linked",
            PersonalityType.FRIENDLY,
            customer_name="Maria",
        )
        assert "Maria" in result
        assert "🎉" in result

    def test_friendly_welcome_back(self) -> None:
        """5.12-UNIT-004c: Friendly welcome back should use customer name."""
        result = PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "welcome_back",
            PersonalityType.FRIENDLY,
            customer_name="Maria",
        )
        assert "Maria" in result
        assert "Welcome back" in result
        assert "👋" in result

    def test_professional_welcome_back(self) -> None:
        """5.12-UNIT-004d: Professional welcome back should be formal."""
        result = PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "welcome_back",
            PersonalityType.PROFESSIONAL,
            customer_name="Maria",
        )
        assert "Maria" in result
        assert "Welcome back" in result
        assert "👋" not in result

    def test_enthusiastic_welcome_back(self) -> None:
        """5.12-UNIT-004e: Enthusiastic welcome back should be very excited."""
        result = PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "welcome_back",
            PersonalityType.ENTHUSIASTIC,
            customer_name="Maria",
        )
        assert "Maria" in result
        assert "!!!" in result or "WELCOME" in result.upper()
