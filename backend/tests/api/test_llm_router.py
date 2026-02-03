"""LLM Router API tests.

Tests for LLM router service with primary/backup failover logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.llm_configuration import LLMConfiguration
from app.models.merchant import Merchant
from app.core.database import get_db
from app.services.llm.llm_router import LLMRouter
from app.services.llm.base_llm_service import LLMMessage, LLMResponse
from app.core.errors import APIError, ErrorCode

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


class TestLLMRouterPrimary:
    """Test LLM Router with primary provider."""

    @pytest.mark.asyncio
    async def test_primary_provider_chat_success(self, async_session):
        """[P0] Should successfully route chat through primary provider."""
        config = {
            "primary_provider": "ollama",
            "primary_config": {
                "ollama_url": "http://localhost:11434",
                "model": "llama3"
            }
        }

        router = LLMRouter(config, is_testing=True)
        messages = [LLMMessage(role="user", content="Hello")]

        response = await router.chat(messages)

        assert response.content is not None
        assert response.tokens_used >= 0
        assert response.model == "llama3"

    @pytest.mark.asyncio
    async def test_primary_provider_with_model_override(self, async_session):
        """[P1] Should use model override when specified."""
        config = {
            "primary_provider": "ollama",
            "primary_config": {"ollama_url": "http://localhost:11434"}
        }

        router = LLMRouter(config, is_testing=True)
        messages = [LLMMessage(role="user", content="Test")]

        response = await router.chat(messages, model="llama2")

        assert response.model == "llama2"

    @pytest.mark.asyncio
    async def test_primary_provider_with_temperature(self, async_session):
        """[P2] Should pass temperature parameter to provider."""
        config = {
            "primary_provider": "openai",
            "primary_config": {"api_key": "test-key"}
        }

        router = LLMRouter(config, is_testing=True)
        messages = [LLMMessage(role="user", content="Test")]

        response = await router.chat(messages, temperature=0.5)

        assert response.content is not None

    @pytest.mark.asyncio
    async def test_primary_provider_max_tokens(self, async_session):
        """[P2] Should pass max_tokens parameter to provider."""
        config = {
            "primary_provider": "ollama",
            "primary_config": {"ollama_url": "http://localhost:11434"}
        }

        router = LLMRouter(config, is_testing=True)
        messages = [LLMMessage(role="user", content="Test")]

        response = await router.chat(messages, max_tokens=500)

        assert response.content is not None


class TestLLMRouterFailover:
    """Test LLM Router automatic failover logic."""

    @pytest.mark.asyncio
    async def test_failover_to_backup_on_primary_failure(self, async_session):
        """[P0] Should fallback to backup provider when primary fails."""
        config = {
            "primary_provider": "ollama",
            "primary_config": {"ollama_url": "http://invalid:11434"},
            "backup_provider": "openai",
            "backup_config": {"api_key": "test-key"}
        }

        with patch('app.services.llm.llm_factory.LLMProviderFactory.create_provider') as mock_factory:
            # Mock primary to fail
            primary_mock = AsyncMock()
            primary_mock.chat.side_effect = Exception("Primary failed")

            # Mock backup to succeed
            backup_mock = AsyncMock()
            backup_mock.chat.return_value = LLMResponse(
                content="Backup response",
                model="gpt-3.5-turbo",
                tokens_used=50,
                provider="openai"
            )

            def create_provider_side_effect(provider_name, config, is_testing=False):
                if provider_name == "ollama":
                    return primary_mock
                return backup_mock

            mock_factory.side_effect = create_provider_side_effect

            router = LLMRouter(config, is_testing=True)
            messages = [LLMMessage(role="user", content="Test")]

            response = await router.chat(messages)

            assert response.content == "Backup response"
            assert response.model == "gpt-3.5-turbo"
            assert response.tokens_used == 50

    @pytest.mark.asyncio
    async def test_both_providers_fail_raises_error(self, async_session):
        """[P0] Should raise error when both primary and backup fail."""
        config = {
            "primary_provider": "ollama",
            "primary_config": {"ollama_url": "http://invalid:11434"},
            "backup_provider": "openai",
            "backup_config": {"api_key": "invalid-key"}
        }

        with patch('app.services.llm.llm_factory.LLMProviderFactory.create_provider') as mock_factory:
            # Mock both to fail
            primary_mock = AsyncMock()
            primary_mock.chat.side_effect = Exception("Primary failed")

            backup_mock = AsyncMock()
            backup_mock.chat.side_effect = Exception("Backup failed")

            def create_provider_side_effect(provider_name, config, is_testing=False):
                if provider_name == "ollama":
                    return primary_mock
                return backup_mock

            mock_factory.side_effect = create_provider_side_effect

            router = LLMRouter(config, is_testing=True)
            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(APIError) as exc_info:
                await router.chat(messages)

            assert exc_info.value.code == ErrorCode.LLM_ROUTER_BOTH_FAILED

    @pytest.mark.asyncio
    async def test_force_backup_provider(self, async_session):
        """[P1] Should use backup when use_backup=True."""
        config = {
            "primary_provider": "ollama",
            "primary_config": {"ollama_url": "http://localhost:11434"},
            "backup_provider": "openai",
            "backup_config": {"api_key": "test-key"}
        }

        router = LLMRouter(config, is_testing=True)
        messages = [LLMMessage(role="user", content="Test")]

        response = await router.chat(messages, use_backup=True)

        assert response.content is not None


class TestLLMRouterHealthCheck:
    """Test LLM Router health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_primary_only(self, async_session):
        """[P0] Should return health status for primary provider only."""
        config = {
            "primary_provider": "ollama",
            "primary_config": {"ollama_url": "http://localhost:11434"}
        }

        router = LLMRouter(config, is_testing=True)
        health = await router.health_check()

        assert health["router"] == "healthy"
        assert health["primary_provider"] is not None
        assert health["backup_provider"] is None

    @pytest.mark.asyncio
    async def test_health_check_with_backup(self, async_session):
        """[P1] Should return health status for both providers."""
        config = {
            "primary_provider": "ollama",
            "primary_config": {"ollama_url": "http://localhost:11434"},
            "backup_provider": "openai",
            "backup_config": {"api_key": "test-key"}
        }

        router = LLMRouter(config, is_testing=True)
        health = await router.health_check()

        assert health["router"] == "healthy"
        assert health["primary_provider"] is not None
        assert health["backup_provider"] is not None


