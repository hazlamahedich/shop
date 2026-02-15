"""Tests for LLM Model Discovery Service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.llm.model_discovery_service import (
    ModelDiscoveryService,
    ModelInfo,
    ModelDiscoveryCache,
    get_model_discovery_service,
)


class TestModelInfo:
    def test_to_dict(self):
        model = ModelInfo(
            id="gpt-4o-mini",
            name="GPT-4o Mini",
            provider="openai",
            description="Fast model",
            context_length=128000,
            input_price_per_million=0.15,
            output_price_per_million=0.60,
            is_local=False,
            is_downloaded=False,
            features=["fast", "affordable"],
        )

        result = model.to_dict()

        assert result["id"] == "gpt-4o-mini"
        assert result["name"] == "GPT-4o Mini"
        assert result["provider"] == "openai"
        assert result["contextLength"] == 128000
        assert result["pricing"]["inputCostPerMillion"] == 0.15
        assert result["pricing"]["outputCostPerMillion"] == 0.60
        assert result["isLocal"] is False
        assert result["isDownloaded"] is False
        assert "fast" in result["features"]


class TestModelDiscoveryCache:
    def test_set_and_get(self):
        cache = ModelDiscoveryCache(ttl_seconds=60)
        data = [{"id": "model-1", "name": "Model 1"}]

        cache.set("test-key", data)
        result = cache.get("test-key")

        assert result == data

    def test_get_expired(self):
        cache = ModelDiscoveryCache(ttl_seconds=-1)  # Already expired
        data = [{"id": "model-1"}]
        cache.set("test-key", data)

        result = cache.get("test-key")

        assert result is None

    def test_get_missing(self):
        cache = ModelDiscoveryCache()

        result = cache.get("nonexistent")

        assert result is None

    def test_clear_specific_key(self):
        cache = ModelDiscoveryCache()
        cache.set("key1", [{"id": "1"}])
        cache.set("key2", [{"id": "2"}])

        cache.clear("key1")

        assert cache.get("key1") is None
        assert cache.get("key2") is not None

    def test_clear_all(self):
        cache = ModelDiscoveryCache()
        cache.set("key1", [{"id": "1"}])
        cache.set("key2", [{"id": "2"}])

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_get_cache_info(self):
        cache = ModelDiscoveryCache(ttl_seconds=60)
        cache.set("key1", [{"id": "1"}])

        info = cache.get_cache_info()

        assert "key1" in info["keys"]
        assert "key1" in info["entries"]


class TestModelDiscoveryService:
    @pytest.fixture
    def service(self):
        return ModelDiscoveryService(cache_ttl_seconds=60)

    def test_fallback_models_openai(self, service):
        fallback = service._get_fallback_models("openai")

        assert len(fallback) > 0
        assert any(m["id"] == "gpt-4o-mini" for m in fallback)

    def test_fallback_models_anthropic(self, service):
        fallback = service._get_fallback_models("anthropic")

        assert len(fallback) > 0
        assert any(m["id"] == "claude-3-haiku" for m in fallback)

    def test_fallback_models_ollama(self, service):
        fallback = service._get_fallback_models("ollama")

        # Ollama doesn't have cloud fallback
        assert fallback == []

    def test_fallback_models_unknown_provider(self, service):
        fallback = service._get_fallback_models("unknown")

        assert fallback == []

    def test_extract_features_vision(self, service):
        model_data = {
            "architecture": {
                "input_modalities": ["text", "image"],
            },
            "context_length": 128000,
        }

        features = service._extract_features(model_data)

        assert "vision" in features
        assert "long-context" in features

    def test_extract_features_audio(self, service):
        model_data = {
            "architecture": {
                "input_modalities": ["text", "audio"],
            },
            "context_length": 4096,
        }

        features = service._extract_features(model_data)

        assert "audio" in features
        assert "long-context" not in features

    @pytest.mark.asyncio
    async def test_get_models_for_provider_caching(self, service):
        mock_models = [{"id": "model-1", "provider": "openai"}]

        with patch.object(
            service,
            "_fetch_cloud_provider_models",
            new_callable=AsyncMock,
            return_value=mock_models,
        ):
            result1 = await service.get_models_for_provider("openai")
            result2 = await service.get_models_for_provider("openai")

        assert result1 == mock_models
        assert result2 == mock_models

    @pytest.mark.asyncio
    async def test_clear_cache(self, service):
        mock_models = [{"id": "model-1"}]

        with patch.object(
            service,
            "_fetch_cloud_provider_models",
            new_callable=AsyncMock,
            return_value=mock_models,
        ):
            await service.get_models_for_provider("openai")

        service.clear_cache("openai")

        assert service._cache.get("models:openai") is None

    @pytest.mark.asyncio
    async def test_fetch_ollama_downloaded_models(self, service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3:latest", "details": {"family": "llama"}},
                {"name": "mistral:latest", "details": {"family": "mistral"}},
            ]
        }

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        service._http_client = mock_client

        models = await service._fetch_ollama_downloaded_models("http://localhost:11434")

        assert len(models) == 2
        assert models[0]["id"] == "llama3"
        assert models[0]["isDownloaded"] is True
        assert models[1]["id"] == "mistral"

    @pytest.mark.asyncio
    async def test_fetch_ollama_downloaded_models_failure(self, service):
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        service._http_client = mock_client

        models = await service._fetch_ollama_downloaded_models("http://localhost:11434")

        assert models == []

    @pytest.mark.asyncio
    async def test_fetch_ollama_library_models(self, service):
        models = await service._fetch_ollama_library_models()

        assert len(models) > 0
        assert any(m["id"] == "llama3" for m in models)
        assert any(m["id"] == "mistral" for m in models)
        assert all(m["isLocal"] for m in models)
        assert all(not m["isDownloaded"] for m in models)


class TestGetModelDiscoveryService:
    def test_singleton(self):
        service1 = get_model_discovery_service()
        service2 = get_model_discovery_service()

        assert service1 is service2
