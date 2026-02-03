"""OpenAI provider implementation.

Uses OpenAI API for GPT models.
Pricing: gpt-4o-mini - $0.15/1M input, $0.60/1M output
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


class OpenAIService(BaseLLMService):
    """OpenAI provider implementation.

    Uses OpenAI API for GPT models.
    Pricing: gpt-4o-mini - $0.15/1M input, $0.60/1M output
    """

    # OpenAI API endpoints
    OPENAI_API_URL = "https://api.openai.com/v1"

    # Default model
    DEFAULT_MODEL = "gpt-4o-mini"

    # Pricing per 1M tokens (as of 2026-02)
    PRICING = {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4o": {"input": 2.50, "output": 10.0},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }

    @property
    def provider_name(self) -> str:
        return "openai"

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
                    base_url=self.OPENAI_API_URL,
                    timeout=60.0,
                    headers={
                        "Authorization": f"Bearer {self.config.get('api_key')}",
                        "Content-Type": "application/json",
                    },
                )
        return self._async_client

    async def test_connection(self) -> bool:
        """Test OpenAI API connectivity with simple message."""
        try:
            if self.is_testing:
                return True

            api_key = self.config.get("api_key")
            if not api_key:
                return False

            response = await self.async_client.post(
                "/chat/completions",
                json={
                    "model": self.DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 5,
                },
            )
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            logger.error(
                "openai_connection_failed",
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
        """Send chat completion to OpenAI."""
        api_key = self.config.get("api_key")
        if not api_key:
            raise APIError(
                ErrorCode.LLM_API_KEY_MISSING,
                "OpenAI API key not configured",
            )

        model_name = model or self.config.get("model", self.DEFAULT_MODEL)

        # Convert LLMMessage to OpenAI format
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": model_name,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            if self.is_testing:
                return LLMResponse(
                    content="Test response from OpenAI",
                    tokens_used=10,
                    model=model_name,
                    provider="openai",
                    metadata={"test": True},
                )

            response = await self.async_client.post(
                "/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            # Extract response
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", input_tokens + output_tokens)

            return LLMResponse(
                content=content,
                tokens_used=total_tokens,
                model=model_name,
                provider="openai",
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "finish_reason": data["choices"][0].get("finish_reason"),
                },
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "openai_chat_failed",
                status_code=e.response.status_code,
                error=str(e),
            )
            raise APIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"OpenAI chat failed: {e.response.text}",
            )

    def count_tokens(self, text: str) -> int:
        """Approximate token count for OpenAI.

        OpenAI uses cl100k_base encoding.
        Approximately 4 characters per token.
        """
        return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for OpenAI."""
        model = self.config.get("model", self.DEFAULT_MODEL)
        pricing = self.PRICING.get(model, self.PRICING[self.DEFAULT_MODEL])

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost
