"""Tests for deployment log ORM model."""

import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deployment_log import DeploymentLog
from app.models.merchant import Merchant


class TestDeploymentLogModel:
    """Tests for DeploymentLog ORM model."""

    @pytest.mark.asyncio
    async def test_create_deployment_log(self, async_session: AsyncSession):
        """Test creating a deployment log entry."""
        # Create a merchant first
        merchant = Merchant(
            merchant_key="shop-logs",
            platform="flyio",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create a deployment log
        log = DeploymentLog(
            deployment_id="test-deployment-123",
            merchant_id=merchant.id,
            level="info",
            step="check_cli",
            message="Starting deployment process",
        )
        async_session.add(log)
        await async_session.commit()
        await async_session.refresh(log)

        assert log.id is not None
        assert log.deployment_id == "test-deployment-123"
        assert log.merchant_id == merchant.id
        assert log.level == "info"
        assert log.step == "check_cli"
        assert log.message == "Starting deployment process"
        assert log.timestamp is not None

    @pytest.mark.asyncio
    async def test_deployment_log_defaults(self, async_session: AsyncSession):
        """Test deployment log default values."""
        # Create a merchant first
        merchant = Merchant(
            merchant_key="shop-logs-defaults",
            platform="railway",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create a deployment log without step
        log = DeploymentLog(
            deployment_id="test-deployment-456",
            merchant_id=merchant.id,
            level="error",
            message="Deployment failed",
        )
        async_session.add(log)
        await async_session.commit()
        await async_session.refresh(log)

        assert log.step is None
        assert log.timestamp is not None

    @pytest.mark.asyncio
    async def test_deployment_log_foreign_key(self, async_session: AsyncSession):
        """Test that deployment log references a valid merchant."""
        # Create a merchant first
        merchant = Merchant(
            merchant_key="shop-fk-test",
            platform="render",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        # Create deployment logs
        log1 = DeploymentLog(
            deployment_id="test-deployment-fk-1",
            merchant_id=merchant.id,
            level="info",
            message="First log entry",
        )
        log2 = DeploymentLog(
            deployment_id="test-deployment-fk-2",
            merchant_id=merchant.id,
            level="warning",
            message="Second log entry",
        )
        async_session.add(log1)
        async_session.add(log2)
        await async_session.commit()

        # Query logs for this merchant
        result = await async_session.execute(
            select(DeploymentLog).where(DeploymentLog.merchant_id == merchant.id)
        )
        logs = result.scalars().all()

        assert len(logs) == 2

    @pytest.mark.asyncio
    async def test_deployment_log_query_by_deployment_id(self, async_session: AsyncSession):
        """Test querying logs by deployment_id."""
        # Create a merchant first
        merchant = Merchant(
            merchant_key="shop-query-test",
            platform="flyio",
        )
        async_session.add(merchant)
        await async_session.commit()
        await async_session.refresh(merchant)

        deployment_id = "query-test-123"

        # Create multiple logs for the same deployment
        for i in range(3):
            log = DeploymentLog(
                deployment_id=deployment_id,
                merchant_id=merchant.id,
                level="info",
                message=f"Log entry {i}",
            )
            async_session.add(log)
        await async_session.commit()

        # Query logs by deployment_id
        result = await async_session.execute(
            select(DeploymentLog).where(DeploymentLog.deployment_id == deployment_id)
        )
        logs = result.scalars().all()

        assert len(logs) == 3
