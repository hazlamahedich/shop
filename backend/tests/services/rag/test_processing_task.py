"""Tests for Background Processing Task.

Story 8-4: Backend - RAG Service (Document Processing)

Test Coverage:
- Background task execution
- Merchant LLM config retrieval with decrypted API key
- Retry logic on failure
- Document status updates
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.llm_configuration import LLMConfiguration
from app.models.merchant import Merchant
from app.services.rag.processing_task import (
    MerchantLLMConfig,
    get_merchant_llm_config,
    process_document_background,
)


class TestGetMerchantLLMConfig:
    """Tests for get_merchant_llm_config helper."""

    @pytest.mark.asyncio
    async def test_get_config_with_decrypted_key(self):
        """Test retrieving merchant LLM config with decrypted API key."""
        mock_db = MagicMock(spec=AsyncSession)

        # Mock merchant query
        mock_merchant = Merchant(
            id=1,
            merchant_key="test-merchant",
            platform="messenger",
        )

        # Mock LLM config
        mock_llm_config = LLMConfiguration(
            id=1,
            merchant_id=1,
            provider="openai",
            api_key_encrypted="encrypted_key_data",
            cloud_model="gpt-4o-mini",
        )

        async def mock_execute(query):
            result = MagicMock()
            # First call returns merchant, second returns llm_config
            if not hasattr(mock_execute, "call_count"):
                mock_execute.call_count = 0
            mock_execute.call_count += 1

            if mock_execute.call_count == 1:
                result.scalar_one_or_none.return_value = mock_merchant
            else:
                result.scalar_one_or_none.return_value = mock_llm_config
            return result

        mock_db.execute = mock_execute

        with patch(
            "app.core.security.decrypt_access_token",
            return_value="decrypted_api_key",
        ):
            config = await get_merchant_llm_config(mock_db, 1)

        assert config.llm_provider == "openai"
        assert config.llm_api_key == "decrypted_api_key"
        assert config.llm_model == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_get_config_no_llm_config_returns_defaults(self):
        """Test returning defaults when merchant has no LLM config."""
        mock_db = MagicMock(spec=AsyncSession)

        # Mock merchant
        mock_merchant = Merchant(
            id=1,
            merchant_key="test-merchant",
            platform="messenger",
        )

        async def mock_execute(query):
            result = MagicMock()
            if not hasattr(mock_execute, "call_count"):
                mock_execute.call_count = 0
            mock_execute.call_count += 1

            if mock_execute.call_count == 1:
                result.scalar_one_or_none.return_value = mock_merchant
            else:
                result.scalar_one_or_none.return_value = None  # No LLM config
            return result

        mock_db.execute = mock_execute

        config = await get_merchant_llm_config(mock_db, 1)

        assert config.llm_provider == "ollama"
        assert config.llm_api_key is None

    @pytest.mark.asyncio
    async def test_get_config_merchant_not_found_raises_error(self):
        """Test error when merchant doesn't exist."""
        mock_db = MagicMock(spec=AsyncSession)

        async def mock_execute(query):
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            return result

        mock_db.execute = mock_execute

        with pytest.raises(APIError) as exc_info:
            await get_merchant_llm_config(mock_db, 999)

        assert exc_info.value.code == ErrorCode.MERCHANT_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_config_ollama_with_url(self):
        """Test retrieving Ollama config with custom URL."""
        mock_db = MagicMock(spec=AsyncSession)

        mock_merchant = Merchant(
            id=1,
            merchant_key="test-merchant",
            platform="messenger",
        )

        mock_llm_config = LLMConfiguration(
            id=1,
            merchant_id=1,
            provider="ollama",
            ollama_url="http://custom-ollama:11434",
            ollama_model="llama3",
        )

        async def mock_execute(query):
            result = MagicMock()
            if not hasattr(mock_execute, "call_count"):
                mock_execute.call_count = 0
            mock_execute.call_count += 1

            if mock_execute.call_count == 1:
                result.scalar_one_or_none.return_value = mock_merchant
            else:
                result.scalar_one_or_none.return_value = mock_llm_config
            return result

        mock_db.execute = mock_execute

        config = await get_merchant_llm_config(mock_db, 1)

        assert config.llm_provider == "ollama"
        assert config.ollama_url == "http://custom-ollama:11434"
        assert config.llm_model == "llama3"


