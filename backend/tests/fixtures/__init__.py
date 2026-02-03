"""Test fixtures and test doubles for deterministic testing.

This package provides:
- Mock LLM providers for all supported providers
- Test data factories for generating test entities
- Common fixtures for pytest tests
"""

# Mock LLM providers
from tests.fixtures.mock_llm import (
    LLMResponse,
    MockLLMProvider,
    MockOllamaProvider,
    MockOpenAIProvider,
    MockAnthropicProvider,
    MockGeminiProvider,
    MockGLMProvider,
    get_mock_llm,
)

# Test factories
from tests.fixtures.factory import (
    UserFactory,
    ProductFactory,
    CartFactory,
    OrderFactory,
    ConversationFactory,
    MessageFactory,
    SequenceFactory,
    random_string,
    random_email,
    random_phone,
)

__all__ = [
    # Mock LLM providers
    "LLMResponse",
    "MockLLMProvider",
    "MockOllamaProvider",
    "MockOpenAIProvider",
    "MockAnthropicProvider",
    "MockGeminiProvider",
    "MockGLMProvider",
    "get_mock_llm",
    # Test factories
    "UserFactory",
    "ProductFactory",
    "CartFactory",
    "OrderFactory",
    "ConversationFactory",
    "MessageFactory",
    "SequenceFactory",
    "random_string",
    "random_email",
    "random_phone",
]
