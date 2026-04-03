from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

from .fixtures import count_emojis


@pytest.mark.parametrize(
    "template, personality, min_emojis, max_emojis, has_exclamation, keyword",
    [
        ("bot_paused", PersonalityType.PROFESSIONAL, 0, 0, False, "unavailable"),
        ("bot_paused", PersonalityType.FRIENDLY, 1, 99, False, None),
        ("bot_paused", PersonalityType.ENTHUSIASTIC, 1, 99, True, None),
        ("welcome_back_fallback", PersonalityType.PROFESSIONAL, 0, 0, False, "welcome"),
        ("welcome_back_fallback", PersonalityType.FRIENDLY, 1, 99, False, None),
        ("welcome_back_fallback", PersonalityType.ENTHUSIASTIC, 1, 99, True, None),
    ],
    ids=[
        "bot_paused-professional",
        "bot_paused-friendly",
        "bot_paused-enthusiastic",
        "welcome_back-professional",
        "welcome_back-friendly",
        "welcome_back-enthusiastic",
    ],
)
@pytest.mark.test_id("11-5-INT-033")
def test_template_formatting_matches_personality(
    template, personality, min_emojis, max_emojis, has_exclamation, keyword
):
    result = PersonalityAwareResponseFormatter.format_response(
        "conversation", template, personality
    )
    emoji_count = count_emojis(result)
    assert min_emojis <= emoji_count <= max_emojis
    if has_exclamation:
        assert "!" in result
    if keyword:
        assert keyword in result.lower()
