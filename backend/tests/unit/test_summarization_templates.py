"""Unit tests for register_summarization_templates (Story 11-9 P2).

Verify that summarization templates are registered correctly for all personalities.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.conversation_templates import (
    SUMMARIZATION_TEMPLATES,
    register_summarization_templates,
)
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


class TestSummarizationTemplateRegistration:
    """P2: Verify SUMMARIZATION_TEMPLATES are registered correctly."""

    def test_all_personalities_have_templates(self):
        for personality in PersonalityType:
            assert personality in SUMMARIZATION_TEMPLATES, (
                f"Missing templates for personality: {personality}"
            )

    def test_all_template_keys_present(self):
        required_keys = {"summary_intro", "short_conversation", "summary_closing"}
        for personality in PersonalityType:
            actual_keys = set(SUMMARIZATION_TEMPLATES[personality].keys())
            assert required_keys.issubset(actual_keys), (
                f"Missing keys for {personality}: {required_keys - actual_keys}"
            )

    def test_templates_non_empty(self):
        for personality in PersonalityType:
            for key, template in SUMMARIZATION_TEMPLATES[personality].items():
                assert isinstance(template, str), (
                    f"Template {key} for {personality} is not a string"
                )
                assert len(template) > 0, f"Template {key} for {personality} is empty"

    def test_no_placeholder_text(self):
        placeholders = ["TODO", "FIXME", "PLACEHOLDER", "{{", "}}"]
        for personality in PersonalityType:
            for key, template in SUMMARIZATION_TEMPLATES[personality].items():
                for placeholder in placeholders:
                    assert placeholder not in template, (
                        f"Template {key} for {personality} contains placeholder: {placeholder}"
                    )

    def test_registration_creates_category(self):
        register_summarization_templates()
        registered = PersonalityAwareResponseFormatter._custom_templates.get("summarization")
        assert registered is not None, "summarization category not registered"
        assert isinstance(registered, dict)

    def test_registration_includes_all_personalities(self):
        register_summarization_templates()
        registered = PersonalityAwareResponseFormatter._custom_templates.get("summarization")
        for personality in PersonalityType:
            assert personality in registered, (
                f"Personality {personality} not in registered templates"
            )

    def test_friendly_templates_are_friendly(self):
        friendly = SUMMARIZATION_TEMPLATES[PersonalityType.FRIENDLY]
        assert any(
            emoji in friendly[key]
            for key in ["summary_intro", "short_conversation", "summary_closing"]
            for emoji in ["😊", "📋", "✨"]
        )

    def test_professional_templates_are_formal(self):
        professional = SUMMARIZATION_TEMPLATES[PersonalityType.PROFESSIONAL]
        for key in ["summary_intro", "short_conversation", "summary_closing"]:
            assert any(c.isupper() for c in professional[key] if c.isalpha()), (
                f"Professional {key} should have formal tone"
            )
