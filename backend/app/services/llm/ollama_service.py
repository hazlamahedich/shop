"""Ollama provider implementation (local, free).

Ollama runs locally on the merchant's server providing:
- Zero API costs
- Privacy (data never leaves the server)
- Multiple open-source models (Llama, Mistral, Qwen, etc.)
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


class OllamaService(BaseLLMService):
    """Ollama provider implementation (local, free).

    Pricing: $0.00 (local hosting)
    Default Model: llama3
    """

    # Default model
    DEFAULT_MODEL = "llama3"

    # Pricing: Ollama is free
    PRICING = {"input": 0.0, "output": 0.0}

    @property
    def provider_name(self) -> str:
        return "ollama"

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
                ollama_url = self.config.get("ollama_url", "http://localhost:11434")
                self._async_client = httpx.AsyncClient(
                    base_url=ollama_url,
                    timeout=60.0,  # Ollama can be slow on first request
                )
        return self._async_client

    async def test_connection(self) -> bool:
        """Test Ollama connectivity by fetching available models."""
        try:
            if self.is_testing:
                return True

            response = await self.async_client.get("/api/tags")
            response.raise_for_status()
            data = response.json()

            # Check if models are available
            models = data.get("models", [])
            return len(models) > 0

        except httpx.HTTPError as e:
            logger.error("ollama_connection_failed", error=str(e))
            return False

    async def chat(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Send chat completion to Ollama.

        Ollama uses /api/generate endpoint with streaming disabled.
        """
        model_name = model or self.config.get("model", self.DEFAULT_MODEL)

        # Build prompt from messages
        prompt = self._build_prompt(messages)

        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,  # Disable streaming for simplicity
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            if self.is_testing:
                return LLMResponse(
                    content="Test response from Ollama",
                    tokens_used=10,
                    model=model_name,
                    provider="ollama",
                    metadata={"test": True},
                )

            response = await self.async_client.post(
                "/api/generate",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            # Extract response
            content = data.get("response", "")
            prompt_eval_count = data.get("prompt_eval_count", 0)
            eval_count = data.get("eval_count", 0)
            total_tokens = prompt_eval_count + eval_count

            return LLMResponse(
                content=content,
                tokens_used=total_tokens,
                model=model_name,
                provider="ollama",
                metadata={
                    "prompt_eval_count": prompt_eval_count,
                    "eval_count": eval_count,
                },
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "ollama_chat_failed",
                error=str(e),
                response=e.response.text,
            )
            raise APIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"Ollama chat failed: {e.response.text}",
            )

    def _build_prompt(self, messages: list[LLMMessage]) -> str:
        """Build prompt from message history.

        Ollama expects a simple string prompt, not message array.
        """
        prompt_parts = []
        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"System: {msg.content}")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}")

        return "\n".join(prompt_parts)

    def count_tokens(self, text: str) -> int:
        """Approximate token count for Ollama.

        Ollama uses tokenization similar to LLaMA,
        approximately 4 characters per token.
        """
        return len(text) // 4

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Ollama is free (local hosting)."""
        return 0.0
