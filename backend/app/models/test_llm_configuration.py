"""Tests for LLM Configuration ORM model.

Tests model validation, relationships, and CRUD operations.
"""

from __future__ import annotations

import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_configuration import LLMConfiguration
from app.models.merchant import Merchant
from app.core.database import async_session


@pytest.mark.asyncio
async def test_llm_configuration_creation(db_session: AsyncSession) -> None:
    """Test creating an LLM configuration record."""

    # First create a merchant
    merchant = Merchant(
        merchant_key="test-merchant-llm",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create LLM configuration
    config = LLMConfiguration(
        merchant_id=merchant.id,
        provider="openai",
        api_key_encrypted="encrypted_key_here",
        cloud_model="gpt-4o-mini",
        status="active",
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    assert config.id is not None
    assert config.merchant_id == merchant.id
    assert config.provider == "openai"
    assert config.api_key_encrypted == "encrypted_key_here"
    assert config.cloud_model == "gpt-4o-mini"
    assert config.status == "active"
    assert config.configured_at is not None
    assert config.total_tokens_used == 0
    assert config.total_cost_usd == 0.0


@pytest.mark.asyncio
async def test_llm_configuration_ollama(db_session: AsyncSession) -> None:
    """Test creating an Ollama configuration."""

    # Create merchant
    merchant = Merchant(
        merchant_key="test-merchant-ollama",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create Ollama configuration
    config = LLMConfiguration(
        merchant_id=merchant.id,
        provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="llama3",
        status="active",
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    assert config.provider == "ollama"
    assert config.ollama_url == "http://localhost:11434"
    assert config.ollama_model == "llama3"
    assert config.api_key_encrypted is None


@pytest.mark.asyncio
async def test_llm_configuration_with_backup(db_session: AsyncSession) -> None:
    """Test creating an LLM configuration with backup provider."""

    # Create merchant
    merchant = Merchant(
        merchant_key="test-merchant-backup",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create configuration with backup
    config = LLMConfiguration(
        merchant_id=merchant.id,
        provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="llama3",
        backup_provider="openai",
        backup_api_key_encrypted="encrypted_backup_key",
        status="active",
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    assert config.provider == "ollama"
    assert config.backup_provider == "openai"
    assert config.backup_api_key_encrypted == "encrypted_backup_key"


@pytest.mark.asyncio
async def test_llm_configuration_unique_merchant(db_session: AsyncSession) -> None:
    """Test that each merchant can only have one LLM configuration."""

    # Create merchant
    merchant = Merchant(
        merchant_key="test-merchant-unique",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create first configuration
    config1 = LLMConfiguration(
        merchant_id=merchant.id,
        provider="openai",
        api_key_encrypted="encrypted_key_1",
        cloud_model="gpt-4o-mini",
        status="active",
    )
    db_session.add(config1)
    await db_session.commit()

    # Attempt to create second configuration for same merchant
    config2 = LLMConfiguration(
        merchant_id=merchant.id,
        provider="anthropic",
        api_key_encrypted="encrypted_key_2",
        cloud_model="claude-3-haiku",
        status="active",
    )
    db_session.add(config2)

    with pytest.raises(Exception):  # IntegrityError expected
        await db_session.commit()


@pytest.mark.asyncio
async def test_llm_configuration_test_result(db_session: AsyncSession) -> None:
    """Test storing test result metadata."""

    # Create merchant
    merchant = Merchant(
        merchant_key="test-merchant-test-result",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create configuration with test result
    test_result = {
        "success": True,
        "latency_ms": 123.4,
        "model": "gpt-4o-mini",
        "tokens_used": 10,
    }
    config = LLMConfiguration(
        merchant_id=merchant.id,
        provider="openai",
        api_key_encrypted="encrypted_key",
        cloud_model="gpt-4o-mini",
        status="active",
        test_result=test_result,
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    assert config.test_result == test_result
    assert config.test_result["success"] is True
    assert config.test_result["latency_ms"] == 123.4


@pytest.mark.asyncio
async def test_llm_configuration_updated_at(db_session: AsyncSession) -> None:
    """Test that updated_at changes on modification."""

    # Create merchant
    merchant = Merchant(
        merchant_key="test-merchant-updated-at",
        platform="fly.io",
        status="active",
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    # Create configuration
    config = LLMConfiguration(
        merchant_id=merchant.id,
        provider="openai",
        api_key_encrypted="encrypted_key",
        cloud_model="gpt-4o-mini",
        status="pending",
    )
    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    original_updated_at = config.updated_at

    # Update configuration
    config.status = "active"
    await db_session.commit()
    await db_session.refresh(config)

    assert config.updated_at > original_updated_at
