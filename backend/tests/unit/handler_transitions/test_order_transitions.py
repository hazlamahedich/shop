"""Order handler transition tests (Story 11-4)."""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import (
    RESPONSE_TYPE_TO_TRANSITION,
    TransitionCategory,
    get_phrases_for_mode,
)
from app.services.personality.transition_selector import get_transition_selector
from tests.unit.helpers.transition_assertions import (
    assert_no_double_transition,
    assert_starts_with_transition,
)


class TestOrderHandlerTransitions:
    RESPONSE_TYPE = "order_tracking"
    EXPECTED_CATEGORY = TransitionCategory.SHOWING_RESULTS

    @pytest.mark.parametrize(
        "template_key",
        ["found", "found_shipped", "found_delivered", "found_processing"],
    )
    def test_templates_with_openings_no_double(self, template_key):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            template_key,
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="order-opening",
            mode="ecommerce",
            order_details="Order #123",
            tracking_info="Tracking: 1Z999",
        )
        assert_no_double_transition(
            result,
            self.EXPECTED_CATEGORY,
            PersonalityType.FRIENDLY,
        )

    def test_not_found_gets_transition(self):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            "not_found",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="order-notfound",
            mode="ecommerce",
        )
        assert_starts_with_transition(
            result,
            self.EXPECTED_CATEGORY,
            PersonalityType.FRIENDLY,
        )

    def test_selector_direct_use_showing_results(self):
        selector = get_transition_selector()
        phrase = selector.select(
            self.EXPECTED_CATEGORY,
            PersonalityType.PROFESSIONAL,
            conversation_id="order-direct",
            mode="ecommerce",
        )
        valid = get_phrases_for_mode(
            self.EXPECTED_CATEGORY,
            PersonalityType.PROFESSIONAL,
            "ecommerce",
        )
        assert phrase in valid

    def test_selector_direct_use_offering_help(self):
        selector = get_transition_selector()
        phrase = selector.select(
            TransitionCategory.OFFERING_HELP,
            PersonalityType.PROFESSIONAL,
            conversation_id="order-help",
            mode="ecommerce",
        )
        valid = get_phrases_for_mode(
            TransitionCategory.OFFERING_HELP,
            PersonalityType.PROFESSIONAL,
            "ecommerce",
        )
        assert phrase in valid

    def test_response_type_maps_to_showing_results(self):
        assert RESPONSE_TYPE_TO_TRANSITION[self.RESPONSE_TYPE] == self.EXPECTED_CATEGORY
