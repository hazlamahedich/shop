"""Factory for creating LLM service instances.

Ensures consistent instantiation pattern and enforces
single provider per merchant.
Pricing fetched dynamically from OpenRouter via ModelDiscoveryService.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.errors import APIError, ErrorCode
from app.core.config import is_testing
from app.services.llm.base_llm_service import BaseLLMService
from app.services.llm.ollama_service import OllamaService
from app.services.llm.openai_service import OpenAIService
from app.services.llm.anthropic_service import AnthropicService
from app.services.llm.gemini_service import GeminiService
from app.services.llm.glm_service import GLMService
from app.services.llm.mock_service import MockLLMService


class LLMProviderFactory:
    """Factory for creating LLM service instances.

    Ensures consistent instantiation pattern and enforces
    single provider per merchant.
    Pricing fetched dynamically from OpenRouter via ModelDiscoveryService.
    """

    _providers = {
        "ollama": OllamaService,
        "openai": OpenAIService,
        "anthropic": AnthropicService,
        "gemini": GeminiService,
        "glm": GLMService,
        "mock": MockLLMService,
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
            config: Provider configuration dict (api_key, model, etc.)

        Returns:
            Instantiated LLM service with pricing included in config

        Raises:
            APIError: If provider not found
        """
        if is_testing():
            return MockLLMService(config, is_testing=True)

        provider_class = cls._providers.get(provider_name)

        if not provider_class:
            raise APIError(
                ErrorCode.LLM_PROVIDER_NOT_FOUND,
                f"Unknown LLM provider: {provider_name}",
            )

        enriched_config = cls._enrich_config_with_pricing(provider_name, config)

        return provider_class(enriched_config, is_testing=is_testing())

    @classmethod
    def _enrich_config_with_pricing(
        cls,
        provider_name: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Enrich config with pricing from ModelDiscoveryService.

        Args:
            provider_name: Provider name
            config: Original config dict

        Returns:
            Config with pricing added
        """
        from app.services.llm.model_discovery_service import get_model_discovery_service

        enriched = config.copy()

        if provider_name == "ollama":
            enriched["pricing"] = {"input": 0.0, "output": 0.0}
            return enriched

        model_id = config.get("model", "")
        if model_id:
            try:
                discovery = get_model_discovery_service()
                pricing = discovery.get_model_pricing_sync(provider_name, model_id)
                enriched["pricing"] = pricing
            except Exception:
                enriched["pricing"] = {"input": 0.0, "output": 0.0}

        return enriched

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
                "features": [
                    "fast",
                    "accurate",
                    "cost-effective",
                    "wide-adoption",
                ],
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
                "models": ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"],
                "features": ["fast", "huge-context", "google-integration"],
            },
            {
                "id": "glm",
                "name": "GLM-4 (Zhipu AI)",
                "description": "China market support",
                "pricing": {
                    "inputCost": 0.10,
                    "outputCost": 0.10,
                    "currency": "USD",
                },
                "models": ["glm-4-flash", "glm-4-plus"],
                "features": ["china-market", "chinese-language", "affordable"],
            },
        ]

    @classmethod
    async def get_available_providers_async(cls) -> List[Dict[str, Any]]:
        """Get list of available providers with dynamic pricing from OpenRouter.

        Returns:
            List of provider dicts with name, description, pricing, models, features
        """
        from app.services.llm.model_discovery_service import get_model_discovery_service

        discovery = get_model_discovery_service()

        providers = []
        for provider_id in ["ollama", "openai", "anthropic", "gemini", "glm"]:
            try:
                provider_info = await discovery.get_provider_info(provider_id)
                providers.append(provider_info)
            except Exception:
                providers.extend(
                    [p for p in cls.get_available_providers() if p["id"] == provider_id]
                )

        return providers
