"""Search handler transition tests (Story 11-4)."""

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


class TestSearchHandlerTransitions:
    RESPONSE_TYPE = "product_search"
    EXPECTED_CATEGORY = TransitionCategory.SHOWING_RESULTS

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_no_results_gets_transition(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            "no_results",
            personality,
            include_transition=True,
            conversation_id="search-no-results",
            mode="ecommerce",
            query="shoes",
            business_name="Test Store",
        )
        assert_starts_with_transition(result, self.EXPECTED_CATEGORY, personality)
        assert "shoes" in result.lower()

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_fallback_gets_transition(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            "fallback",
            personality,
            include_transition=True,
            conversation_id="search-fallback",
            mode="ecommerce",
            business_name="Store",
            query="boots",
            products="item1",
        )
        assert_starts_with_transition(result, self.EXPECTED_CATEGORY, personality)

    @pytest.mark.parametrize(
        "template_key",
        ["found_single", "found_multiple", "recommendation_single", "recommendation_multiple"],
    )
    def test_templates_with_openings_skip_transition(self, template_key):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            template_key,
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="search-opening",
            mode="ecommerce",
            business_name="Store",
            title="Shirt",
            price=" $20",
            products="item1\nitem2",
            more_options="",
        )
        assert_no_double_transition(
            result,
            self.EXPECTED_CATEGORY,
            PersonalityType.FRIENDLY,
        )

    def test_response_type_maps_to_showing_results(self):
        assert RESPONSE_TYPE_TO_TRANSITION[self.RESPONSE_TYPE] == self.EXPECTED_CATEGORY

    def test_offering_help_used_for_more_results(self):
        selector = get_transition_selector()
        phrase = selector.select(
            TransitionCategory.OFFERING_HELP,
            PersonalityType.FRIENDLY,
            conversation_id="search-offering",
            mode="ecommerce",
        )
        valid = get_phrases_for_mode(
            TransitionCategory.OFFERING_HELP,
            PersonalityType.FRIENDLY,
            "ecommerce",
        )
        assert phrase in valid
