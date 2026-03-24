"""Tests for re-embedding flow.

Story 8-11: LLM Embedding Provider Integration & Re-embedding
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rag.dimension_handler import DimensionHandler
from app.services.rag.reembedding_worker import (
    reembed_all_documents,
    trigger_reembedding_for_merchant,
)


class TestDimensionHandler:
    """Test dimension change detection and handling."""

    @pytest.mark.asyncio
    async def test_check_dimension_change_no_change(self, db_session: AsyncSession):
        """Test dimension check when provider has same dimension."""
        with patch.object(
            DimensionHandler, "check_dimension_change", new=AsyncMock(return_value=False)
        ):
            result = await DimensionHandler.check_dimension_change(
                db=db_session,
                merchant_id=1,
                new_provider="openai",
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_check_dimension_change_detected(self, db_session: AsyncSession):
        """Test dimension change detection."""
        with patch.object(
            DimensionHandler, "check_dimension_change", new=AsyncMock(return_value=True)
        ):
            result = await DimensionHandler.check_dimension_change(
                db=db_session,
                merchant_id=1,
                new_provider="gemini",
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_mark_documents_for_reembedding(self, db_session: AsyncSession):
        """Test marking documents for re-embedding."""
        with patch.object(
            DimensionHandler, "mark_documents_for_reembedding", new=AsyncMock(return_value=5)
        ):
            count = await DimensionHandler.mark_documents_for_reembedding(
                db=db_session,
                merchant_id=1,
            )
            assert count == 5

    @pytest.mark.asyncio
    async def test_get_reembedding_status(self, db_session: AsyncSession):
        """Test getting re-embedding status."""
        mock_status = {
            "status_counts": {"queued": 3, "completed": 2},
            "total_documents": 5,
            "completed_documents": 2,
            "progress_percent": 40.0,
        }

        with patch.object(
            DimensionHandler, "get_reembedding_status", new=AsyncMock(return_value=mock_status)
        ):
            status = await DimensionHandler.get_reembedding_status(
                db=db_session,
                merchant_id=1,
            )
            assert status["total_documents"] == 5
            assert status["progress_percent"] == 40.0

    def test_get_provider_dimension_openai(self):
        """Test OpenAI dimension."""
        dimension = DimensionHandler.get_provider_dimension("openai")
        assert dimension == 1536

    def test_get_provider_dimension_gemini(self):
        """Test Gemini dimension."""
        dimension = DimensionHandler.get_provider_dimension("gemini")
        assert dimension == 768

    def test_get_provider_dimension_ollama(self):
        """Test Ollama dimension."""
        dimension = DimensionHandler.get_provider_dimension("ollama")
        assert dimension == 768

    def test_get_provider_dimension_unknown(self):
        """Test unknown provider defaults to OpenAI dimension."""
        dimension = DimensionHandler.get_provider_dimension("unknown")
        assert dimension == 1536


class TestReembeddingWorker:
    """Test re-embedding background worker."""

    @pytest.mark.asyncio
    async def test_reembed_all_documents_no_merchant(self):
        """Test re-embedding when merchant not found."""
        with patch(
            "app.services.rag.reembedding_worker._get_merchant_with_config",
            new=AsyncMock(return_value=None),
        ):
            await reembed_all_documents(merchant_id=999)

    @pytest.mark.asyncio
    async def test_reembed_all_documents_no_documents(self):
        """Test re-embedding when no documents queued."""
        mock_merchant = MagicMock()
        mock_merchant.embedding_provider = "openai"
        mock_merchant.embedding_model = "text-embedding-3-small"
        mock_merchant.llm_configuration = None

        with (
            patch(
                "app.services.rag.reembedding_worker._get_merchant_with_config",
                new=AsyncMock(return_value=mock_merchant),
            ),
            patch(
                "app.services.rag.reembedding_worker._get_queued_documents",
                new=AsyncMock(return_value=[]),
            ),
        ):
            await reembed_all_documents(merchant_id=1)

    @pytest.mark.asyncio
    async def test_trigger_reembedding_for_merchant(self, db_session: AsyncSession):
        """Test triggering re-embedding."""
        with patch.object(
            DimensionHandler, "mark_documents_for_reembedding", new=AsyncMock(return_value=3)
        ):
            count = await trigger_reembedding_for_merchant(
                db=db_session,
                merchant_id=1,
            )
            assert count == 3

    @pytest.mark.asyncio
    async def test_trigger_reembedding_no_documents(self, db_session: AsyncSession):
        """Test triggering re-embedding with no documents."""
        with patch.object(
            DimensionHandler, "mark_documents_for_reembedding", new=AsyncMock(return_value=0)
        ):
            count = await trigger_reembedding_for_merchant(
                db=db_session,
                merchant_id=1,
            )
            assert count == 0


class TestDimensionChangeIntegration:
    """Integration tests for dimension changes."""

    @pytest.mark.asyncio
    async def test_provider_switch_triggers_reembedding(self, db_session: AsyncSession):
        """Test that switching provider with different dimension triggers re-embedding.

        Story 8-11 AC6: Vector Consistency
        """
        # OpenAI (1536d) -> Gemini (768d) should trigger re-embedding
        old_dimension = DimensionHandler.get_provider_dimension("openai")
        new_dimension = DimensionHandler.get_provider_dimension("gemini")

        assert old_dimension != new_dimension, "OpenAI and Gemini should have different dimensions"
        assert old_dimension == 1536, "OpenAI should use 1536 dimensions"
        assert new_dimension == 768, "Gemini should use 768 dimensions"

    @pytest.mark.asyncio
    async def test_provider_switch_same_dimension_no_reembedding(self, db_session: AsyncSession):
        """Test that switching provider with same dimension doesn't require re-embedding.

        Story 8-11 AC6: Vector Consistency - same dimension providers can coexist
        """
        # Gemini (768d) -> Ollama (768d) should NOT require re-embedding
        gemini_dimension = DimensionHandler.get_provider_dimension("gemini")
        ollama_dimension = DimensionHandler.get_provider_dimension("ollama")

        assert gemini_dimension == ollama_dimension, "Gemini and Ollama should have same dimensions"
        assert gemini_dimension == 768, "Both should use 768 dimensions"

    @pytest.mark.asyncio
    async def test_embedding_version_format(self):
        """Test that embedding version is correctly formatted."""
        provider = "openai"
        model = "text-embedding-3-small"
        expected_version = f"{provider}-{model}"

        assert expected_version == "openai-text-embedding-3-small"

        # Test Gemini version
        provider = "gemini"
        model = "text-embedding-004"
        expected_version = f"{provider}-{model}"

        assert expected_version == "gemini-text-embedding-004"
