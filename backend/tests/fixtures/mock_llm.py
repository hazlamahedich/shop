"""LLM Provider Test Doubles for deterministic testing.

This module provides mock LLM providers that return deterministic responses
based on prompt keywords. All real LLM providers should be replaced with these
doubles in tests via the IS_TESTING environment variable.

Response Schema:
- intent: Primary intent (product_search, checkout, order_status, etc.)
- confidence: Float 0-1 (0.95+ = high confidence, <0.80 = need clarification)
- extracted_params: Dict of extracted constraints (budget, size, category, etc.)
- raw_response: Simulated LLM text response
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    """Structured LLM response matching real provider interface."""

    intent: str
    confidence: float
    extracted_params: dict[str, Any]
    raw_response: str


class MockLLMProvider:
    """Deterministic test double for LLM providers.

    This mock returns predefined responses based on prompt keywords,
    enabling deterministic testing without calling real LLM APIs.

    Usage:
        ```python
        from backend.app.core.config import is_testing
        from backend.tests.fixtures.mock_llm import MockLLMProvider

        def get_llm_service():
            if is_testing():
                return MockLLMProvider(provider="test")
            return RealLLMProvider(...)
        ```
    """

    PREDEFINED_RESPONSES = {
        "product_search_simple": LLMResponse(
            intent="product_search",
            confidence=0.95,
            extracted_params={"category": "shoes", "budget": 100, "size": "8"},
            raw_response="Showing shoes under $100, size 8",
        ),
        "product_search_vague": LLMResponse(
            intent="product_search",
            confidence=0.65,  # Triggers clarification
            extracted_params={"category": "shoes"},
            raw_response="What's your budget and shoe size?",
        ),
        "checkout_request": LLMResponse(
            intent="checkout",
            confidence=0.98,
            extracted_params={},
            raw_response="Generating checkout link...",
        ),
        "order_status": LLMResponse(
            intent="order_tracking",
            confidence=0.92,
            extracted_params={"order_id": "12345"},
            raw_response="Checking order status...",
        ),
        "human_handoff": LLMResponse(
            intent="human_handoff",
            confidence=0.99,
            extracted_params={"reason": "explicit_request"},
            raw_response="Connecting you to a human agent...",
        ),
        "add_to_cart": LLMResponse(
            intent="add_to_cart",
            confidence=0.97,
            extracted_params={"product_id": "123", "quantity": 1},
            raw_response="Added to cart",
        ),
        "view_cart": LLMResponse(
            intent="view_cart",
            confidence=0.99,
            extracted_params={},
            raw_response="Showing cart contents",
        ),
    }

    def __init__(self, provider: str) -> None:
        """Initialize mock provider.

        Args:
            provider: Provider name for logging (ollama, openai, etc.)
        """
        self.provider = provider
        self.call_count = 0

    async def chat(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Return deterministic response based on prompt keywords.

        Args:
            prompt: User message or prompt
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with deterministic intent and parameters
        """
        self.call_count += 1
        prompt_lower = prompt.lower()

        # Detect intent from keywords
        if any(word in prompt_lower for word in ["checkout", "buy", "purchase"]):
            return self.PREDEFINED_RESPONSES["checkout_request"]
        if any(word in prompt_lower for word in ["order", "where is", "track"]):
            return self.PREDEFINED_RESPONSES["order_status"]
        if any(word in prompt_lower for word in ["human", "person", "agent", "speak to"]):
            return self.PREDEFINED_RESPONSES["human_handoff"]
        if any(word in prompt_lower for word in ["cart", "bag"]):
            return self.PREDEFINED_RESPONSES["view_cart"]
        if any(word in prompt_lower for word in ["add", "put"]):
            return self.PREDEFINED_RESPONSES["add_to_cart"]
        # Default to product search
        if any(word in prompt_lower for word in ["budget", "size", "under", "less than"]):
            return self.PREDEFINED_RESPONSES["product_search_simple"]
        return self.PREDEFINED_RESPONSES["product_search_vague"]

    async def stream(self, prompt: str, **kwargs: Any):
        """Mock streaming response (yields single response)."""
        response = await self.chat(prompt, **kwargs)
        yield response.raw_response

    def reset(self) -> None:
        """Reset call count (useful between tests)."""
        self.call_count = 0


# Provider-specific mocks (all use same base class)
class MockOllamaProvider(MockLLMProvider):
    """Mock Ollama provider."""

    def __init__(self) -> None:
        super().__init__("ollama")


class MockOpenAIProvider(MockLLMProvider):
    """Mock OpenAI provider."""

    def __init__(self) -> None:
        super().__init__("openai")


class MockAnthropicProvider(MockLLMProvider):
    """Mock Anthropic provider."""

    def __init__(self) -> None:
        super().__init__("anthropic")


class MockGeminiProvider(MockLLMProvider):
    """Mock Google Gemini provider."""

    def __init__(self) -> None:
        super().__init__("gemini")


class MockGLMProvider(MockLLMProvider):
    """Mock GLM-4.7 provider."""

    def __init__(self) -> None:
        super().__init__("glm-4.7")


def get_mock_llm(provider: str = "test") -> MockLLMProvider:
    """Factory function to get appropriate mock LLM.

    Args:
        provider: Provider name (ollama, openai, anthropic, gemini, glm-4.7)

    Returns:
        Appropriate mock provider instance
    """
    provider_classes = {
        "ollama": MockOllamaProvider,
        "openai": MockOpenAIProvider,
        "anthropic": MockAnthropicProvider,
        "gemini": MockGeminiProvider,
        "glm-4.7": MockGLMProvider,
    }
    provider_class = provider_classes.get(provider, MockLLMProvider)

    # Provider-specific classes don't need a parameter
    if provider in provider_classes:
        return provider_class()
    return provider_class(provider)
