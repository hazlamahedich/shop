"""General mode fallback handler transition tests (Story 11-4)."""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import (
    RESPONSE_TYPE_TO_TRANSITION,
    TransitionCategory,
)
from tests.unit.helpers.transition_assertions import assert_starts_with_transition


class TestGeneralModeFallbackTransitions:
    RESPONSE_TYPE = "general_mode_fallback"
    EXPECTED_CATEGORY = TransitionCategory.ACKNOWLEDGING

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_ecommerce_not_supported_gets_transition(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            "ecommerce_not_supported",
            personality,
            include_transition=True,
            conversation_id="general-fallback",
            mode="general",
        )
        assert_starts_with_transition(result, self.EXPECTED_CATEGORY, personality, mode="general")

    def test_response_type_maps_to_acknowledging(self):
        assert RESPONSE_TYPE_TO_TRANSITION[self.RESPONSE_TYPE] == self.EXPECTED_CATEGORY
