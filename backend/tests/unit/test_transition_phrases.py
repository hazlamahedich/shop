"""Unit tests for transition_phrases module.

Story 11-4: Tests phrase library completeness, structure, and
get_phrases_for_mode() combining base + mode-specific phrases.
"""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.transition_phrases import (
    ECOMMERCE_TRANSITIONS,
    GENERAL_MODE_TRANSITIONS,
    RESPONSE_TYPE_TO_TRANSITION,
    TEMPLATES_WITH_OPENINGS,
    TRANSITION_PHRASES,
    TransitionCategory,
    get_phrases_for_mode,
)


class TestTransitionCategoryCompleteness:
    def test_all_categories_have_all_personalities(self):
        for category in TransitionCategory:
            for personality in PersonalityType:
                assert personality in TRANSITION_PHRASES[category], (
                    f"Missing {personality.value} in {category.value}"
                )

    def test_each_personality_has_at_least_5_phrases(self):
        for category in TransitionCategory:
            for personality in PersonalityType:
                phrases = TRANSITION_PHRASES[category][personality]
                assert len(phrases) >= 5, (
                    f"{category.value}/{personality.value} has only {len(phrases)} phrases"
                )

    def test_no_duplicate_phrases_within_personality(self):
        for category in TransitionCategory:
            for personality in PersonalityType:
                phrases = TRANSITION_PHRASES[category][personality]
                assert len(phrases) == len(set(phrases)), (
                    f"Duplicates in {category.value}/{personality.value}"
                )

    def test_all_phrases_are_non_empty_strings(self):
        for category in TransitionCategory:
            for personality in PersonalityType:
                for phrase in TRANSITION_PHRASES[category][personality]:
                    assert isinstance(phrase, str) and phrase.strip(), (
                        f"Empty phrase in {category.value}/{personality.value}"
                    )


class TestResponseTypeToTransitionMapping:
    def test_all_response_types_mapped(self):
        expected_types = {
            "product_search",
            "cart",
            "checkout",
            "order_tracking",
            "handoff",
            "error",
            "order_confirmation",
            "general_mode_fallback",
            "proactive_gathering",
        }
        assert set(RESPONSE_TYPE_TO_TRANSITION.keys()) == expected_types

    def test_all_mapped_categories_are_valid(self):
        for rt, cat in RESPONSE_TYPE_TO_TRANSITION.items():
            assert isinstance(cat, TransitionCategory), f"Invalid category for {rt}: {cat}"

    @pytest.mark.parametrize(
        "response_type,expected_category",
        [
            ("product_search", TransitionCategory.SHOWING_RESULTS),
            ("cart", TransitionCategory.CONFIRMING),
            ("checkout", TransitionCategory.CONFIRMING),
            ("order_tracking", TransitionCategory.SHOWING_RESULTS),
            ("handoff", TransitionCategory.ACKNOWLEDGING),
            ("error", TransitionCategory.ACKNOWLEDGING),
            ("order_confirmation", TransitionCategory.CONFIRMING),
        ],
    )
    def test_specific_mappings(self, response_type, expected_category):
        assert RESPONSE_TYPE_TO_TRANSITION[response_type] == expected_category


class TestTemplatesWithOpenings:
    def test_all_keys_are_valid_response_types(self):
        for rt in TEMPLATES_WITH_OPENINGS:
            assert rt in RESPONSE_TYPE_TO_TRANSITION or rt == "order_confirmation", (
                f"TEMPLATES_WITH_OPENINGS has unknown type: {rt}"
            )

    def test_entries_are_sets_of_strings(self):
        for rt, keys in TEMPLATES_WITH_OPENINGS.items():
            assert isinstance(keys, set)
            for key in keys:
                assert isinstance(key, str)


class TestEcommerceTransitions:
    def test_has_offering_help(self):
        assert TransitionCategory.OFFERING_HELP in ECOMMERCE_TRANSITIONS

    def test_has_transitioning_topics(self):
        assert TransitionCategory.TRANSITIONING_TOPICS in ECOMMERCE_TRANSITIONS

    def test_has_showing_results(self):
        assert TransitionCategory.SHOWING_RESULTS in ECOMMERCE_TRANSITIONS

    def test_all_personalities_present(self):
        for cat in ECOMMERCE_TRANSITIONS:
            for personality in PersonalityType:
                assert personality in ECOMMERCE_TRANSITIONS[cat], (
                    f"Missing {personality.value} in ecommerce {cat.value}"
                )


class TestGeneralModeTransitions:
    def test_has_offering_help(self):
        assert TransitionCategory.OFFERING_HELP in GENERAL_MODE_TRANSITIONS

    def test_has_transitioning_topics(self):
        assert TransitionCategory.TRANSITIONING_TOPICS in GENERAL_MODE_TRANSITIONS

    def test_all_personalities_present(self):
        for cat in GENERAL_MODE_TRANSITIONS:
            for personality in PersonalityType:
                assert personality in GENERAL_MODE_TRANSITIONS[cat], (
                    f"Missing {personality.value} in general {cat.value}"
                )


class TestGetPhrasesForMode:
    def test_ecommerce_combines_base_and_mode(self):
        result = get_phrases_for_mode(
            TransitionCategory.OFFERING_HELP,
            PersonalityType.FRIENDLY,
            "ecommerce",
        )
        base_count = len(
            TRANSITION_PHRASES[TransitionCategory.OFFERING_HELP][PersonalityType.FRIENDLY]
        )
        mode_count = len(
            ECOMMERCE_TRANSITIONS.get(TransitionCategory.OFFERING_HELP, {}).get(
                PersonalityType.FRIENDLY, []
            )
        )
        assert len(result) == base_count + mode_count

    def test_general_combines_base_and_mode(self):
        result = get_phrases_for_mode(
            TransitionCategory.OFFERING_HELP,
            PersonalityType.FRIENDLY,
            "general",
        )
        base_count = len(
            TRANSITION_PHRASES[TransitionCategory.OFFERING_HELP][PersonalityType.FRIENDLY]
        )
        mode_count = len(
            GENERAL_MODE_TRANSITIONS.get(TransitionCategory.OFFERING_HELP, {}).get(
                PersonalityType.FRIENDLY, []
            )
        )
        assert len(result) == base_count + mode_count

    def test_default_mode_is_ecommerce(self):
        result_default = get_phrases_for_mode(
            TransitionCategory.OFFERING_HELP,
            PersonalityType.FRIENDLY,
        )
        result_ecommerce = get_phrases_for_mode(
            TransitionCategory.OFFERING_HELP,
            PersonalityType.FRIENDLY,
            "ecommerce",
        )
        assert result_default == result_ecommerce

    def test_base_phrases_always_included(self):
        for personality in PersonalityType:
            result = get_phrases_for_mode(
                TransitionCategory.CLARIFYING,
                personality,
                "ecommerce",
            )
            base = TRANSITION_PHRASES[TransitionCategory.CLARIFYING][personality]
            for phrase in base:
                assert phrase in result

    def test_returns_list(self):
        result = get_phrases_for_mode(
            TransitionCategory.SHOWING_RESULTS,
            PersonalityType.PROFESSIONAL,
        )
        assert isinstance(result, list)

    def test_all_results_non_empty(self):
        for category in TransitionCategory:
            for personality in PersonalityType:
                result = get_phrases_for_mode(category, personality, "ecommerce")
                assert len(result) > 0, f"Empty result for {category.value}/{personality.value}"
