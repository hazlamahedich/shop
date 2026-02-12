"""GLM-4.7 provider implementation (Zhipu AI, China market).

Uses Zhipu AI API for GLM models.
Pricing: glm-4-flash - ¥0.10/1M input, ¥0.10/1M output
"""

from __future__ import annotations

import asyncio
import json
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


class RateLimiter:
    """Token bucket rate limiter for API requests."""

    def __init__(self, requests_per_second: float = 2.0):
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests to allow per second
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until rate limit allows next request."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_request

            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                logger.debug(
                    "rate_limit_wait",
                    wait_seconds=wait_time,
                )
                await asyncio.sleep(wait_time)

            self.last_request = asyncio.get_event_loop().time()


# Shared rate limiter for all GLM requests (2 requests/sec = 120/min)
_glm_rate_limiter = RateLimiter(requests_per_second=2.0)


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

            await _glm_rate_limiter.acquire()

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

    async def _chat_with_retry(
        self,
        api_key: str,
        payload: Dict[str, Any],
        max_retries: int = 3,
    ) -> httpx.Response:
        """Execute chat request with exponential backoff retry.

        Args:
            api_key: GLM API key
            payload: Request payload
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            Successful HTTP response

        Raises:
            APIError: If all retries are exhausted
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                await _glm_rate_limiter.acquire()

                response = await self.async_client.post(
                    "/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                # Handle 429 Rate Limit Error specifically
                if response.status_code == 429:
                    error_data = response.json()
                    error_code = error_data.get("error", {}).get("code")
                    error_msg = error_data.get("error", {}).get("message", "Rate limit reached")

                    logger.warning(
                        "glm_rate_limited",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        error_code=error_code,
                        error_message=error_msg,
                    )

                    if attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s, ...
                        wait_time = (2 ** attempt) + 0.5  # 1.5s, 2.5s, 4.5s
                        logger.info(
                            "glm_retry_backoff",
                            wait_seconds=wait_time,
                            next_attempt=attempt + 2,
                        )
                        await asyncio.sleep(wait_time)
                        last_error = error_msg
                        continue
                    else:
                        raise APIError(
                            ErrorCode.LLM_RATE_LIMIT,
                            f"GLM rate limit exceeded after {max_retries} retries: {error_msg}",
                        )

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    continue  # Let the retry loop handle it
                raise

        # Should not reach here, but just in case
        raise APIError(
            ErrorCode.LLM_RATE_LIMIT,
            f"GLM request failed after {max_retries} retries. Last error: {last_error}",
        )

    async def chat(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Send chat completion to GLM-4.7 with automatic retry on rate limit."""
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

        if self.is_testing:
            return LLMResponse(
                content="Test response from GLM",
                tokens_used=10,
                model=model_name,
                provider="glm",
                metadata={"test": True},
            )

        try:
            response = await self._chat_with_retry(api_key, payload)
            data = response.json()

            # Extract response
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", input_tokens + completion_tokens)

            logger.info(
                "glm_chat_success",
                model=model_name,
                input_tokens=input_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

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

        except APIError:
            raise
        except Exception as e:
            logger.error(
                "glm_chat_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise APIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"GLM chat failed: {str(e)}",
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
