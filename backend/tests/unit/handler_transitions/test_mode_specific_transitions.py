"""Mode-specific transition tests per handler (Story 11-4)."""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.transition_phrases import (
    ECOMMERCE_TRANSITIONS,
    GENERAL_MODE_TRANSITIONS,
    TransitionCategory,
)
from app.services.personality.transition_selector import get_transition_selector
from tests.unit.helpers.transition_assertions import assert_mode_includes_phrases


class TestModeSpecificTransitionsPerHandler:
    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_ecommerce_mode_adds_ecommerce_offering_help(self, personality):
        selector = get_transition_selector()
        ecommerce_phrases = ECOMMERCE_TRANSITIONS.get(
            TransitionCategory.OFFERING_HELP,
            {},
        ).get(personality, [])
        assert_mode_includes_phrases(
            selector,
            TransitionCategory.OFFERING_HELP,
            personality,
            "ecommerce",
            ecommerce_phrases,
            conv_id_prefix="mode-ecommerce",
        )

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_general_mode_adds_general_offering_help(self, personality):
        selector = get_transition_selector()
        general_phrases = GENERAL_MODE_TRANSITIONS.get(
            TransitionCategory.OFFERING_HELP,
            {},
        ).get(personality, [])
        assert_mode_includes_phrases(
            selector,
            TransitionCategory.OFFERING_HELP,
            personality,
            "general",
            general_phrases,
            conv_id_prefix="mode-general",
        )
