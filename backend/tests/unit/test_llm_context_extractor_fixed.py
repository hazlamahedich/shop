"""Unit tests for LLMContextExtractor fixes.

Story 11-3: Tests that LLMContextExtractor uses correct API
(chat() not generate(), LLMMessage objects, response.content).
"""

import pytest

from app.services.context.llm_context_extractor import LLMContextExtractor
from app.services.llm.base_llm_service import LLMMessage, LLMResponse


class MockLLMService:
    def __init__(self, response_content='{"categories": ["shoes"]}'):
        self.response_content = response_content
        self.last_messages = None
        self.last_temperature = None

    @property
    def provider_name(self):
        return "mock"

    async def test_connection(self):
        return True

    async def chat(self, messages, model=None, temperature=0.7, max_tokens=1000):
        self.last_messages = messages
        self.last_temperature = temperature
        return LLMResponse(
            content=self.response_content,
            tokens_used=50,
            model="mock-model",
            provider="mock",
        )

    def count_tokens(self, text):
        return len(text.split())


@pytest.fixture
def mock_llm():
    return MockLLMService()


@pytest.fixture
def extractor(mock_llm):
    return LLMContextExtractor(mock_llm)


class TestLLMContextExtractorAPI:
    @pytest.mark.asyncio
    async def test_passes_llm_message_objects(self, extractor, mock_llm):
        await extractor.extract("show me shoes", "ecommerce", {})
        assert mock_llm.last_messages is not None
        for msg in mock_llm.last_messages:
            assert isinstance(msg, LLMMessage)

    @pytest.mark.asyncio
    async def test_passes_system_and_user_roles(self, extractor, mock_llm):
        await extractor.extract("show me shoes", "ecommerce", {})
        roles = [m.role for m in mock_llm.last_messages]
        assert "system" in roles
        assert "user" in roles

    @pytest.mark.asyncio
    async def test_uses_low_temperature(self, extractor, mock_llm):
        await extractor.extract("show me shoes", "ecommerce", {})
        assert mock_llm.last_temperature == 0.1

    @pytest.mark.asyncio
    async def test_parses_json_response(self, extractor):
        result = await extractor.extract("show me shoes", "ecommerce", {})
        assert "categories" in result

    @pytest.mark.asyncio
    async def test_handles_markdown_json(self, mock_llm):
        mock_llm.response_content = '```json\n{"categories": ["boots"]}\n```'
        extractor = LLMContextExtractor(mock_llm)
        result = await extractor.extract("show me boots", "ecommerce", {})
        assert result.get("categories") == ["boots"]

    @pytest.mark.asyncio
    async def test_handles_general_mode(self, extractor, mock_llm):
        mock_llm.response_content = '{"topics": ["login"], "sentiment": "neutral"}'
        result = await extractor.extract("can't login", "general", {})
        assert "topics" in result

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self, mock_llm):
        class FailingLLM(MockLLMService):
            async def chat(self, messages, **kwargs):
                raise RuntimeError("LLM failed")

        extractor = LLMContextExtractor(FailingLLM())
        result = await extractor.extract("test", "ecommerce", {})
        assert result == {}

    @pytest.mark.asyncio
    async def test_passes_existing_context_in_prompt(self, extractor, mock_llm):
        await extractor.extract(
            "in blue",
            "ecommerce",
            {"categories": ["shoes"]},
        )
        user_msg = [m for m in mock_llm.last_messages if m.role == "user"][0]
        assert "shoes" in user_msg.content
