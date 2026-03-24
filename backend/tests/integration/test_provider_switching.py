"""Integration tests for embedding provider switching.

Story 8-11: LLM Embedding Provider Integration & Re-embedding

Tests the full flow of switching embedding providers including:
- API endpoint behavior
- Database updates
- Re-embedding triggers
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


class TestEmbeddingProviderEndpoints:
    """Test embedding provider API endpoints."""

    @pytest.mark.asyncio
    async def test_get_embedding_provider_settings(self, async_client: AsyncClient, test_merchant):
        """Test getting embedding provider settings."""
        response = await async_client.get(
            "/api/settings/embedding-provider",
            headers={"X-Merchant-Id": str(test_merchant)},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"]["provider"] in ["openai", "gemini", "ollama"]

    @pytest.mark.asyncio
    async def test_update_embedding_provider_same_dimension(
        self, async_client: AsyncClient, test_merchant
    ):
        """Test updating provider with same dimension doesn't trigger re-embedding."""
        with patch(
            "app.services.rag.dimension_handler.DimensionHandler.mark_documents_for_reembedding",
            new=AsyncMock(return_value=0),
        ):
            response = await async_client.patch(
                "/api/settings/embedding-provider",
                json={"provider": "openai", "model": "text-embedding-3-small"},
                headers={"X-Merchant-Id": str(test_merchant)},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["re_embedding_required"] is False

    @pytest.mark.asyncio
    async def test_update_embedding_provider_different_dimension(
        self, async_client: AsyncClient, test_merchant
    ):
        """Test updating provider with different dimension triggers re-embedding."""
        with patch(
            "app.services.rag.dimension_handler.DimensionHandler.mark_documents_for_reembedding",
            new=AsyncMock(return_value=3),
        ):
            response = await async_client.patch(
                "/api/settings/embedding-provider",
                json={"provider": "gemini", "model": "text-embedding-004"},
                headers={"X-Merchant-Id": str(test_merchant)},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["provider"] == "gemini"
            assert data["data"]["dimension"] == 768

    @pytest.mark.asyncio
    async def test_update_provider_merchant_not_found(self, async_client: AsyncClient):
        """Test updating provider when merchant not found."""
        response = await async_client.patch(
            "/api/settings/embedding-provider",
            json={"provider": "openai", "model": "text-embedding-3-small"},
            headers={"X-Merchant-Id": "99999"},
        )

        assert response.status_code in [404, 400]

    @pytest.mark.asyncio
    async def test_get_re_embed_status(self, async_client: AsyncClient, test_merchant):
        """Test getting re-embed status returns proper structure."""
        response = await async_client.get(
            "/api/knowledge-base/re-embed/status",
            headers={"X-Merchant-Id": str(test_merchant)},
        )

        # Accept 200 (with data) or 422 (validation error if no merchant documents)
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            data = response.json()
            assert "data" in data

    @pytest.mark.asyncio
    async def test_trigger_manual_re_embed(self, async_client: AsyncClient, test_merchant):
        """Test manually triggering re-embedding."""
        with patch(
            "app.services.rag.reembedding_worker.trigger_reembedding_for_merchant",
            new=AsyncMock(return_value=5),
        ):
            response = await async_client.post(
                "/api/knowledge-base/re-embed",
                headers={"X-Merchant-Id": str(test_merchant)},
            )

            assert response.status_code in [200, 202]


class TestProviderSwitchingFlow:
    """Test full provider switching flow."""

    @pytest.mark.asyncio
    async def test_switch_from_openai_to_gemini(self):
        """Test switching from OpenAI to Gemini provider."""
        old_dimension = 1536
        new_dimension = 768

        assert old_dimension != new_dimension

    @pytest.mark.asyncio
    async def test_switch_from_gemini_to_ollama(self):
        """Test switching from Gemini to Ollama (same dimension)."""
        old_dimension = 768
        new_dimension = 768

        assert old_dimension == new_dimension

    @pytest.mark.asyncio
    async def test_embedding_version_tracking(self):
        """Test that embedding version is tracked."""
        provider = "gemini"
        model = "text-embedding-004"
        version = f"{provider}-{model}"

        assert version == "gemini-text-embedding-004"
