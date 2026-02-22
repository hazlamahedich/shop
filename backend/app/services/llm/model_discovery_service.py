"""LLM Model Discovery Service.

Fetches available models and pricing from:
- OpenRouter API for cloud providers (OpenAI, Anthropic, Gemini, etc.)
- Local Ollama instance for downloaded models
- Ollama library for available models to pull

Caches results with TTL to avoid repeated API calls.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import httpx
import structlog

from app.core.errors import APIError, ErrorCode


logger = structlog.get_logger(__name__)


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"
OLLAMA_LIBRARY_URL = "https://ollama.com/library"


class ModelInfo:
    """Model information with pricing."""

    def __init__(
        self,
        id: str,
        name: str,
        provider: str,
        description: str = "",
        context_length: int = 4096,
        input_price_per_million: float = 0.0,
        output_price_per_million: float = 0.0,
        is_local: bool = False,
        is_downloaded: bool = False,
        features: Optional[List[str]] = None,
    ):
        self.id = id
        self.name = name
        self.provider = provider
        self.description = description
        self.context_length = context_length
        self.input_price_per_million = input_price_per_million
        self.output_price_per_million = output_price_per_million
        self.is_local = is_local
        self.is_downloaded = is_downloaded
        self.features = features or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "description": self.description,
            "contextLength": self.context_length,
            "pricing": {
                "inputCostPerMillion": self.input_price_per_million,
                "outputCostPerMillion": self.output_price_per_million,
                "currency": "USD",
            },
            "isLocal": self.is_local,
            "isDownloaded": self.is_downloaded,
            "features": self.features,
        }


class ModelDiscoveryCache:
    """In-memory cache with TTL for model data."""

    def __init__(self, ttl_seconds: int = 86400):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        if key not in self._cache:
            return None
        entry = self._cache[key]
        if time.time() > entry["expires_at"]:
            del self._cache[key]
            return None
        return entry["data"]

    def set(self, key: str, data: List[Dict[str, Any]]) -> None:
        self._cache[key] = {
            "data": data,
            "expires_at": time.time() + self._ttl_seconds,
            "cached_at": datetime.utcnow().isoformat(),
        }

    def clear(self, key: Optional[str] = None) -> None:
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()

    def get_cache_info(self) -> Dict[str, Any]:
        return {
            "keys": list(self._cache.keys()),
            "entries": {
                k: {
                    "cached_at": v["cached_at"],
                    "expires_in_seconds": max(0, int(v["expires_at"] - time.time())),
                }
                for k, v in self._cache.items()
            },
        }


PROVIDER_ID_MAPPING = {
    "openai": "openai",
    "anthropic": "anthropic",
    "gemini": "google",
    "google": "google",
    "glm": "zhipu",
    "meta-llama": "meta",
    "mistralai": "mistral",
}


class ModelDiscoveryService:
    """Service for discovering available LLM models and pricing."""

    def __init__(self, cache_ttl_seconds: int = 86400):
        self._cache = ModelDiscoveryCache(cache_ttl_seconds)
        self._http_client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def get_models_for_provider(
        self,
        provider: str,
        ollama_url: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get available models for a specific provider.

        Args:
            provider: Provider ID (ollama, openai, anthropic, gemini, glm)
            ollama_url: Ollama server URL (required for ollama provider)

        Returns:
            List of model info dictionaries
        """
        cache_key = f"models:{provider}"
        if ollama_url:
            cache_key = f"{cache_key}:{ollama_url}"

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        if provider == "ollama":
            models = await self._fetch_ollama_models(ollama_url)
        else:
            models = await self._fetch_cloud_provider_models(provider)

        self._cache.set(cache_key, models)
        return models

    async def _fetch_ollama_models(
        self,
        ollama_url: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch Ollama models: downloaded locally + available in library."""
        base_url = ollama_url or "http://localhost:11434"
        models: List[Dict[str, Any]] = []

        downloaded_models = await self._fetch_ollama_downloaded_models(base_url)
        models.extend(downloaded_models)

        library_models = await self._fetch_ollama_library_models()

        downloaded_ids = {m["id"] for m in downloaded_models}
        for lib_model in library_models:
            if lib_model["id"] not in downloaded_ids:
                lib_model["isDownloaded"] = False
                models.append(lib_model)

        return models

    async def _fetch_ollama_downloaded_models(
        self,
        ollama_url: str,
    ) -> List[Dict[str, Any]]:
        """Fetch models downloaded on local Ollama instance."""
        models: List[Dict[str, Any]] = []

        try:
            response = await self.http_client.get(f"{ollama_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                for model in data.get("models", []):
                    model_info = ModelInfo(
                        id=model.get("name", "").split(":")[0],
                        name=model.get("name", ""),
                        provider="ollama",
                        description=f"Local model - {model.get('details', {}).get('family', 'Unknown')}",
                        context_length=4096,
                        input_price_per_million=0.0,
                        output_price_per_million=0.0,
                        is_local=True,
                        is_downloaded=True,
                        features=["local", "free", "downloaded"],
                    )
                    models.append(model_info.to_dict())
        except Exception as e:
            logger.warning("ollama_local_fetch_failed", error=str(e), url=ollama_url)

        return models

    async def _fetch_ollama_library_models(self) -> List[Dict[str, Any]]:
        """Fetch popular models from Ollama library."""
        cache_key = "ollama:library"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        popular_models = [
            {"id": "llama3", "name": "Llama 3", "description": "Meta's latest open model"},
            {
                "id": "llama3.1",
                "name": "Llama 3.1",
                "description": "Meta Llama 3.1 with improved reasoning",
            },
            {
                "id": "llama3.2",
                "name": "Llama 3.2",
                "description": "Meta Llama 3.2 lightweight models",
            },
            {"id": "mistral", "name": "Mistral", "description": "Mistral 7B efficient model"},
            {"id": "codellama", "name": "Code Llama", "description": "Llama fine-tuned for coding"},
            {"id": "qwen2", "name": "Qwen 2", "description": "Alibaba's Qwen 2 model"},
            {
                "id": "qwen2.5",
                "name": "Qwen 2.5",
                "description": "Alibaba's Qwen 2.5 with improved performance",
            },
            {"id": "gemma2", "name": "Gemma 2", "description": "Google's Gemma 2 open model"},
            {"id": "phi3", "name": "Phi-3", "description": "Microsoft's small but capable model"},
            {
                "id": "deepseek-coder",
                "name": "DeepSeek Coder",
                "description": "DeepSeek coding model",
            },
            {"id": "deepseek-r1", "name": "DeepSeek R1", "description": "DeepSeek reasoning model"},
            {"id": "llava", "name": "LLaVA", "description": "Vision-language model"},
            {
                "id": "nomic-embed-text",
                "name": "Nomic Embed",
                "description": "Text embedding model",
            },
        ]

        models = []
        for m in popular_models:
            model_info = ModelInfo(
                id=m["id"],
                name=m["name"],
                provider="ollama",
                description=m["description"],
                context_length=4096,
                input_price_per_million=0.0,
                output_price_per_million=0.0,
                is_local=True,
                is_downloaded=False,
                features=["local", "free", "library"],
            )
            models.append(model_info.to_dict())

        self._cache.set(cache_key, models)
        return models

    async def _fetch_cloud_provider_models(
        self,
        provider: str,
    ) -> List[Dict[str, Any]]:
        """Fetch models from OpenRouter API for cloud providers."""
        cache_key = "openrouter:all"

        cached = self._cache.get(cache_key)
        all_models = cached

        if all_models is None:
            try:
                all_models = await self._fetch_openrouter_models()
                self._cache.set(cache_key, all_models)
                from app.services.cost_tracking.pricing import update_pricing_from_discovery

                updated = update_pricing_from_discovery(all_models)
                logger.info("pricing_updated_from_openrouter", models_updated=updated)
            except Exception as e:
                logger.error("openrouter_fetch_failed", error=str(e))
                return self._get_fallback_models(provider)

        provider_prefix = PROVIDER_ID_MAPPING.get(provider, provider)
        filtered_models = []

        for model in all_models:
            model_id = model.get("id", "")
            if model_id.startswith(f"{provider_prefix}/"):
                model["provider"] = provider
                model["id"] = model_id.split("/", 1)[1]
                filtered_models.append(model)

        if not filtered_models:
            return self._get_fallback_models(provider)

        return filtered_models

    async def _fetch_openrouter_models(self) -> List[Dict[str, Any]]:
        """Fetch all models from OpenRouter API."""
        response = await self.http_client.get(OPENROUTER_API_URL)
        response.raise_for_status()
        data = response.json()

        models = []
        for model_data in data.get("data", []):
            pricing = model_data.get("pricing", {})
            prompt_price = float(pricing.get("prompt", 0))
            completion_price = float(pricing.get("completion", 0))

            input_per_million = prompt_price * 1_000_000
            output_per_million = completion_price * 1_000_000

            model_info = ModelInfo(
                id=model_data.get("id", ""),
                name=model_data.get("name", model_data.get("id", "")),
                provider=model_data.get("id", "").split("/")[0],
                description=model_data.get("description", "")[:200]
                if model_data.get("description")
                else "",
                context_length=model_data.get("context_length", 4096),
                input_price_per_million=input_per_million,
                output_price_per_million=output_per_million,
                is_local=False,
                is_downloaded=False,
                features=self._extract_features(model_data),
            )
            models.append(model_info.to_dict())

        return models

    def _extract_features(self, model_data: Dict[str, Any]) -> List[str]:
        """Extract feature tags from model data."""
        features = []

        arch = model_data.get("architecture", {})
        if "text" in arch.get("input_modalities", []):
            features.append("text-input")
        if "image" in arch.get("input_modalities", []):
            features.append("vision")
        if "audio" in arch.get("input_modalities", []):
            features.append("audio")

        context = model_data.get("context_length", 0)
        if context >= 100000:
            features.append("long-context")

        top_provider = model_data.get("top_provider", {})
        if top_provider.get("is_moderated"):
            features.append("moderated")

        return features

    def _get_fallback_models(self, provider: str) -> List[Dict[str, Any]]:
        """Fallback model list when API fails."""
        fallback = {
            "openai": [
                {
                    "id": "gpt-4o-mini",
                    "name": "GPT-4o Mini",
                    "provider": "openai",
                    "description": "Fast and affordable",
                    "contextLength": 128000,
                    "pricing": {
                        "inputCostPerMillion": 0.15,
                        "outputCostPerMillion": 0.60,
                        "currency": "USD",
                    },
                    "isLocal": False,
                    "isDownloaded": False,
                    "features": ["fast", "affordable"],
                },
                {
                    "id": "gpt-4o",
                    "name": "GPT-4o",
                    "provider": "openai",
                    "description": "Most capable GPT-4 model",
                    "contextLength": 128000,
                    "pricing": {
                        "inputCostPerMillion": 2.50,
                        "outputCostPerMillion": 10.0,
                        "currency": "USD",
                    },
                    "isLocal": False,
                    "isDownloaded": False,
                    "features": ["capable", "vision"],
                },
                {
                    "id": "gpt-3.5-turbo",
                    "name": "GPT-3.5 Turbo",
                    "provider": "openai",
                    "description": "Fast and efficient",
                    "contextLength": 16385,
                    "pricing": {
                        "inputCostPerMillion": 0.50,
                        "outputCostPerMillion": 1.50,
                        "currency": "USD",
                    },
                    "isLocal": False,
                    "isDownloaded": False,
                    "features": ["fast", "affordable"],
                },
            ],
            "anthropic": [
                {
                    "id": "claude-3-haiku",
                    "name": "Claude 3 Haiku",
                    "provider": "anthropic",
                    "description": "Fast and affordable",
                    "contextLength": 200000,
                    "pricing": {
                        "inputCostPerMillion": 0.25,
                        "outputCostPerMillion": 1.25,
                        "currency": "USD",
                    },
                    "isLocal": False,
                    "isDownloaded": False,
                    "features": ["fast", "affordable"],
                },
                {
                    "id": "claude-3-sonnet",
                    "name": "Claude 3 Sonnet",
                    "provider": "anthropic",
                    "description": "Balanced performance",
                    "contextLength": 200000,
                    "pricing": {
                        "inputCostPerMillion": 3.0,
                        "outputCostPerMillion": 15.0,
                        "currency": "USD",
                    },
                    "isLocal": False,
                    "isDownloaded": False,
                    "features": ["balanced", "capable"],
                },
            ],
            "gemini": [
                {
                    "id": "google/gemini-2.5-flash-lite",
                    "name": "Gemini 2.5 Flash Lite",
                    "provider": "gemini",
                    "description": "Lightweight and cost-effective (latest)",
                    "contextLength": 1000000,
                    "pricing": {
                        "inputCostPerMillion": 0.10,
                        "outputCostPerMillion": 0.40,
                        "currency": "USD",
                    },
                    "isLocal": False,
                    "isDownloaded": False,
                    "features": ["fast", "affordable", "long-context"],
                },
                {
                    "id": "google/gemini-2.0-flash",
                    "name": "Gemini 2.0 Flash",
                    "provider": "gemini",
                    "description": "Fast and efficient",
                    "contextLength": 1000000,
                    "pricing": {
                        "inputCostPerMillion": 0.10,
                        "outputCostPerMillion": 0.40,
                        "currency": "USD",
                    },
                    "isLocal": False,
                    "isDownloaded": False,
                    "features": ["fast", "long-context"],
                },
                {
                    "id": "google/gemini-2.0-flash-lite",
                    "name": "Gemini 2.0 Flash Lite",
                    "provider": "gemini",
                    "description": "Lightweight and cost-effective",
                    "contextLength": 1000000,
                    "pricing": {
                        "inputCostPerMillion": 0.075,
                        "outputCostPerMillion": 0.30,
                        "currency": "USD",
                    },
                    "isLocal": False,
                    "isDownloaded": False,
                    "features": ["fast", "affordable", "long-context"],
                },
                {
                    "id": "google/gemini-1.5-flash",
                    "name": "Gemini 1.5 Flash",
                    "provider": "gemini",
                    "description": "Fast and efficient",
                    "contextLength": 1000000,
                    "pricing": {
                        "inputCostPerMillion": 0.075,
                        "outputCostPerMillion": 0.30,
                        "currency": "USD",
                    },
                    "isLocal": False,
                    "isDownloaded": False,
                    "features": ["fast", "long-context"],
                },
                {
                    "id": "google/gemini-1.5-pro",
                    "name": "Gemini 1.5 Pro",
                    "provider": "gemini",
                    "description": "Most capable",
                    "contextLength": 2000000,
                    "pricing": {
                        "inputCostPerMillion": 1.25,
                        "outputCostPerMillion": 10.0,
                        "currency": "USD",
                    },
                    "isLocal": False,
                    "isDownloaded": False,
                    "features": ["capable", "long-context"],
                },
            ],
            "glm": [
                {
                    "id": "glm-4-flash",
                    "name": "GLM-4 Flash",
                    "provider": "glm",
                    "description": "Fast and affordable",
                    "contextLength": 128000,
                    "pricing": {
                        "inputCostPerMillion": 0.10,
                        "outputCostPerMillion": 0.10,
                        "currency": "USD",
                    },
                    "isLocal": False,
                    "isDownloaded": False,
                    "features": ["fast", "affordable", "chinese"],
                },
                {
                    "id": "glm-4-plus",
                    "name": "GLM-4 Plus",
                    "provider": "glm",
                    "description": "More capable model",
                    "contextLength": 128000,
                    "pricing": {
                        "inputCostPerMillion": 0.50,
                        "outputCostPerMillion": 0.50,
                        "currency": "USD",
                    },
                    "isLocal": False,
                    "isDownloaded": False,
                    "features": ["capable", "chinese"],
                },
            ],
        }
        return fallback.get(provider, [])

    def clear_cache(self, provider: Optional[str] = None) -> None:
        """Clear cached model data."""
        if provider:
            self._cache.clear(f"models:{provider}")
            self._cache.clear(f"models:{provider}:*")
        else:
            self._cache.clear()

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache status information."""
        return self._cache.get_cache_info()

    def get_model_pricing_sync(
        self,
        provider: str,
        model_id: str,
    ) -> Dict[str, float]:
        """Get pricing for a specific model from cache (sync version).

        Returns cached pricing if available, otherwise returns free pricing.
        Use get_model_pricing() for async version that fetches from API.

        Args:
            provider: Provider ID (openai, anthropic, gemini, glm)
            model_id: Model ID (e.g., "gpt-4o-mini", "claude-3-haiku")

        Returns:
            Dict with 'input' and 'output' prices per million tokens
        """
        cache_key = f"models:{provider}"
        cached = self._cache.get(cache_key)

        if cached:
            for model in cached:
                if model.get("id") == model_id or model.get("id", "").endswith(f"/{model_id}"):
                    pricing = model.get("pricing", {})
                    return {
                        "input": float(pricing.get("inputCostPerMillion", 0)),
                        "output": float(pricing.get("outputCostPerMillion", 0)),
                    }

        fallback = self._get_fallback_models(provider)
        for model in fallback:
            if model.get("id") == model_id:
                pricing = model.get("pricing", {})
                return {
                    "input": float(pricing.get("inputCostPerMillion", 0)),
                    "output": float(pricing.get("outputCostPerMillion", 0)),
                }

        return {"input": 0.0, "output": 0.0}

    async def get_model_pricing(
        self,
        provider: str,
        model_id: str,
    ) -> Dict[str, float]:
        """Get pricing for a specific model (async version that fetches if needed).

        Args:
            provider: Provider ID (openai, anthropic, gemini, glm)
            model_id: Model ID (e.g., "gpt-4o-mini", "claude-3-haiku")

        Returns:
            Dict with 'input' and 'output' prices per million tokens
        """
        models = await self.get_models_for_provider(provider)
        for model in models:
            if model.get("id") == model_id or model.get("id", "").endswith(f"/{model_id}"):
                pricing = model.get("pricing", {})
                return {
                    "input": float(pricing.get("inputCostPerMillion", 0)),
                    "output": float(pricing.get("outputCostPerMillion", 0)),
                }

        return {"input": 0.0, "output": 0.0}

    async def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """Get provider metadata with dynamic pricing from OpenRouter.

        Args:
            provider: Provider ID (openai, anthropic, gemini, glm, ollama)

        Returns:
            Provider info dict with name, description, pricing, models, features
        """
        provider_metadata = {
            "ollama": {
                "name": "Ollama (Local)",
                "description": "Free, runs on your server",
                "features": ["local", "free", "privacy-first", "no-api-key-needed"],
            },
            "openai": {
                "name": "OpenAI",
                "description": "Fast, accurate, cost-effective",
                "features": ["fast", "accurate", "cost-effective", "wide-adoption"],
            },
            "anthropic": {
                "name": "Anthropic",
                "description": "Fast, accurate",
                "features": ["fast", "accurate", "long-context", "reliable"],
            },
            "gemini": {
                "name": "Google Gemini",
                "description": "Google ecosystem, huge context",
                "features": ["fast", "huge-context", "google-integration"],
            },
            "glm": {
                "name": "GLM-4 (Zhipu AI)",
                "description": "China market support",
                "features": ["china-market", "chinese-language", "affordable"],
            },
        }

        models = await self.get_models_for_provider(provider)

        default_pricing = {"inputCostPerMillion": 0, "outputCostPerMillion": 0, "currency": "USD"}
        if models:
            first_model = models[0]
            pricing = first_model.get("pricing", default_pricing)
            model_ids = [m.get("id") for m in models[:10]]
        else:
            pricing = default_pricing
            model_ids = []

        metadata = provider_metadata.get(
            provider,
            {
                "name": provider.capitalize(),
                "description": f"{provider.capitalize()} provider",
                "features": [],
            },
        )

        return {
            "id": provider,
            "name": metadata["name"],
            "description": metadata["description"],
            "pricing": pricing,
            "models": model_ids,
            "features": metadata["features"],
        }


_model_discovery_service: Optional[ModelDiscoveryService] = None


def get_model_discovery_service() -> ModelDiscoveryService:
    """Get or create the global model discovery service instance."""
    global _model_discovery_service
    if _model_discovery_service is None:
        _model_discovery_service = ModelDiscoveryService()
    return _model_discovery_service
