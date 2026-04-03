"""Tests for personality enforcement middleware (Story 11-5, AC11)."""

import asyncio

import pytest

from app.models.merchant import PersonalityType
from app.services.conversation.schemas import ConversationResponse
from app.services.personality.personality_middleware import (
    _apply_personality_heuristic,
    _detect_raw_personality,
    _looks_unformatted,
    with_personality,
)


class TestDetectRawPersonality:
    """Heuristic personality detection from raw text."""

    def test_enthusiastic_detected(self):
        result = _detect_raw_personality("AMAZING finds!!! You're gonna LOVE these! 🔥")
        assert result == PersonalityType.ENTHUSIASTIC

    def test_friendly_detected(self):
        result = _detect_raw_personality("Sure thing! Here's what I found.")
        assert result == PersonalityType.FRIENDLY

    def test_professional_detected(self):
        result = _detect_raw_personality("Certainly. Here are the options.")
        assert result == PersonalityType.PROFESSIONAL

    def test_neutral_defaults_friendly(self):
        result = _detect_raw_personality("The results are ready.")
        assert result == PersonalityType.FRIENDLY

    def test_empty_string_defaults_friendly(self):
        result = _detect_raw_personality("")
        assert result == PersonalityType.FRIENDLY


class TestApplyPersonalityHeuristic:
    """Lightweight personality adjustment for raw strings."""

    def test_professional_strips_emojis(self):
        result = _apply_personality_heuristic("Great news! 🎉", PersonalityType.PROFESSIONAL)
        assert "🎉" not in result

    def test_enthusiastic_adds_exclamation(self):
        result = _apply_personality_heuristic("Here are the results.", PersonalityType.ENTHUSIASTIC)
        assert result.endswith("!")

    def test_friendly_returns_unchanged(self):
        text = "Sure thing! Here you go 😊"
        result = _apply_personality_heuristic(text, PersonalityType.FRIENDLY)
        assert result == text

    def test_empty_string_unchanged(self):
        assert _apply_personality_heuristic("", PersonalityType.PROFESSIONAL) == ""

    def test_whitespace_only_unchanged(self):
        assert _apply_personality_heuristic("   ", PersonalityType.PROFESSIONAL) == "   "


class TestLooksUnformatted:
    """Heuristic detection of unformatted responses."""

    def test_professional_with_emoji_is_unformatted(self):
        assert _looks_unformatted("Here are the results! 🎉", PersonalityType.PROFESSIONAL)

    def test_professional_without_emoji_is_formatted(self):
        assert not _looks_unformatted(
            "Here are the available options.", PersonalityType.PROFESSIONAL
        )

    def test_enthusiastic_without_exclamation_is_unformatted(self):
        assert _looks_unformatted("Here are the results.", PersonalityType.ENTHUSIASTIC)

    def test_enthusiastic_with_exclamation_is_formatted(self):
        assert not _looks_unformatted("AMAZING results!!! 🔥", PersonalityType.ENTHUSIASTIC)

    def test_empty_string_not_unformatted(self):
        assert not _looks_unformatted("", PersonalityType.FRIENDLY)


class TestWithPersonalityDecorator:
    """Decorator enforcement on handler return values."""

    @pytest.mark.asyncio
    async def test_async_raw_string_gets_adjusted(self):
        @with_personality(PersonalityType.PROFESSIONAL)
        async def handler():
            return "Here are the results! 🎉"

        result = await handler()
        assert isinstance(result, str)
        assert "🎉" not in result

    @pytest.mark.asyncio
    async def test_async_conversation_response_gets_adjusted(self):
        @with_personality(PersonalityType.PROFESSIONAL)
        async def handler():
            return ConversationResponse(
                message="Results are here! 🎉",
                intent="general",
                confidence=1.0,
            )

        result = await handler()
        assert isinstance(result, ConversationResponse)
        assert "🎉" not in result.message

    @pytest.mark.asyncio
    async def test_async_dict_passthrough(self):
        @with_personality(PersonalityType.FRIENDLY)
        async def handler():
            return {"status": "ok"}

        result = await handler()
        assert result == {"status": "ok"}

    def test_sync_raw_string_gets_adjusted(self):
        @with_personality(PersonalityType.PROFESSIONAL)
        def handler():
            return "Here are the results! 🎉"

        result = handler()
        assert isinstance(result, str)
        assert "🎉" not in result

    @pytest.mark.asyncio
    async def test_preserves_formatted_response(self):
        formatted_msg = "Here are the available options."

        @with_personality(PersonalityType.PROFESSIONAL)
        async def handler():
            return ConversationResponse(
                message=formatted_msg,
                intent="general",
                confidence=1.0,
            )

        result = await handler()
        assert result.message == formatted_msg
