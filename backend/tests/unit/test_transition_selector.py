"""Unit tests for transition_selector module.

Story 11-4: Tests singleton pattern, anti-repetition logic,
mode-specific phrases, and conversation cleanup.
"""

import random

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.transition_phrases import TransitionCategory
from app.services.personality.transition_selector import (
    MAX_RECENT_PER_CONVERSATION,
    TransitionSelector,
    get_transition_selector,
)


@pytest.fixture(autouse=True)
def reset_selector():
    selector = get_transition_selector()
    selector.reset()
    random.seed(42)
    yield
    random.seed(42)
    selector.reset()


class TestSingletonPattern:
    def test_get_transition_selector_returns_same_instance(self):
        a = get_transition_selector()
        b = get_transition_selector()
        assert a is b

    def test_direct_instantiation_returns_singleton(self):
        a = TransitionSelector()
        b = TransitionSelector()
        assert a is b


class TestBasicSelection:
    def test_returns_string(self):
        selector = get_transition_selector()
        result = selector.select(
            TransitionCategory.SHOWING_RESULTS,
            PersonalityType.FRIENDLY,
        )
        assert isinstance(result, str)

    def test_result_is_non_empty(self):
        selector = get_transition_selector()
        result = selector.select(
            TransitionCategory.SHOWING_RESULTS,
            PersonalityType.FRIENDLY,
        )
        assert len(result) > 0

    def test_returns_phrase_from_valid_pool(self):
        from app.services.personality.transition_phrases import get_phrases_for_mode

        selector = get_transition_selector()
        result = selector.select(
            TransitionCategory.SHOWING_RESULTS,
            PersonalityType.FRIENDLY,
            mode="ecommerce",
        )
        valid_phrases = get_phrases_for_mode(
            TransitionCategory.SHOWING_RESULTS, PersonalityType.FRIENDLY, "ecommerce"
        )
        assert result in valid_phrases

    def test_all_categories_work(self):
        selector = get_transition_selector()
        for category in TransitionCategory:
            result = selector.select(category, PersonalityType.FRIENDLY)
            assert isinstance(result, str) and len(result) > 0

    def test_all_personalities_work(self):
        selector = get_transition_selector()
        for personality in PersonalityType:
            result = selector.select(TransitionCategory.SHOWING_RESULTS, personality)
            assert isinstance(result, str) and len(result) > 0


class TestAntiRepetition:
    def test_tracks_used_phrase(self):
        selector = get_transition_selector()
        conv_id = "test-conv-1"
        selector.select(TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, conv_id)
        assert selector.get_recent_count(conv_id) == 1

    def test_multiple_selections_increase_count(self):
        selector = get_transition_selector()
        conv_id = "test-conv-2"
        for _ in range(5):
            selector.select(TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, conv_id)
        assert selector.get_recent_count(conv_id) == 5

    def test_no_tracking_without_conversation_id(self):
        selector = get_transition_selector()
        selector.select(TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY)
        selector.select(TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY)
        assert selector.get_recent_count("any") == 0

    def test_different_conversations_tracked_separately(self):
        selector = get_transition_selector()
        selector.select(TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, "conv-a")
        selector.select(TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, "conv-a")
        selector.select(TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, "conv-b")
        assert selector.get_recent_count("conv-a") == 2
        assert selector.get_recent_count("conv-b") == 1

    def test_exhaustion_resets_and_repeats(self):
        from app.services.personality.transition_phrases import get_phrases_for_mode

        selector = get_transition_selector()
        conv_id = "test-exhaustion"

        all_phrases = get_phrases_for_mode(
            TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, "ecommerce"
        )
        num_phrases = len(all_phrases)

        selected = set()
        for _ in range(num_phrases + 5):
            phrase = selector.select(
                TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, conv_id
            )
            selected.add(phrase)

        assert len(selected) == num_phrases

    def test_avoids_recent_within_pool(self):
        from app.services.personality.transition_phrases import get_phrases_for_mode

        selector = get_transition_selector()
        conv_id = "test-avoid-recent"

        all_phrases = get_phrases_for_mode(
            TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, "ecommerce"
        )
        if len(all_phrases) <= 1:
            pytest.skip("Need at least 2 phrases")

        first = selector.select(TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, conv_id)
        remaining = [p for p in all_phrases if p != first]
        assert len(remaining) > 0

        second = selector.select(TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, conv_id)
        assert second != first


class TestClearConversation:
    def test_clear_removes_tracking(self):
        selector = get_transition_selector()
        conv_id = "test-clear"
        selector.select(TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, conv_id)
        assert selector.get_recent_count(conv_id) == 1
        selector.clear_conversation(conv_id)
        assert selector.get_recent_count(conv_id) == 0

    def test_clear_nonexistent_no_error(self):
        selector = get_transition_selector()
        selector.clear_conversation("nonexistent")


class TestReset:
    def test_reset_clears_all(self):
        selector = get_transition_selector()
        selector.select(TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, "a")
        selector.select(TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, "b")
        selector.reset()
        assert selector.get_recent_count("a") == 0
        assert selector.get_recent_count("b") == 0


class TestMaxRecentEnforcement:
    def test_does_not_exceed_max(self):
        selector = get_transition_selector()
        conv_id = "test-max"

        for _ in range(MAX_RECENT_PER_CONVERSATION + 20):
            selector.select(TransitionCategory.SHOWING_RESULTS, PersonalityType.FRIENDLY, conv_id)

        assert selector.get_recent_count(conv_id) <= MAX_RECENT_PER_CONVERSATION


class TestModeSpecificPhrases:
    def test_ecommerce_mode_includes_ecommerce_phrases(self):
        from app.services.personality.transition_phrases import ECOMMERCE_TRANSITIONS

        selector = get_transition_selector()
        conv_id = "test-ecommerce-mode"

        results = set()
        for _ in range(30):
            results.add(
                selector.select(
                    TransitionCategory.OFFERING_HELP,
                    PersonalityType.FRIENDLY,
                    conv_id,
                    "ecommerce",
                )
            )

        ecommerce_phrases = ECOMMERCE_TRANSITIONS[TransitionCategory.OFFERING_HELP][
            PersonalityType.FRIENDLY
        ]
        found_ecommerce = any(p in results for p in ecommerce_phrases)
        assert found_ecommerce

    def test_general_mode_includes_general_phrases(self):
        from app.services.personality.transition_phrases import GENERAL_MODE_TRANSITIONS

        selector = get_transition_selector()
        conv_id = "test-general-mode"

        results = set()
        for _ in range(30):
            results.add(
                selector.select(
                    TransitionCategory.OFFERING_HELP,
                    PersonalityType.FRIENDLY,
                    conv_id,
                    "general",
                )
            )

        general_phrases = GENERAL_MODE_TRANSITIONS[TransitionCategory.OFFERING_HELP][
            PersonalityType.FRIENDLY
        ]
        found_general = any(p in results for p in general_phrases)
        assert found_general
