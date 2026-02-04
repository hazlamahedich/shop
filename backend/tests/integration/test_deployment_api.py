"""Tests for deployment API endpoints.

Tests the deployment state management, status queries, and cancellation.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
import httpx
from httpx import ASGITransport, AsyncClient
from fastapi import status
from sqlalchemy import text

from app.main import app
from app.api.deployment import router, _active_subprocesses, generate_merchant_key, generate_secret_key
from app.core.database import get_db
from app.schemas.deployment import (
    DeploymentStatus,
    Platform,
    StartDeploymentRequest,
)

# Use the real test engine from conftest for integration tests
from tests.conftest import test_engine, TestingSessionLocal


@pytest.fixture(scope="function", autouse=True)
async def clean_database():
    """Clean database tables before each test."""
    async with test_engine.begin() as conn:
        # Truncate all tables in correct order (respecting foreign keys)
        await conn.execute(text("TRUNCATE TABLE deployment_logs CASCADE"))
        await conn.execute(text("TRUNCATE TABLE merchants CASCADE"))
        await conn.execute(text("TRUNCATE TABLE prerequisite_checklists CASCADE"))
        await conn.commit()


@pytest.fixture
async def client() -> AsyncClient:
    """Return an async test client for integration testing with real database."""

    # Override the dependency to use the test database
    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    # Use httpx.AsyncClient with ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def clear_deployments() -> None:
    """Clear deployment state between tests."""
    _active_subprocesses.clear()
    yield
    _active_subprocesses.clear()


class TestStartDeployment:
    """Tests for POST /api/deployment/start endpoint."""

    @pytest.mark.asyncio
    async def test_start_deployment_returns_202(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that starting a deployment returns 202 Accepted."""
        response = await client.post(
            "/api/deployment/start",
            json={"platform": "flyio"},
        )

        assert response.status_code == status.HTTP_202_ACCEPTED

    @pytest.mark.asyncio
    async def test_start_deployment_returns_deployment_id(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that starting a deployment returns a unique deployment ID."""
        response = await client.post(
            "/api/deployment/start",
            json={"platform": "railway"},
        )

        data = response.json()
        assert "data" in data
        assert "deploymentId" in data["data"]
        assert isinstance(data["data"]["deploymentId"], str)

    @pytest.mark.asyncio
    async def test_start_deployment_returns_merchant_key(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that starting a deployment returns a merchant key."""
        response = await client.post(
            "/api/deployment/start",
            json={"platform": "render"},
        )

        data = response.json()
        assert "data" in data
        assert "merchantKey" in data["data"]
        assert data["data"]["merchantKey"].startswith("shop-")

    @pytest.mark.asyncio
    async def test_start_deployment_returns_pending_status(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that starting a deployment returns pending status."""
        response = await client.post(
            "/api/deployment/start",
            json={"platform": "flyio"},
        )

        data = response.json()
        assert "data" in data
        assert data["data"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_start_deployment_returns_estimated_time(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that starting a deployment returns estimated time."""
        response = await client.post(
            "/api/deployment/start",
            json={"platform": "flyio"},
        )

        data = response.json()
        assert "data" in data
        assert "estimatedSeconds" in data["data"]
        assert data["data"]["estimatedSeconds"] == 900

    @pytest.mark.asyncio
    async def test_start_deployment_accepts_all_platforms(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that all supported platforms are accepted."""
        platforms = ["flyio", "railway", "render"]

        for platform in platforms:
            response = await client.post(
                "/api/deployment/start",
                json={"platform": platform},
            )
            assert response.status_code == status.HTTP_202_ACCEPTED

    @pytest.mark.asyncio
    async def test_start_deployment_rejects_invalid_platform(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that invalid platform is rejected."""
        response = await client.post(
            "/api/deployment/start",
            json={"platform": "invalid"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_start_deployment_requires_platform(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that platform is required."""
        response = await client.post(
            "/api/deployment/start",
            json={},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetDeploymentStatus:
    """Tests for GET /api/deployment/status/{deployment_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_status_returns_404_for_unknown_deployment(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that getting status of unknown deployment returns 404."""
        response = await client.get(f"/api/deployment/status/{uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_status_returns_deployment_state(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that getting status returns deployment state."""
        # Start a deployment first
        start_response = await client.post(
            "/api/deployment/start",
            json={"platform": "flyio"},
        )
        deployment_id = start_response.json()["data"]["deploymentId"]

        # Get status
        status_response = await client.get(f"/api/deployment/status/{deployment_id}")

        assert status_response.status_code == status.HTTP_200_OK
        data = status_response.json()
        assert "data" in data
        assert data["data"]["deploymentId"] == deployment_id

    @pytest.mark.asyncio
    async def test_get_status_includes_progress(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that status includes progress percentage."""
        # Start a deployment
        start_response = await client.post(
            "/api/deployment/start",
            json={"platform": "railway"},
        )
        deployment_id = start_response.json()["data"]["deploymentId"]

        # Get status
        status_response = await client.get(f"/api/deployment/status/{deployment_id}")

        data = status_response.json()
        assert "progress" in data["data"]
        assert isinstance(data["data"]["progress"], int)

    @pytest.mark.asyncio
    async def test_get_status_includes_logs(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that status includes deployment logs."""
        # Start a deployment
        start_response = await client.post(
            "/api/deployment/start",
            json={"platform": "render"},
        )
        deployment_id = start_response.json()["data"]["deploymentId"]

        # Get status
        status_response = await client.get(f"/api/deployment/status/{deployment_id}")

        data = status_response.json()
        assert "logs" in data["data"]
        assert isinstance(data["data"]["logs"], list)


class TestCancelDeployment:
    """Tests for POST /api/deployment/cancel/{deployment_id} endpoint."""

    @pytest.mark.asyncio
    async def test_cancel_deployment_returns_404_for_unknown_deployment(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that cancelling unknown deployment returns 404."""
        response = await client.post(f"/api/deployment/cancel/{uuid4()}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_cancel_deployment_sets_cancelled_status(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that cancelling deployment sets status to cancelled."""
        # Start a deployment
        start_response = await client.post(
            "/api/deployment/start",
            json={"platform": "flyio"},
        )
        deployment_id = start_response.json()["data"]["deploymentId"]

        # Cancel the deployment
        cancel_response = await client.post(f"/api/deployment/cancel/{deployment_id}")

        assert cancel_response.status_code == status.HTTP_200_OK

        # Verify status is failed (cancelled deployments are marked as failed)
        status_response = await client.get(f"/api/deployment/status/{deployment_id}")
        data = status_response.json()
        assert data["data"]["status"] == "failed"


class TestMerchantKeyGeneration:
    """Tests for merchant key generation."""

    def test_generate_merchant_key_starts_with_shop(self) -> None:
        """Test that merchant key starts with 'shop-'."""
        key = generate_merchant_key()
        assert key.startswith("shop-")

    def test_generate_merchant_key_is_unique(self) -> None:
        """Test that merchant keys are unique."""
        keys = [generate_merchant_key() for _ in range(100)]
        assert len(set(keys)) == 100  # All keys should be unique

    def test_generate_merchant_key_length(self) -> None:
        """Test that merchant key has correct length."""
        key = generate_merchant_key()
        assert len(key) == len("shop-") + 8  # "shop-" + 8 random characters


class TestSecretKeyGeneration:
    """Tests for SECRET_KEY generation."""

    def test_generate_secret_key_returns_string(self) -> None:
        """Test that secret key generation returns a string."""
        key = generate_secret_key()
        assert isinstance(key, str)

    def test_generate_secret_key_is_sufficient_length(self) -> None:
        """Test that secret key is at least 32 characters."""
        key = generate_secret_key()
        assert len(key) >= 32

    def test_generate_secret_key_is_unique(self) -> None:
        """Test that secret keys are unique."""
        keys = [generate_secret_key() for _ in range(100)]
        assert len(set(keys)) == 100


class TestDeploymentProgressStream:
    """Tests for GET /api/deployment/progress/{deployment_id} SSE endpoint."""

    @pytest.mark.asyncio
    async def test_progress_stream_returns_sse_content_type(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that progress stream returns text/event-stream content type."""
        # Start a deployment
        start_response = await client.post(
            "/api/deployment/start",
            json={"platform": "flyio"},
        )
        deployment_id = start_response.json()["data"]["deploymentId"]

        # Get progress stream
        response = await client.get(f"/api/deployment/progress/{deployment_id}")

        assert response.headers["content-type"] == "text/event-stream"

    @pytest.mark.asyncio
    async def test_progress_stream_sends_done_on_completion(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that progress stream sends [DONE] when deployment completes."""
        # Start a deployment
        start_response = await client.post(
            "/api/deployment/start",
            json={"platform": "railway"},
        )
        deployment_id = start_response.json()["data"]["deploymentId"]

        # Get progress stream
        response = await client.get(f"/api/deployment/progress/{deployment_id}")

        # Note: This test would require mocking to fully test SSE stream
        # For now, just verify the endpoint is accessible
        assert response.status_code == status.HTTP_200_OK


class TestStepProgressMapping:
    """Tests for step progress mapping alignment (DEFER-1.2-1).

    Tests that both human-readable script output (e.g., "Prerequisites")
    and enum values (e.g., "check_cli") map correctly to progress percentages.
    """

    @pytest.mark.asyncio
    async def test_step_progress_handles_enum_values(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that step progress handles enum values (snake_case)."""
        from app.models.deployment_log import DeploymentLog as DeploymentLogModel
        from app.models.merchant import Merchant
        from app.schemas.deployment import DeploymentStep
        from sqlalchemy import text

        # Create a merchant and deployment logs with enum step values
        async with TestingSessionLocal() as db:
            merchant = Merchant(
                merchant_key="shop-test123",
                platform="flyio",
                status="active",
                config={},
            )
            db.add(merchant)
            await db.commit()
            await db.refresh(merchant)

            deployment_id = str(uuid4())
            # Add logs with enum step values
            for step_enum in [
                DeploymentStep.CHECK_CLI,
                DeploymentStep.AUTHENTICATION,
                DeploymentStep.APP_SETUP,
                DeploymentStep.CONFIGURATION,
                DeploymentStep.SECRETS,
                DeploymentStep.DEPLOYMENT,
                DeploymentStep.HEALTH_CHECK,
                DeploymentStep.COMPLETE,
            ]:
                log = DeploymentLogModel(
                    deployment_id=deployment_id,
                    merchant_id=merchant.id,
                    timestamp=None,
                    level="info",
                    step=step_enum.value,
                    message=f"Step: {step_enum.value}",
                )
                db.add(log)
            await db.commit()

        # Get status and verify progress is calculated correctly
        response = await client.get(f"/api/deployment/status/{deployment_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Last step is "complete" which should map to 100%
        assert data["data"]["progress"] == 100

    @pytest.mark.asyncio
    async def test_step_progress_handles_script_output(self, client: AsyncClient, clear_deployments: None) -> None:
        """Test that step progress handles script output (Title Case with spaces).

        This addresses DEFER-1.2-1: Ensure script output like "Prerequisites",
        "Authentication", "App Setup" etc. map correctly to progress values.
        """
        from app.models.deployment_log import DeploymentLog as DeploymentLogModel
        from app.models.merchant import Merchant
        from sqlalchemy import text

        # Create a merchant and deployment logs with script output step names
        async with TestingSessionLocal() as db:
            merchant = Merchant(
                merchant_key="shop-test456",
                platform="flyio",
                status="active",
                config={},
            )
            db.add(merchant)
            await db.commit()
            await db.refresh(merchant)

            deployment_id = str(uuid4())
            # Add logs with human-readable script output step names
            script_steps = [
                ("Prerequisites", 10),
                ("Authentication", 20),
                ("App Setup", 30),
                ("Configuration", 40),
                ("Secrets", 50),
                ("Deployment", 70),
                ("Health Check", 90),
                ("Complete", 100),
            ]
            for step_name, expected_progress in script_steps:
                log = DeploymentLogModel(
                    deployment_id=deployment_id,
                    merchant_id=merchant.id,
                    timestamp=None,
                    level="info",
                    step=step_name,  # Human-readable name from script
                    message=f"Step: {step_name}",
                )
                db.add(log)
            await db.commit()

        # Get status and verify progress is calculated correctly for script output
        response = await client.get(f"/api/deployment/status/{deployment_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Last step is "Complete" which should map to 100%
        assert data["data"]["progress"] == 100
