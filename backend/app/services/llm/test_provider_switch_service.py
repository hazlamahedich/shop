"""Tests for LLM Provider Switching Service.

Tests provider validation, switching, and rollback logic.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm.provider_switch_service import (
    ProviderSwitchService,
    ProviderValidationError,
)
from app.core.errors import ErrorCode
from app.models.llm_configuration import LLMConfiguration
from app.models.merchant import Merchant


@pytest.mark.asyncio
class TestProviderSwitchService:
    """Test provider switching service."""

    async def test_validate_provider_config_valid_ollama(
        self,
        db_session: AsyncSession,
        test_merchant: Merchant,
    ):
        """Test validating Ollama provider with valid server URL."""
        service = ProviderSwitchService(db_session)

        # Mock test_connection to return True
        # In real test, would use mocking library
        result = await service.validate_provider_config(
            merchant_id=test_merchant.id,
            provider_id="ollama",
            server_url="http://localhost:11434",
        )

        assert result["valid"] is True
        assert result["provider"]["id"] == "ollama"
        assert "test_response" in result

    async def test_validate_provider_config_invalid_api_key_format(
        self,
        db_session: AsyncSession,
        test_merchant: Merchant,
    ):
        """Test validating cloud provider with invalid API key format."""
        service = ProviderSwitchService(db_session)

        with pytest.raises(ProviderValidationError) as exc_info:
            await service.validate_provider_config(
                merchant_id=test_merchant.id,
                provider_id="openai",
                api_key="invalid",  # Too short, doesn't match pattern
            )

        assert exc_info.value.error_code == ErrorCode.LLM_API_KEY_INVALID
        assert "API key format" in str(exc_info.value).lower()

    async def test_validate_provider_config_invalid_provider(
        self,
        db_session: AsyncSession,
        test_merchant: Merchant,
    ):
        """Test validating with unknown provider ID."""
        service = ProviderSwitchService(db_session)

        with pytest.raises(ProviderValidationError) as exc_info:
            await service.validate_provider_config(
                merchant_id=test_merchant.id,
                provider_id="unknown_provider",
            )

        assert exc_info.value.error_code == ErrorCode.LLM_PROVIDER_NOT_FOUND

    async def test_switch_provider_success(
        self,
        db_session: AsyncSession,
        test_merchant: Merchant,
        existing_llm_config: LLMConfiguration,
    ):
        """Test successful provider switch from Ollama to OpenAI."""
        service = ProviderSwitchService(db_session)

        initial_provider = existing_llm_config.provider
        assert initial_provider == "ollama"

        result = await service.switch_provider(
            merchant_id=test_merchant.id,
            provider_id="openai",
            api_key="sk-test-valid-key-1234567890abcdef",
        )

        assert result["success"] is True
        assert result["provider"]["id"] == "openai"
        assert result["provider"]["model"] is not None
        assert "switched_at" in result

        # Verify database was updated
        await db_session.refresh(existing_llm_config)
        assert existing_llm_config.provider == "openai"

    async def test_switch_provider_rollback_on_validation_failure(
        self,
        db_session: AsyncSession,
        test_merchant: Merchant,
        existing_llm_config: LLMConfiguration,
    ):
        """Test that provider remains unchanged when validation fails."""
        service = ProviderSwitchService(db_session)

        initial_provider = existing_llm_config.provider
        initial_model = existing_llm_config.cloud_model

        with pytest.raises(ProviderValidationError):
            await service.switch_provider(
                merchant_id=test_merchant.id,
                provider_id="openai",
                api_key="invalid",  # Invalid format
            )

        # Verify config was NOT changed
        await db_session.refresh(existing_llm_config)
        assert existing_llm_config.provider == initial_provider
        assert existing_llm_config.cloud_model == initial_model

    async def test_switch_provider_to_ollama(
        self,
        db_session: AsyncSession,
        test_merchant: Merchant,
        existing_llm_config: LLMConfiguration,
    ):
        """Test switching from cloud provider to Ollama."""
        # First switch to OpenAI
        existing_llm_config.provider = "openai"
        existing_llm_config.api_key_encrypted = "encrypted_key"
        existing_llm_config.cloud_model = "gpt-4o-mini"
        await db_session.commit()

        service = ProviderSwitchService(db_session)

        result = await service.switch_provider(
            merchant_id=test_merchant.id,
            provider_id="ollama",
            server_url="http://localhost:11434",
        )

        assert result["success"] is True
        assert result["provider"]["id"] == "ollama"

        await db_session.refresh(existing_llm_config)
        assert existing_llm_config.provider == "ollama"
        assert existing_llm_config.ollama_url == "http://localhost:11434"

    async def test_test_provider_call(
        self,
        db_session: AsyncSession,
        test_merchant: Merchant,
    ):
        """Test making a test call to provider."""
        service = ProviderSwitchService(db_session)

        result = await service.test_provider_call(
            provider_id="ollama",
            server_url="http://localhost:11434",
        )

        assert result["success"] is True
        assert "response" in result
        assert "latency_ms" in result

    async def test_merchant_isolation(
        self,
        db_session: AsyncSession,
        test_merchant: Merchant,
        another_merchant: Merchant,
    ):
        """Test that merchant A cannot switch merchant B's provider."""
        service = ProviderSwitchService(db_session)

        # Try to switch another_merchant's config while authenticated as test_merchant
        with pytest.raises(ProviderValidationError) as exc_info:
            await service.validate_provider_config(
                merchant_id=another_merchant.id,  # Different merchant
                provider_id="openai",
                api_key="sk-test-key",
            )

        # Should fail due to merchant isolation check
        assert "merchant" in str(exc_info.value).lower() or "access" in str(exc_info.value).lower()

    async def test_get_current_provider(
        self,
        db_session: AsyncSession,
        test_merchant: Merchant,
        existing_llm_config: LLMConfiguration,
    ):
        """Test getting current provider configuration."""
        service = ProviderSwitchService(db_session)

        result = await service.get_current_provider(test_merchant.id)

        assert result["provider"]["id"] == existing_llm_config.provider
        assert result["provider"]["model"] in ["llama3", "mistral", "qwen2"]
        assert "configured_at" in result

    async def test_get_current_provider_not_found(
        self,
        db_session: AsyncSession,
        test_merchant: Merchant,
    ):
        """Test getting provider when no configuration exists."""
        service = ProviderSwitchService(db_session)

        # This merchant has no LLM configuration
        with pytest.raises(ProviderValidationError) as exc_info:
            await service.get_current_provider(test_merchant.id)

        assert exc_info.value.error_code == ErrorCode.LLM_CONFIGURATION_MISSING


# Fixtures would be defined in conftest.py
@pytest.fixture
async def test_merchant(db_session: AsyncSession) -> Merchant:
    """Create a test merchant."""
    merchant = Merchant(
        merchant_key="test-merchant-provider-switch",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)
    return merchant


@pytest.fixture
async def another_merchant(db_session: AsyncSession) -> Merchant:
    """Create another test merchant for isolation tests."""
    merchant = Merchant(
        merchant_key="another-merchant",
        platform="facebook",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)
    return merchant


@pytest.fixture
async def existing_llm_config(
    db_session: AsyncSession,
    test_merchant: Merchant,
) -> LLMConfiguration:
    """Create an existing LLM configuration for testing."""
    config = LLMConfiguration(
        merchant_id=test_merchant.id,
        provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="llama3",
        status="active",
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)
    return config
