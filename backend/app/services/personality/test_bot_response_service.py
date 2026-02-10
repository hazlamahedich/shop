"""Tests for Bot Response Service (Story 1.10).

Tests the generation of personality-appropriate bot responses.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant, PersonalityType
from app.services.personality.bot_response_service import BotResponseService


class TestBotResponseService:
    """Tests for BotResponseService class."""

    @pytest.mark.asyncio
    async def test_get_greeting_friendly(self, db_session: AsyncSession) -> None:
        """Test getting friendly greeting (Story 1.10 AC 4)."""
        # Create merchant with friendly personality
        merchant = Merchant(
            merchant_key="test-greeting-friendly",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        greeting = await service.get_greeting(merchant.id, db_session)

        # Should be a friendly greeting
        assert greeting
        assert any(word in greeting.lower() for word in ["hey", "hi", "hello", "welcome"])

    @pytest.mark.asyncio
    async def test_get_greeting_professional(self, db_session: AsyncSession) -> None:
        """Test getting professional greeting (Story 1.10 AC 5)."""
        merchant = Merchant(
            merchant_key="test-greeting-professional",
            platform="facebook",
            status="active",
            personality=PersonalityType.PROFESSIONAL,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        greeting = await service.get_greeting(merchant.id, db_session)

        # Should be a professional greeting
        assert greeting
        assert any(word in greeting.lower() for word in ["good day", "hello", "welcome", "may"])

    @pytest.mark.asyncio
    async def test_get_greeting_enthusiastic(self, db_session: AsyncSession) -> None:
        """Test getting enthusiastic greeting (Story 1.10 AC 5)."""
        merchant = Merchant(
            merchant_key="test-greeting-enthusiastic",
            platform="facebook",
            status="active",
            personality=PersonalityType.ENTHUSIASTIC,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        greeting = await service.get_greeting(merchant.id, db_session)

        # Should be an enthusiastic greeting with exclamation marks
        assert greeting
        assert "!!!" in greeting  # Enthusiastic greetings always have !!!

    @pytest.mark.asyncio
    async def test_get_greeting_custom(self, db_session: AsyncSession) -> None:
        """Test getting custom greeting (Story 1.10 AC 4)."""
        custom_greeting = "Welcome to Alex's Awesome Shop!!! How can I help you today?"
        merchant = Merchant(
            merchant_key="test-greeting-custom",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
            custom_greeting=custom_greeting,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        greeting = await service.get_greeting(merchant.id, db_session)

        # Should use custom greeting
        assert greeting == custom_greeting

    @pytest.mark.asyncio
    async def test_get_greeting_default_personality(self, db_session: AsyncSession) -> None:
        """Test default greeting for merchant without personality (Story 1.10 AC 3)."""
        # Create merchant without personality (defaults to friendly)
        merchant = Merchant(
            merchant_key="test-greeting-default",
            platform="facebook",
            status="active",
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        greeting = await service.get_greeting(merchant.id, db_session)

        # Should use friendly greeting as default
        assert greeting
        assert any(word in greeting.lower() for word in ["hey", "hi", "hello", "welcome"])

    @pytest.mark.asyncio
    async def test_get_greeting_merchant_not_found(self, db_session: AsyncSession) -> None:
        """Test greeting when merchant not found uses default."""
        service = BotResponseService()
        greeting = await service.get_greeting(99999, db_session)

        # Should use friendly greeting as default
        assert greeting
        assert any(word in greeting.lower() for word in ["hey", "hi", "hello", "welcome"])

    @pytest.mark.asyncio
    async def test_get_help_response_friendly(self, db_session: AsyncSession) -> None:
        """Test getting friendly help response."""
        merchant = Merchant(
            merchant_key="test-help-friendly",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        response = await service.get_help_response(merchant.id, db_session)

        # Should be friendly
        assert response
        assert any(word in response.lower() for word in ["sure", "no problem", "happy"])

    @pytest.mark.asyncio
    async def test_get_help_response_professional(self, db_session: AsyncSession) -> None:
        """Test getting professional help response."""
        merchant = Merchant(
            merchant_key="test-help-professional",
            platform="facebook",
            status="active",
            personality=PersonalityType.PROFESSIONAL,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        response = await service.get_help_response(merchant.id, db_session)

        # Should be professional
        assert response
        assert any(word in response.lower() for word in ["certainly", "assist", "happy to help"])

    @pytest.mark.asyncio
    async def test_get_help_response_enthusiastic(self, db_session: AsyncSession) -> None:
        """Test getting enthusiastic help response."""
        merchant = Merchant(
            merchant_key="test-help-enthusiastic",
            platform="facebook",
            status="active",
            personality=PersonalityType.ENTHUSIASTIC,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        response = await service.get_help_response(merchant.id, db_session)

        # Should be enthusiastic
        assert response
        assert "!" in response
        assert any(word in response.lower() for word in ["yay", "woohoo", "amazing", "excited"])

    @pytest.mark.asyncio
    async def test_get_error_response_friendly(self, db_session: AsyncSession) -> None:
        """Test getting friendly error response."""
        merchant = Merchant(
            merchant_key="test-error-friendly",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        response = await service.get_error_response(merchant.id, db_session)

        # Should be friendly but apologetic
        assert response
        assert any(word in response.lower() for word in ["oops", "sorry", "apologize"])

    @pytest.mark.asyncio
    async def test_get_error_response_professional(self, db_session: AsyncSession) -> None:
        """Test getting professional error response."""
        merchant = Merchant(
            merchant_key="test-error-professional",
            platform="facebook",
            status="active",
            personality=PersonalityType.PROFESSIONAL,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        response = await service.get_error_response(merchant.id, db_session)

        # Should be professional
        assert response
        assert any(word in response.lower() for word in ["apologize", "apologies", "inconvenience"])

    @pytest.mark.asyncio
    async def test_get_error_response_enthusiastic(self, db_session: AsyncSession) -> None:
        """Test getting enthusiastic error response."""
        merchant = Merchant(
            merchant_key="test-error-enthusiastic",
            platform="facebook",
            status="active",
            personality=PersonalityType.ENTHUSIASTIC,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        response = await service.get_error_response(merchant.id, db_session)

        # Should be enthusiastic even in error
        assert response
        assert "!" in response
        assert any(word in response.lower() for word in ["oh no", "aww", "oops"])

    @pytest.mark.asyncio
    async def test_get_system_prompt_friendly(self, db_session: AsyncSession) -> None:
        """Test getting system prompt for friendly personality (Story 1.10 AC 4)."""
        merchant = Merchant(
            merchant_key="test-prompt-friendly",
            platform="facebook",
            status="active",
            personality=PersonalityType.FRIENDLY,
            custom_greeting="Welcome to my awesome store!",
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        prompt = await service.get_system_prompt(merchant.id, db_session)

        # Should contain personality and custom greeting
        assert "friendly" in prompt.lower()
        assert "STORE GREETING:" in prompt
        assert "Welcome to my awesome store!" in prompt

    @pytest.mark.asyncio
    async def test_get_system_prompt_no_custom_greeting(self, db_session: AsyncSession) -> None:
        """Test system prompt without custom greeting (Story 1.10 AC 3)."""
        merchant = Merchant(
            merchant_key="test-prompt-no-greeting",
            platform="facebook",
            status="active",
            personality=PersonalityType.PROFESSIONAL,
        )
        db_session.add(merchant)
        await db_session.commit()
        await db_session.refresh(merchant)

        service = BotResponseService()
        prompt = await service.get_system_prompt(merchant.id, db_session)

        # Should contain personality but no STORE GREETING section
        assert "professional" in prompt.lower()
        assert "STORE GREETING:" not in prompt

    @pytest.mark.asyncio
    async def test_get_system_prompt_merchant_not_found(self, db_session: AsyncSession) -> None:
        """Test system prompt when merchant not found uses default."""
        service = BotResponseService()
        prompt = await service.get_system_prompt(99999, db_session)

        # Should use friendly default
        assert "friendly" in prompt.lower()
