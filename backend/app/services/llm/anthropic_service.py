"""Anthropic provider implementation.

Uses Anthropic API for Claude models.
Pricing: claude-3-haiku - $0.25/1M input, $1.25/1M output
"""

from __future__ import annotations

from typing import Any
import httpx
import structlog

from app.services.llm.base_llm_service import (
    BaseLLMService,
    LLMMessage,
    LLMResponse,
)
from app.core.errors import APIError, ErrorCode


logger = structlog.get_logger(__name__)


class AnthropicService(BaseLLMService):
    """Anthropic provider implementation.

    Uses Anthropic API for Claude models.
    Pricing: claude-3-haiku - $0.25/1M input, $1.25/1M output
    """

    # Anthropic API endpoints
    ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

    # Default model
    DEFAULT_MODEL = "claude-3-haiku"

    # Pricing per 1M tokens (as of 2026-02)
    PRICING = {
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
        "claude-3-sonnet": {"input": 3.0, "output": 15.0},
    }

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client with testing support."""
        if self._async_client is None:
            if self.is_testing:
                from httpx import ASGITransport

                self._async_client = httpx.AsyncClient(
                    transport=ASGITransport(),
                    base_url="http://test",
                    timeout=30.0,
                )
            else:
                self._async_client = httpx.AsyncClient(
                    base_url=self.ANTHROPIC_API_URL,
                    timeout=60.0,
                )
        return self._async_client

    async def test_connection(self) -> bool:
        """Test Anthropic API connectivity with simple message."""
        try:
            if self.is_testing:
                return True

            api_key = self.config.get("api_key")
            if not api_key:
                return False

            response = await self.async_client.post(
                "/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.DEFAULT_MODEL,
                    "max_tokens": 10,
                    "messages": [{"role": "user", "content": "Hello"}],
                },
            )
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            logger.error(
                "anthropic_connection_failed",
                status_code=e.response.status_code,
                error=str(e),
            )
            return False

    async def chat(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Send chat completion to Anthropic."""
        api_key = self.config.get("api_key")
        if not api_key:
            raise APIError(
                ErrorCode.LLM_API_KEY_MISSING,
                "Anthropic API key not configured",
            )

        model_name = model or self.config.get("model", self.DEFAULT_MODEL)

        # Convert LLMMessage to Anthropic format
        anthropic_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": model_name,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            if self.is_testing:
                return LLMResponse(
                    content="Test response from Anthropic",
                    tokens_used=10,
                    model=model_name,
                    provider="anthropic",
                    metadata={"test": True},
                )

            response = await self.async_client.post(
                "/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            # Extract response
            content = data["content"][0]["text"]
            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

            return LLMResponse(
                content=content,
                tokens_used=total_tokens,
                model=model_name,
                provider="anthropic",
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "stop_reason": data.get("stop_reason"),
                },
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "anthropic_chat_failed",
                status_code=e.response.status_code,
                error=str(e),
            )
            raise APIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"Anthropic chat failed: {e.response.text}",
            )

    def count_tokens(self, text: str) -> int:
        """Approximate token count for Anthropic.

        Anthropic uses cl100k_base encoding similar to OpenAI.
        Approximately 4 characters per token.
        """
        return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for Anthropic."""
        model = self.config.get("model", self.DEFAULT_MODEL)
        pricing = self.PRICING.get(model, self.PRICING[self.DEFAULT_MODEL])

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost
