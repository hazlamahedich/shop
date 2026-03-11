"""Embedding service for RAG document processing.

Follows existing LLM provider patterns from app/services/llm/.
Supports OpenAI (text-embedding-3-small) and Ollama (nomic-embed-text).
Anthropic does not support embeddings.

Story 8-4: Backend - RAG Service (Document Processing)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
import structlog

from app.core.config import is_testing, settings
from app.core.errors import APIError, ErrorCode

logger = structlog.get_logger(__name__)

# Embedding dimensions by provider
EMBEDDING_DIMENSIONS = {
    "openai": 1536,  # text-embedding-3-small
    "ollama": 768,  # nomic-embed-text
}

# Default models by provider
EMBEDDING_MODELS = {
    "openai": "text-embedding-3-small",
    "ollama": "nomic-embed-text",
}

# Rate limiting configuration
EMBEDDING_RATE_LIMIT_RPM = 3000  # OpenAI limit
EMBEDDING_RETRY_MAX_ATTEMPTS = 3
EMBEDDING_RETRY_BACKOFF_FACTOR = 2.0  # Exponential: 1s → 2s → 4s


class EmbeddingError(Exception):
    """Base exception for embedding errors."""

    pass


class RateLimitError(EmbeddingError):
    """Raised when rate limit is exceeded."""

    pass


class InvalidProviderError(EmbeddingError):
    """Raised when provider doesn't support embeddings."""

    pass


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""

    embeddings: List[List[float]]
    model: str
    provider: str
    dimension: int = 1536
    token_count: int = 0


class EmbeddingService:
    """Embedding service following established LLM provider patterns.

    Supports:
    - OpenAI: text-embedding-3-small (1536 dimensions)
    - Ollama: nomic-embed-text (768 dimensions)
    - Anthropic: NOT supported (raises EMBEDDING_INVALID_PROVIDER)

    Features:
    - Batch processing (OpenAI: max 100 texts per batch)
    - Concurrent requests for Ollama with rate limiting
    - Exponential backoff retry on rate limits
    - IS_TESTING mode support for mock responses
    """

    def __init__(
        self,
        provider: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        ollama_url: Optional[str] = None,
    ) -> None:
        """Initialize embedding service.

        Args:
            provider: Provider name (openai, ollama)
            api_key: API key for cloud providers
            model: Model override (optional)
            ollama_url: Ollama server URL (optional, defaults to config)

        Raises:
            InvalidProviderError: If provider doesn't support embeddings
        """
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model or EMBEDDING_MODELS.get(self.provider)
        self.ollama_url = ollama_url or settings().get(
            "OLLAMA_DEFAULT_URL", "http://localhost:11434"
        )
        self._async_client: Optional[httpx.AsyncClient] = None

        # Validate provider - Anthropic is explicitly not supported
        if self.provider == "anthropic":
            raise InvalidProviderError(
                "Anthropic does not support embeddings. "
                "Use OpenAI or Ollama for embedding generation."
            )

        if self.provider not in EMBEDDING_DIMENSIONS:
            raise InvalidProviderError(
                f"Provider '{self.provider}' does not support embeddings. "
                f"Supported providers: {list(EMBEDDING_DIMENSIONS.keys())}"
            )

        self.dimension = EMBEDDING_DIMENSIONS[self.provider]

        logger.info(
            "embedding_service_initialized",
            provider=self.provider,
            model=self.model,
            dimension=self.dimension,
        )

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._async_client is None:
            if self.provider == "openai":
                self._async_client = httpx.AsyncClient(
                    base_url="https://api.openai.com/v1",
                    timeout=60.0,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
            else:  # ollama
                self._async_client = httpx.AsyncClient(
                    base_url=self.ollama_url,
                    timeout=60.0,
                )
        return self._async_client

    @async_client.setter
    def async_client(self, value: Optional[httpx.AsyncClient]) -> None:
        """Set async client (for testing)."""
        self._async_client = value

    @async_client.deleter
    def async_client(self) -> None:
        """Delete async client (for testing)."""
        self._async_client = None

    async def close(self) -> None:
        """Close the async client."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None

    async def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of text strings to embed

        Returns:
            EmbeddingResult with embeddings and metadata

        Raises:
            EmbeddingError: If embedding generation fails
            RateLimitError: If rate limit exceeded after retries
        """
        if not texts:
            return EmbeddingResult(
                embeddings=[],
                model=self.model or "",
                provider=self.provider,
                dimension=self.dimension,
                token_count=0,
            )

        # Use mock in testing mode
        if is_testing():
            return self._mock_embed_texts(texts)

        # Retry with exponential backoff
        last_error: Optional[Exception] = None
        for attempt in range(EMBEDDING_RETRY_MAX_ATTEMPTS):
            try:
                if self.provider == "openai":
                    return await self._embed_texts_openai(texts)
                else:  # ollama
                    return await self._embed_texts_ollama(texts)
            except RateLimitError as e:
                last_error = e
                if attempt < EMBEDDING_RETRY_MAX_ATTEMPTS - 1:
                    wait_time = (EMBEDDING_RETRY_BACKOFF_FACTOR**attempt) * 1.0
                    logger.warning(
                        "embedding_rate_limited",
                        attempt=attempt,
                        wait_seconds=wait_time,
                        provider=self.provider,
                    )
                    await asyncio.sleep(wait_time)
                else:
                    raise APIError(
                        ErrorCode.EMBEDDING_RATE_LIMITED,
                        f"Embedding rate limit exceeded after {EMBEDDING_RETRY_MAX_ATTEMPTS} attempts",
                    )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Rate limit - set last_error and continue to retry
                    last_error = e
                    if attempt < EMBEDDING_RETRY_MAX_ATTEMPTS - 1:
                        wait_time = (EMBEDDING_RETRY_BACKOFF_FACTOR**attempt) * 1.0
                        logger.warning(
                            "embedding_rate_limited",
                            attempt=attempt,
                            wait_seconds=wait_time,
                            provider=self.provider,
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise APIError(
                            ErrorCode.EMBEDDING_RATE_LIMITED,
                            f"Embedding rate limit exceeded after {EMBEDDING_RETRY_MAX_ATTEMPTS} attempts",
                        )
                raise APIError(
                    ErrorCode.EMBEDDING_GENERATION_FAILED,
                    f"Embedding API error: {e.response.text}",
                )
            except Exception as e:
                logger.error("embedding_generation_failed", error=str(e), provider=self.provider)
                raise APIError(
                    ErrorCode.EMBEDDING_GENERATION_FAILED,
                    f"Failed to generate embeddings: {str(e)}",
                )

        # Should not reach here, but just in case
        raise APIError(
            ErrorCode.EMBEDDING_GENERATION_FAILED,
            f"Failed to generate embeddings: {last_error}",
        )

    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query.

        Args:
            query: Query text

        Returns:
            Embedding vector

        Raises:
            EmbeddingError: If embedding generation fails
        """
        result = await self.embed_texts([query])
        return result.embeddings[0] if result.embeddings else []

    async def _embed_texts_openai(self, texts: List[str]) -> EmbeddingResult:
        """Generate embeddings using OpenAI text-embedding-3-small.

        OpenAI supports batch embeddings (max 100 texts per batch).
        """
        if not self.api_key:
            raise APIError(
                ErrorCode.LLM_API_KEY_MISSING,
                "OpenAI API key not configured for embeddings",
            )

        # Process in batches of 100 (OpenAI limit)
        all_embeddings: List[List[float]] = []
        batch_size = 100

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            response = await self.async_client.post(
                "/embeddings",
                json={
                    "model": self.model,
                    "input": batch,
                    "encoding_format": "float",
                },
            )
            response.raise_for_status()
            data = response.json()

            # Extract embeddings in order
            batch_embeddings = [item["embedding"] for item in data["data"]]
            all_embeddings.extend(batch_embeddings)

        # Estimate token count (rough approximation)
        total_chars = sum(len(t) for t in texts)
        token_count = total_chars // 4

        return EmbeddingResult(
            embeddings=all_embeddings,
            model=self.model or "text-embedding-3-small",
            provider="openai",
            dimension=self.dimension,
            token_count=token_count,
        )

    async def _embed_texts_ollama(self, texts: List[str]) -> EmbeddingResult:
        """Generate embeddings using Ollama nomic-embed-text.

        Uses asyncio.gather() for concurrent requests with rate limiting.
        """
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests

        async def embed_single(text: str) -> List[float]:
            async with semaphore:
                response = await self.async_client.post(
                    "/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text,
                    },
                )
                response.raise_for_status()
                return response.json()["embedding"]

        # Process all texts concurrently
        tasks = [embed_single(text) for text in texts]
        embeddings = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any failures - results can be List[float] or Exception
        results: List[List[float]] = []
        for i, result in enumerate(embeddings):
            if isinstance(result, Exception):
                logger.error("ollama_embedding_failed", text_index=i, error=str(result))
                raise APIError(
                    ErrorCode.EMBEDDING_GENERATION_FAILED,
                    f"Ollama embedding failed for text at index {i}: {str(result)}",
                )
            # At this point, result is guaranteed to be List[float]
            results.append(result)  # type: ignore[arg-type]

        # Estimate token count (rough approximation)
        total_chars = sum(len(t) for t in texts)
        token_count = total_chars // 4

        return EmbeddingResult(
            embeddings=results,
            model=self.model or "nomic-embed-text",
            provider="ollama",
            dimension=self.dimension,
            token_count=token_count,
        )

    def _mock_embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """Generate mock embeddings for testing."""
        import random

        # Generate deterministic mock embeddings based on text hash
        embeddings: List[List[float]] = []
        for text in texts:
            # Use text hash as seed for deterministic results
            random.seed(hash(text) % (2**32))
            embedding = [random.uniform(-1, 1) for _ in range(self.dimension)]
            # Normalize to unit vector
            norm = sum(x * x for x in embedding) ** 0.5
            normalized = [x / norm for x in embedding]
            embeddings.append(normalized)

        return EmbeddingResult(
            embeddings=embeddings,
            model=self.model or "mock-embedding",
            provider="mock",
            dimension=self.dimension,
            token_count=sum(len(t) for t in texts) // 4,
        )

    def get_dimension(self) -> int:
        """Get embedding dimension for current provider."""
        return self.dimension
