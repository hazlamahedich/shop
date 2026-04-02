"""Cart handler transition tests (Story 11-4)."""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import (
    RESPONSE_TYPE_TO_TRANSITION,
    TransitionCategory,
)
from tests.unit.helpers.transition_assertions import (
    assert_no_double_transition,
    assert_starts_with_transition,
)


class TestCartHandlerTransitions:
    RESPONSE_TYPE = "cart"
    EXPECTED_CATEGORY = TransitionCategory.CONFIRMING

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_view_empty_gets_transition(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            "view_empty",
            personality,
            include_transition=True,
            conversation_id="cart-empty",
            mode="ecommerce",
        )
        assert_starts_with_transition(result, self.EXPECTED_CATEGORY, personality)

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_remove_success_gets_transition(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            "remove_success",
            personality,
            include_transition=True,
            conversation_id="cart-remove",
            mode="ecommerce",
        )
        assert_starts_with_transition(result, self.EXPECTED_CATEGORY, personality)

    @pytest.mark.parametrize("template_key", ["add_success", "view_items"])
    def test_templates_with_openings_skip_transition(self, template_key):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            template_key,
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="cart-opening",
            mode="ecommerce",
            title="Widget",
            items="item1",
            subtotal="10.00",
        )
        assert_no_double_transition(
            result,
            self.EXPECTED_CATEGORY,
            PersonalityType.FRIENDLY,
        )

    def test_response_type_maps_to_confirming(self):
        assert RESPONSE_TYPE_TO_TRANSITION[self.RESPONSE_TYPE] == self.EXPECTED_CATEGORY
