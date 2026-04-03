from __future__ import annotations

import re

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.conversation_templates import CONVERSATION_TEMPLATES

from .fixtures import count_emojis


class TestConversationTemplatePersonalityCompliance:
    TEMPLATE_KEYS = [
        "welcome_back_fallback",
        "bot_paused",
        "clarification_fallback",
        "consent_check_error",
        "forget_rate_limited",
        "forget_error",
        "forget_unexpected_error",
        "llm_classification_leak",
        "llm_fallback",
    ]

    @pytest.mark.test_id("11-5-INT-011")
    def test_professional_no_emojis_all_templates(self):
        for key in self.TEMPLATE_KEYS:
            text = CONVERSATION_TEMPLATES[PersonalityType.PROFESSIONAL][key]
            assert count_emojis(text) == 0, (
                f"Professional template '{key}' should have no emojis, got: {text}"
            )

    @pytest.mark.test_id("11-5-INT-012")
    def test_professional_no_slang_all_templates(self):
        slang_re = re.compile(r"\b(awesome|gonna|wanna|yeah|yep|nope|omg|lol|oops|oopsie)\b", re.I)
        for key in self.TEMPLATE_KEYS:
            text = CONVERSATION_TEMPLATES[PersonalityType.PROFESSIONAL][key]
            assert not slang_re.search(text), (
                f"Professional template '{key}' should not contain slang, got: {text}"
            )

    @pytest.mark.test_id("11-5-INT-013")
    def test_enthusiastic_has_exclamation_or_emoji_all_templates(self):
        for key in self.TEMPLATE_KEYS:
            text = CONVERSATION_TEMPLATES[PersonalityType.ENTHUSIASTIC][key]
            has_exclamation = "!" in text
            has_emoji = count_emojis(text) > 0
            assert has_exclamation or has_emoji, (
                f"Enthusiastic template '{key}' should have exclamation or emoji, got: {text}"
            )

    @pytest.mark.test_id("11-5-INT-014")
    def test_friendly_moderate_emojis_all_templates(self):
        for key in self.TEMPLATE_KEYS:
            text = CONVERSATION_TEMPLATES[PersonalityType.FRIENDLY][key]
            emoji_count = count_emojis(text)
            assert 0 <= emoji_count <= 3, (
                f"Friendly template '{key}' should have 0-3 emojis, got {emoji_count}: {text}"
            )

    @pytest.mark.test_id("11-5-INT-015")
    def test_all_keys_present_for_all_personalities(self):
        for ptype in PersonalityType:
            for key in self.TEMPLATE_KEYS:
                assert key in CONVERSATION_TEMPLATES[ptype], (
                    f"Missing template key '{key}' for personality {ptype.value}"
                )

    @pytest.mark.test_id("11-5-INT-016")
    def test_llm_fallback_contains_business_name_placeholder(self):
        for ptype in PersonalityType:
            text = CONVERSATION_TEMPLATES[ptype]["llm_fallback"]
            assert "{business_name}" in text, (
                f"llm_fallback for {ptype.value} should contain {{business_name}} placeholder"
            )

    @pytest.mark.test_id("11-5-INT-017")
    def test_professional_templates_formal_tone(self):
        informal_re = re.compile(
            r"\b(I'm|can't|won't|don't|isn't|aren't|couldn't|wouldn't|let's)\b",
            re.I,
        )
        for key in self.TEMPLATE_KEYS:
            text = CONVERSATION_TEMPLATES[PersonalityType.PROFESSIONAL][key]
            assert not informal_re.search(text), (
                f"Professional template '{key}' should avoid contractions, got: {text}"
            )

    @pytest.mark.test_id("11-5-INT-018")
    def test_enthusiastic_templates_upbeat_words(self):
        for key in self.TEMPLATE_KEYS:
            text = CONVERSATION_TEMPLATES[PersonalityType.ENTHUSIASTIC][key]
            has_energy = any(
                w in text.upper()
                for w in ["LOVE", "AMAZING", "SO", "!!!", "WOW", "EXCITED", "AWESOME", "TINY"]
            )
            has_emoji = count_emojis(text) > 0
            assert has_energy or has_emoji, (
                f"Enthusiastic template '{key}' should feel energetic, got: {text}"
            )
