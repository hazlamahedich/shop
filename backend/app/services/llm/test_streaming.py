"""Tests for LLM streaming support (Story 11-1).

Tests stream_chat() implementations for:
- MockLLMService (simulated streaming)
- OpenAIService (SSE format parsing)
- AnthropicService (SSE format parsing)
- OllamaService (NDJSON format parsing)
- LLMRouter (streaming failover)
- BaseLLMService (default fallback to chat())
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.llm.anthropic_service import AnthropicService
from app.services.llm.base_llm_service import (
    BaseLLMService,
    LLMMessage,
    LLMResponse,
    StreamEvent,
)
from app.services.llm.llm_router import LLMRouter
from app.services.llm.mock_service import MockLLMService
from app.services.llm.ollama_service import OllamaService
from app.services.llm.openai_service import OpenAIService


class TestStreamEventModel:
    """Test StreamEvent data class."""

    def test_stream_event_creation(self) -> None:
        event = StreamEvent(type="token", content="hello")
        assert event.type == "token"
        assert event.content == "hello"
        assert event.metadata == {}

    def test_stream_event_with_metadata(self) -> None:
        event = StreamEvent(
            type="done",
            content="",
            metadata={"tokens_used": 50, "model": "gpt-4o-mini"},
        )
        assert event.type == "done"
        assert event.metadata["tokens_used"] == 50

    def test_stream_event_defaults(self) -> None:
        event = StreamEvent(type="token")
        assert event.content == ""
        assert event.metadata == {}


class TestMockServiceStreaming:
    """Test MockLLMService stream_chat()."""

    @pytest.mark.asyncio
    async def test_stream_yields_token_events(self) -> None:
        service = MockLLMService({}, is_testing=True)
        messages = [LLMMessage(role="user", content="hello")]

        events = []
        async for event in service.stream_chat(messages):
            events.append(event)

        token_events = [e for e in events if e.type == "token"]
        done_events = [e for e in events if e.type == "done"]

        assert len(token_events) > 0
        assert len(done_events) == 1

        full_content = "".join(e.content for e in token_events)
        assert "Hi there!" in full_content or "help" in full_content.lower()

    @pytest.mark.asyncio
    async def test_stream_done_event_has_metadata(self) -> None:
        service = MockLLMService({}, is_testing=True)
        messages = [LLMMessage(role="user", content="hello")]

        events = []
        async for event in service.stream_chat(messages):
            events.append(event)

        done_event = next(e for e in events if e.type == "done")
        assert done_event.metadata["tokens_used"] > 0
        assert done_event.metadata["model"] == "mock-model"
        assert done_event.metadata["provider"] == "mock"

    @pytest.mark.asyncio
    async def test_stream_classification_returns_json(self) -> None:
        service = MockLLMService({}, is_testing=True)
        messages = [
            LLMMessage(role="system", content="Classify the ecommerce intent"),
            LLMMessage(role="user", content="I want to buy shoes"),
        ]

        events = []
        async for event in service.stream_chat(messages):
            events.append(event)

        full_content = "".join(e.content for e in events if e.type == "token")
        assert "intent" in full_content

    @pytest.mark.asyncio
    async def test_stream_has_realistic_timing(self) -> None:
        service = MockLLMService({}, is_testing=True)
        messages = [LLMMessage(role="user", content="hello")]

        import time

        start = time.time()
        events = []
        async for event in service.stream_chat(messages):
            events.append(event)
        elapsed = time.time() - start

        assert elapsed > 0.02


class TestBaseServiceDefaultStreaming:
    """Test BaseLLMService default stream_chat() falls back to chat()."""

    @pytest.mark.asyncio
    async def test_default_stream_returns_single_token_event(self) -> None:
        class MinimalService(BaseLLMService):
            @property
            def provider_name(self) -> str:
                return "minimal"

            async def test_connection(self) -> bool:
                return True

            async def chat(self, messages, model=None, temperature=0.7, max_tokens=1000):
                return LLMResponse(
                    content="Hello world",
                    tokens_used=5,
                    model="test",
                    provider="minimal",
                )

            def count_tokens(self, text: str) -> int:
                return len(text) // 4

        service = MinimalService({})
        messages = [LLMMessage(role="user", content="hi")]

        events = []
        async for event in service.stream_chat(messages):
            events.append(event)

        assert len(events) == 1
        assert events[0].type == "token"
        assert events[0].content == "Hello world"
        assert events[0].metadata["tokens_used"] == 5


class TestOpenAIStreaming:
    """Test OpenAIService stream_chat() with mock HTTP."""

    @pytest.mark.asyncio
    async def test_stream_in_testing_mode(self) -> None:
        service = OpenAIService({"api_key": "test-key"}, is_testing=True)
        messages = [LLMMessage(role="user", content="Hello")]

        events = []
        async for event in service.stream_chat(messages):
            events.append(event)

        token_events = [e for e in events if e.type == "token"]
        done_events = [e for e in events if e.type == "done"]

        assert len(token_events) > 0
        assert len(done_events) == 1

        full_content = "".join(e.content for e in token_events)
        assert "OpenAI" in full_content

        done_event = done_events[0]
        assert done_event.metadata["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_stream_raises_without_api_key(self) -> None:
        service = OpenAIService({}, is_testing=False)
        messages = [LLMMessage(role="user", content="Hello")]

        with pytest.raises(Exception):
            async for _ in service.stream_chat(messages):
                pass


class TestAnthropicStreaming:
    """Test AnthropicService stream_chat() with mock HTTP."""

    @pytest.mark.asyncio
    async def test_stream_in_testing_mode(self) -> None:
        service = AnthropicService({"api_key": "test-key"}, is_testing=True)
        messages = [LLMMessage(role="user", content="Hello")]

        events = []
        async for event in service.stream_chat(messages):
            events.append(event)

        token_events = [e for e in events if e.type == "token"]
        done_events = [e for e in events if e.type == "done"]

        assert len(token_events) > 0
        assert len(done_events) == 1

        full_content = "".join(e.content for e in token_events)
        assert "Anthropic" in full_content

        done_event = done_events[0]
        assert done_event.metadata["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_stream_raises_without_api_key(self) -> None:
        service = AnthropicService({}, is_testing=False)
        messages = [LLMMessage(role="user", content="Hello")]

        with pytest.raises(Exception):
            async for _ in service.stream_chat(messages):
                pass


class TestOllamaStreaming:
    """Test OllamaService stream_chat() with mock HTTP."""

    @pytest.mark.asyncio
    async def test_stream_in_testing_mode(self) -> None:
        service = OllamaService({}, is_testing=True)
        messages = [LLMMessage(role="user", content="Hello")]

        events = []
        async for event in service.stream_chat(messages):
            events.append(event)

        token_events = [e for e in events if e.type == "token"]
        done_events = [e for e in events if e.type == "done"]

        assert len(token_events) > 0
        assert len(done_events) == 1

        full_content = "".join(e.content for e in token_events)
        assert "Ollama" in full_content

        done_event = done_events[0]
        assert done_event.metadata["provider"] == "ollama"


class TestLLMRouterStreaming:
    """Test LLMRouter stream_chat() with failover."""

    @pytest.mark.asyncio
    async def test_stream_through_primary(self) -> None:
        config = {
            "primary_provider": "ollama",
            "primary_config": {"ollama_url": "http://localhost:11434"},
        }

        with patch(
            "app.services.llm.llm_factory.LLMProviderFactory.create_provider"
        ) as mock_factory:
            primary_mock = AsyncMock()

            async def primary_stream(*args, **kwargs):
                yield StreamEvent(type="token", content="Hello ")
                yield StreamEvent(type="token", content="world")
                yield StreamEvent(
                    type="done",
                    content="",
                    metadata={"tokens_used": 10, "model": "llama3", "provider": "ollama"},
                )

            primary_mock.stream_chat = primary_stream

            mock_factory.return_value = primary_mock

            router = LLMRouter(config, is_testing=True)
            messages = [LLMMessage(role="user", content="Hello")]

            events = []
            async for event in router.stream_chat(messages):
                events.append(event)

            assert len(events) == 3
            done_event = next((e for e in events if e.type == "done"), None)
            assert done_event is not None
            assert done_event.metadata["tokens_used"] == 10

    @pytest.mark.asyncio
    async def test_stream_failover_to_backup(self) -> None:
        config = {
            "primary_provider": "ollama",
            "primary_config": {},
            "backup_provider": "openai",
            "backup_config": {"api_key": "test-key"},
        }

        with patch(
            "app.services.llm.llm_factory.LLMProviderFactory.create_provider"
        ) as mock_factory:
            primary_mock = AsyncMock()

            async def primary_fail(*args, **kwargs):
                raise Exception("Primary failed")
                yield

            primary_mock.stream_chat = primary_fail

            backup_mock = AsyncMock()

            async def backup_stream(*args, **kwargs):
                yield StreamEvent(type="token", content="Backup ")
                yield StreamEvent(type="token", content="response")
                yield StreamEvent(
                    type="done",
                    content="",
                    metadata={"tokens_used": 10, "model": "gpt-4o-mini", "provider": "openai"},
                )

            backup_mock.stream_chat = backup_stream

            def create_provider_side_effect(provider_name, cfg, is_testing=False):
                if provider_name == "ollama":
                    return primary_mock
                return backup_mock

            mock_factory.side_effect = create_provider_side_effect

            router = LLMRouter(config, is_testing=True)
            messages = [LLMMessage(role="user", content="Test")]

            events = []
            async for event in router.stream_chat(messages):
                events.append(event)

            full_content = "".join(e.content for e in events if e.type == "token")
            assert full_content == "Backup response"

    @pytest.mark.asyncio
    async def test_stream_both_fail_raises_error(self) -> None:
        config = {
            "primary_provider": "ollama",
            "primary_config": {},
            "backup_provider": "openai",
            "backup_config": {"api_key": "test-key"},
        }

        with patch(
            "app.services.llm.llm_factory.LLMProviderFactory.create_provider"
        ) as mock_factory:
            primary_mock = AsyncMock()

            async def primary_fail(*args, **kwargs):
                raise Exception("Primary failed")
                yield

            primary_mock.stream_chat = primary_fail

            backup_mock = AsyncMock()

            async def backup_fail(*args, **kwargs):
                raise Exception("Backup failed")
                yield

            backup_mock.stream_chat = backup_fail

            def create_provider_side_effect(provider_name, cfg, is_testing=False):
                if provider_name == "ollama":
                    return primary_mock
                return backup_mock

            mock_factory.side_effect = create_provider_side_effect

            router = LLMRouter(config, is_testing=True)
            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(Exception) as exc_info:
                async for _ in router.stream_chat(messages):
                    pass

            assert "failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_stream_force_backup(self) -> None:
        config = {
            "primary_provider": "ollama",
            "primary_config": {},
            "backup_provider": "openai",
            "backup_config": {"api_key": "test-key"},
        }

        with patch(
            "app.services.llm.llm_factory.LLMProviderFactory.create_provider"
        ) as mock_factory:
            backup_mock = AsyncMock()

            async def backup_stream(*args, **kwargs):
                yield StreamEvent(type="token", content="Hello from backup")
                yield StreamEvent(
                    type="done",
                    content="",
                    metadata={"tokens_used": 5, "model": "gpt-4o-mini", "provider": "openai"},
                )

            backup_mock.stream_chat = backup_stream

            def create_provider_side_effect(provider_name, cfg, is_testing=False):
                return backup_mock

            mock_factory.side_effect = create_provider_side_effect

            router = LLMRouter(config, is_testing=True)
            messages = [LLMMessage(role="user", content="Hello")]

            events = []
            async for event in router.stream_chat(messages, use_backup=True):
                events.append(event)

            assert len(events) > 0
