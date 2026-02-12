"""API tests for LLM configuration endpoints.

Tests LLM provider configuration, status checking, testing, updates,
and clearing using httpx.AsyncClient with ASGITransport.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.llm_configuration import LLMConfiguration
from app.models.merchant import Merchant
from app.core.database import get_db

# Use the real test engine from conftest for integration tests
from tests.conftest import test_engine, TestingSessionLocal


# Apply rate limiter check that doesn't fail in tests
@pytest.fixture(autouse=True)
def bypass_rate_limit(monkeypatch):
    """Bypass rate limiting in tests."""
    from app.core import rate_limiter
    monkeypatch.setattr(rate_limiter.RateLimiter, "is_rate_limited", lambda *args, **kwargs: False)


@pytest.fixture
async def client_with_db():
    """Return an async test client with a properly configured database setup.

    Uses dependency injection override to share the same session between
    test data creation and API calls.
    """
    # Clean database first - use CASCADE to handle foreign key constraints
    async with test_engine.begin() as conn:
        try:
            await conn.execute(text("TRUNCATE TABLE llm_conversation_costs CASCADE"))
        except Exception:
            pass  # Table may not exist yet
        try:
            await conn.execute(text("TRUNCATE TABLE llm_configurations CASCADE"))
        except Exception:
            pass  # Table may not exist yet
        try:
            await conn.execute(text("TRUNCATE TABLE merchants CASCADE"))
        except Exception:
            pass  # Table may not exist yet

    # Create the session that will be shared
    shared_session = TestingSessionLocal()

    # Track the session for cleanup
    sessions_to_close = [shared_session]

    # Override get_db to yield our shared session
    async def override_get_db():
        yield shared_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        # Use httpx.AsyncClient with ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac, shared_session
    finally:
        # Cleanup
        app.dependency_overrides.clear()
        for session in sessions_to_close:
            try:
                await session.rollback()
                await session.close()
            except Exception:
                pass


@pytest.mark.asyncio
async def test_configure_llm_ollama(client_with_db) -> None:
    """Test POST /api/llm/configure with Ollama provider."""
    client, db = client_with_db

    # Create merchant
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_llm",
        platform="facebook"
    )
    db.add(merchant)
    await db.commit()

    response = await client.post(
        "/api/llm/configure",
        json={
            "provider": "ollama",
            "ollama_config": {
                "ollama_url": "http://localhost:11434",
                "ollama_model": "llama3",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Validate envelope structure
    assert "data" in data
    assert "meta" in data

    # Validate response data
    assert data["data"]["provider"] == "ollama"
    assert data["data"]["model"] == "llama3"
    assert data["data"]["status"] == "active"
    assert data["data"]["message"] == "LLM provider configured successfully"

    # Verify database record created
    result = await db.execute(
        select(LLMConfiguration).where(
            LLMConfiguration.merchant_id == 1
        )
    )
    config = result.scalar_one_or_none()
    assert config is not None
    assert config.provider == "ollama"
    assert config.ollama_url == "http://localhost:11434"
    assert config.ollama_model == "llama3"


@pytest.mark.asyncio
async def test_configure_llm_openai(client_with_db) -> None:
    """Test POST /api/llm/configure with OpenAI provider."""
    client, db = client_with_db

    # Create merchant
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_openai",
        platform="facebook"
    )
    db.add(merchant)
    await db.commit()

    response = await client.post(
        "/api/llm/configure",
        json={
            "provider": "openai",
            "cloud_config": {
                "provider": "openai",
                "api_key": "sk-test-key",
                "model": "gpt-4o-mini",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["data"]["provider"] == "openai"
    assert data["data"]["model"] == "gpt-4o-mini"
    assert data["data"]["status"] == "active"


@pytest.mark.asyncio
async def test_configure_llm_with_backup(client_with_db) -> None:
    """Test POST /api/llm/configure with backup provider."""
    client, db = client_with_db

    # Create merchant
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_backup",
        platform="facebook"
    )
    db.add(merchant)
    await db.commit()

    response = await client.post(
        "/api/llm/configure",
        json={
            "provider": "openai",
            "cloud_config": {
                "provider": "openai",
                "api_key": "sk-test-key",
                "model": "gpt-4o-mini",
            },
            "backup_provider": "ollama",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["data"]["provider"] == "openai"

    # Verify backup stored
    result = await db.execute(
        select(LLMConfiguration).where(
            LLMConfiguration.merchant_id == 1
        )
    )
    config = result.scalar_one_or_none()
    assert config is not None
    assert config.backup_provider == "ollama"


@pytest.mark.asyncio
async def test_configure_llm_duplicate_fails(client_with_db) -> None:
    """Test POST /api/llm/configure fails when config already exists."""
    client, db = client_with_db

    # Create merchant and existing config
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_duplicate",
        platform="facebook"
    )
    db.add(merchant)

    existing_config = LLMConfiguration(
        merchant_id=1,
        provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="llama3",
        status="active",
    )
    db.add(existing_config)
    await db.commit()

    response = await client.post(
        "/api/llm/configure",
        json={
            "provider": "ollama",
            "ollama_config": {
                "ollama_url": "http://localhost:11434",
                "ollama_model": "llama3",
            },
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_llm_status(client_with_db) -> None:
    """Test GET /api/llm/status returns current configuration."""
    from datetime import datetime

    client, db = client_with_db

    # Create merchant and config
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_status",
        platform="facebook"
    )
    db.add(merchant)

    config = LLMConfiguration(
        merchant_id=1,
        provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="llama3",
        status="active",
        configured_at=datetime.utcnow(),
        last_test_at=datetime.utcnow(),
        test_result={"success": True},
        total_tokens_used=1000,
        total_cost_usd=0.0,
    )
    db.add(config)
    await db.commit()

    response = await client.get("/api/llm/status")

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert data["data"]["provider"] == "ollama"
    assert data["data"]["model"] == "llama3"
    assert data["data"]["status"] == "active"
    assert data["data"]["total_tokens_used"] == 1000
    assert data["data"]["total_cost_usd"] == 0.0


@pytest.mark.asyncio
async def test_get_llm_status_not_found(client_with_db) -> None:
    """Test GET /api/llm/status returns 404 when no config exists."""
    client, db = client_with_db

    # Create merchant without config
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_no_config",
        platform="facebook"
    )
    db.add(merchant)
    await db.commit()

    response = await client.get("/api/llm/status")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_test_llm_endpoint(client_with_db) -> None:
    """Test POST /api/llm/test with testing mode enabled."""
    client, db = client_with_db

    # Create merchant and config
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_test_endpoint",
        platform="facebook"
    )
    db.add(merchant)

    config = LLMConfiguration(
        merchant_id=1,
        provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="llama3",
        status="active",
    )
    db.add(config)
    await db.commit()

    response = await client.post(
        "/api/llm/test",
        json={"test_prompt": "Hello test"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert data["data"]["success"] is True
    assert data["data"]["provider"] == "ollama"
    assert "response" in data["data"]
    assert "latency_ms" in data["data"]
    assert data["data"]["tokens_used"] > 0


@pytest.mark.asyncio
async def test_update_llm_configuration(client_with_db) -> None:
    """Test PUT /api/llm/update updates existing configuration."""
    client, db = client_with_db

    # Create merchant and config
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_update",
        platform="facebook"
    )
    db.add(merchant)

    config = LLMConfiguration(
        merchant_id=1,
        provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="llama3",
        status="active",
    )
    db.add(config)
    await db.commit()
    config_id = config.id

    response = await client.put(
        "/api/llm/update",
        json={
            "ollama_model": "mistral",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["data"]["message"] == "LLM configuration updated"
    assert "ollama_model" in data["data"]["updated_fields"]

    # Verify database update
    await db.refresh(config)
    assert config.ollama_model == "mistral"


@pytest.mark.asyncio
async def test_update_llm_no_fields_fails(client_with_db) -> None:
    """Test PUT /api/llm/update fails with no fields to update."""
    client, db = client_with_db

    # Create merchant and config
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_no_fields",
        platform="facebook"
    )
    db.add(merchant)

    config = LLMConfiguration(
        merchant_id=1,
        provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="llama3",
        status="active",
    )
    db.add(config)
    await db.commit()

    response = await client.put(
        "/api/llm/update",
        json={},  # No fields to update
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_clear_llm_configuration(client_with_db) -> None:
    """Test DELETE /api/llm/clear removes configuration."""
    client, db = client_with_db

    # Create merchant and config
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_clear",
        platform="facebook"
    )
    db.add(merchant)

    config = LLMConfiguration(
        merchant_id=1,
        provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="llama3",
        status="active",
    )
    db.add(config)
    await db.commit()
    config_id = config.id

    response = await client.delete("/api/llm/clear")

    assert response.status_code == 200
    data = response.json()

    assert data["data"]["message"] == "LLM configuration cleared"

    # Verify deletion
    result = await db.execute(
        select(LLMConfiguration).where(LLMConfiguration.id == config_id)
    )
    deleted_config = result.scalar_one_or_none()
    assert deleted_config is None


@pytest.mark.asyncio
async def test_get_providers(client_with_db) -> None:
    """Test GET /api/llm/providers lists available providers."""
    client, _ = client_with_db

    response = await client.get("/api/llm/providers")

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert "providers" in data["data"]
    providers = data["data"]["providers"]

    # Verify expected providers exist
    provider_ids = [p["id"] for p in providers]
    assert "ollama" in provider_ids
    assert "openai" in provider_ids
    assert "anthropic" in provider_ids
    assert "gemini" in provider_ids
    assert "glm" in provider_ids

    # Verify provider structure
    for provider in providers:
        assert "id" in provider
        assert "name" in provider
        assert "description" in provider
        assert "pricing" in provider
        assert "models" in provider
        assert "features" in provider


@pytest.mark.asyncio
async def test_health_check_no_config(client_with_db) -> None:
    """Test GET /api/llm/health when no configuration exists."""
    client, db = client_with_db

    # Create merchant without config
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_no_config_health",
        platform="facebook"
    )
    db.add(merchant)
    await db.commit()

    response = await client.get("/api/llm/health")

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert data["data"]["router"] == "not_configured"
    assert data["data"]["primary_provider"] is None
    assert data["data"]["backup_provider"] is None


@pytest.mark.asyncio
async def test_health_check_with_config(client_with_db) -> None:
    """Test GET /api/llm/health with active configuration."""
    client, db = client_with_db

    # Create merchant and config
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_health",
        platform="facebook"
    )
    db.add(merchant)

    config = LLMConfiguration(
        merchant_id=1,
        provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="llama3",
        status="active",
    )
    db.add(config)
    await db.commit()

    response = await client.get("/api/llm/health")

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert data["data"]["router"] == "configured"
    assert data["data"]["primary_provider"] is not None
    assert data["data"]["primary_provider"]["provider"] == "ollama"
    assert data["data"]["primary_provider"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_api_key_encryption(client_with_db) -> None:
    """Test that API keys are encrypted when stored."""
    client, db = client_with_db

    # Create merchant
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_encryption",
        platform="facebook"
    )
    db.add(merchant)
    await db.commit()

    original_key = "sk-test-api-key-12345"

    await client.post(
        "/api/llm/configure",
        json={
            "provider": "openai",
            "cloud_config": {
                "provider": "openai",
                "api_key": original_key,
                "model": "gpt-4o-mini",
            },
        },
    )

    # Verify encryption in database
    result = await db.execute(
        select(LLMConfiguration).where(
            LLMConfiguration.merchant_id == 1
        )
    )
    config = result.scalar_one_or_none()

    assert config is not None
    assert config.api_key_encrypted is not None
    # Encrypted value should not equal plaintext
    assert config.api_key_encrypted != original_key


@pytest.mark.asyncio
async def test_configure_ollama_without_config_fails(client_with_db) -> None:
    """Test POST /api/llm/configure fails for Ollama without ollama_config."""
    client, _ = client_with_db

    response = await client.post(
        "/api/llm/configure",
        json={
            "provider": "ollama",
            # Missing ollama_config
        },
    )

    # Should return validation error
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_configure_cloud_without_config_fails(client_with_db) -> None:
    """Test POST /api/llm/configure fails for cloud without cloud_config."""
    client, _ = client_with_db

    response = await client.post(
        "/api/llm/configure",
        json={
            "provider": "openai",
            # Missing cloud_config
        },
    )

    # Should return validation error
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_update_multiple_fields(client_with_db) -> None:
    """Test PUT /api/llm/update updates multiple fields at once."""
    client, db = client_with_db

    # Create merchant and config
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_multi_update",
        platform="facebook"
    )
    db.add(merchant)

    config = LLMConfiguration(
        merchant_id=1,
        provider="ollama",
        ollama_url="http://localhost:11434",
        ollama_model="llama3",
        status="active",
    )
    db.add(config)
    await db.commit()

    response = await client.put(
        "/api/llm/update",
        json={
            "ollama_url": "http://localhost:11435",
            "ollama_model": "mistral",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "ollama_url" in data["data"]["updated_fields"]
    assert "ollama_model" in data["data"]["updated_fields"]
    assert len(data["data"]["updated_fields"]) == 2


@pytest.mark.asyncio
async def test_configure_anthropic_provider(client_with_db) -> None:
    """Test POST /api/llm/configure with Anthropic provider."""
    client, db = client_with_db

    # Create merchant
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_anthropic",
        platform="facebook"
    )
    db.add(merchant)
    await db.commit()

    response = await client.post(
        "/api/llm/configure",
        json={
            "provider": "anthropic",
            "cloud_config": {
                "provider": "anthropic",
                "api_key": "sk-ant-test-key",
                "model": "claude-3-haiku-20240307",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["data"]["provider"] == "anthropic"
    assert data["data"]["model"] == "claude-3-haiku-20240307"


@pytest.mark.asyncio
async def test_configure_gemini_provider(client_with_db) -> None:
    """Test POST /api/llm/configure with Gemini provider."""
    client, db = client_with_db

    # Create merchant
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_gemini",
        platform="facebook"
    )
    db.add(merchant)
    await db.commit()

    response = await client.post(
        "/api/llm/configure",
        json={
            "provider": "gemini",
            "cloud_config": {
                "provider": "gemini",
                "api_key": "test-gemini-key",
                "model": "gemini-1.5-flash",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["data"]["provider"] == "gemini"
    assert data["data"]["model"] == "gemini-1.5-flash"


@pytest.mark.asyncio
async def test_configure_glm_provider(client_with_db) -> None:
    """Test POST /api/llm/configure with GLM provider."""
    client, db = client_with_db

    # Create merchant
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_glm",
        platform="facebook"
    )
    db.add(merchant)
    await db.commit()

    response = await client.post(
        "/api/llm/configure",
        json={
            "provider": "glm",
            "cloud_config": {
                "provider": "glm",
                "api_key": "test-glm-key",
                "model": "glm-4-plus",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["data"]["provider"] == "glm"
    assert data["data"]["model"] == "glm-4-plus"


@pytest.mark.asyncio
async def test_ollama_cost_always_zero(client_with_db) -> None:
    """Test that Ollama provider always has zero cost."""
    client, db = client_with_db

    # Create merchant
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_ollama_cost",
        platform="facebook"
    )
    db.add(merchant)
    await db.commit()

    response = await client.post(
        "/api/llm/configure",
        json={
            "provider": "ollama",
            "ollama_config": {
                "ollama_url": "http://localhost:11434",
                "ollama_model": "llama3",
            },
        },
    )

    assert response.status_code == 200

    # Verify cost is zero in database
    result = await db.execute(
        select(LLMConfiguration).where(
            LLMConfiguration.merchant_id == 1
        )
    )
    config = result.scalar_one_or_none()
    assert config is not None
    assert config.total_cost_usd == 0.0


@pytest.mark.asyncio
async def test_test_llm_with_cloud_provider(client_with_db) -> None:
    """Test POST /api/llm/test with cloud provider (testing mode)."""
    from app.core.security import encrypt_access_token

    client, db = client_with_db

    # Create merchant and config with OpenAI
    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_openai_test",
        platform="facebook"
    )
    db.add(merchant)
    await db.flush()  # Ensure merchant is inserted first

    # Create a properly encrypted API key
    encrypted_key = encrypt_access_token("sk-test-key-12345")

    config = LLMConfiguration(
        merchant_id=1,
        provider="openai",
        cloud_model="gpt-4o-mini",
        api_key_encrypted=encrypted_key,
        status="active",
    )
    db.add(config)
    await db.commit()

    response = await client.post(
        "/api/llm/test",
        json={"test_prompt": "Hello test"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "data" in data
    assert data["data"]["success"] is True
    assert data["data"]["provider"] == "openai"
