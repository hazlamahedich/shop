"""Tests for FAQ personality rephrasing.

Tests the rephrase_faq_with_personality function that applies
bot personality tone to FAQ answers.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.merchant import PersonalityType
from app.services.faq import rephrase_faq_with_personality
from app.services.llm.base_llm_service import LLMResponse


@pytest.fixture
def mock_llm_service():
    """Create mock LLM service."""
    service = AsyncMock()
    service.chat = AsyncMock()
    return service


class TestRephraseFaqWithPersonality:
    """Tests for rephrase_faq_with_personality function."""

    @pytest.mark.asyncio
    async def test_rephrase_friendly_personality(self, mock_llm_service):
        """Friendly personality should use casual tone."""
        mock_llm_service.chat.return_value = LLMResponse(
            content="Hey there! We're open Monday-Friday 9am-6pm! 😊",
            tokens_used=50,
            model="llama3.2",
            provider="ollama",
        )

        result = await rephrase_faq_with_personality(
            llm_service=mock_llm_service,
            faq_answer="We're open Monday-Friday 9am-6pm.",
            personality_type=PersonalityType.FRIENDLY,
            business_name="Cool Store",
            bot_name="Buddy",
        )

        assert "Hey" in result or "9am-6pm" in result
        mock_llm_service.chat.assert_called_once()
        call_args = mock_llm_service.chat.call_args
        messages = call_args[0][0]  # First positional argument
        assert any("friendly" in m.content.lower() for m in messages)

    @pytest.mark.asyncio
    async def test_rephrase_professional_personality(self, mock_llm_service):
        """Professional personality should use formal tone."""
        mock_llm_service.chat.return_value = LLMResponse(
            content="Our business hours are Monday through Friday, 9:00 AM to 6:00 PM.",
            tokens_used=50,
            model="llama3.2",
            provider="ollama",
        )

        result = await rephrase_faq_with_personality(
            llm_service=mock_llm_service,
            faq_answer="We're open Monday-Friday 9am-6pm.",
            personality_type=PersonalityType.PROFESSIONAL,
            business_name="Professional Store",
            bot_name="Assistant",
        )

        assert "Monday" in result or "6:00" in result
        mock_llm_service.chat.assert_called_once()
        call_args = mock_llm_service.chat.call_args
        messages = call_args[0][0]  # First positional argument
        assert any("professional" in m.content.lower() for m in messages)

    @pytest.mark.asyncio
    async def test_rephrase_enthusiastic_personality(self, mock_llm_service):
        """Enthusiastic personality should use energetic tone."""
        mock_llm_service.chat.return_value = LLMResponse(
            content="We're SO excited to help! We're open Mon-Fri 9am-6pm! 🎉",
            tokens_used=50,
            model="llama3.2",
            provider="ollama",
        )

        result = await rephrase_faq_with_personality(
            llm_service=mock_llm_service,
            faq_answer="We're open Monday-Friday 9am-6pm.",
            personality_type=PersonalityType.ENTHUSIASTIC,
            business_name="Fun Store",
            bot_name="Sparky",
        )

        assert "9am-6pm" in result or "Mon-Fri" in result
        mock_llm_service.chat.assert_called_once()
        call_args = mock_llm_service.chat.call_args
        messages = call_args[0][0]  # First positional argument
        assert any("enthusiastic" in m.content.lower() for m in messages)

    @pytest.mark.asyncio
    async def test_rephrase_fallback_on_timeout(self, mock_llm_service):
        """Should return original answer on timeout."""
        import asyncio

        mock_llm_service.chat.side_effect = asyncio.TimeoutError()

        original_answer = "We're open Monday-Friday 9am-6pm."
        result = await rephrase_faq_with_personality(
            llm_service=mock_llm_service,
            faq_answer=original_answer,
            personality_type=PersonalityType.FRIENDLY,
            business_name="Test Store",
            bot_name="Bot",
            timeout_seconds=0.1,
        )

        assert result == original_answer

    @pytest.mark.asyncio
    async def test_rephrase_fallback_on_error(self, mock_llm_service):
        """Should return original answer on LLM error."""
        mock_llm_service.chat.side_effect = Exception("LLM service error")

        original_answer = "We're open Monday-Friday 9am-6pm."
        result = await rephrase_faq_with_personality(
            llm_service=mock_llm_service,
            faq_answer=original_answer,
            personality_type=PersonalityType.FRIENDLY,
            business_name="Test Store",
            bot_name="Bot",
        )

        assert result == original_answer

    @pytest.mark.asyncio
    async def test_rephrase_preserves_information(self, mock_llm_service):
        """Rephrased answer should preserve key information."""
        original_answer = (
            "We offer free shipping on orders over $50. Delivery takes 3-5 business days."
        )
        mock_llm_service.chat.return_value = LLMResponse(
            content="Great news! We've got FREE shipping on orders over $50, and it'll be at your door in 3-5 business days! 🚚",
            tokens_used=60,
            model="llama3.2",
            provider="ollama",
        )

        result = await rephrase_faq_with_personality(
            llm_service=mock_llm_service,
            faq_answer=original_answer,
            personality_type=PersonalityType.FRIENDLY,
            business_name="Test Store",
            bot_name="Bot",
        )

        assert "$50" in result
        assert "3-5" in result or "3 to 5" in result

    @pytest.mark.asyncio
    async def test_rephrase_with_custom_bot_name(self, mock_llm_service):
        """Should include bot name in system prompt."""
        mock_llm_service.chat.return_value = LLMResponse(
            content="This is Sparky! We're open Monday-Friday.",
            tokens_used=30,
            model="llama3.2",
            provider="ollama",
        )

        await rephrase_faq_with_personality(
            llm_service=mock_llm_service,
            faq_answer="We're open Monday-Friday.",
            personality_type=PersonalityType.FRIENDLY,
            business_name="Test Store",
            bot_name="Sparky",
        )

        call_args = mock_llm_service.chat.call_args
        messages = call_args[0][0]  # First positional argument
        system_message = next(m for m in messages if m.role == "system")
        assert "Sparky" in system_message.content

    @pytest.mark.asyncio
    async def test_rephrase_with_business_name(self, mock_llm_service):
        """Should include business name in system prompt."""
        mock_llm_service.chat.return_value = LLMResponse(
            content="Welcome to Acme Corp! We're open Monday-Friday.",
            tokens_used=30,
            model="llama3.2",
            provider="ollama",
        )

        await rephrase_faq_with_personality(
            llm_service=mock_llm_service,
            faq_answer="We're open Monday-Friday.",
            personality_type=PersonalityType.FRIENDLY,
            business_name="Acme Corp",
            bot_name="Bot",
        )

        call_args = mock_llm_service.chat.call_args
        messages = call_args[0][0]  # First positional argument
        system_message = next(m for m in messages if m.role == "system")
        assert "Acme Corp" in system_message.content
