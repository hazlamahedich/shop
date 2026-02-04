"""Abstract base class for LLM providers.

All LLM providers must implement these methods to ensure
consistent interface across providers for easy switching and
automatic failover.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
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
    metadata: Dict[str, Any] = {}


class BaseLLMService(ABC):
    """Abstract base class for LLM providers.

    All LLM providers must implement these methods to ensure
    consistent interface across providers.
    """

    def __init__(self, config: Dict[str, Any], is_testing: bool = False) -> None:
        """Initialize LLM service with configuration.

        Args:
            config: Provider-specific configuration
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
        messages: List[LLMMessage],
        model: Optional[str] = None,
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

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text (approximate for most providers).

        Args:
            text: Text to count

        Returns:
            Estimated token count
        """
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for token usage.

        Args:
            input_tokens: Input prompt tokens
            output_tokens: Completion tokens

        Returns:
            Estimated cost in USD
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
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
