"""Tests for Ollama service provider."""

from __future__ import annotations

import pytest
import httpx
from httpx import ASGITransport

from app.services.llm.ollama_service import OllamaService
from app.services.llm.base_llm_service import LLMMessage


@pytest.mark.asyncio
async def test_ollama_provider_name() -> None:
    """Test Ollama provider name."""
    service = OllamaService({"ollama_url": "http://localhost:11434"})
    assert service.provider_name == "ollama"


@pytest.mark.asyncio
async def test_ollama_test_connection_testing_mode() -> None:
    """Test Ollama connection in testing mode."""
    service = OllamaService({}, is_testing=True)
    assert await service.test_connection() is True


@pytest.mark.asyncio
async def test_ollama_chat_testing_mode() -> None:
    """Test Ollama chat in testing mode."""
    service = OllamaService({}, is_testing=True)
    messages = [
        LLMMessage(role="system", content="You are a helpful assistant."),
        LLMMessage(role="user", content="Hello!"),
    ]

    response = await service.chat(messages)

    assert response.content == "Test response from Ollama"
    assert response.tokens_used == 10
    assert response.provider == "ollama"
    assert response.metadata["test"] is True


@pytest.mark.asyncio
async def test_ollama_count_tokens() -> None:
    """Test Ollama token counting (approximately 4 chars per token)."""
    service = OllamaService({})

    # 15 characters / 4 = 3 tokens (integer division)
    text = "This is a test"
    tokens = service.count_tokens(text)
    assert tokens == 3


@pytest.mark.asyncio
async def test_ollama_estimate_cost() -> None:
    """Test Ollama cost estimation (always free)."""
    service = OllamaService({})

    cost = service.estimate_cost(1000, 500)
    assert cost == 0.0


@pytest.mark.asyncio
async def test_ollama_health_check_testing_mode() -> None:
    """Test Ollama health check in testing mode."""
    service = OllamaService({}, is_testing=True)
    health = await service.health_check()

    assert health["provider"] == "ollama"
    assert health["status"] == "healthy"
    assert "latency_ms" in health
    assert health["model"] == "default"


@pytest.mark.asyncio
async def test_ollama_default_model() -> None:
    """Test Ollama default model."""
    service = OllamaService({})
    assert service.DEFAULT_MODEL == "llama3"


@pytest.mark.asyncio
async def test_ollama_build_prompt() -> None:
    """Test prompt building from messages."""
    service = OllamaService({})

    messages = [
        LLMMessage(role="system", content="You are helpful."),
        LLMMessage(role="user", content="Hello!"),
        LLMMessage(role="assistant", content="Hi there!"),
    ]

    prompt = service._build_prompt(messages)
    expected = (
        "System: You are helpful.\n"
        "User: Hello!\n"
        "Assistant: Hi there!"
    )
    assert prompt == expected


@pytest.mark.asyncio
async def test_ollama_chat_with_model_override() -> None:
    """Test Ollama chat with model override."""
    service = OllamaService(
        {"model": "llama3"},
        is_testing=True,
    )

    response = await service.chat(
        [LLMMessage(role="user", content="Hello")],
        model="mistral",
    )

    assert response.model == "mistral"


@pytest.mark.asyncio
async def test_ollama_async_client_creation() -> None:
    """Test async client is created properly."""
    service = OllamaService(
        {"ollama_url": "http://localhost:11434"},
        is_testing=False,
    )

    client = service.async_client
    assert client is not None
    assert client.base_url == "http://localhost:11434"
