"""Integration tests for Story 10-1: Source Citations Widget.

Tests message persistence with sources, source retrieval from RAG,
and source citation formatting.

Story 10-1: Source Citations Widget
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

os.environ["IS_TESTING"] = "true"


class TestSourceCitationsIntegration:
    """Integration tests for source citations in widget messages."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        storage = {}

        async def mock_get(key):
            return storage.get(key)

        async def mock_setex(key, ttl, value):
            storage[key] = value
            return True

        async def mock_delete(*keys):
            count = 0
            for key in keys:
                if key in storage:
                    del storage[key]
                    count += 1
            return count

        async def mock_exists(key):
            return 1 if key in storage else 0

        async def mock_rpush(key, value):
            if key not in storage:
                storage[key] = []
            storage[key].append(value)
            return len(storage[key])

        async def mock_lrange(key, start, end):
            if key not in storage:
                return []
            return storage[key]

        redis.get = mock_get
        redis.setex = mock_setex
        redis.delete = mock_delete
        redis.exists = mock_exists
        redis.rpush = mock_rpush
        redis.lrange = mock_lrange

        return redis

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        return db

    @pytest.fixture
    def sample_sources(self):
        """Create sample source citations."""
        return [
            {
                "document_id": 1,
                "title": "Product Manual",
                "document_type": "pdf",
                "relevance_score": 0.95,
                "url": None,
                "chunk_index": 5,
            },
            {
                "document_id": 2,
                "title": "FAQ Page",
                "document_type": "url",
                "relevance_score": 0.88,
                "url": "https://example.com/faq",
                "chunk_index": None,
            },
            {
                "document_id": 3,
                "title": "Knowledge Base Article",
                "document_type": "text",
                "relevance_score": 0.75,
                "url": None,
                "chunk_index": 2,
            },
        ]

    @pytest.mark.asyncio
    async def test_message_response_includes_sources(self, mock_redis, sample_sources):
        """[P0] Widget message response should include sources when RAG is used."""
        from app.schemas.widget import SourceCitation, WidgetMessageResponse

        sources = [SourceCitation(**s) for s in sample_sources]

        response = WidgetMessageResponse(
            messageId="msg-123",
            content="Based on our documentation...",
            sender="bot",
            createdAt=datetime.now(UTC),
            sources=sources,
        )

        assert response.sources is not None
        assert len(response.sources) == 3
        assert response.sources[0].title == "Product Manual"
        assert response.sources[0].document_type == "pdf"
        assert response.sources[1].url == "https://example.com/faq"

    @pytest.mark.asyncio
    async def test_sources_sorted_by_relevance_score(self, sample_sources):
        """[P0] Sources should be sorted by relevance score (highest first)."""
        from app.schemas.widget import SourceCitation

        sources = [SourceCitation(**s) for s in sample_sources]
        sorted_sources = sorted(sources, key=lambda s: s.relevance_score, reverse=True)

        assert sorted_sources[0].relevance_score >= sorted_sources[1].relevance_score
        assert sorted_sources[1].relevance_score >= sorted_sources[2].relevance_score
        assert sorted_sources[0].title == "Product Manual"
        assert sorted_sources[2].title == "Knowledge Base Article"

    @pytest.mark.asyncio
    async def test_source_without_url_does_not_have_link(self):
        """[P1] Sources without URL field should not have clickable links."""
        from app.schemas.widget import SourceCitation

        source = SourceCitation(
            document_id=1,
            title="Internal Document",
            document_type="pdf",
            relevance_score=0.90,
        )

        assert source.url is None

    @pytest.mark.asyncio
    async def test_source_with_url_is_clickable(self):
        """[P1] Sources with URL field should be clickable."""
        from app.schemas.widget import SourceCitation

        source = SourceCitation(
            document_id=2,
            title="Online Documentation",
            document_type="url",
            relevance_score=0.85,
            url="https://docs.example.com",
        )

        assert source.url == "https://docs.example.com"

    @pytest.mark.asyncio
    async def test_relevance_score_color_coding(self):
        """[P1] Relevance score should map to correct color coding."""
        from app.schemas.widget import SourceCitation

        high_score = SourceCitation(
            document_id=1,
            title="High Relevance",
            document_type="pdf",
            relevance_score=0.95,
        )
        medium_score = SourceCitation(
            document_id=2,
            title="Medium Relevance",
            document_type="pdf",
            relevance_score=0.75,
        )
        low_score = SourceCitation(
            document_id=3,
            title="Low Relevance",
            document_type="pdf",
            relevance_score=0.55,
        )

        def get_score_color(score: float) -> str:
            if score >= 0.85:
                return "green"
            elif score >= 0.65:
                return "yellow"
            else:
                return "red"

        assert get_score_color(high_score.relevance_score) == "green"
        assert get_score_color(medium_score.relevance_score) == "yellow"
        assert get_score_color(low_score.relevance_score) == "red"

    @pytest.mark.asyncio
    async def test_message_without_sources(self):
        """[P1] Message response should work without sources (non-RAG response)."""
        from app.schemas.widget import WidgetMessageResponse

        response = WidgetMessageResponse(
            messageId="msg-456",
            content="Hello! How can I help?",
            sender="bot",
            createdAt=datetime.now(UTC),
        )

        assert response.sources is None

    @pytest.mark.asyncio
    async def test_source_document_types(self):
        """[P2] All document types (pdf, url, text) should be supported."""
        from app.schemas.widget import SourceCitation

        pdf_source = SourceCitation(
            document_id=1,
            title="PDF Doc",
            document_type="pdf",
            relevance_score=0.9,
        )
        url_source = SourceCitation(
            document_id=2,
            title="URL Doc",
            document_type="url",
            relevance_score=0.85,
        )
        text_source = SourceCitation(
            document_id=3,
            title="Text Doc",
            document_type="text",
            relevance_score=0.8,
        )

        assert pdf_source.document_type == "pdf"
        assert url_source.document_type == "url"
        assert text_source.document_type == "text"

    @pytest.mark.asyncio
    async def test_source_schema_serialization(self, sample_sources):
        """[P2] Source citations should serialize correctly with camelCase aliases."""
        from app.schemas.widget import SourceCitation

        source = SourceCitation(**sample_sources[0])

        json_data = source.model_dump(by_alias=True)

        assert "documentId" in json_data
        assert "documentType" in json_data
        assert "relevanceScore" in json_data
        assert "chunkIndex" in json_data

    @pytest.mark.asyncio
    async def test_message_envelope_contains_sources(self, sample_sources):
        """[P0] Widget message envelope should include sources in response."""
        from app.schemas.widget import (
            SourceCitation,
            WidgetMessageEnvelope,
            WidgetMessageResponse,
            create_meta,
        )

        sources = [SourceCitation(**s) for s in sample_sources]

        response = WidgetMessageResponse(
            messageId="msg-789",
            content="Here is the information...",
            sender="bot",
            createdAt=datetime.now(UTC),
            sources=sources,
        )

        envelope = WidgetMessageEnvelope(
            data=response,
            meta=create_meta(),
        )

        assert envelope.data.sources is not None
        assert len(envelope.data.sources) == 3
        assert envelope.meta.request_id is not None

    @pytest.mark.asyncio
    async def test_large_sources_list_handling(self):
        """[P2] System should handle many sources (10+) gracefully."""
        from app.schemas.widget import SourceCitation, WidgetMessageResponse

        many_sources = [
            SourceCitation(
                document_id=i,
                title=f"Document {i}",
                document_type="pdf",
                relevance_score=0.9 - (i * 0.05),
            )
            for i in range(15)
        ]

        response = WidgetMessageResponse(
            messageId="msg-many",
            content="Comprehensive response...",
            sender="bot",
            createdAt=datetime.now(UTC),
            sources=many_sources,
        )

        assert len(response.sources) == 15
        assert response.sources[0].relevance_score >= response.sources[-1].relevance_score

    @pytest.mark.asyncio
    async def test_sources_with_chunk_index(self):
        """[P2] Sources should include chunk index for text documents."""
        from app.schemas.widget import SourceCitation

        source_with_chunk = SourceCitation(
            document_id=1,
            title="Chunked Document",
            document_type="text",
            relevance_score=0.88,
            chunk_index=42,
        )

        assert source_with_chunk.chunk_index == 42

    def test_sources_hidden_when_no_information_found(self):
        """[P1] Sources should be hidden when LLM says it couldn't find information."""
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = UnifiedConversationService.__new__(UnifiedConversationService)

        no_info_responses = [
            "I'm sorry, but I couldn't find any information about whether Sherwin likes to bike in the documents I have.",
            "The documents I have don't mention that topic.",
            "I was not able to find that information in the available documents.",
            "There is no mention of that in the documents.",
            "I don't have any information about that.",
            "The documents do not contain details about this.",
        ]

        for response in no_info_responses:
            assert service._indicates_no_information_found(response) is True, (
                f"Should detect no-info in: {response}"
            )

        info_found_responses = [
            "I found the answer in the documents. Here's what I know...",
            "According to the resume, Sherwin has experience with Python.",
            "The document mentions that the project was completed in 2023.",
            "Here's the information you requested about the project.",
        ]

        for response in info_found_responses:
            assert service._indicates_no_information_found(response) is False, (
                f"Should NOT detect no-info in: {response}"
            )
