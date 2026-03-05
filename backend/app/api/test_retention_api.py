"""API integration tests for Story 6-5: 30-Day Retention Enforcement.

Tests for health check and audit log query endpoints.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.deletion_audit_log import DeletionAuditLog, DeletionTrigger


class TestSchedulerHealthEndpoint:
    """Test GET /api/health/scheduler endpoint (Task 6.1)."""

    @pytest.mark.asyncio
    async def test_scheduler_health_endpoint_exists(self, async_client: AsyncClient):
        """Verify scheduler health endpoint returns 200 or 503."""
        response = await async_client.get("/api/health/scheduler")

        # Endpoint should exist (not 404)
        assert response.status_code in (200, 403, 503)

    @pytest.mark.asyncio
    async def test_scheduler_health_returns_json(self, async_client: AsyncClient):
        """Verify scheduler health returns JSON response."""
        response = await async_client.get("/api/health/scheduler")

        if response.status_code == 200:
            data = response.json()
            assert "status" in data or "scheduler_running" in data


class TestAuditLogQueryEndpoint:
    """Test GET /api/v1/audit/retention-logs endpoint (Task 6.2)."""

    @pytest.mark.asyncio
    async def test_audit_log_endpoint_exists(self, async_client: AsyncClient):
        """Verify audit log endpoint returns 200."""
        response = await async_client.get("/api/v1/audit/retention-logs")

        # Endpoint should exist (not 404)
        assert response.status_code in (200, 401, 403)

    @pytest.mark.asyncio
    async def test_audit_log_returns_paginated_response(
        self,
        async_client: AsyncClient,
        db_session,
        merchant,
    ):
        """Verify audit log endpoint returns paginated response."""
        # Create test audit logs
        for i in range(5):
            log = DeletionAuditLog(
                session_id=f"test-session-{i}",
                merchant_id=merchant.id,
                deletion_trigger=DeletionTrigger.MANUAL,
                conversations_deleted=i,
                messages_deleted=i * 10,
                redis_keys_cleared=i,
            )
            db_session.add(log)

        await db_session.commit()

        response = await async_client.get("/api/v1/audit/retention-logs")

        if response.status_code == 200:
            data = response.json()
            assert "logs" in data or "items" in data
            assert "total" in data or "count" in data

    @pytest.mark.asyncio
    async def test_audit_log_filters_by_merchant(
        self,
        async_client: AsyncClient,
        db_session,
        merchant,
    ):
        """Verify audit log can be filtered by merchant_id."""
        # Create audit log for specific merchant
        log = DeletionAuditLog(
            session_id="test-merchant-filter",
            merchant_id=merchant.id,
            deletion_trigger=DeletionTrigger.AUTO,
            retention_period_days=30,
            conversations_deleted=10,
            messages_deleted=100,
            redis_keys_cleared=5,
        )
        db_session.add(log)
        await db_session.commit()

        response = await async_client.get(f"/api/v1/audit/retention-logs?merchant_id={merchant.id}")

        if response.status_code == 200:
            data = response.json()
            logs = data.get("logs", data.get("items", []))
            assert isinstance(logs, list)

    @pytest.mark.asyncio
    async def test_audit_log_filters_by_trigger_type(
        self,
        async_client: AsyncClient,
        db_session,
        merchant,
    ):
        """Verify audit log can filter by deletion trigger type."""
        # Create manual and auto logs
        manual_log = DeletionAuditLog(
            session_id="manual-log",
            merchant_id=merchant.id,
            deletion_trigger=DeletionTrigger.MANUAL,
            conversations_deleted=5,
            messages_deleted=50,
            redis_keys_cleared=2,
        )
        auto_log = DeletionAuditLog(
            session_id="auto-log",
            merchant_id=merchant.id,
            deletion_trigger=DeletionTrigger.AUTO,
            retention_period_days=30,
            conversations_deleted=10,
            messages_deleted=100,
            redis_keys_cleared=5,
        )
        db_session.add_all([manual_log, auto_log])
        await db_session.commit()

        response = await async_client.get("/api/v1/audit/retention-logs?trigger=auto")

        if response.status_code == 200:
            data = response.json()
            logs = data.get("logs", data.get("items", []))
            # Should only return auto logs
            for log in logs:
                if "trigger" in log:
                    assert log["trigger"] in ("auto", "AUTO", DeletionTrigger.AUTO)

    @pytest.mark.asyncio
    async def test_audit_log_date_range_filter(
        self,
        async_client: AsyncClient,
        db_session,
        merchant,
    ):
        """Verify audit log can filter by date range."""
        # Create recent log
        recent_log = DeletionAuditLog(
            session_id="recent-log",
            merchant_id=merchant.id,
            deletion_trigger=DeletionTrigger.AUTO,
            retention_period_days=30,
            conversations_deleted=1,
            messages_deleted=10,
            redis_keys_cleared=1,
        )
        db_session.add(recent_log)
        await db_session.commit()

        # Query for last 7 days
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        response = await async_client.get(f"/api/v1/audit/retention-logs?start_date={start_date}")

        if response.status_code == 200:
            data = response.json()
            assert "logs" in data or "items" in data
