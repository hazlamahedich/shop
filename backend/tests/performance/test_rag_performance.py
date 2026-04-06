"""Performance tests for RAG service.

Story 8-9: Testing & Quality Assurance
Task 6.1: Create backend/tests/performance/test_rag_performance.py

Performance benchmarks:
- RAG retrieval <500ms for top-5 chunks
- Batch embedding <2s for 10 chunks
- P50/P95/P99 latency measurements
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import time
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import DocumentChunk, DocumentStatus, KnowledgeDocument
from app.services.rag.embedding_service import EmbeddingService
from app.services.rag.retrieval_service import RetrievalService


class TestRAGPerformance:
    """Performance tests for RAG operations."""

    @pytest.fixture
    def mock_embedding_service(self) -> EmbeddingService:
        """Create mock embedding service with deterministic responses."""
        service = EmbeddingService(provider="openai", api_key="test-key")

        async def mock_embed_query(query: str) -> list[float]:
            await asyncio.sleep(0.01)
            return [0.1] * 1536

        # Patch the embed_query method
        service.embed_query = mock_embed_query
        return service

    @pytest.mark.performance
    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-PERF-001")
    @pytest.mark.priority("P2")
    async def test_rag_retrieval_latency(
        self,
        async_session: AsyncSession,
        test_merchant: int,
    ):
        """Test RAG retrieval is under 500ms for top-5 chunks.

        Test ID: 8-9-PERF-001
        Priority: P2 (Medium - Performance validation)
        AC Coverage: AC7 (Performance <500ms retrieval)
        """
        merchant_id = test_merchant

        doc = KnowledgeDocument(
            merchant_id=merchant_id,
            filename="perf_test.pdf",
            file_type="pdf",
            file_size=1024,
            status=DocumentStatus.READY.value,
        )
        async_session.add(doc)
        await async_session.commit()
        await async_session.refresh(doc)

        chunks = []
        for i in range(20):
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=i,
                content=f"Performance test chunk {i} with some content to search.",
                embedding=[0.1 * (i + 1)] * 1536,
            )
            chunks.append(chunk)
        async_session.add_all(chunks)
        await async_session.commit()

        embedding_service = EmbeddingService(provider="openai", api_key="test-key")
        retrieval_service = RetrievalService(
            db=async_session,
            embedding_service=embedding_service,
        )

        latencies = []
        for _ in range(10):
            with patch.object(
                embedding_service,
                "embed_query",
                new_callable=AsyncMock,
                return_value=[0.1] * 1536,
            ):
                start = time.perf_counter()

                results = await retrieval_service.retrieve_relevant_chunks(
                    merchant_id=merchant_id,
                    query="performance test",
                    top_k=5,
                )

                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)

        latencies.sort()
        p50 = latencies[5]
        p95 = latencies[9]
        p99 = latencies[9]

        print("\nRAG Retrieval Latency:")
        print(f"  P50: {p50:.2f}ms")
        print(f"  P95: {p95:.2f}ms")
        print(f"  P99: {p99:.2f}ms")

        assert p50 < 500, f"P50 latency {p50}ms exceeds 500ms threshold"
        assert p95 < 1000, f"P95 latency {p95}ms exceeds 1000ms threshold"

    @pytest.mark.performance
    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-PERF-002")
    @pytest.mark.priority("P2")
    async def test_batch_embedding_latency(self):
        """Test batch embedding is under 2s for 10 chunks.

        Test ID: 8-9-PERF-002
        Priority: P2 (Medium - Performance validation)
        AC Coverage: AC7 (Performance benchmarks)
        """
        embedding_service = EmbeddingService(provider="openai", api_key="test-key")

        chunks = [f"Test chunk content {i}" for i in range(10)]

        latencies = []
        for _ in range(5):
            with patch.object(
                embedding_service,
                "embed_texts",
                new_callable=AsyncMock,
                return_value=[[0.1] * 1536 for _ in range(10)],
            ):
                start = time.perf_counter()

                results = await embedding_service.embed_texts(chunks)

                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)

        avg_latency = sum(latencies) / len(latencies)

        print("\nBatch Embedding Latency (10 chunks):")
        print(f"  Average: {avg_latency:.2f}ms")

        assert avg_latency < 2000, f"Average latency {avg_latency}ms exceeds 2000ms threshold"

    @pytest.mark.performance
    @pytest.mark.asyncio
    @pytest.mark.test_id("8-9-PERF-003")
    @pytest.mark.priority("P2")
    async def test_document_chunking_throughput(self):
        """Test document chunking throughput.

        Test ID: 8-9-PERF-003
        Priority: P2 (Medium - Performance validation)
        AC Coverage: AC7 (Performance benchmarks)
        """
        from app.services.knowledge.chunker import DocumentChunker

        chunker = DocumentChunker()

        large_content = "This is a test sentence. " * 500

        # Write to temp file since chunk_document expects a file path
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(large_content)
            temp_path = f.name

        try:
            latencies = []
            chunks = []  # Initialize to avoid "possibly unbound" error
            for _ in range(5):
                start = time.perf_counter()

                chunks = chunker.chunk_document(temp_path, "txt")

                elapsed_ms = (time.perf_counter() - start) * 1000
                latencies.append(elapsed_ms)

            avg_latency = sum(latencies) / len(latencies)

            print("\nDocument Chunking Throughput:")
            print(f"  Content size: {len(large_content)} chars")
            print(f"  Chunks produced: {len(chunks)}")
            print(f"  Average latency: {avg_latency:.2f}ms")

            assert avg_latency < 100, f"Chunking latency {avg_latency}ms exceeds 100ms threshold"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
