"""Unit tests for error recovery personality templates (Story 11-7).

Tests that templates register correctly and produce non-empty strings
for all personalities and message keys.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.error_recovery_templates import (
    ERROR_RECOVERY_TEMPLATES,
    register_error_recovery_templates,
)
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

EXPECTED_TEMPLATE_KEYS = [
    "search_retry_with_last_query",
    "search_browse_viewed",
    "cart_retry_viewed_product",
    "checkout_retry_with_cart",
    "order_lookup_retry",
    "llm_timeout_with_last_query",
    "llm_timeout_generic",
    "context_lost_suggestion",
]


@pytest.fixture(autouse=True)
def _register_templates():
    register_error_recovery_templates()


class TestTemplateStructure:
    # GIVEN error recovery templates are registered
    # WHEN checking the template registry
    # THEN every PersonalityType has an entry
    def test_all_personalities_present(self):
        for personality in PersonalityType:
            assert personality in ERROR_RECOVERY_TEMPLATES

    # GIVEN a specific personality
    # WHEN checking for all expected template keys
    # THEN every key is present in the personality's template set
    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_all_expected_keys_present(self, personality):
        templates = ERROR_RECOVERY_TEMPLATES[personality]
        for key in EXPECTED_TEMPLATE_KEYS:
            assert key in templates, f"Missing key '{key}' for {personality.value}"

    # GIVEN a specific personality
    # WHEN inspecting all template values
    # THEN every value is a non-empty string
    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_all_template_values_are_nonempty_strings(self, personality):
        templates = ERROR_RECOVERY_TEMPLATES[personality]
        for key in EXPECTED_TEMPLATE_KEYS:
            assert isinstance(templates[key], str), f"{key} is not str for {personality.value}"
            assert len(templates[key]) > 0, f"{key} is empty for {personality.value}"


class TestRegistration:
    # GIVEN error recovery templates have been registered
    # WHEN checking the formatter's custom template registry
    # THEN "error_recovery" is present as a template type
    def test_register_creates_custom_template_type(self):
        assert "error_recovery" in PersonalityAwareResponseFormatter._custom_templates

    # GIVEN a friendly personality and a last_query value
    # WHEN formatting a search_retry_with_last_query template
    # THEN the result is a string containing the query value
    def test_format_search_retry_returns_string(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "error_recovery",
            "search_retry_with_last_query",
            PersonalityType.FRIENDLY,
            last_query="blue shoes",
        )
        assert isinstance(result, str)
        assert "blue shoes" in result

    # GIVEN any personality type
    # WHEN formatting an order_lookup_retry template
    # THEN the result is a non-empty string
    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_format_order_lookup_returns_string(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "error_recovery",
            "order_lookup_retry",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    # GIVEN any personality type
    # WHEN formatting a context_lost_suggestion template
    # THEN the result is a non-empty string
    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_format_context_lost_returns_string(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "error_recovery",
            "context_lost_suggestion",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    # GIVEN a professional personality
    # WHEN formatting the llm_timeout_generic template
    # THEN the result is a non-empty string
    def test_format_llm_timeout_generic_returns_string(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "error_recovery",
            "llm_timeout_generic",
            PersonalityType.PROFESSIONAL,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    # GIVEN an enthusiastic personality and a last_query value
    # WHEN formatting the llm_timeout_with_last_query template
    # THEN the result substitutes the query value into the string
    def test_format_llm_timeout_with_query_substitutes(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "error_recovery",
            "llm_timeout_with_last_query",
            PersonalityType.ENTHUSIASTIC,
            last_query="red dress",
        )
        assert "red dress" in result

    # GIVEN a friendly personality
    # WHEN formatting the checkout_retry_with_cart template
    # THEN the result is a non-empty string
    def test_format_checkout_retry_returns_string(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "error_recovery",
            "checkout_retry_with_cart",
            PersonalityType.FRIENDLY,
        )
        assert isinstance(result, str)
        assert len(result) > 0
