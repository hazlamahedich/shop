"""Abstract base class for LLM providers.

All LLM providers must implement these methods to ensure
consistent interface across providers for easy switching and
automatic failover.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Standardized message format for all LLM providers."""

    role: str  # "system", "user", "assistant"
    content: str


class LLMResponse(BaseModel):
    """Standardized response format from all LLM providers."""

    content: str
    tokens_used: int
    model: str
    provider: str
    metadata: dict[str, Any] = {}


class StreamEvent(BaseModel):
    """Event emitted during streaming chat completion."""

    type: str
    content: str = ""
    metadata: dict[str, Any] = {}


class BaseLLMService(ABC):
    """Abstract base class for LLM providers.

    All LLM providers must implement these methods to ensure
    consistent interface across providers.
    """

    def __init__(self, config: dict[str, Any], is_testing: bool = False) -> None:
        """Initialize LLM service with configuration.

        Args:
            config: Provider-specific configuration
                - api_key: API key for cloud providers
                - model: Model ID to use
                - pricing: Dict with 'input' and 'output' prices per million tokens
            is_testing: Force mock responses (IS_TESTING pattern)
        """
        self.config = config
        self.is_testing = is_testing
        self._async_client = None

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name (e.g., 'ollama', 'openai')."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test LLM connectivity with simple prompt.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Send chat completion request to LLM provider.

        Args:
            messages: Conversation history
            model: Model override (optional)
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response

        Returns:
            LLM response with content and metadata
        """
        pass

    async def stream_chat(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream chat completion tokens from LLM provider.

        Default implementation falls back to non-streaming chat()
        and yields the full response as a single token event.

        Providers that support streaming should override this method
        to yield StreamEvent objects as tokens arrive.

        Args:
            messages: Conversation history
            model: Model override (optional)
            temperature: Response randomness (0.0-1.0)
            max_tokens: Maximum tokens in response

        Yields:
            StreamEvent objects with incremental content
        """
        response = await self.chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        yield StreamEvent(
            type="token",
            content=response.content,
            metadata={
                "tokens_used": response.tokens_used,
                "model": response.model,
                "provider": response.provider,
            },
        )

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text (approximate for most providers).

        Args:
            text: Text to count

        Returns:
            Estimated token count
        """
        pass

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for token usage.

        Uses pricing from config (passed during provider creation).
        Falls back to 0 if pricing not available.

        Args:
            input_tokens: Input prompt tokens
            output_tokens: Completion tokens

        Returns:
            Estimated cost in USD
        """
        pricing = self.config.get("pricing", {})
        input_price = pricing.get("input", 0.0)
        output_price = pricing.get("output", 0.0)

        input_cost = (input_tokens / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * output_price

        return input_cost + output_cost

    async def health_check(self) -> dict[str, Any]:
        """Perform health check and return status.

        Returns:
            Health status dict with provider, status, latency, etc.
        """
        import time

        start = time.time()
        is_healthy = await self.test_connection()
        latency = time.time() - start

        return {
            "provider": self.provider_name,
            "status": "healthy" if is_healthy else "unhealthy",
            "latency_ms": round(latency * 1000, 2),
            "model": self.config.get("model", "default"),
        }