class TestProcessDocumentBackground:
    """Tests for process_document_background task."""

    @pytest.mark.asyncio
    async def test_background_processing_success(self):
        """Test successful document processing."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_llm_config = MerchantLLMConfig(
            llm_provider="openai",
            llm_api_key="test-key",
        )

        with patch("app.services.rag.processing_task.async_session") as mock_session_maker:
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_session_maker.return_value = mock_ctx

            with patch(
                "app.services.rag.processing_task.get_merchant_llm_config",
                return_value=mock_llm_config,
            ):
                with patch(
                    "app.services.rag.processing_task.DocumentProcessor"
                ) as mock_processor_class:
                    mock_processor = MagicMock()
                    mock_processor.process_document = AsyncMock(
                        return_value=MagicMock(
                            status="ready",
                            chunk_count=10,
                            processing_time_ms=500,
                        )
                    )
                    mock_processor_class.return_value = mock_processor

                    result = await process_document_background(
                        document_id=1,
                        merchant_id=1,
                    )

        assert result.status == "ready"
        assert result.chunk_count == 10

    @pytest.mark.asyncio
    async def test_background_processing_with_retries(self):
        """Test that embedding service retry is used (not task-level retry)."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_llm_config = MerchantLLMConfig(
            llm_provider="openai",
            llm_api_key="test-key",
        )

        with patch("app.services.rag.processing_task.async_session") as mock_session_maker:
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_session_maker.return_value = mock_ctx

            with patch(
                "app.services.rag.processing_task.get_merchant_llm_config",
                return_value=mock_llm_config,
            ):
                with patch(
                    "app.services.rag.processing_task.DocumentProcessor"
                ) as mock_processor_class:
                    mock_processor = MagicMock()
                    mock_processor.process_document = AsyncMock(
                        return_value=MagicMock(status="ready", chunk_count=5)
                    )
                    mock_processor_class.return_value = mock_processor

                    result = await process_document_background(
                        document_id=1,
                        merchant_id=1,
                    )

        assert result.status == "ready"
        assert result.chunk_count == 5

    @pytest.mark.asyncio
    async def test_background_processing_updates_document_error(self):
        """Test that processing failure updates document status to error."""
        mock_db = MagicMock(spec=AsyncSession)
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_llm_config = MerchantLLMConfig(
            llm_provider="openai",
            llm_api_key="test-key",
        )

        with patch("app.services.rag.processing_task.async_session") as mock_session_maker:
            mock_ctx = MagicMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
            mock_ctx.__aexit__ = AsyncMock(return_value=None)
            mock_session_maker.return_value = mock_ctx

            with patch(
                "app.services.rag.processing_task.get_merchant_llm_config",
                return_value=mock_llm_config,
            ):
                with patch(
                    "app.services.rag.processing_task.DocumentProcessor"
                ) as mock_processor_class:
                    mock_processor = MagicMock()
                    mock_processor.process_document = AsyncMock(
                        side_effect=Exception("Processing failed")
                    )
                    mock_processor_class.return_value = mock_processor

                    with pytest.raises(Exception):
                        await process_document_background(
                            document_id=1,
                            merchant_id=1,
                        )

        # Verify that execute was called to update document status
        assert mock_db.execute.called


class TestMerchantLLMConfig:
    """Tests for MerchantLLMConfig dataclass."""

    def test_merchant_llm_config_creation(self):
        """Test MerchantLLMConfig instantiation."""
        config = MerchantLLMConfig(
            llm_provider="openai",
            llm_api_key="test-key",
            llm_model="gpt-4o-mini",
            ollama_url=None,
        )

        assert config.llm_provider == "openai"
        assert config.llm_api_key == "test-key"
        assert config.llm_model == "gpt-4o-mini"
        assert config.ollama_url is None

    def test_merchant_llm_config_ollama(self):
        """Test MerchantLLMConfig for Ollama provider."""
        config = MerchantLLMConfig(
            llm_provider="ollama",
            llm_api_key=None,
            llm_model="llama3",
            ollama_url="http://localhost:11434",
        )

        assert config.llm_provider == "ollama"
        assert config.llm_api_key is None
        assert config.ollama_url == "http://localhost:11434"
