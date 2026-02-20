"""Tests for LLM Provider Factory."""

from __future__ import annotations

from unittest.mock import patch
import pytest

from app.services.llm.llm_factory import LLMProviderFactory
from app.services.llm.ollama_service import OllamaService
from app.services.llm.openai_service import OpenAIService
from app.services.llm.anthropic_service import AnthropicService
from app.services.llm.gemini_service import GeminiService
from app.services.llm.glm_service import GLMService
from app.core.errors import APIError, ErrorCode


@patch("app.services.llm.llm_factory.is_testing", return_value=False)
@pytest.mark.asyncio
async def test_factory_create_ollama(mock_testing) -> None:
    """Test creating Ollama provider."""
    provider = LLMProviderFactory.create_provider(
        "ollama",
        {"ollama_url": "http://localhost:11434"},
    )

    assert isinstance(provider, OllamaService)
    assert provider.provider_name == "ollama"


@patch("app.services.llm.llm_factory.is_testing", return_value=False)
@pytest.mark.asyncio
async def test_factory_create_openai(mock_testing) -> None:
    """Test creating OpenAI provider."""
    provider = LLMProviderFactory.create_provider(
        "openai",
        {"api_key": "test-key"},
    )

    assert isinstance(provider, OpenAIService)
    assert provider.provider_name == "openai"


@patch("app.services.llm.llm_factory.is_testing", return_value=False)
@pytest.mark.asyncio
async def test_factory_create_anthropic(mock_testing) -> None:
    """Test creating Anthropic provider."""
    provider = LLMProviderFactory.create_provider(
        "anthropic",
        {"api_key": "test-key"},
    )

    assert isinstance(provider, AnthropicService)
    assert provider.provider_name == "anthropic"


@patch("app.services.llm.llm_factory.is_testing", return_value=False)
@pytest.mark.asyncio
async def test_factory_create_gemini(mock_testing) -> None:
    """Test creating Gemini provider."""
    provider = LLMProviderFactory.create_provider(
        "gemini",
        {"api_key": "test-key"},
    )

    assert isinstance(provider, GeminiService)
    assert provider.provider_name == "gemini"


@patch("app.services.llm.llm_factory.is_testing", return_value=False)
@pytest.mark.asyncio
async def test_factory_create_glm(mock_testing) -> None:
    """Test creating GLM provider."""
    provider = LLMProviderFactory.create_provider(
        "glm",
        {"api_key": "test-key"},
    )

    assert isinstance(provider, GLMService)
    assert provider.provider_name == "glm"


@patch("app.services.llm.llm_factory.is_testing", return_value=False)
@pytest.mark.asyncio
async def test_factory_invalid_provider(mock_testing) -> None:
    """Test factory raises error for invalid provider."""
    with pytest.raises(APIError) as exc_info:
        LLMProviderFactory.create_provider("invalid", {})

    assert exc_info.value.code == ErrorCode.LLM_PROVIDER_NOT_FOUND
    assert "Unknown LLM provider" in str(exc_info.value)


@pytest.mark.asyncio
async def test_factory_get_available_providers() -> None:
    """Test getting list of available providers."""
    providers = LLMProviderFactory.get_available_providers()

    assert len(providers) == 5

    provider_ids = [p["id"] for p in providers]
    assert "ollama" in provider_ids
    assert "openai" in provider_ids
    assert "anthropic" in provider_ids
    assert "gemini" in provider_ids
    assert "glm" in provider_ids


@pytest.mark.asyncio
async def test_factory_provider_metadata() -> None:
    """Test provider metadata structure."""
    providers = LLMProviderFactory.get_available_providers()

    ollama = next(p for p in providers if p["id"] == "ollama")
    assert ollama["name"] == "Ollama (Local)"
    assert ollama["pricing"]["inputCost"] == 0.0
    assert ollama["pricing"]["outputCost"] == 0.0
    assert "llama3" in ollama["models"]

    openai = next(p for p in providers if p["id"] == "openai")
    assert openai["name"] == "OpenAI"
    assert openai["pricing"]["inputCost"] == 0.15
    assert openai["pricing"]["outputCost"] == 0.60
    assert "gpt-4o-mini" in openai["models"]


@pytest.mark.asyncio
async def test_factory_uses_is_testing() -> None:
    """Test factory respects IS_TESTING environment variable."""
    from unittest.mock import patch

    with patch("app.services.llm.llm_factory.is_testing", return_value=True):
        provider = LLMProviderFactory.create_provider(
            "ollama",
            {"ollama_url": "http://localhost:11434"},
        )
        assert provider.is_testing is True

    with patch("app.services.llm.llm_factory.is_testing", return_value=False):
        provider = LLMProviderFactory.create_provider(
            "ollama",
            {"ollama_url": "http://localhost:11434"},
        )
        assert provider.is_testing is False
