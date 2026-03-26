"""Tests for Personality Prompt Service (Story 1.10).

Tests the generation of personality-based system prompts for bot conversations.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.personality_prompts import (
    PersonalityPromptService,
    get_personality_system_prompt,
)


class TestGetPersonalitySystemPrompt:
    """Tests for get_personality_system_prompt function."""

    @pytest.mark.asyncio
    async def test_friendly_personality_ecommerce_mode(self) -> None:
        """Test friendly personality prompt in e-commerce mode."""
        prompt = get_personality_system_prompt(
            PersonalityType.FRIENDLY,
            onboarding_mode="ecommerce",
        )

        # E-commerce mode should contain shopping assistant language
        assert "shopping assistant" in prompt.lower()

        # Should contain friendly personality cues
        assert "warm" in prompt.lower()
        assert "casual" in prompt.lower()

    @pytest.mark.asyncio
    async def test_friendly_personality_general_mode(self) -> None:
        """Test friendly personality prompt in general mode."""
        prompt = get_personality_system_prompt(
            PersonalityType.FRIENDLY,
            onboarding_mode="general",
        )

        # General mode should NOT contain shopping assistant language
        assert "shopping assistant" not in prompt.lower()

        # Should contain general assistant language
        assert "helpful ai assistant" in prompt.lower()

        # Should still contain friendly personality cues
        assert "warm" in prompt.lower()
        assert "casual" in prompt.lower()

    @pytest.mark.asyncio
    async def test_professional_personality_ecommerce_mode(self) -> None:
        """Test professional personality prompt in e-commerce mode."""
        prompt = get_personality_system_prompt(
            PersonalityType.PROFESSIONAL,
            onboarding_mode="ecommerce",
        )

        # E-commerce mode should contain shopping assistant language
        assert "shopping assistant" in prompt.lower()

        # Should contain professional personality cues
        assert "professional" in prompt.lower()
        assert "polite" in prompt.lower()

    @pytest.mark.asyncio
    async def test_professional_personality_general_mode(self) -> None:
        """Test professional personality prompt in general mode."""
        prompt = get_personality_system_prompt(
            PersonalityType.PROFESSIONAL,
            onboarding_mode="general",
        )

        # General mode should NOT contain shopping assistant language
        assert "shopping assistant" not in prompt.lower()

        # Should contain general assistant language
        assert "helpful ai assistant" in prompt.lower()

        # Should still contain professional personality cues
        assert "professional" in prompt.lower()
        assert "polite" in prompt.lower()

    @pytest.mark.asyncio
    async def test_enthusiastic_personality_ecommerce_mode(self) -> None:
        """Test enthusiastic personality prompt in e-commerce mode."""
        prompt = get_personality_system_prompt(
            PersonalityType.ENTHUSIASTIC,
            onboarding_mode="ecommerce",
        )

        # E-commerce mode should contain shopping assistant language
        assert "shopping assistant" in prompt.lower()

        # Should contain enthusiastic personality cues
        assert "energetic" in prompt.lower()
        assert "excited" in prompt.lower()

    @pytest.mark.asyncio
    async def test_enthusiastic_personality_general_mode(self) -> None:
        """Test enthusiastic personality prompt in general mode."""
        prompt = get_personality_system_prompt(
            PersonalityType.ENTHUSIASTIC,
            onboarding_mode="general",
        )

        # General mode should NOT contain shopping assistant language
        assert "shopping assistant" not in prompt.lower()

        # Should contain general assistant language
        assert "helpful ai assistant" in prompt.lower()

        # Should still contain enthusiastic personality cues
        assert "energetic" in prompt.lower()
        assert "excited" in prompt.lower()

    @pytest.mark.asyncio
    async def test_bot_name_included(self) -> None:
        """Test that bot_name is included in prompt."""
        prompt = get_personality_system_prompt(
            PersonalityType.FRIENDLY,
            bot_name="Sherms",
            onboarding_mode="general",
        )

        assert "Your name is Sherms" in prompt

    @pytest.mark.asyncio
    async def test_default_mode_is_ecommerce(self) -> None:
        """Test that default mode (no onboarding_mode) is e-commerce."""
        prompt = get_personality_system_prompt(PersonalityType.FRIENDLY)

        # Should default to e-commerce
        assert "shopping assistant" in prompt.lower()

    @pytest.mark.asyncio
    async def test_custom_greeting_not_in_prompt(self) -> None:
        """Test that custom greeting is NOT in the LLM system prompt.

        Note: Custom greeting is handled by frontend widget, not LLM prompt.
        """
        custom_greeting = "Welcome to Alex's Athletic Gear! How can I help you find today?"
        prompt = get_personality_system_prompt(
            PersonalityType.FRIENDLY,
            custom_greeting=custom_greeting,
        )

        # Custom greeting should NOT be in the prompt (handled by frontend)
        assert custom_greeting not in prompt

    @pytest.mark.asyncio
    async def test_business_info_included(self) -> None:
        """Test that business info is included in prompt."""
        prompt = get_personality_system_prompt(
            PersonalityType.PROFESSIONAL,
            business_name="Tech Store",
            business_description="We sell tech products",
            business_hours="9-5 M-F",
            onboarding_mode="ecommerce",
        )

        assert "Business Name: Tech Store" in prompt
        assert "Description: We sell tech products" in prompt
        assert "Hours: 9-5 M-F" in prompt

    @pytest.mark.asyncio
    async def test_product_context_only_in_ecommerce_mode(self) -> None:
        """Test that product context is only included in e-commerce mode."""
        product_context = "Categories: Electronics, Gadgets"

        # E-commerce mode should include product context
        ecommerce_prompt = get_personality_system_prompt(
            PersonalityType.FRIENDLY,
            product_context=product_context,
            onboarding_mode="ecommerce",
        )
        assert "STORE PRODUCTS:" in ecommerce_prompt
        assert product_context in ecommerce_prompt

        # General mode should NOT include product context
        general_prompt = get_personality_system_prompt(
            PersonalityType.FRIENDLY,
            product_context=product_context,
            onboarding_mode="general",
        )
        assert "STORE PRODUCTS:" not in general_prompt
        assert product_context not in general_prompt


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

        assert "warm" in prompt.lower()
        assert "casual" in prompt.lower()

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
