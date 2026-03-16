"""Gemini embedding provider for RAG document processing.

Implements embedding generation using Google's Gemini text-embedding-004 model.
Uses the google-genai SDK for async embedding calls.

Story 8-11: LLM Embedding Provider Integration & Re-embedding
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Optional

import structlog

from app.core.config import is_testing
from app.core.errors import APIError, ErrorCode

logger = structlog.get_logger(__name__)

GEMINI_MODEL = "text-embedding-004"
GEMINI_DIMENSION = 768
GEMINI_BATCH_SIZE = 100


class GeminiEmbeddingError(Exception):
    """Base exception for Gemini embedding errors."""

    pass


class GeminiRateLimitError(GeminiEmbeddingError):
    """Raised when Gemini rate limit is exceeded."""

    pass


@dataclass
class GeminiEmbeddingResult:
    """Result of Gemini embedding generation."""

    embeddings: List[List[float]]
    model: str
    dimension: int = GEMINI_DIMENSION
    token_count: int = 0


class GeminiEmbeddingProvider:
    """Gemini embedding provider using google-genai SDK.

    Features:
    - Uses text-embedding-004 model (768 dimensions)
    - Batch processing support
    - Rate limiting with exponential backoff
    - IS_TESTING mode support for mock responses
    """

    MODEL = GEMINI_MODEL
    DIMENSION = GEMINI_DIMENSION

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
    ) -> None:
        """Initialize Gemini embedding provider.

        Args:
            api_key: Google AI API key
            model: Model override (optional)

        Raises:
            ValueError: If API key is not provided
        """
        if not api_key:
            raise APIError(
                ErrorCode.LLM_API_KEY_MISSING,
                "Gemini API key not configured for embeddings",
            )

        self.api_key = api_key
        self.model = model or self.MODEL
        self._client = None

        logger.info(
            "gemini_embedding_provider_initialized",
            model=self.model,
            dimension=self.DIMENSION,
        )

    @property
    def client(self):
        """Get or create Gemini client (lazy initialization)."""
        if self._client is None:
            try:
                from google import genai

                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise APIError(
                    ErrorCode.EMBEDDING_INVALID_PROVIDER,
                    "google-genai SDK not installed. Run: pip install google-genai",
                )
        return self._client

    @client.setter
    def client(self, value):
        """Set client (for testing)."""
        self._client = value

    async def embed_texts(self, texts: List[str]) -> GeminiEmbeddingResult:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of text strings to embed

        Returns:
            GeminiEmbeddingResult with embeddings and metadata

        Raises:
            GeminiEmbeddingError: If embedding generation fails
            GeminiRateLimitError: If rate limit exceeded
        """
        if not texts:
            return GeminiEmbeddingResult(
                embeddings=[],
                model=self.model,
                dimension=self.DIMENSION,
                token_count=0,
            )

        if is_testing():
            return self._mock_embed_texts(texts)

        try:
            embeddings = await self._embed_with_retry(texts)
            token_count = sum(len(t) for t in texts) // 4

            return GeminiEmbeddingResult(
                embeddings=embeddings,
                model=self.model,
                dimension=self.DIMENSION,
                token_count=token_count,
            )

        except GeminiRateLimitError:
            raise APIError(
                ErrorCode.EMBEDDING_RATE_LIMITED,
                "Gemini embedding rate limit exceeded",
            )
        except Exception as e:
            logger.error(
                "gemini_embedding_failed",
                error=str(e),
                texts_count=len(texts),
            )
            raise APIError(
                ErrorCode.EMBEDDING_GENERATION_FAILED,
                f"Gemini embedding failed: {str(e)}",
            )

    async def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query.

        Args:
            query: Query text

        Returns:
            Embedding vector

        Raises:
            GeminiEmbeddingError: If embedding generation fails
        """
        result = await self.embed_texts([query])
        return result.embeddings[0] if result.embeddings else []

    async def _embed_with_retry(
        self,
        texts: List[str],
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
    ) -> List[List[float]]:
        """Embed texts with retry logic for rate limits.

        Args:
            texts: List of texts to embed
            max_attempts: Maximum retry attempts
            backoff_factor: Exponential backoff multiplier

        Returns:
            List of embedding vectors

        Raises:
            GeminiRateLimitError: If rate limit exceeded after retries
            GeminiEmbeddingError: If embedding fails
        """
        last_error: Optional[Exception] = None

        for attempt in range(max_attempts):
            try:
                return await self._embed_batch(texts)
            except Exception as e:
                error_str = str(e).lower()
                is_rate_limit = "429" in error_str or "rate" in error_str or "quota" in error_str

                if is_rate_limit:
                    last_error = e
                    if attempt < max_attempts - 1:
                        wait_time = (backoff_factor**attempt) * 1.0
                        logger.warning(
                            "gemini_rate_limited",
                            attempt=attempt,
                            wait_seconds=wait_time,
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise GeminiRateLimitError(f"Rate limit exceeded: {e}")

                raise GeminiEmbeddingError(f"Embedding failed: {e}")

        raise GeminiRateLimitError(f"Rate limit exceeded after retries: {last_error}")

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts using Gemini API.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (768 dimensions each)
        """
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), GEMINI_BATCH_SIZE):
            batch = texts[i : i + GEMINI_BATCH_SIZE]

            for text in batch:
                result = await self.client.aio.models.embed_content(
                    model=self.model,
                    contents=text,
                )
                all_embeddings.append(list(result.embeddings[0].values))

        return all_embeddings

    def _mock_embed_texts(self, texts: List[str]) -> GeminiEmbeddingResult:
        """Generate mock embeddings for testing."""
        import random

        embeddings: List[List[float]] = []
        for text in texts:
            random.seed(hash(text) % (2**32))
            embedding = [random.uniform(-1, 1) for _ in range(self.DIMENSION)]
            norm = sum(x * x for x in embedding) ** 0.5
            normalized = [x / norm for x in embedding]
            embeddings.append(normalized)

        return GeminiEmbeddingResult(
            embeddings=embeddings,
            model=self.model,
            dimension=self.DIMENSION,
            token_count=sum(len(t) for t in texts) // 4,
        )

    def get_dimension(self) -> int:
        """Get embedding dimension for current provider."""
        return self.DIMENSION
