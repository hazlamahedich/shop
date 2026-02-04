"""Factory for creating LLM service instances.

Ensures consistent instantiation pattern and enforces
single provider per merchant.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.core.errors import APIError, ErrorCode
from app.core.config import is_testing
from app.services.llm.base_llm_service import BaseLLMService
from app.services.llm.ollama_service import OllamaService
from app.services.llm.openai_service import OpenAIService
from app.services.llm.anthropic_service import AnthropicService
from app.services.llm.gemini_service import GeminiService
from app.services.llm.glm_service import GLMService


class LLMProviderFactory:
    """Factory for creating LLM service instances.

    Ensures consistent instantiation pattern and enforces
    single provider per merchant.
    """

    _providers = {
        "ollama": OllamaService,
        "openai": OpenAIService,
        "anthropic": AnthropicService,
        "gemini": GeminiService,
        "glm": GLMService,
    }

    @classmethod
    def create_provider(
        cls,
        provider_name: str,
        config: Dict[str, Any],
    ) -> BaseLLMService:
        """Create LLM service instance for provider.

        Args:
            provider_name: Provider name (ollama, openai, anthropic, gemini, glm)
            config: Provider configuration dict

        Returns:
            Instantiated LLM service

        Raises:
            APIError: If provider not found
        """
        provider_class = cls._providers.get(provider_name)

        if not provider_class:
            raise APIError(
                ErrorCode.LLM_PROVIDER_NOT_FOUND,
                f"Unknown LLM provider: {provider_name}",
            )

        return provider_class(config, is_testing=is_testing())

    @classmethod
    def get_available_providers(cls) -> List[Dict[str, Any]]:
        """Get list of available providers with metadata.

        Returns:
            List of provider dicts with name, display_name, pricing
        """
        return [
            {
                "id": "ollama",
                "name": "Ollama (Local)",
                "description": "Free, runs on your server",
                "pricing": {
                    "inputCost": 0.0,
                    "outputCost": 0.0,
                    "currency": "USD",
                },
                "models": ["llama3", "mistral", "qwen2", "codellama"],
                "features": [
                    "local",
                    "free",
                    "privacy-first",
                    "no-api-key-needed",
                ],
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "Fast, accurate, cost-effective",
                "pricing": {
                    "inputCost": 0.15,
                    "outputCost": 0.60,
                    "currency": "USD",
                },
                "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                "features": ["fast", "accurate", "cost-effective", "wide-adoption"],
            },
            {
                "id": "anthropic",
                "name": "Anthropic",
                "description": "Fast, accurate",
                "pricing": {
                    "inputCost": 0.25,
                    "outputCost": 1.25,
                    "currency": "USD",
                },
                "models": ["claude-3-haiku", "claude-3-sonnet"],
                "features": ["fast", "accurate", "long-context", "reliable"],
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "description": "Google ecosystem, huge context",
                "pricing": {
                    "inputCost": 0.075,
                    "outputCost": 0.30,
                    "currency": "USD",
                },
                "models": ["gemini-1.5-flash", "gemini-pro"],
                "features": ["fast", "huge-context", "google-integration"],
            },
            {
                "id": "glm",
                "name": "GLM-4.7 (Zhipu AI)",
                "description": "China market support",
                "pricing": {
                    "inputCost": 0.10,
                    "outputCost": 0.10,
                    "currency": "CNY",
                    "usd_equivalent": 0.014,
                },
                "models": ["glm-4-flash", "glm-4-plus"],
                "features": ["china-market", "chinese-language", "affordable"],
            },
        ]
