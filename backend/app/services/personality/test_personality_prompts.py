"""Tests for Personality Prompt Service (Story 1.10).

Tests the generation of personality-based system prompts for bot conversations.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.personality_prompts import (
    get_personality_system_prompt,
    PersonalityPromptService,
)


class TestGetPersonalitySystemPrompt:
    """Tests for get_personality_system_prompt function."""

    @pytest.mark.asyncio
    async def test_friendly_personality_prompt(self) -> None:
        """Test friendly personality prompt generation (Story 1.10 AC 4)."""
        prompt = get_personality_system_prompt(PersonalityType.FRIENDLY)

        # Should contain base system prompt
        assert "helpful shopping assistant" in prompt.lower()
        assert "product search" in prompt.lower()

        # Should contain friendly personality cues
        assert "friendly" in prompt.lower()
        assert "casual" in prompt.lower()
        assert "warm" in prompt.lower()

        # Should contain friendly example phrases
        assert "Hey there!" in prompt
        assert "No problem!" in prompt

    @pytest.mark.asyncio
    async def test_professional_personality_prompt(self) -> None:
        """Test professional personality prompt generation (Story 1.10 AC 4)."""
        prompt = get_personality_system_prompt(PersonalityType.PROFESSIONAL)

        # Should contain base system prompt
        assert "helpful shopping assistant" in prompt.lower()

        # Should contain professional personality cues
        assert "professional" in prompt.lower()
        assert "polite" in prompt.lower()
        assert "efficient" in prompt.lower()

        # Should contain professional example phrases
        assert "Certainly" in prompt
        assert "How may I assist you" in prompt

    @pytest.mark.asyncio
    async def test_enthusiastic_personality_prompt(self) -> None:
        """Test enthusiastic personality prompt generation (Story 1.10 AC 4)."""
        prompt = get_personality_system_prompt(PersonalityType.ENTHUSIASTIC)

        # Should contain base system prompt
        assert "helpful shopping assistant" in prompt.lower()

        # Should contain enthusiastic personality cues
        assert "enthusiastic" in prompt.lower()
        assert "energetic" in prompt.lower()
        assert "excited" in prompt.lower()

        # Should contain enthusiastic example phrases
        assert "Amazing!" in prompt
        assert "You'll love this!" in prompt

    @pytest.mark.asyncio
    async def test_custom_greeting_friendly(self) -> None:
        """Test friendly personality with custom greeting.

        Note: Custom greeting is NO LONGER included in the LLM system prompt
        to prevent the bot from re-introducing itself on every response.
        The greeting is handled by the frontend widget instead.
        """
        custom_greeting = "Welcome to Alex's Athletic Gear! How can I help you find today?"
        prompt = get_personality_system_prompt(
            PersonalityType.FRIENDLY,
            custom_greeting=custom_greeting,
        )

        # Custom greeting should NOT be in the prompt (handled by frontend)
        assert "STORE GREETING:" not in prompt
        assert custom_greeting not in prompt

        # Should still include friendly personality
        assert "friendly" in prompt.lower()

    @pytest.mark.asyncio
    async def test_custom_greeting_professional(self) -> None:
        """Test professional personality with custom greeting.

        Note: Custom greeting is NO LONGER included in the LLM system prompt.
        """
        custom_greeting = "Thank you for visiting TechHub. How may I assist you?"
        prompt = get_personality_system_prompt(
            PersonalityType.PROFESSIONAL,
            custom_greeting=custom_greeting,
        )

        # Custom greeting should NOT be in the prompt (handled by frontend)
        assert "STORE GREETING:" not in prompt
        assert custom_greeting not in prompt

    @pytest.mark.asyncio
    async def test_custom_greeting_enthusiastic(self) -> None:
        """Test enthusiastic personality with custom greeting.

        Note: Custom greeting is NO LONGER included in the LLM system prompt.
        """
        custom_greeting = "Hey!!! Welcome to TrendyStyles!!! Let's find you something amazing!!!"
        prompt = get_personality_system_prompt(
            PersonalityType.ENTHUSIASTIC,
            custom_greeting=custom_greeting,
        )

        # Custom greeting should NOT be in the prompt (handled by frontend)
        assert "STORE GREETING:" not in prompt
        assert custom_greeting not in prompt

    @pytest.mark.asyncio
    async def test_no_custom_greeting(self) -> None:
        """Test prompt without custom greeting (Story 1.10 AC 3)."""
        prompt = get_personality_system_prompt(PersonalityType.FRIENDLY)

        # Should NOT contain STORE GREETING section
        assert "STORE GREETING:" not in prompt

    @pytest.mark.asyncio
    async def test_none_custom_greeting(self) -> None:
        """Test prompt with None as custom greeting."""
        prompt = get_personality_system_prompt(
            PersonalityType.FRIENDLY,
            custom_greeting=None,
        )

        # Should NOT contain STORE GREETING section
        assert "STORE GREETING:" not in prompt

    @pytest.mark.asyncio
    async def test_empty_custom_greeting(self) -> None:
        """Test prompt with empty string as custom greeting (Story 1.10 AC 3)."""
        # Empty string should not create STORE GREETING section (same as None)
        prompt = get_personality_system_prompt(
            PersonalityType.FRIENDLY,
            custom_greeting="",
        )

        # Empty greeting should NOT create the section
        assert "STORE GREETING:" not in prompt

    @pytest.mark.asyncio
    async def test_long_custom_greeting(self) -> None:
        """Test prompt with very long custom greeting (500 chars).

        Note: Custom greeting is NO LONGER included in the LLM system prompt.
        """
        long_greeting = "Welcome! " * 100  # 900 characters
        prompt = get_personality_system_prompt(
            PersonalityType.FRIENDLY,
            custom_greeting=long_greeting,
        )

        # Long greeting should NOT be in the prompt (handled by frontend)
        assert long_greeting not in prompt
        assert "STORE GREETING:" not in prompt


class TestPersonalityPromptService:
    """Tests for PersonalityPromptService class."""

    @pytest.mark.asyncio
    async def test_service_initialization(self) -> None:
        """Test service can be instantiated."""
        service = PersonalityPromptService()
        assert service is not None

    @pytest.mark.asyncio
    async def test_get_system_prompt_friendly(self) -> None:
        """Test get_system_prompt with friendly personality."""
        service = PersonalityPromptService()
        prompt = service.get_system_prompt(PersonalityType.FRIENDLY)

        assert "friendly" in prompt.lower()
        assert "casual" in prompt.lower()

    @pytest.mark.asyncio
    async def test_get_system_prompt_with_custom_greeting(self) -> None:
        """Test get_system_prompt with custom greeting.

        Note: Custom greeting is NO LONGER included in the LLM system prompt.
        """
        service = PersonalityPromptService()
        custom_greeting = "Welcome to my store!"
        prompt = service.get_system_prompt(
            PersonalityType.FRIENDLY,
            custom_greeting=custom_greeting,
        )

        # Custom greeting should NOT be in the prompt (handled by frontend)
        assert custom_greeting not in prompt
        assert "STORE GREETING:" not in prompt

    @pytest.mark.asyncio
    async def test_get_prompt_description_friendly(self) -> None:
        """Test get_prompt_description for friendly personality (Story 1.10 AC 1)."""
        service = PersonalityPromptService()
        description = service.get_prompt_description(PersonalityType.FRIENDLY)

        assert "warm" in description.lower()
        assert "casual" in description.lower()
        assert "friendly" in description.lower()

    @pytest.mark.asyncio
    async def test_get_prompt_description_professional(self) -> None:
        """Test get_prompt_description for professional personality."""
        service = PersonalityPromptService()
        description = service.get_prompt_description(PersonalityType.PROFESSIONAL)

        assert "polite" in description.lower()
        assert "efficient" in description.lower()
        assert "professional" in description.lower()

    @pytest.mark.asyncio
    async def test_get_prompt_description_enthusiastic(self) -> None:
        """Test get_prompt_description for enthusiastic personality."""
        service = PersonalityPromptService()
        description = service.get_prompt_description(PersonalityType.ENTHUSIASTIC)

        assert "energetic" in description.lower()
        assert "excited" in description.lower()
        assert "enthusiastic" in description.lower()

    @pytest.mark.asyncio
    async def test_all_personalities_have_descriptions(self) -> None:
        """Test that all personality types have descriptions."""
        service = PersonalityPromptService()

        for personality in PersonalityType:
            description = service.get_prompt_description(personality)
            assert description
            assert len(description) > 0
            assert personality.value in description.lower()
