"""Error handler transition tests (Story 11-4)."""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import (
    RESPONSE_TYPE_TO_TRANSITION,
    TEMPLATES_WITH_OPENINGS,
)


class TestErrorHandlerTransitions:
    RESPONSE_TYPE = "error"

    @pytest.mark.parametrize(
        "message_key",
        ["general", "search_failed", "cart_failed", "checkout_failed", "order_lookup_failed"],
    )
    def test_error_templates_do_not_get_transition(self, message_key):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            message_key,
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id=f"error-{message_key}",
            mode="ecommerce",
        )
        assert result, f"Empty result for error/{message_key}"

    def test_error_not_in_response_type_to_transition(self):
        assert self.RESPONSE_TYPE not in RESPONSE_TYPE_TO_TRANSITION, (
            "Error responses should not have transition phrases"
        )

    def test_error_has_no_templates_with_openings(self):
        openings = TEMPLATES_WITH_OPENINGS.get(self.RESPONSE_TYPE, set())
        assert len(openings) == 0, "Error templates should not have built-in openings"