class TestLLMAPIEndpoints:
    """Test LLM Configuration API endpoints."""

    @pytest.mark.asyncio
    async def test_configure_ollama_provider(self, client_with_db):
        """[P0] Should configure Ollama provider successfully."""
        client, db = client_with_db

        # Create merchant
        merchant = Merchant(
            id=1,
            merchant_key="test_merchant_llm_router",
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
                    "ollama_model": "llama3"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["provider"] == "ollama"
        assert data["data"]["model"] == "llama3"
        assert data["data"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_configure_cloud_provider(self, client_with_db):
        """[P0] Should configure cloud provider successfully."""
        client, db = client_with_db

        # Create merchant
        merchant = Merchant(
            id=1,
            merchant_key="test_merchant_cloud_router",
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
                    "model": "gpt-3.5-turbo"
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_configure_duplicate_returns_400(self, client_with_db):
        """[P1] Should return 400 when configuring duplicate LLM."""
        client, db = client_with_db

        # Create merchant
        merchant = Merchant(
            id=1,
            merchant_key="test_merchant_duplicate_router",
            platform="facebook"
        )
        db.add(merchant)
        await db.commit()

        # First configure
        await client.post(
            "/api/llm/configure",
            json={
                "provider": "ollama",
                "ollama_config": {
                    "ollama_url": "http://localhost:11434",
                    "ollama_model": "llama3"
                }
            }
        )

        # Second configure should fail
        response = await client.post(
            "/api/llm/configure",
            json={
                "provider": "ollama",
                "ollama_config": {
                    "ollama_url": "http://localhost:11434",
                    "ollama_model": "llama3"
                }
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_status(self, client_with_db):
        """[P0] Should return current LLM status."""
        client, db = client_with_db

        # Create merchant
        merchant = Merchant(
            id=1,
            merchant_key="test_merchant_status_router",
            platform="facebook"
        )
        db.add(merchant)
        await db.commit()

        # First configure
        await client.post(
            "/api/llm/configure",
            json={
                "provider": "ollama",
                "ollama_config": {
                    "ollama_url": "http://localhost:11434",
                    "ollama_model": "llama3"
                }
            }
        )

        # Get status
        response = await client.get("/api/llm/status")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["provider"] == "ollama"
        assert data["data"]["model"] == "llama3"

    @pytest.mark.asyncio
    async def test_get_status_not_configured_returns_404(self, client_with_db):
        """[P1] Should return 404 when LLM not configured."""
        client, db = client_with_db

        # Create merchant
        merchant = Merchant(
            id=1,
            merchant_key="test_merchant_no_config_router",
            platform="facebook"
        )
        db.add(merchant)
        await db.commit()

        response = await client.get("/api/llm/status")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_llm_configuration(self, client_with_db):
        """[P1] Should update LLM configuration."""
        client, db = client_with_db

        # Create merchant
        merchant = Merchant(
            id=1,
            merchant_key="test_merchant_update_router",
            platform="facebook"
        )
        db.add(merchant)
        await db.commit()

        # First configure
        await client.post(
            "/api/llm/configure",
            json={
                "provider": "ollama",
                "ollama_config": {
                    "ollama_url": "http://localhost:11434",
                    "ollama_model": "llama3"
                }
            }
        )

        # Update model
        response = await client.put(
            "/api/llm/update",
            json={"ollama_model": "llama2"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "ollama_model" in data["data"]["updated_fields"]

    @pytest.mark.asyncio
    async def test_clear_llm_configuration(self, client_with_db):
        """[P1] Should clear LLM configuration."""
        client, db = client_with_db

        # Create merchant
        merchant = Merchant(
            id=1,
            merchant_key="test_merchant_clear_router",
            platform="facebook"
        )
        db.add(merchant)
        await db.commit()

        # First configure
        await client.post(
            "/api/llm/configure",
            json={
                "provider": "ollama",
                "ollama_config": {
                    "ollama_url": "http://localhost:11434",
                    "ollama_model": "llama3"
                }
            }
        )

        # Clear
        response = await client.delete("/api/llm/clear")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["message"] == "LLM configuration cleared"

    @pytest.mark.asyncio
    async def test_get_providers(self, client_with_db):
        """[P2] Should return list of available providers."""
        client, db = client_with_db
        response = await client.get("/api/llm/providers")

        assert response.status_code == 200
        data = response.json()
        assert "providers" in data["data"]

    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, client_with_db):
        """[P0] Should return health check status."""
        client, db = client_with_db
        response = await client.get("/api/llm/health")

        assert response.status_code == 200
        data = response.json()
        assert "router" in data["data"]

    @pytest.mark.asyncio
    async def test_llm_test_endpoint(self, client_with_db):
        """[P1] Should test LLM with validation call."""
        client, db = client_with_db

        # Create merchant
        merchant = Merchant(
            id=1,
            merchant_key="test_merchant_test_endpoint_router",
            platform="facebook"
        )
        db.add(merchant)
        await db.commit()

        # First configure
        await client.post(
            "/api/llm/configure",
            json={
                "provider": "ollama",
                "ollama_config": {
                    "ollama_url": "http://localhost:11434",
                    "ollama_model": "llama3"
                }
            }
        )

        # Test
        response = await client.post(
            "/api/llm/test",
            json={"test_prompt": "Hello"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data["data"]
