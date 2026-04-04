"""Unit tests for ContextSummarizerService.summarize_for_customer (Story 11-9 P1).

Direct tests for the customer-facing summarization method and its helpers.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.context_summarizer import ContextSummarizerService


def _make_context_dict(
    customer_turns: int = 5,
    bot_turns: int | None = None,
) -> dict:
    if bot_turns is None:
        bot_turns = customer_turns
    history = []
    for i in range(customer_turns):
        history.append({"role": "customer", "content": f"Customer message {i}"})
    for i in range(bot_turns):
        history.append({"role": "bot", "content": f"Bot response {i}"})
    return {
        "conversation_history": history,
        "session_id": "test-session-123",
    }


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_llm():
    service = AsyncMock()
    service.chat = AsyncMock(return_value=MagicMock(content="## Summary\n\n- Item 1\n- Item 2"))
    return service


@pytest.fixture
def service(mock_db, mock_llm):
    return ContextSummarizerService(db=mock_db, llm_service=mock_llm)


class TestGetCustomerSystemPrompt:
    """Verify system prompt content for both modes."""

    def test_ecommerce_prompt_contains_sections(self, service):
        prompt = service._get_customer_system_prompt("ecommerce")
        assert "Products Discussed" in prompt
        assert "Preferences" in prompt
        assert "Cart Status" in prompt
        assert "Next Steps" in prompt
        assert "markdown" in prompt.lower()

    def test_general_prompt_contains_sections(self, service):
        prompt = service._get_customer_system_prompt("general")
        assert "Topics Covered" in prompt
        assert "Documents Referenced" in prompt
        assert "Issues" in prompt
        assert "Open Items" in prompt
        assert "markdown" in prompt.lower()

    def test_unknown_mode_defaults_to_general(self, service):
        prompt = service._get_customer_system_prompt("unknown_mode")
        assert "Topics Covered" in prompt


class TestBuildUserPrompt:
    """Verify user prompt includes conversation context."""

    def test_user_prompt_contains_history(self, service):
        context_dict = _make_context_dict(customer_turns=3)
        prompt = service._build_user_prompt(context_dict, "ecommerce")
        assert "Customer message" in prompt

    def test_user_prompt_ecommerce_mode(self, service):
        context_dict = _make_context_dict(customer_turns=2)
        prompt = service._build_user_prompt(context_dict, "ecommerce")
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_user_prompt_general_mode(self, service):
        context_dict = _make_context_dict(customer_turns=2)
        prompt = service._build_user_prompt(context_dict, "general")
        assert isinstance(prompt, str)
        assert len(prompt) > 0


class TestSummarizeForCustomer:
    """Test the main summarize_for_customer method."""

    @pytest.mark.asyncio
    async def test_ecommerce_mode_returns_summary(self, service, mock_llm):
        context_dict = _make_context_dict(customer_turns=5)
        result = await service.summarize_for_customer(
            context_dict=context_dict,
            mode="ecommerce",
            conversation_id="test-conv-123",
        )
        assert isinstance(result, str)
        assert len(result) > 0
        mock_llm.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_general_mode_returns_summary(self, service, mock_llm):
        context_dict = _make_context_dict(customer_turns=4)
        result = await service.summarize_for_customer(
            context_dict=context_dict,
            mode="general",
            conversation_id="test-conv-456",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_llm_failure_uses_fallback(self, service, mock_llm):
        mock_llm.chat = AsyncMock(side_effect=Exception("LLM timeout"))
        context_dict = _make_context_dict(customer_turns=5)
        result = await service.summarize_for_customer(
            context_dict=context_dict,
            mode="ecommerce",
            conversation_id="test-conv-789",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_empty_history_returns_fallback(self, service, mock_llm):
        context_dict = {"conversation_history": []}
        result = await service.summarize_for_customer(
            context_dict=context_dict,
            mode="ecommerce",
            conversation_id="test-conv-empty",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_llm_called_with_correct_params(self, service, mock_llm):
        context_dict = _make_context_dict(customer_turns=3)
        await service.summarize_for_customer(
            context_dict=context_dict,
            mode="ecommerce",
            conversation_id="test-conv-params",
        )
        call_args = mock_llm.chat.call_args
        messages = call_args[0][0] if call_args[0] else call_args.kwargs.get("messages", [])
        assert any("system" in str(m.role).lower() for m in messages)
        assert any("user" in str(m.role).lower() for m in messages)


class TestFallbackCustomerSummary:
    """Test the _fallback_customer_summary method."""

    def test_ecommerce_mode_with_history(self, service):
        context_dict = _make_context_dict(customer_turns=3)
        result = service._fallback_customer_summary(context_dict, "ecommerce")
        assert "Summary" in result
        assert "Customer message" in result

    def test_general_mode_with_history(self, service):
        context_dict = _make_context_dict(customer_turns=3)
        result = service._fallback_customer_summary(context_dict, "general")
        assert "Topics Covered" in result
        assert "Customer message" in result

    def test_empty_history(self, service):
        context_dict = {"conversation_history": []}
        result = service._fallback_customer_summary(context_dict, "ecommerce")
        assert "No conversation history" in result

    def test_no_history_key(self, service):
        result = service._fallback_customer_summary({}, "ecommerce")
        assert "No conversation history" in result

    def test_malformed_messages_handled_gracefully(self, service):
        context_dict = {
            "conversation_history": [
                {"role": "customer"},
                {"content": "orphan content"},
                None,
            ]
        }
        result = service._fallback_customer_summary(context_dict, "ecommerce")
        assert isinstance(result, str)
