"""Tests for LLM mock providers."""

import pytest

from tests.fixtures.mock_llm import (
    LLMResponse,
    MockLLMProvider,
    MockOllamaProvider,
    MockOpenAIProvider,
    MockAnthropicProvider,
    MockGeminiProvider,
    MockGLMProvider,
    get_mock_llm,
)


class TestLLMResponse:
    """Test LLM response data structure."""

    def test_llm_response_creation(self):
        """Test creating an LLM response."""
        response = LLMResponse(
            intent="product_search",
            confidence=0.95,
            extracted_params={"category": "shoes"},
            raw_response="Showing shoes"
        )

        assert response.intent == "product_search"
        assert response.confidence == 0.95
        assert response.extracted_params["category"] == "shoes"
        assert response.raw_response == "Showing shoes"


class TestMockLLMProvider:
    """Test base mock LLM provider."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test provider initialization."""
        provider = MockLLMProvider("test")
        assert provider.provider == "test"
        assert provider.call_count == 0

    @pytest.mark.asyncio
    async def test_chat_returns_response(self):
        """Test that chat returns LLMResponse."""
        provider = MockLLMProvider("test")
        response = await provider.chat("I want to buy shoes")

        assert isinstance(response, LLMResponse)
        assert response.intent is not None
        assert response.confidence >= 0
        assert response.raw_response is not None

    @pytest.mark.asyncio
    async def test_intent_detection_checkout(self):
        """Test detecting checkout intent."""
        provider = MockLLMProvider("test")
        response = await provider.chat("I want to checkout now")

        assert response.intent == "checkout"
        assert response.confidence > 0.9

    @pytest.mark.asyncio
    async def test_intent_detection_order_tracking(self):
        """Test detecting order tracking intent."""
        provider = MockLLMProvider("test")
        response = await provider.chat("Where is my order")

        assert response.intent == "order_tracking"

    @pytest.mark.asyncio
    async def test_intent_detection_human_handoff(self):
        """Test detecting human handoff intent."""
        provider = MockLLMProvider("test")
        response = await provider.chat("I want to speak to a human")

        assert response.intent == "human_handoff"
        assert response.confidence > 0.9

    @pytest.mark.asyncio
    async def test_product_search_with_constraints(self):
        """Test product search with constraints extraction."""
        provider = MockLLMProvider("test")
        response = await provider.chat("Show me shoes under $100 size 8")

        assert response.intent == "product_search"
        assert response.confidence > 0.9
        assert response.extracted_params["budget"] == 100
        assert response.extracted_params["size"] == "8"

    @pytest.mark.asyncio
    async def test_vague_query_triggers_clarification(self):
        """Test vague query triggers low confidence."""
        provider = MockLLMProvider("test")
        response = await provider.chat("I want shoes")

        assert response.intent == "product_search"
        assert response.confidence < 0.8  # Should trigger clarification

    @pytest.mark.asyncio
    async def test_call_count_increments(self):
        """Test that call count increments."""
        provider = MockLLMProvider("test")
        assert provider.call_count == 0

        await provider.chat("test")
        assert provider.call_count == 1

        await provider.chat("test2")
        assert provider.call_count == 2

    @pytest.mark.asyncio
    async def test_stream_returns_generator(self):
        """Test that stream is a generator."""
        provider = MockLLMProvider("test")
        stream = provider.stream("test message")

        # Should be async generator
        assert hasattr(stream, "__aiter__")

        async for chunk in stream:
            assert isinstance(chunk, str)
            break  # Only need first chunk

    @pytest.mark.asyncio
    async def test_reset_clears_call_count(self):
        """Test that reset clears call count."""
        provider = MockLLMProvider("test")
        await provider.chat("test")
        assert provider.call_count == 1

        provider.reset()
        assert provider.call_count == 0


class TestProviderSpecificMocks:
    """Test provider-specific mock classes."""

    @pytest.mark.asyncio
    async def test_ollama_provider(self):
        """Test Ollama-specific mock."""
        provider = MockOllamaProvider()
        assert provider.provider == "ollama"

        response = await provider.chat("test")
        assert isinstance(response, LLMResponse)

    @pytest.mark.asyncio
    async def test_openai_provider(self):
        """Test OpenAI-specific mock."""
        provider = MockOpenAIProvider()
        assert provider.provider == "openai"

        response = await provider.chat("test")
        assert isinstance(response, LLMResponse)

    @pytest.mark.asyncio
    async def test_anthropic_provider(self):
        """Test Anthropic-specific mock."""
        provider = MockAnthropicProvider()
        assert provider.provider == "anthropic"

        response = await provider.chat("test")
        assert isinstance(response, LLMResponse)

    @pytest.mark.asyncio
    async def test_gemini_provider(self):
        """Test Gemini-specific mock."""
        provider = MockGeminiProvider()
        assert provider.provider == "gemini"

        response = await provider.chat("test")
        assert isinstance(response, LLMResponse)

    @pytest.mark.asyncio
    async def test_glm_provider(self):
        """Test GLM-4.7-specific mock."""
        provider = MockGLMProvider()
        assert provider.provider == "glm-4.7"

        response = await provider.chat("test")
        assert isinstance(response, LLMResponse)


class TestMockLLMFactory:
    """Test mock LLM factory function."""

    @pytest.mark.asyncio
    async def test_get_mock_llm_default(self):
        """Test factory with unknown provider."""
        provider = get_mock_llm("unknown")
        assert isinstance(provider, MockLLMProvider)

    @pytest.mark.asyncio
    async def test_get_mock_llm_ollama(self):
        """Test factory returns Ollama mock."""
        provider = get_mock_llm("ollama")
        assert isinstance(provider, MockOllamaProvider)

    @pytest.mark.asyncio
    async def test_get_mock_llm_openai(self):
        """Test factory returns OpenAI mock."""
        provider = get_mock_llm("openai")
        assert isinstance(provider, MockOpenAIProvider)

    @pytest.mark.asyncio
    async def test_get_mock_llm_anthropic(self):
        """Test factory returns Anthropic mock."""
        provider = get_mock_llm("anthropic")
        assert isinstance(provider, MockAnthropicProvider)

    @pytest.mark.asyncio
    async def test_get_mock_llm_gemini(self):
        """Test factory returns Gemini mock."""
        provider = get_mock_llm("gemini")
        assert isinstance(provider, MockGeminiProvider)

    @pytest.mark.asyncio
    async def test_get_mock_llm_glm(self):
        """Test factory returns GLM mock."""
        provider = get_mock_llm("glm-4.7")
        assert isinstance(provider, MockGLMProvider)
