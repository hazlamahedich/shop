"""Tests for LLM base service and data classes."""

from __future__ import annotations

import pytest

from app.services.llm.base_llm_service import LLMMessage, LLMResponse


def test_llm_message_creation() -> None:
    """Test creating LLM message."""
    message = LLMMessage(role="user", content="Hello, world!")
    assert message.role == "user"
    assert message.content == "Hello, world!"


def test_llm_message_system_role() -> None:
    """Test creating system message."""
    message = LLMMessage(
        role="system",
        content="You are a helpful assistant.",
    )
    assert message.role == "system"
    assert "helpful assistant" in message.content


def test_llm_response_creation() -> None:
    """Test creating LLM response."""
    response = LLMResponse(
        content="Test response",
        tokens_used=10,
        model="gpt-4o-mini",
        provider="openai",
        metadata={"finish_reason": "stop"},
    )
    assert response.content == "Test response"
    assert response.tokens_used == 10
    assert response.model == "gpt-4o-mini"
    assert response.provider == "openai"
    assert response.metadata["finish_reason"] == "stop"


def test_llm_response_metadata_defaults() -> None:
    """Test LLM response metadata defaults to empty dict."""
    response = LLMResponse(
        content="Test",
        tokens_used=5,
        model="test-model",
        provider="test",
    )
    assert response.metadata == {}


@pytest.mark.asyncio
async def test_abstract_methods_required() -> None:
    """Test that abstract methods must be implemented."""

    from app.services.llm.base_llm_service import BaseLLMService

    # Attempting to create a class without implementing abstract methods should fail
    with pytest.raises(TypeError):
        class IncompleteService(BaseLLMService):
            @property
            def provider_name(self) -> str:
                return "test"
            # Missing required abstract methods

        IncompleteService({}, is_testing=False)
