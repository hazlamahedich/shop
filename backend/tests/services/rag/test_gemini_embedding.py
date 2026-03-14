"""Tests for Gemini embedding provider.

Story 8-11: LLM Embedding Provider Integration & Re-embedding
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.rag.gemini_embedding_provider import (
    GeminiEmbeddingProvider,
    GeminiEmbeddingError,
    GeminiRateLimitError,
    GEMINI_DIMENSION,
)
from app.core.errors import APIError, ErrorCode


class TestGeminiEmbeddingProvider:
    """Test Gemini embedding provider functionality."""

    def test_init_with_api_key(self):
        """Test provider initialization with API key."""
        provider = GeminiEmbeddingProvider(api_key="test-api-key")
        assert provider.api_key == "test-api-key"
        assert provider.model == "text-embedding-004"
        assert provider.DIMENSION == GEMINI_DIMENSION

    def test_init_without_api_key_raises_error(self):
        """Test that missing API key raises error."""
        with pytest.raises(APIError) as exc_info:
            GeminiEmbeddingProvider(api_key="")

        assert exc_info.value.code == ErrorCode.LLM_API_KEY_MISSING

    def test_init_with_custom_model(self):
        """Test provider initialization with custom model."""
        provider = GeminiEmbeddingProvider(api_key="test-key", model="custom-model")
        assert provider.model == "custom-model"

    @pytest.mark.asyncio
    async def test_embed_texts_empty_list(self):
        """Test embedding empty list returns empty result."""
        provider = GeminiEmbeddingProvider(api_key="test-key")
        result = await provider.embed_texts([])

        assert result.embeddings == []
        assert result.model == "text-embedding-004"
        assert result.dimension == GEMINI_DIMENSION
        assert result.token_count == 0

    @pytest.mark.asyncio
    async def test_embed_texts_mock_mode(self):
        """Test embedding in mock/testing mode."""
        with patch("app.services.rag.gemini_embedding_provider.is_testing", return_value=True):
            provider = GeminiEmbeddingProvider(api_key="test-key")
            result = await provider.embed_texts(["hello", "world"])

            assert len(result.embeddings) == 2
            assert len(result.embeddings[0]) == GEMINI_DIMENSION
            assert all(isinstance(e, list) for e in result.embeddings)

    @pytest.mark.asyncio
    async def test_embed_query_returns_single_embedding(self):
        """Test embed_query returns single embedding."""
        with patch("app.services.rag.gemini_embedding_provider.is_testing", return_value=True):
            provider = GeminiEmbeddingProvider(api_key="test-key")
            embedding = await provider.embed_query("test query")

            assert isinstance(embedding, list)
            assert len(embedding) == GEMINI_DIMENSION

    @pytest.mark.asyncio
    async def test_embed_texts_rate_limit_handling(self):
        """Test rate limit error handling."""
        provider = GeminiEmbeddingProvider(api_key="test-key")

        mock_client = MagicMock()
        mock_client.aio.models.embed_content = AsyncMock(side_effect=Exception("429 rate limit"))
        provider._client = mock_client

        with patch("app.services.rag.gemini_embedding_provider.is_testing", return_value=False):
            with pytest.raises(APIError) as exc_info:
                await provider.embed_texts(["test"])

            assert exc_info.value.code == ErrorCode.EMBEDDING_RATE_LIMITED

    @pytest.mark.asyncio
    async def test_embed_texts_general_error_handling(self):
        """Test general error handling."""
        provider = GeminiEmbeddingProvider(api_key="test-key")

        mock_client = MagicMock()
        mock_client.aio.models.embed_content = AsyncMock(side_effect=Exception("Connection failed"))
        provider._client = mock_client

        with patch("app.services.rag.gemini_embedding_provider.is_testing", return_value=False):
            with pytest.raises(APIError) as exc_info:
                await provider.embed_texts(["test"])

            assert exc_info.value.code == ErrorCode.EMBEDDING_GENERATION_FAILED

    def test_get_dimension(self):
        """Test get_dimension returns correct value."""
        provider = GeminiEmbeddingProvider(api_key="test-key")
        assert provider.get_dimension() == GEMINI_DIMENSION

    def test_mock_embed_texts_normalization(self):
        """Test that mock embeddings are normalized."""
        provider = GeminiEmbeddingProvider(api_key="test-key")
        result = provider._mock_embed_texts(["test"])

        embedding = result.embeddings[0]
        norm = sum(x * x for x in embedding) ** 0.5
        assert abs(norm - 1.0) < 0.0001
