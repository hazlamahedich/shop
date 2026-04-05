"""Unit tests for natural clarification question templates (Story 11-11).

Tests cover:
- Template registration with PersonalityAwareResponseFormatter
- All personality variants present for each template key
- Template substitution produces non-empty results
- Error fallback behavior
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.clarification_question_templates import (
    CLARIFICATION_QUESTION_TEMPLATES,
    register_natural_question_templates,
)
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


class TestTemplateRegistration:
    def test_templates_registered_successfully(self):
        register_natural_question_templates()
        assert "clarification_natural" in PersonalityAwareResponseFormatter._custom_templates

    def test_all_personalities_present(self):
        for personality in PersonalityType:
            assert personality in CLARIFICATION_QUESTION_TEMPLATES


class TestTemplateKeys:
    EXPECTED_KEYS = {
        "constraint_added_acknowledgment",
        "transition_to_results",
        "transition_to_results_thanks",
        "near_limit_summary",
        "invalid_response_retry",
        "partial_response_acknowledge",
        "combined_question_wrapper",
    }

    def test_all_expected_keys_present(self):
        for personality in PersonalityType:
            templates = CLARIFICATION_QUESTION_TEMPLATES[personality]
            assert self.EXPECTED_KEYS <= set(templates.keys()), (
                f"Missing keys for {personality}: {self.EXPECTED_KEYS - set(templates.keys())}"
            )

    def test_no_extra_keys_beyond_expected(self):
        for personality in PersonalityType:
            templates = CLARIFICATION_QUESTION_TEMPLATES[personality]
            extra = set(templates.keys()) - self.EXPECTED_KEYS
            assert not extra, f"Unexpected keys for {personality}: {extra}"


class TestTemplateSubstitution:
    @pytest.fixture(autouse=True)
    def setup(self):
        register_natural_question_templates()

    def test_constraint_added_acknowledgment(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "clarification_natural",
            "constraint_added_acknowledgment",
            PersonalityType.FRIENDLY,
            understanding="So you're looking for shoes from Nike.",
        )
        assert "shoes" in result
        assert "Nike" in result

    def test_transition_to_results(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "clarification_natural",
            "transition_to_results",
            PersonalityType.PROFESSIONAL,
            understanding="So you're looking for shoes.",
        )
        assert "shoes" in result

    def test_near_limit_summary(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "clarification_natural",
            "near_limit_summary",
            PersonalityType.ENTHUSIASTIC,
            understanding="So you're looking for shoes.",
        )
        assert len(result) > 0

    def test_invalid_response_retry_no_substitution(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "clarification_natural",
            "invalid_response_retry",
            PersonalityType.FRIENDLY,
        )
        assert "rephrasing" in result.lower() or "try again" in result.lower()

    def test_combined_question_wrapper(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "clarification_natural",
            "combined_question_wrapper",
            PersonalityType.FRIENDLY,
            combined_question="Do you have a preference for size or color?",
        )
        assert "size" in result
        assert "color" in result


class TestPersonalityTone:
    @pytest.fixture(autouse=True)
    def setup(self):
        register_natural_question_templates()

    def test_friendly_tone_uses_casual_language(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "clarification_natural",
            "invalid_response_retry",
            PersonalityType.FRIENDLY,
        )
        assert any(word in result.lower() for word in ["quite catch", "rephrasing", "could you"])

    def test_professional_tone_uses_formal_language(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "clarification_natural",
            "invalid_response_retry",
            PersonalityType.PROFESSIONAL,
        )
        assert any(
            word in result.lower()
            for word in ["unable to process", "please rephrase", "specifying"]
        )

    def test_enthusiastic_tone_uses_excited_language(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "clarification_natural",
            "constraint_added_acknowledgment",
            PersonalityType.ENTHUSIASTIC,
            understanding="So you're looking for shoes.",
        )
        assert any(c in result for c in ["!", "GOT IT", "AMAZING"])
