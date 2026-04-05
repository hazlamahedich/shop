"""Unit tests for sentiment-adaptive templates (Story 11-10).

Tests that all sentiment template keys are registered and produce
non-empty output for all personality types.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.conversation_templates import (
    SENTIMENT_ADAPTIVE_TEMPLATES,
    register_sentiment_adaptive_templates,
)
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


@pytest.fixture(autouse=True)
def _register_templates():
    register_sentiment_adaptive_templates()


BASE_KEYS = {
    "pre_empathetic",
    "pre_empathetic_ecommerce",
    "pre_empathetic_general",
    "pre_concise",
    "pre_concise_ecommerce",
    "pre_concise_general",
    "pre_detailed",
    "pre_enthusiastic",
    "post_empathetic",
    "post_empathetic_ecommerce",
    "post_empathetic_general",
    "post_enthusiastic",
    "escalation_message",
}


class TestSentimentTemplateCompleteness:
    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_all_personalities_have_same_keys(self, personality: PersonalityType):
        keys = set(SENTIMENT_ADAPTIVE_TEMPLATES[personality].keys())
        assert keys == BASE_KEYS, f"{personality.value} missing keys: {BASE_KEYS - keys}"

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_all_templates_non_empty(self, personality: PersonalityType):
        for key, value in SENTIMENT_ADAPTIVE_TEMPLATES[personality].items():
            assert value.strip(), f"Template '{key}' for {personality.value} is empty"


class TestSentimentTemplateFormatting:
    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_pre_empathetic_formats(self, personality: PersonalityType):
        result = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            "pre_empathetic",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_pre_concise_formats(self, personality: PersonalityType):
        result = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            "pre_concise",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_pre_detailed_formats(self, personality: PersonalityType):
        result = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            "pre_detailed",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_pre_enthusiastic_formats(self, personality: PersonalityType):
        result = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            "pre_enthusiastic",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_post_empathetic_formats(self, personality: PersonalityType):
        result = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            "post_empathetic",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_escalation_message_formats(self, personality: PersonalityType):
        result = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            "escalation_message",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_ecommerce_variant_formats(self, personality: PersonalityType):
        for suffix in ("_ecommerce", "_general"):
            base_keys_with_mode = [k for k in BASE_KEYS if suffix in k]
            for key in base_keys_with_mode:
                result = PersonalityAwareResponseFormatter.format_response(
                    "sentiment_adaptive",
                    key,
                    personality,
                )
                assert isinstance(result, str) and len(result) > 0, (
                    f"Empty result for {personality.value}/{key}"
                )

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_mode_parameter_respected(self, personality: PersonalityType):
        result = PersonalityAwareResponseFormatter.format_response(
            "sentiment_adaptive",
            "pre_empathetic",
            personality,
            mode="ecommerce",
        )
        assert isinstance(result, str)
        assert len(result) > 0
