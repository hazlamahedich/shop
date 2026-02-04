"""GLM-4.7 provider implementation (Zhipu AI, China market).

Uses Zhipu AI API for GLM models.
Pricing: glm-4-flash - ¥0.10/1M input, ¥0.10/1M output
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import httpx
import structlog

from app.services.llm.base_llm_service import (
    BaseLLMService,
    LLMMessage,
    LLMResponse,
)
from app.core.errors import APIError, ErrorCode


logger = structlog.get_logger(__name__)


class GLMService(BaseLLMService):
    """GLM-4.7 provider implementation (China market).

    Uses Zhipu AI API for GLM models.
    Pricing: glm-4-flash - ¥0.10/1M input, ¥0.10/1M output
    """

    # GLM API endpoints
    GLM_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    # Default model
    DEFAULT_MODEL = "glm-4-flash"

    # Pricing per 1M tokens (as of 2026-02) in CNY
    PRICING = {
        "glm-4-flash": {"input": 0.10, "output": 0.10},
        "glm-4-plus": {"input": 0.50, "output": 0.50},
    }

    # CNY to USD conversion rate (approximately)
    USD_RATE = 1.0 / 7.0

    @property
    def provider_name(self) -> str:
        return "glm"

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
                    base_url=self.GLM_API_URL,
                    timeout=60.0,
                )
        return self._async_client

    async def test_connection(self) -> bool:
        """Test GLM API connectivity with simple message."""
        try:
            if self.is_testing:
                return True

            api_key = self.config.get("api_key")
            if not api_key:
                return False

            response = await self.async_client.post(
                "/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.DEFAULT_MODEL,
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 10,
                },
            )
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            logger.error(
                "glm_connection_failed",
                status_code=e.response.status_code,
                error=str(e),
            )
            return False

    async def chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Send chat completion to GLM-4.7."""
        api_key = self.config.get("api_key")
        if not api_key:
            raise APIError(
                ErrorCode.LLM_API_KEY_MISSING,
                "GLM API key not configured",
            )

        model_name = model or self.config.get("model", self.DEFAULT_MODEL)

        # Convert LLMMessage to GLM format
        glm_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

        payload = {
            "model": model_name,
            "messages": glm_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            if self.is_testing:
                return LLMResponse(
                    content="Test response from GLM",
                    tokens_used=10,
                    model=model_name,
                    provider="glm",
                    metadata={"test": True},
                )

            response = await self.async_client.post(
                "/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            # Extract response
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", input_tokens + completion_tokens)

            return LLMResponse(
                content=content,
                tokens_used=total_tokens,
                model=model_name,
                provider="glm",
                metadata={
                    "input_tokens": input_tokens,
                    "completion_tokens": completion_tokens,
                    "finish_reason": data["choices"][0].get("finish_reason"),
                },
            )

        except httpx.HTTPStatusError as e:
            logger.error(
                "glm_chat_failed",
                status_code=e.response.status_code,
                error=str(e),
            )
            raise APIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"GLM chat failed: {e.response.text}",
            )

    def count_tokens(self, text: str) -> int:
        """Approximate token count for GLM.

        GLM uses tokenization similar to Chinese models.
        Approximately 3 characters per token.
        """
        return len(text) // 3

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for GLM."""
        model = self.config.get("model", self.DEFAULT_MODEL)
        pricing = self.PRICING.get(model, self.PRICING[self.DEFAULT_MODEL])

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        # Convert CNY to USD
        return (input_cost + output_cost) * self.USD_RATE
