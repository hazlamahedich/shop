"""Comprehensive API tests for deployment endpoints.

Tests all deployment API endpoints with various scenarios including:
- Happy paths for all endpoints
- Validation errors
- Rate limiting
- Error handling for deployment not found
- Response structure validation
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from fastapi import status

from app.core.errors import APIError, ErrorCode
from app.main import app
from app.schemas.deployment import Platform, DeploymentStatus, LogLevel, DeploymentStep


class TestDeploymentAPI:
    """Test suite for deployment API endpoints."""

    @pytest.fixture
    def test_client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def valid_deployment_request(self):
        """Valid deployment request data."""
        return {
            "platform": "flyio"
        }

    @pytest.fixture
    def deployment_request_with_prerequisites(self):
        """Deployment request with prerequisites."""
        return {
            "platform": "railway",
            "prerequisites": {
                "cloudAccount": True,
                "facebookAccount": True,
                "shopifyAccess": True,
                "llmProviderChoice": True
            }
        }

    @pytest.fixture
    def invalid_platform_request(self):
        """Invalid platform request data."""
        return {
            "platform": "invalid_platform"
        }

    @pytest.fixture
    def empty_request(self):
        """Empty request data."""
        return {}

    # Helper functions
    async def _create_mock_deployment_logs(self, db, deployment_id, merchant_id):
        """Create mock deployment logs."""
        from app.models.deployment_log import DeploymentLog as DeploymentLogModel
        
        # Create initial log
        initial_log = DeploymentLogModel(
            deployment_id=deployment_id,
            merchant_id=merchant_id,
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO.value,
            step=DeploymentStep.CHECK_CLI.value,
            message="Deployment initiated",
        )
        db.add(initial_log)
        
        # Create progress logs
        steps = [
            (DeploymentStep.CHECK_CLI, "Checking CLI tools", 10),
            (DeploymentStep.AUTHENTICATION, "Authenticating", 20),
            (DeploymentStep.APP_SETUP, "Setting up app", 30),
            (DeploymentStep.CONFIGURATION, "Configuring app", 40),
            (DeploymentStep.SECRETS, "Setting secrets", 50),
            (DeploymentStep.DEPLOYMENT, "Deploying to platform", 70),
            (DeploymentStep.HEALTH_CHECK, "Performing health check", 90),
        ]
        
        for step, message, progress in steps:
            log = DeploymentLogModel(
                deployment_id=deployment_id,
                merchant_id=merchant_id,
                timestamp=datetime.utcnow(),
                level=LogLevel.INFO.value,
                step=step.value if step else None,
                message=message,
            )
            db.add(log)
        
        await db.commit()
        
        # Return merchant logs for verification
        return [initial_log] + [log for _, _, _ in steps]

    # Test POST /start endpoint
    @pytest.mark.asyncio
    async def test_start_deployment_happy_path(self, test_client, async_session, valid_deployment_request):
        """Test successful deployment start."""
        with patch('app.api.deployment.DeploymentService.generate_merchant_key') as mock_gen_key, \
             patch('app.api.deployment.DeploymentService.create_merchant') as mock_create_merchant, \
             patch('app.api.deployment.DeploymentService.migrate_prerequisites') as mock_migrate, \
             patch('app.api.deployment._get_script_path') as mock_script_path, \
             patch('app.api.deployment.asyncio.create_subprocess_exec') as mock_subprocess:
            
            # Mock the script path
            mock_path = Mock(spec=Path)
            mock_path.exists.return_value = True
            mock_script_path.return_value = mock_path
            
            # Mock the merchant key generation
            test_merchant_key = "shop-test123"
            mock_gen_key.return_value = test_merchant_key
            
            # Mock merchant creation
            mock_merchant = MagicMock()
            mock_merchant.id = 1
            mock_create_merchant.return_value = mock_merchant
            
            # Mock prerequisites (not called for this request)
            mock_migrate.return_value = None
            
            # Mock subprocess
            mock_process = AsyncMock()
            mock_process.wait.return_value = 0
            mock_subprocess.return_value = mock_process
            
            response = test_client.post("/api/deployment/start", json=valid_deployment_request)
            
            # Verify response
            assert response.status_code == status.HTTP_202_ACCEPTED
            data = response.json()
            
            # Verify envelope structure
            assert "data" in data
            assert "meta" in data
            assert data["meta"]["requestId"] is not None
            
            # Verify deployment data
            deployment_data = data["data"]
            assert "deploymentId" in deployment_data
            assert "merchantKey" in deployment_data
            assert "status" in deployment_data
            assert "estimatedSeconds" in deployment_data
            
            # Verify values
            assert deployment_data["status"] == "pending"
            assert deployment_data["merchantKey"] == test_merchant_key
            assert deployment_data["estimatedSeconds"] == 900
            
            # Verify service calls
            mock_gen_key.assert_called_once()
            mock_create_merchant.assert_called_once()
            mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_deployment_with_prerequisites(self, test_client, async_session, deployment_request_with_prerequisites):
        """Test deployment start with prerequisites."""
        with patch('app.api.deployment.DeploymentService.generate_merchant_key') as mock_gen_key, \
             patch('app.api.deployment.DeploymentService.create_merchant') as mock_create_merchant, \
             patch('app.api.deployment.DeploymentService.migrate_prerequisites') as mock_migrate, \
             patch('app.api.deployment._get_script_path') as mock_script_path, \
             patch('app.api.deployment.asyncio.create_subprocess_exec') as mock_subprocess:
            
            # Mock dependencies
            mock_path = Mock(spec=Path)
            mock_path.exists.return_value = True
            mock_script_path.return_value = mock_path
            test_merchant_key = "shop-prereq123"
            mock_gen_key.return_value = test_merchant_key
            mock_merchant = MagicMock()
            mock_merchant.id = 1
            mock_create_merchant.return_value = mock_merchant
            
            # Mock prerequisites
            mock_migrate.return_value = None
            
            response = test_client.post("/api/deployment/start", json=deployment_request_with_prerequisites)
            
            assert response.status_code == status.HTTP_202_ACCEPTED
            data = response.json()
            
            # Verify migration was called
            mock_migrate.assert_called_once()
            args, kwargs = mock_migrate.call_args
            assert args[0] == async_session
            assert args[1] == mock_merchant.id
            assert "prerequisites" in kwargs
            assert kwargs["prerequisites"]["cloudAccount"] is True

    @pytest.mark.asyncio
    async def test_start_deployment_empty_body(self, test_client, async_session, empty_request):
        """Test deployment start with empty request body."""
        response = test_client.post("/api/deployment/start", json=empty_request)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        
        assert "error_code" in data
        assert data["error_code"] == ErrorCode.VALIDATION_ERROR
        assert "Platform field is required" in data["message"]
        assert "errors" in data["details"]
        assert len(data["details"]["errors"]) == 1
        assert data["details"]["errors"][0]["field"] == "platform"

    @pytest.mark.asyncio
    async def test_start_deployment_missing_platform(self, test_client, async_session):
        """Test deployment start with missing platform field."""
        response = test_client.post("/api/deployment/start", json={"other_field": "value"})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        
        assert data["error_code"] == ErrorCode.VALIDATION_ERROR
        assert "Platform field is required" in data["message"]

    @pytest.mark.asyncio
    async def test_start_deployment_invalid_platform(self, test_client, async_session, invalid_platform_request):
        """Test deployment start with invalid platform value."""
        response = test_client.post("/api/deployment/start", json=invalid_platform_request)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        
        assert data["error_code"] == ErrorCode.VALIDATION_ERROR
        assert "Invalid platform value" in data["message"]

    @pytest.mark.asyncio
    async def test_start_deployment_rate_limit_exceeded(self, test_client, async_session, valid_deployment_request):
        """Test deployment start rate limiting."""
        with patch('app.api.deployment.DeploymentService.generate_merchant_key') as mock_gen_key, \
             patch('app.api.deployment.DeploymentService.create_merchant') as mock_create_merchant, \
             patch('app.api.deployment.DeploymentService.migrate_prerequisites') as mock_migrate, \
             patch('app.api.deployment._get_script_path') as mock_script_path, \
             patch('app.services.deployment.select') as mock_select, \
             patch('app.services.deployment.func') as mock_func:
            
            # Mock database to simulate existing deployment
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 1  # One existing deployment
            
            mock_select.return_value.where.return_value = mock_select.return_value
            mock_func.count.return_value = mock_count_result
            
            # Mock other dependencies
            mock_path = Mock(spec=Path)
            mock_path.exists.return_value = True
            mock_script_path.return_value = mock_path
            mock_gen_key.return_value = "shop-test123"
            mock_merchant = MagicMock()
            mock_merchant.id = 1
            mock_create_merchant.return_value = mock_merchant
            mock_migrate.return_value = None
            
            response = test_client.post("/api/deployment/start", json=valid_deployment_request)
            
            assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            data = response.json()
            
            assert data["error_code"] == ErrorCode.DEPLOYMENT_IN_PROGRESS
            assert "Deployment already in progress" in data["message"]
            assert "retryAfterSeconds" in data["details"]

    @pytest.mark.asyncio
    async def test_start_deployment_script_not_found(self, test_client, async_session, valid_deployment_request):
        """Test deployment start when script is not found."""
        with patch('app.api.deployment._get_script_path') as mock_script_path:
            mock_path = Mock(spec=Path)
            mock_path.exists.return_value = False
            mock_script_path.return_value = mock_path
            
            response = test_client.post("/api/deployment/start", json=valid_deployment_request)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            
            assert data["error_code"] == ErrorCode.DEPLOYMENT_FAILED
            assert "Deployment script not found" in data["message"]

    # Test GET /status/{deployment_id} endpoint
    @pytest.mark.asyncio
    async def test_get_deployment_status_happy_path(self, test_client, async_session):
        """Test successful deployment status retrieval."""
        deployment_id = str(uuid4())
        merchant_id = 1
        
        # Create mock logs
        await self._create_mock_deployment_logs(async_session, deployment_id, merchant_id)
        
        # Create merchant
        from app.models.merchant import Merchant
        merchant = Merchant(
            id=merchant_id,
            merchant_key="shop-test123",
            platform="flyio",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        async_session.add(merchant)
        await async_session.commit()
        
        response = test_client.get(f"/status/{deployment_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify envelope structure
        assert "data" in data
        assert "meta" in data
        
        # Verify deployment state
        deployment_data = data["data"]
        assert deployment_data["deploymentId"] == deployment_id
        assert deployment_data["merchantKey"] == "shop-test123"
        assert deployment_data["status"] == "success"
        assert deployment_data["platform"] == "flyio"
        assert deployment_data["progress"] == 100
        assert "logs" in deployment_data
        assert len(deployment_data["logs"]) > 0
        assert deployment_data["createdAt"] is not None
        assert deployment_data["updatedAt"] is not None

    @pytest.mark.asyncio
    async def test_get_deployment_status_not_found(self, test_client, async_session):
        """Test deployment status for non-existent deployment."""
        deployment_id = str(uuid4())
        
        response = test_client.get(f"/status/{deployment_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        
        assert data["error_code"] == ErrorCode.MERCHANT_NOT_FOUND
        assert f"Deployment not found: {deployment_id}" in data["message"]

    @pytest.mark.asyncio
    async def test_get_deployment_status_in_progress(self, test_client, async_session):
        """Test deployment status for in-progress deployment."""
        deployment_id = str(uuid4())
        merchant_id = 1
        
        # Create partial logs
        from app.models.deployment_log import DeploymentLog as DeploymentLogModel
        
        log = DeploymentLogModel(
            deployment_id=deployment_id,
            merchant_id=merchant_id,
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO.value,
            step=DeploymentStep.DEPLOYMENT.value,
            message="Deploying to platform",
        )
        async_session.add(log)
        await async_session.commit()
        
        # Create merchant with pending status
        from app.models.merchant import Merchant
        merchant = Merchant(
            id=merchant_id,
            merchant_key="shop-inprogress",
            platform="railway",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        async_session.add(merchant)
        await async_session.commit()
        
        response = test_client.get(f"/status/{deployment_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["data"]["status"] == "in-progress"
        assert data["data"]["progress"] == 70
        assert data["data"]["currentStep"] == "deploy"

    @pytest.mark.asyncio
    async def test_get_deployment_status_failed(self, test_client, async_session):
        """Test deployment status for failed deployment."""
        deployment_id = str(uuid4())
        merchant_id = 1
        
        # Create merchant with failed status
        from app.models.merchant import Merchant
        merchant = Merchant(
            id=merchant_id,
            merchant_key="shop-failed",
            platform="render",
            status="failed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        async_session.add(merchant)
        await async_session.commit()
        
        # Create error log
        from app.models.deployment_log import DeploymentLog as DeploymentLogModel
        
        error_log = DeploymentLogModel(
            deployment_id=deployment_id,
            merchant_id=merchant_id,
            timestamp=datetime.utcnow(),
            level=LogLevel.ERROR.value,
            step=None,
            message="Deployment failed: authentication error",
        )
        async_session.add(error_log)
        await async_session.commit()
        
        response = test_client.get(f"/status/{deployment_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["data"]["status"] == "failed"
        assert data["data"]["progress"] == 0

    # Test GET /progress/{deployment_id} endpoint
    @pytest.mark.asyncio
    async def test_stream_deployment_progress_happy_path(self, test_client, async_session):
        """Test successful deployment progress streaming."""
        deployment_id = str(uuid4())
        merchant_id = 1
        
        # Create merchant
        from app.models.merchant import Merchant
        merchant = Merchant(
            id=merchant_id,
            merchant_key="shop-stream123",
            platform="flyio",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        async_session.add(merchant)
        await async_session.commit()
        
        # Create initial log
        from app.models.deployment_log import DeploymentLog as DeploymentLogModel
        
        log = DeploymentLogModel(
            deployment_id=deployment_id,
            merchant_id=merchant_id,
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO.value,
            step=DeploymentStep.COMPLETE.value,
            message="Deployment completed successfully",
        )
        async_session.add(log)
        await async_session.commit()
        
        # Make streaming request
        with test_client.stream("GET", f"/progress/{deployment_id}") as response:
            assert response.status_code == status.HTTP_200_OK
            
            # Check headers
            assert response.headers["content-type"] == "text/event-stream"
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["connection"] == "keep-alive"
            assert response.headers["x-accel-buffering"] == "no"
            
            # Read events
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    event_data = json.loads(line[6:])
                    events.append(event_data)
                    
                    # Check event structure
                    assert "deploymentId" in event_data
                    assert "merchantKey" in event_data
                    assert "status" in event_data
                    assert "progress" in event_data
                    assert "logs" in event_data
                    
                    # Check for completion signal
                    if event_data["status"] == "success":
                        assert "error" not in event_data
                        
                        # Check for DONE signal
                        break
        
        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_stream_deployment_progress_not_found(self, test_client, async_session):
        """Test streaming for non-existent deployment."""
        deployment_id = str(uuid4())
        
        with test_client.stream("GET", f"/progress/{deployment_id}") as response:
            assert response.status_code == status.HTTP_200_OK
            
            # Read error event
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    assert "error" in data
                    assert f"Deployment not found: {deployment_id}" in data["error"]
                    break

    @pytest.mark.asyncio
    async def test_stream_deployment_progress_in_progress(self, test_client, async_session):
        """Test streaming for in-progress deployment."""
        deployment_id = str(uuid4())
        merchant_id = 1
        
        # Create merchant
        from app.models.merchant import Merchant
        merchant = Merchant(
            id=merchant_id,
            merchant_key="shop-stream-progress",
            platform="railway",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        async_session.add(merchant)
        await async_session.commit()
        
        # Create initial log
        from app.models.deployment_log import DeploymentLog as DeploymentLogModel
        
        log = DeploymentLogModel(
            deployment_id=deployment_id,
            merchant_id=merchant_id,
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO.value,
            step=DeploymentStep.APP_SETUP.value,
            message="Setting up app",
        )
        async_session.add(log)
        await async_session.commit()
        
        # Test streaming (stream will timeout after 15 minutes max)
        with patch('app.api.deployment.asyncio.sleep') as mock_sleep:
            mock_sleep.return_value = asyncio.sleep(0.01)  # Fast forward
            
            with test_client.stream("GET", f"/progress/{deployment_id}") as response:
                assert response.status_code == status.HTTP_200_OK
                
                # Read events until completion or timeout
                events = []
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        event_data = json.loads(line[6:])
                        events.append(event_data)
                        
                        if event_data["status"] == "failed":
                            break
                    elif line == "data: [DONE]\n":
                        break
        
        # Verify we received progress updates
        assert len(events) > 0
        assert events[0]["status"] == "pending"

    # Test POST /cancel/{deployment_id} endpoint
    @pytest.mark.asyncio
    async def test_cancel_deployment_happy_path(self, test_client, async_session):
        """Test successful deployment cancellation."""
        deployment_id = str(uuid4())
        merchant_id = 1
        
        # Create merchant with pending status
        from app.models.merchant import Merchant
        merchant = Merchant(
            id=merchant_id,
            merchant_key="shop-cancel123",
            platform="flyio",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        async_session.add(merchant)
        await async_session.commit()
        
        # Create initial log
        from app.models.deployment_log import DeploymentLog as DeploymentLogModel
        
        initial_log = DeploymentLogModel(
            deployment_id=deployment_id,
            merchant_id=merchant_id,
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO.value,
            step=DeploymentStep.CHECK_CLI.value,
            message="Deployment initiated",
        )
        async_session.add(initial_log)
        await async_session.commit()
        
        # Mock subprocess
        mock_process = AsyncMock()
        with patch('app.api.deployment._active_subprocesses', {deployment_id: mock_process}):
            response = test_client.post(f"/cancel/{deployment_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Verify envelope structure
        assert "data" in data
        assert "meta" in data
        
        # Verify cancellation data
        assert data["data"]["message"] == "Deployment cancelled"
        assert data["data"]["deploymentId"] == deployment_id
        
        # Verify merchant status was updated
        updated_merchant = await async_session.get(Merchant, merchant_id)
        assert updated_merchant.status == "failed"
        
        # Verify subprocess was terminated
        mock_process.terminate.assert_called_once()
        
        # Verify cancellation log was created
        result = await async_session.execute(
            DeploymentLogModel.__table__.select()
            .where(DeploymentLogModel.deployment_id == deployment_id)
        )
        logs = result.scalars().all()
        
        # Should have initial log + cancellation log
        assert len(logs) >= 2
        cancel_log = logs[-1]
        assert cancel_log.level == "warning"
        assert cancel_log.message == "Deployment cancelled by user"

    @pytest.mark.asyncio
    async def test_cancel_deployment_not_found(self, test_client, async_session):
        """Test cancellation for non-existent deployment."""
        deployment_id = str(uuid4())
        
        response = test_client.post(f"/cancel/{deployment_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        
        assert data["error_code"] == ErrorCode.MERCHANT_NOT_FOUND
        assert f"Deployment not found: {deployment_id}" in data["message"]

    @pytest.mark.asyncio
    async def test_cancel_deployment_already_completed(self, test_client, async_session):
        """Test cancellation for already completed deployment."""
        deployment_id = str(uuid4())
        merchant_id = 1
        
        # Create merchant with active status
        from app.models.merchant import Merchant
        merchant = Merchant(
            id=merchant_id,
            merchant_key="shop-already-active",
            platform="railway",
            status="active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        async_session.add(merchant)
        await async_session.commit()
        
        # Create initial log
        from app.models.deployment_log import DeploymentLog as DeploymentLogModel
        
        initial_log = DeploymentLogModel(
            deployment_id=deployment_id,
            merchant_id=merchant_id,
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO.value,
            step=DeploymentStep.COMPLETE.value,
            message="Deployment completed successfully",
        )
        async_session.add(initial_log)
        await async_session.commit()
        
        response = test_client.post(f"/cancel/{deployment_id}")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data["error_code"] == ErrorCode.DEPLOYMENT_FAILED
        assert "Cannot cancel deployment with status: active" in data["message"]

    @pytest.mark.asyncio
    async def test_cancel_deployment_subprocess_timeout(self, test_client, async_session):
        """Test cancellation when subprocess termination times out."""
        deployment_id = str(uuid4())
        merchant_id = 1
        
        # Create merchant
        from app.models.merchant import Merchant
        merchant = Merchant(
            id=merchant_id,
            merchant_key="shop-timeout",
            platform="flyio",
            status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        async_session.add(merchant)
        await async_session.commit()
        
        # Create initial log
        from app.models.deployment_log import DeploymentLog as DeploymentLogModel
        
        initial_log = DeploymentLogModel(
            deployment_id=deployment_id,
            merchant_id=merchant_id,
            timestamp=datetime.utcnow(),
            level=LogLevel.INFO.value,
            step=DeploymentStep.CHECK_CLI.value,
            message="Deployment initiated",
        )
        async_session.add(initial_log)
        await async_session.commit()
        
        # Mock subprocess that times out
        mock_process = AsyncMock()
        mock_process.terminate.side_effect = Exception("Terminate failed")
        
        with patch('app.api.deployment._active_subprocesses', {deployment_id: mock_process}):
            response = test_client.post(f"/cancel/{deployment_id}")
        
        # Should still succeed despite timeout error
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["data"]["message"] == "Deployment cancelled"

    # Test edge cases and error conditions
    @pytest.mark.asyncio
    async def test_deployment_response_structure_validation(self, test_client, async_session, valid_deployment_request):
        """Test response structure validation for all endpoints."""
        with patch('app.api.deployment.DeploymentService.generate_merchant_key') as mock_gen_key, \
             patch('app.api.deployment.DeploymentService.create_merchant') as mock_create_merchant, \
             patch('app.api.deployment.DeploymentService.migrate_prerequisites') as mock_migrate, \
             patch('app.api.deployment._get_script_path') as mock_script_path, \
             patch('app.api.deployment.asyncio.create_subprocess_exec') as mock_subprocess:
            
            # Mock dependencies
            mock_path = Mock(spec=Path)
            mock_path.exists.return_value = True
            mock_script_path.return_value = mock_path
            test_merchant_key = "shop-struct123"
            mock_gen_key.return_value = test_merchant_key
            mock_merchant = MagicMock()
            mock_merchant.id = 1
            mock_create_merchant.return_value = mock_merchant
            mock_migrate.return_value = None
            mock_process = AsyncMock()
            mock_process.wait.return_value = 0
            mock_subprocess.return_value = mock_process
            
            # Test start endpoint response
            response = test_client.post("/api/deployment/start", json=valid_deployment_request)
            data = response.json()
            
            # Verify all required fields are present
            assert "data" in data
            assert "meta" in data
            assert data["meta"]["requestId"] is not None
            
            deployment_data = data["data"]
            required_fields = ["deploymentId", "merchantKey", "status", "estimatedSeconds"]
            for field in required_fields:
                assert field in deployment_data, f"Missing field: {field}"
            
            # Verify field types
            assert isinstance(deployment_data["deploymentId"], str)
            assert isinstance(deployment_data["merchantKey"], str)
            assert isinstance(deployment_data["status"], str)
            assert isinstance(deployment_data["estimatedSeconds"], int)
            
            # Create test deployment for status endpoint
            deployment_id = response.json()["data"]["deploymentId"]
            await self._create_mock_deployment_logs(async_session, deployment_id, mock_merchant.id)
            
            # Create merchant
            from app.models.merchant import Merchant
            test_merchant = Merchant(
                id=mock_merchant.id,
                merchant_key=test_merchant_key,
                platform="flyio",
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            async_session.add(test_merchant)
            await async_session.commit()
            
            # Test status endpoint response
            status_response = test_client.get(f"/status/{deployment_id}")
            status_data = status_response.json()
            
            # Verify status response structure
            assert "data" in status_data
            assert "meta" in status_data
            
            status_deployment = status_data["data"]
            status_required_fields = ["deploymentId", "merchantKey", "status", "platform", "progress", "logs"]
            for field in status_required_fields:
                assert field in status_deployment, f"Missing field in status: {field}"

    @pytest.mark.asyncio
    async def test_deployment_timeout_handling(self, test_client, async_session, valid_deployment_request):
        """Test deployment timeout error handling."""
        with patch('app.api.deployment.DeploymentService.generate_merchant_key') as mock_gen_key, \
             patch('app.api.deployment.DeploymentService.create_merchant') as mock_create_merchant, \
             patch('app.api.deployment.DeploymentService.migrate_prerequisites') as mock_migrate, \
             patch('app.api.deployment._get_script_path') as mock_script_path, \
             patch('app.api.deployment.asyncio.create_subprocess_exec') as mock_subprocess:
            
            # Mock the script path
            mock_path = Mock(spec=Path)
            mock_path.exists.return_value = True
            mock_script_path.return_value = mock_path
            
            # Mock the merchant key generation
            test_merchant_key = "shop-timeout123"
            mock_gen_key.return_value = test_merchant_key
            
            # Mock merchant creation
            mock_merchant = MagicMock()
            mock_merchant.id = 1
            mock_create_merchant.return_value = mock_merchant
            
            # Mock prerequisites
            mock_migrate.return_value = None
            
            # Mock subprocess that raises timeout error
            mock_process = AsyncMock()
            mock_process.terminate.side_effect = APIError(
                ErrorCode.DEPLOYMENT_TIMEOUT,
                "Deployment exceeded time limit"
            )
            
            # Mock the _run_deployment_script to raise timeout
            with patch('app.api.deployment._run_deployment_script') as mock_run:
                mock_run.side_effect = APIError(
                    ErrorCode.DEPLOYMENT_TIMEOUT,
                    "Deployment exceeded time limit of 900 seconds",
                    {"troubleshootingUrl": "https://docs.example.com/deploy-troubleshoot#flyio"}
                )
                
                response = test_client.post("/api/deployment/start", json=valid_deployment_request)
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                data = response.json()
                
                assert data["error_code"] == ErrorCode.DEPLOYMENT_TIMEOUT
                assert "exceeded time limit" in data["message"]
                assert "troubleshootingUrl" in data["details"]
                assert data["details"]["troubleshootingUrl"] == "https://docs.example.com/deploy-troubleshoot#flyio"

    @pytest.mark.asyncio
    async def test_all_platforms_supported(self, test_client, async_session):
        """Test that all supported platforms work correctly."""
        platforms = ["flyio", "railway", "render"]
        
        for platform in platforms:
            with patch('app.api.deployment.DeploymentService.generate_merchant_key') as mock_gen_key, \
                 patch('app.api.deployment.DeploymentService.create_merchant') as mock_create_merchant, \
                 patch('app.api.deployment.DeploymentService.migrate_prerequisites') as mock_migrate, \
                 patch('app.api.deployment._get_script_path') as mock_script_path, \
                 patch('app.api.deployment.asyncio.create_subprocess_exec') as mock_subprocess:
                
                # Mock dependencies
                mock_path = Mock(spec=Path)
                mock_path.exists.return_value = True
                mock_script_path.return_value = mock_path
                test_merchant_key = f"shop-{platform}123"
                mock_gen_key.return_value = test_merchant_key
                mock_merchant = MagicMock()
                mock_merchant.id = 1
                mock_create_merchant.return_value = mock_merchant
                mock_migrate.return_value = None
                mock_process = AsyncMock()
                mock_process.wait.return_value = 0
                mock_subprocess.return_value = mock_process
                
                response = test_client.post("/api/deployment/start", json={"platform": platform})
                
                assert response.status_code == status.HTTP_202_ACCEPTED
                data = response.json()
                
                assert data["data"]["status"] == "pending"
                assert data["data"]["merchantKey"] == test_merchant_key

    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self, test_client, async_session, valid_deployment_request):
        """Test that database operations are rolled back on failure."""
        with patch('app.api.deployment.DeploymentService.generate_merchant_key') as mock_gen_key, \
             patch('app.api.deployment.DeploymentService.create_merchant') as mock_create_merchant, \
             patch('app.api.deployment.DeploymentService.migrate_prerequisites') as mock_migrate, \
             patch('app.api.deployment._get_script_path') as mock_script_path:
            
            # Mock script not found
            mock_path = Mock(spec=Path)
            mock_path.exists.return_value = False
            mock_script_path.return_value = mock_path
            
            response = test_client.post("/api/deployment/start", json=valid_deployment_request)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            
            # Verify no merchant was created in database
            from app.models.merchant import Merchant
            result = await async_session.execute(
                select(Merchant).where(Merchant.merchant_key == "shop-*")
            )
            merchants = result.scalars().all()
            assert len(merchants) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
