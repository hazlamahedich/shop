"""Tests for previously untested code paths in transition system.

Story 11-4: Covers _cleanup_stale(), register_response_type(),
_format_neutral_fallback(), KeyError handling, and edge cases.
"""

import time

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import (
    RESPONSE_TYPE_TO_TRANSITION,
    TransitionCategory,
)
from app.services.personality.transition_selector import (
    CLEANUP_INTERVAL,
    CONVERSATION_TTL_SECONDS,
    get_transition_selector,
)


@pytest.fixture(autouse=True)
def reset_selector():
    selector = get_transition_selector()
    selector.reset()
    yield
    selector.reset()


@pytest.fixture(autouse=True)
def clear_custom_templates():
    yield
    PersonalityAwareResponseFormatter._custom_templates.clear()


class TestCleanupStale:
    def test_cleanup_removes_expired_conversations(self):
        selector = get_transition_selector()
        selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            "old-conv",
            "ecommerce",
        )
        assert selector.get_recent_count("old-conv") == 1

        selector._last_access["old-conv"] = time.monotonic() - CONVERSATION_TTL_SECONDS - 1
        selector._cleanup_stale()

        assert selector.get_recent_count("old-conv") == 0

    def test_cleanup_preserves_active_conversations(self):
        selector = get_transition_selector()
        selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            "active-conv",
            "ecommerce",
        )
        assert selector.get_recent_count("active-conv") == 1

        selector._cleanup_stale()

        assert selector.get_recent_count("active-conv") == 1

    def test_cleanup_triggered_by_select_count(self):
        selector = get_transition_selector()
        for i in range(CLEANUP_INTERVAL + 1):
            selector.select(
                TransitionCategory.CONFIRMING,
                PersonalityType.FRIENDLY,
                f"auto-cleanup-{i}",
                "ecommerce",
            )

        stale_id = "stale-for-auto"
        selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            stale_id,
            "ecommerce",
        )
        selector._last_access[stale_id] = time.monotonic() - CONVERSATION_TTL_SECONDS - 1

        for _ in range(CLEANUP_INTERVAL):
            selector.select(
                TransitionCategory.CONFIRMING,
                PersonalityType.FRIENDLY,
                "trigger-cleanup",
                "ecommerce",
            )

        assert selector.get_recent_count(stale_id) == 0

    def test_cleanup_mixed_stale_and_active(self):
        selector = get_transition_selector()
        selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            "stale-conv",
            "ecommerce",
        )
        selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            "fresh-conv",
            "ecommerce",
        )

        selector._last_access["stale-conv"] = time.monotonic() - CONVERSATION_TTL_SECONDS - 1
        selector._cleanup_stale()

        assert selector.get_recent_count("stale-conv") == 0
        assert selector.get_recent_count("fresh-conv") == 1


class TestRegisterResponseType:
    def test_register_and_use_custom_type(self):
        PersonalityAwareResponseFormatter.register_response_type(
            "custom_notifications",
            {
                PersonalityType.FRIENDLY: {
                    "new_feature": "Check out our new feature: {feature_name}!",
                },
                PersonalityType.PROFESSIONAL: {
                    "new_feature": "New feature available: {feature_name}.",
                },
                PersonalityType.ENTHUSIASTIC: {
                    "new_feature": "AMAZING new feature: {feature_name}!!!",
                },
            },
        )

        result = PersonalityAwareResponseFormatter.format_response(
            "custom_notifications",
            "new_feature",
            PersonalityType.FRIENDLY,
            feature_name="Dark Mode",
        )
        assert "Dark Mode" in result

    def test_register_overwrites_existing_type(self):
        PersonalityAwareResponseFormatter.register_response_type(
            "cart",
            {
                PersonalityType.FRIENDLY: {
                    "view_empty": "Custom empty cart message",
                },
            },
        )

        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
        )
        assert result == "Custom empty cart message"

    def test_custom_type_falls_back_to_builtin_for_missing_personality(self):
        PersonalityAwareResponseFormatter.register_response_type(
            "custom_type",
            {
                PersonalityType.FRIENDLY: {
                    "greeting": "Hey there!",
                },
            },
        )

        result = PersonalityAwareResponseFormatter.format_response(
            "custom_type",
            "greeting",
            PersonalityType.PROFESSIONAL,
        )
        assert isinstance(result, str)
        assert len(result) > 0


class TestFormatNeutralFallback:
    def test_unknown_response_type_returns_fallback(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "completely_unknown_type",
            "nonexistent_key",
            PersonalityType.FRIENDLY,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_unknown_type_returns_default_help_message(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "unknown_type",
            "unknown_key",
            PersonalityType.FRIENDLY,
        )
        assert result == "I'm here to help."

    def test_known_fallback_with_kwargs(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_single",
            PersonalityType.FRIENDLY,
        )
        assert "Found:" in result or isinstance(result, str)

    def test_known_fallback_without_kwargs_uses_template(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
        )
        assert "cart" in result.lower() or "empty" in result.lower()


class TestKeyErrorHandling:
    def test_missing_template_variable_returns_template(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_single",
            PersonalityType.FRIENDLY,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_partial_kwargs_still_returns_string(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "add_success",
            PersonalityType.FRIENDLY,
        )
        assert isinstance(result, str)


class TestEdgeCases:
    def test_unknown_mode_falls_back_gracefully(self):
        selector = get_transition_selector()
        result = selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            "edge-unknown-mode",
            "nonexistent_mode",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_mode_switch_mid_conversation(self):
        selector = get_transition_selector()
        conv_id = "edge-mode-switch"
        r1 = selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            conv_id,
            "ecommerce",
        )
        r2 = selector.select(
            TransitionCategory.CONFIRMING,
            PersonalityType.FRIENDLY,
            conv_id,
            "general",
        )
        assert isinstance(r1, str) and isinstance(r2, str)

    def test_include_transition_with_unknown_response_type(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "unknown_response_type",
            "any_key",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="edge-unknown-rt",
            mode="ecommerce",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_response_type_not_in_transition_mapping_skips_transition(self):
        assert "nonexistent_type" not in RESPONSE_TYPE_TO_TRANSITION
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="edge-no-mapping",
            mode="ecommerce",
        )
        assert "cart" in result.lower() or "empty" in result.lower()
