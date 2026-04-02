"""Handoff handler transition tests (Story 11-4)."""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import (
    RESPONSE_TYPE_TO_TRANSITION,
    TransitionCategory,
)
from tests.unit.helpers.transition_assertions import assert_starts_with_transition


class TestHandoffHandlerTransitions:
    RESPONSE_TYPE = "handoff"
    EXPECTED_CATEGORY = TransitionCategory.ACKNOWLEDGING

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_standard_gets_transition(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            "standard",
            personality,
            include_transition=True,
            conversation_id="handoff-standard",
            mode="ecommerce",
        )
        assert_starts_with_transition(result, self.EXPECTED_CATEGORY, personality)

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_after_hours_gets_transition(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            "after_hours",
            personality,
            include_transition=True,
            conversation_id="handoff-after-hours",
            mode="ecommerce",
            business_hours="Mon-Fri 9-5",
        )
        assert_starts_with_transition(result, self.EXPECTED_CATEGORY, personality)
        assert "Mon-Fri 9-5" in result

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_queue_position_gets_transition(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            "queue_position",
            personality,
            include_transition=True,
            conversation_id="handoff-queue",
            mode="ecommerce",
            position=3,
        )
        assert_starts_with_transition(result, self.EXPECTED_CATEGORY, personality)

    def test_response_type_maps_to_acknowledging(self):
        assert RESPONSE_TYPE_TO_TRANSITION[self.RESPONSE_TYPE] == self.EXPECTED_CATEGORY
