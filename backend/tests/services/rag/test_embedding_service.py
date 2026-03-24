"""Tests for Embedding Service.

Story 8-4: Backend - RAG Service (Document Processing)

Test Coverage:
- AC1: Embedding generation for OpenAI and Ollama
- Error handling: rate limits, API errors, invalid provider
- Batch processing
- Mock embeddings for testing
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.rag.embedding_service import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODELS,
    EmbeddingResult,
    EmbeddingService,
    InvalidProviderError,
)


class TestEmbeddingServiceInit:
    """Tests for EmbeddingService initialization."""

    def test_init_openai_provider(self):
        """Test initialization with OpenAI provider."""
        service = EmbeddingService(
            provider="openai",
            api_key="test-key",
        )

        assert service.provider == "openai"
        assert service.model == EMBEDDING_MODELS["openai"]
        assert service.dimension == EMBEDDING_DIMENSIONS["openai"]
        assert service.api_key == "test-key"

    def test_init_ollama_provider(self):
        """Test initialization with Ollama provider."""
        service = EmbeddingService(
            provider="ollama",
            ollama_url="http://localhost:11434",
        )

        assert service.provider == "ollama"
        assert service.model == EMBEDDING_MODELS["ollama"]
        assert service.dimension == EMBEDDING_DIMENSIONS["ollama"]
        assert service.ollama_url == "http://localhost:11434"

    def test_init_anthropic_provider_raises_error(self):
        """Test that Anthropic provider raises InvalidProviderError."""
        with pytest.raises(InvalidProviderError) as exc_info:
            EmbeddingService(
                provider="anthropic",
                api_key="test-key",
            )

        assert "Anthropic does not support embeddings" in str(exc_info.value)

    def test_init_unknown_provider_raises_error(self):
        """Test that unknown provider raises InvalidProviderError."""
        with pytest.raises(InvalidProviderError) as exc_info:
            EmbeddingService(
                provider="unknown_provider",
            )

        assert "does not support embeddings" in str(exc_info.value)

    def test_init_custom_model_override(self):
        """Test initialization with custom model override."""
        service = EmbeddingService(
            provider="openai",
            api_key="test-key",
            model="text-embedding-3-large",
        )

        assert service.model == "text-embedding-3-large"


class TestEmbeddingServiceMock:
    """Tests for mock embedding generation (IS_TESTING mode)."""

    @pytest.mark.asyncio
    async def test_mock_embed_texts_returns_embeddings(self):
        """Test mock embedding generation returns correct structure."""
        service = EmbeddingService(provider="openai", api_key="test-key")

        texts = ["Hello world", "Test document"]
        result = service._mock_embed_texts(texts)

        assert isinstance(result, EmbeddingResult)
        assert len(result.embeddings) == 2
        assert len(result.embeddings[0]) == service.dimension
        assert result.provider == "mock"
        assert result.token_count > 0

    @pytest.mark.asyncio
    async def test_mock_embed_texts_deterministic(self):
        """Test mock embeddings are deterministic based on text hash."""
        service = EmbeddingService(provider="openai", api_key="test-key")

        text = "Test document for determinism"
        result1 = service._mock_embed_texts([text])
        result2 = service._mock_embed_texts([text])

        # Same text should produce same embedding
        assert result1.embeddings[0] == result2.embeddings[0]

    @pytest.mark.asyncio
    async def test_mock_embed_texts_empty_list(self):
        """Test mock embedding with empty text list."""
        service = EmbeddingService(provider="openai", api_key="test-key")

        result = service._mock_embed_texts([])

        assert result.embeddings == []
        assert result.token_count == 0


class TestEmbeddingServiceOpenAI:
    """Tests for OpenAI embedding generation."""

    @pytest.mark.asyncio
    async def test_embed_texts_openai_success(self):
        """Test successful OpenAI embedding generation."""
        service = EmbeddingService(provider="openai", api_key="test-key")

        mock_response_data = {
            "data": [
                {"embedding": [0.1] * 1536, "index": 0},
                {"embedding": [0.2] * 1536, "index": 1},
            ],
            "usage": {"prompt_tokens": 10, "total_tokens": 10},
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        service._async_client = mock_client

        with patch("app.services.rag.embedding_service.is_testing", return_value=False):
            result = await service.embed_texts(["Text 1", "Text 2"])

        assert len(result.embeddings) == 2
        assert result.provider == "openai"
        assert result.dimension == 1536

    @pytest.mark.asyncio
    async def test_embed_texts_openai_batch_processing(self):
        """Test OpenAI batch processing for large text lists."""
        service = EmbeddingService(provider="openai", api_key="test-key")

        texts = [f"Text {i}" for i in range(150)]
        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            batch_size = len(kwargs.get("json", {}).get("input", []))
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1] * 1536, "index": i} for i in range(batch_size)],
                "usage": {"prompt_tokens": batch_size * 5, "total_tokens": batch_size * 5},
            }
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_client = AsyncMock()
        mock_client.post = mock_post
        service._async_client = mock_client

        with patch("app.services.rag.embedding_service.is_testing", return_value=False):
            result = await service.embed_texts(texts)

        assert len(result.embeddings) == 150
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_embed_texts_openai_rate_limit_retry(self):
        """Test OpenAI rate limit triggers retry."""
        service = EmbeddingService(provider="openai", api_key="test-key")

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                error = httpx.HTTPStatusError(
                    "Rate limit",
                    request=MagicMock(),
                    response=MagicMock(status_code=429, text="Rate limit exceeded"),
                )
                raise error
            else:
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "data": [{"embedding": [0.1] * 1536, "index": 0}],
                    "usage": {"prompt_tokens": 5, "total_tokens": 5},
                }
                mock_response.raise_for_status = MagicMock()
                return mock_response

        mock_client = AsyncMock()
        mock_client.post = mock_post
        service._async_client = mock_client

        with patch("app.services.rag.embedding_service.is_testing", return_value=False):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await service.embed_texts(["Test"])

        assert len(result.embeddings) == 1
        assert call_count == 3


class TestEmbeddingServiceOllama:
    """Tests for Ollama embedding generation."""

    @pytest.mark.asyncio
    async def test_embed_texts_ollama_success(self):
        """Test successful Ollama embedding generation."""
        service = EmbeddingService(provider="ollama")

        async def mock_post(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.json.return_value = {"embedding": [0.1] * 768}
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_client = AsyncMock()
        mock_client.post = mock_post
        service._async_client = mock_client

        with patch("app.services.rag.embedding_service.is_testing", return_value=False):
            result = await service.embed_texts(["Test text"])

        assert len(result.embeddings) == 1
        assert len(result.embeddings[0]) == 768
        assert result.provider == "ollama"

    @pytest.mark.asyncio
    async def test_embed_texts_ollama_concurrent_requests(self):
        """Test Ollama concurrent requests with rate limiting."""
        service = EmbeddingService(provider="ollama")

        texts = ["Text 1", "Text 2", "Text 3"]
        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_response = MagicMock()
            mock_response.json.return_value = {"embedding": [0.1] * 768}
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_client = AsyncMock()
        mock_client.post = mock_post
        service._async_client = mock_client

        with patch("app.services.rag.embedding_service.is_testing", return_value=False):
            result = await service.embed_texts(texts)

        assert len(result.embeddings) == 3
        assert call_count == 3


class TestEmbeddingServiceEmbedQuery:
    """Tests for single query embedding."""

    @pytest.mark.asyncio
    async def test_embed_query_returns_single_embedding(self):
        """Test embed_query returns single embedding vector."""
        service = EmbeddingService(provider="openai", api_key="test-key")

        with patch.object(
            service,
            "embed_texts",
            new_callable=AsyncMock,
            return_value=EmbeddingResult(
                embeddings=[[0.1] * 1536],
                model="text-embedding-3-small",
                provider="openai",
                dimension=1536,
            ),
        ):
            result = await service.embed_query("Test query")

        assert len(result) == 1536
        assert result == [0.1] * 1536

    @pytest.mark.asyncio
    async def test_embed_query_empty_result(self):
        """Test embed_query with empty result."""
        service = EmbeddingService(provider="openai", api_key="test-key")

        with patch.object(
            service,
            "embed_texts",
            new_callable=AsyncMock,
            return_value=EmbeddingResult(
                embeddings=[],
                model="text-embedding-3-small",
                provider="openai",
                dimension=1536,
            ),
        ):
            result = await service.embed_query("Test query")

        assert result == []


class TestEmbeddingServiceGetDimension:
    """Tests for get_dimension method."""

    def test_get_dimension_openai(self):
        """Test get_dimension returns correct value for OpenAI."""
        service = EmbeddingService(provider="openai", api_key="test-key")
        assert service.get_dimension() == 1536

    def test_get_dimension_ollama(self):
        """Test get_dimension returns correct value for Ollama."""
        service = EmbeddingService(provider="ollama")
        assert service.get_dimension() == 768


class TestEmbeddingServiceClose:
    """Tests for async client cleanup."""

    @pytest.mark.asyncio
    async def test_close_client(self):
        """Test close method properly closes async client."""
        service = EmbeddingService(provider="openai", api_key="test-key")

        # Access async_client to create it
        _ = service.async_client
        assert service._async_client is not None

        await service.close()
        assert service._async_client is None

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """Test close method handles None client gracefully."""
        service = EmbeddingService(provider="openai", api_key="test-key")

        # Should not raise error
        await service.close()
        assert service._async_client is None
