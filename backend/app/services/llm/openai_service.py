"""OpenAI provider implementation.

Uses OpenAI API for GPT models.
Pricing fetched dynamically from OpenRouter via ModelDiscoveryService.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

import httpx
import structlog

from app.core.errors import APIError, ErrorCode
from app.services.llm.base_llm_service import (
    BaseLLMService,
    LLMMessage,
    LLMResponse,
    StreamEvent,
)

logger = structlog.get_logger(__name__)


class OpenAIService(BaseLLMService):
    """OpenAI provider implementation.

    Uses OpenAI API for GPT models.
    Pricing fetched dynamically from config (via ModelDiscoveryService).
    """

    OPENAI_API_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o-mini"

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
        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

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

    async def stream_chat(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream chat completion tokens from OpenAI.

        Uses OpenAI's streaming API with SSE response format.
        Each chunk contains choices[0].delta.content with incremental text.
        The final chunk includes usage data when available.
        """
        api_key = self.config.get("api_key")
        if not api_key:
            raise APIError(
                ErrorCode.LLM_API_KEY_MISSING,
                "OpenAI API key not configured",
            )

        model_name = model or self.config.get("model", self.DEFAULT_MODEL)

        if self.is_testing:
            full_text = "Test streaming response from OpenAI"
            words = full_text.split()
            for i, word in enumerate(words):
                token = word if i == 0 else " " + word
                yield StreamEvent(type="token", content=token)
            yield StreamEvent(
                type="done",
                content="",
                metadata={
                    "tokens_used": 10,
                    "model": model_name,
                    "provider": "openai",
                },
            )
            return

        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        payload = {
            "model": model_name,
            "messages": openai_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with self.async_client.stream(
                "POST",
                f"{self.OPENAI_API_URL}/chat/completions",
                json=payload,
                headers=headers,
                timeout=60.0,
            ) as response:
                response.raise_for_status()

                usage_data = {}
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        yield StreamEvent(type="token", content=content)

                    chunk_usage = chunk.get("usage")
                    if chunk_usage:
                        usage_data = chunk_usage

            yield StreamEvent(
                type="done",
                content="",
                metadata={
                    "tokens_used": usage_data.get(
                        "total_tokens",
                        usage_data.get("prompt_tokens", 0) + usage_data.get("completion_tokens", 0),
                    ),
                    "input_tokens": usage_data.get("prompt_tokens", 0),
                    "output_tokens": usage_data.get("completion_tokens", 0),
                    "model": model_name,
                    "provider": "openai",
                },
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "openai_stream_failed",
                status_code=e.response.status_code,
                error=str(e),
            )
            raise APIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"OpenAI streaming failed: {e.response.text}",
            )

    def count_tokens(self, text: str) -> int:
        """Approximate token count for OpenAI.

        OpenAI uses cl100k_base encoding.
        Approximately 4 characters per token.
        """
        return len(text) // 4
