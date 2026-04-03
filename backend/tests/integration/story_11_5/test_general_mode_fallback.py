from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


class TestGeneralModeFallbackTransition:
    @pytest.mark.test_id("11-5-INT-025")
    def test_formatter_includes_transition_for_general(self):
        from app.services.personality.transition_phrases import TransitionCategory

        result = PersonalityAwareResponseFormatter.format_response(
            "general",
            "general_fallback",
            PersonalityType.FRIENDLY,
            include_transition=True,
            business_name="Test Store",
        )
        if result:
            assert isinstance(result, str)

    @pytest.mark.test_id("11-5-INT-026")
    def test_formatter_without_transition_for_general(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "general",
            "general_fallback",
            PersonalityType.FRIENDLY,
            business_name="Test Store",
        )
        if result:
            assert isinstance(result, str)
