"""Tests for handoff response templates (Story 5-12).

Tests personality-based formatting for human agent handoff responses
including standard handoff and after-hours scenarios.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


@pytest.mark.test_id("5.12-UNIT-005")
@pytest.mark.priority("P1")
class TestHandoffTemplates:
    """Test handoff response templates for each personality."""

    def test_friendly_handoff_standard(self) -> None:
        """5.12-UNIT-005a: Friendly handoff should be reassuring."""
        result = PersonalityAwareResponseFormatter.format_response(
            "handoff",
            "standard",
            PersonalityType.FRIENDLY,
        )
        assert "human agent" in result.lower()
        assert "😊" in result

    def test_friendly_after_hours(self) -> None:
        """5.12-UNIT-005b: Friendly after hours should be helpful."""
        result = PersonalityAwareResponseFormatter.format_response(
            "handoff",
            "after_hours",
            PersonalityType.FRIENDLY,
            business_hours="9 AM - 5 PM",
        )
        assert "offline" in result.lower() or "unavailable" in result.lower()
        assert "9 AM - 5 PM" in result
        assert "😊" in result

    def test_professional_handoff_standard(self) -> None:
        """5.12-UNIT-005c: Professional handoff should be formal."""
        result = PersonalityAwareResponseFormatter.format_response(
            "handoff",
            "standard",
            PersonalityType.PROFESSIONAL,
        )
        assert "human agent" in result.lower()
        assert "😊" not in result
