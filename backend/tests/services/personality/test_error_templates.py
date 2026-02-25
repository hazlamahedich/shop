"""Tests for error response templates (Story 5-12).

Tests personality-based formatting for error responses
including general errors and search failures.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


@pytest.mark.test_id("5.12-UNIT-006")
@pytest.mark.priority("P1")
class TestErrorTemplates:
    """Test error response templates for each personality."""

    def test_friendly_general_error(self) -> None:
        """5.12-UNIT-006a: Friendly error should be apologetic."""
        result = PersonalityAwareResponseFormatter.format_response(
            "error",
            "general",
            PersonalityType.FRIENDLY,
        )
        assert "Oops" in result or "wrong" in result.lower()
        assert "😅" in result

    def test_professional_general_error(self) -> None:
        """5.12-UNIT-006b: Professional error should be formal."""
        result = PersonalityAwareResponseFormatter.format_response(
            "error",
            "general",
            PersonalityType.PROFESSIONAL,
        )
        assert "error occurred" in result.lower()
        assert "😅" not in result

    def test_enthusiastic_general_error(self) -> None:
        """5.12-UNIT-006c: Enthusiastic error should still be positive."""
        result = PersonalityAwareResponseFormatter.format_response(
            "error",
            "general",
            PersonalityType.ENTHUSIASTIC,
        )
        assert "Oops" in result or "wonky" in result.lower()
        assert "💪" in result or "😅" in result
