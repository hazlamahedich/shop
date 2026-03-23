import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.llm import sync_merchant_embedding_settings
from app.models.merchant import Merchant

@pytest.mark.asyncio
async def test_sync_merchant_embedding_settings_gemini():
    # Mock DB session and merchant
    db = MagicMock(spec=AsyncSession)
    merchant = Merchant(id=1, embedding_provider="openai", embedding_model="old")
    
    # Mock db.execute to return the merchant
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = merchant
    db.execute = AsyncMock(return_value=mock_result)
    
    # Run sync for Gemini
    await sync_merchant_embedding_settings(db, 1, "gemini")
    
    # Verify updates
    assert merchant.embedding_provider == "gemini"
    assert merchant.embedding_model == "gemini-embedding-001"
    assert merchant.embedding_dimension == 768

@pytest.mark.asyncio
async def test_sync_merchant_embedding_settings_openai():
    # Mock DB session and merchant
    db = MagicMock(spec=AsyncSession)
    merchant = Merchant(id=1, embedding_provider="gemini", embedding_model="old")
    
    # Mock db.execute to return the merchant
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = merchant
    db.execute = AsyncMock(return_value=mock_result)
    
    # Run sync for OpenAI
    await sync_merchant_embedding_settings(db, 1, "openai")
    
    # Verify updates
    assert merchant.embedding_provider == "openai"
    assert merchant.embedding_model == "text-embedding-3-small"
    assert merchant.embedding_dimension == 1536

@pytest.mark.asyncio
async def test_sync_merchant_embedding_settings_ollama():
    # Mock DB session and merchant
    db = MagicMock(spec=AsyncSession)
    merchant = Merchant(id=1, embedding_provider="openai", embedding_model="old")
    
    # Mock db.execute to return the merchant
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = merchant
    db.execute = AsyncMock(return_value=mock_result)
    
    # Run sync for Ollama
    await sync_merchant_embedding_settings(db, 1, "ollama", ollama_model="llama3")
    
    # Verify updates
    assert merchant.embedding_provider == "ollama"
    assert merchant.embedding_model == "llama3"
    assert merchant.embedding_dimension == 768
