"""Audit log API endpoints.

Story 6-5: 30-Day Retention Enforcement
Task 2.5: Query audit logs for retention deletions

Provides endpoints for querying deletion audit logs with filters.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.deletion_audit_log import DeletionAuditLog, DeletionTrigger

router = APIRouter()


class RetentionLogResponse(BaseModel):
    """Response model for retention audit logs."""

    id: int
    session_id: str = Field(alias="sessionId")
    merchant_id: int = Field(alias="merchantId")
    retention_period_days: int | None = Field(None, alias="retentionPeriodDays")
    deletion_trigger: str = Field(alias="deletionTrigger")
    requested_at: datetime = Field(alias="requestedAt")
    completed_at: datetime | None = Field(None, alias="completedAt")
    conversations_deleted: int = Field(alias="conversationsDeleted")
    messages_deleted: int = Field(alias="messagesDeleted")
    redis_keys_cleared: int = Field(alias="redisKeysCleared")
    error_message: str | None = Field(None, alias="errorMessage")

    class Config:
        from_attributes = True
        populate_by_name = True


class RetentionLogsListResponse(BaseModel):
    """Response model for paginated retention logs list."""

    logs: list[RetentionLogResponse]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    class Config:
        populate_by_name = True


@router.get("/retention-logs", response_model=RetentionLogsListResponse)
async def get_retention_logs(
    merchant_id: int | None = Query(
        None, alias="merchantId", description="Filter by merchant ID"
    ),
    start_date: datetime | None = Query(
        None, alias="startDate", description="Filter logs after this date"
    ),
    end_date: datetime | None = Query(
        None, alias="endDate", description="Filter logs before this date"
    ),
    deletion_trigger: str | None = Query(
        None, alias="trigger", description="Filter by trigger type (manual/auto)"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize", description="Items per page"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Query retention audit logs with filters.

    Story 6-5: Task 2.5 - Audit log query endpoint
    Story 6-5: Task 2.6 - Merchant and date range filters

    Returns paginated list of deletion audit logs with optional filters.

    Args:
        merchant_id: Optional merchant ID filter
        start_date: Optional start date filter (inclusive)
        end_date: Optional end date filter (inclusive)
        deletion_trigger: Optional trigger type filter (manual/auto)
        page: Page number (1-indexed)
        page_size: Number of items per page (max 100)
        db: Database session

    Returns:
        Paginated list of retention audit logs

    Raises:
        HTTPException: 400 if invalid filter parameters
    """
    # Build query with filters
    query = select(DeletionAuditLog)

    # Apply merchant filter
    if merchant_id is not None:
        query = query.where(DeletionAuditLog.merchant_id == merchant_id)

    # Apply date range filters
    if start_date:
        query = query.where(DeletionAuditLog.requested_at >= start_date)
    if end_date:
        query = query.where(DeletionAuditLog.requested_at <= end_date)

    # Apply trigger type filter
    if deletion_trigger:
        try:
            trigger_enum = DeletionTrigger(deletion_trigger)
            query = query.where(DeletionAuditLog.deletion_trigger == trigger_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid trigger type: {deletion_trigger}. Must be 'manual' or 'auto'.",
            )

    # Get total count
    count_query = select(DeletionAuditLog)
    if merchant_id is not None:
        count_query = count_query.where(DeletionAuditLog.merchant_id == merchant_id)
    if start_date:
        count_query = count_query.where(DeletionAuditLog.requested_at >= start_date)
    if end_date:
        count_query = count_query.where(DeletionAuditLog.requested_at <= end_date)
    if deletion_trigger:
        try:
            trigger_enum = DeletionTrigger(deletion_trigger)
            count_query = count_query.where(DeletionAuditLog.deletion_trigger == trigger_enum)
        except ValueError:
            pass  # Already validated above

    result = await db.execute(count_query)
    total = len(result.scalars().all())

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(DeletionAuditLog.requested_at.desc())
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()

    # Convert to response models
    log_responses = [RetentionLogResponse.model_validate(log) for log in logs]

    return {
        "logs": log_responses,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
