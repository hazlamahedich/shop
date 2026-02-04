"""Admin API endpoints for data retention management.

Provides manual trigger and monitoring capabilities for data retention jobs.
Protected endpoints for administrative operations.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.data_retention import DataRetentionService

router = APIRouter()


@router.post("/cleanup")
async def trigger_retention_cleanup(
    dry_run: bool = Query(
        False,
        description="If true, only report what would be deleted without actually deleting"
    ),
    voluntary_days: Optional[int] = Query(
        None,
        description="Override voluntary data retention period (default: 30)"
    ),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Manually trigger data retention cleanup (admin only).

    Executes the retention cleanup job on-demand. Useful for:
    - Testing retention configuration
    - Immediate cleanup before audits
    - Dry-run analysis of affected data

    Args:
        dry_run: If True, only report what would be deleted
        voluntary_days: Optional override for retention period
        db: Database session

    Returns:
        Dictionary with cleanup results from all retention tasks

    Example:
        ```python
        # Dry run to see what would be deleted
        response = await client.post("/api/admin/retention/cleanup?dry_run=true")

        # Actual cleanup with default 30-day retention
        response = await client.post("/api/admin/retention/cleanup")

        # Cleanup with custom 60-day retention
        response = await client.post("/api/admin/retention/cleanup?voluntary_days=60")
        ```
    """
    service = DataRetentionService(
        voluntary_days=voluntary_days or 30
    )

    results = {
        "dry_run": dry_run,
        "voluntary_data": await service.cleanup_voluntary_data(db, dry_run=dry_run),
        "sessions": await service.cleanup_expired_sessions(db, dry_run=dry_run),
    }

    return results


@router.get("/stats")
async def get_retention_stats(
    voluntary_days: Optional[int] = Query(
        None,
        description="Override voluntary data retention period for stats calculation (default: 30)"
    ),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get current data retention statistics.

    Provides visibility into:
    - Total conversation and message counts
    - Data distribution by age brackets
    - Current retention policy settings

    Args:
        voluntary_days: Optional override for retention period
        db: Database session

    Returns:
        Dictionary with retention statistics

    Example:
        ```python
        response = await client.get("/api/admin/retention/stats")
        # Returns:
        # {
        #     "total_conversations": 1500,
        #     "total_messages": 12500,
        #     "conversations_by_age": {
        #         "0_7_days": 500,
        #         "7_30_days": 600,
        #         "30_90_days": 300,
        #         "90_plus_days": 100
        #     },
        #     "retention_policy": {
        #         "voluntary_days": 30,
        #         "session_hours": 24
        #     }
        # }
        ```
    """
    service = DataRetentionService(
        voluntary_days=voluntary_days or 30
    )

    stats = await service.get_retention_stats(db)

    return stats


@router.get("/conversations-to-delete")
async def get_conversations_to_delete(
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of conversations to return"
    ),
    voluntary_days: Optional[int] = Query(
        None,
        description="Override voluntary data retention period (default: 30)"
    ),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get list of conversations that would be deleted by retention policy.

    Useful for audit trails and pre-deletion verification.

    Args:
        limit: Maximum number of conversations to return (1-1000)
        voluntary_days: Optional override for retention period
        db: Database session

    Returns:
        Dictionary with list of conversations and metadata

    Example:
        ```python
        response = await client.get("/api/admin/retention/conversations-to-delete?limit=50")
        # Returns:
        # {
        #     "count": 50,
        #     "conversations": [
        #         {
        #             "id": 123,
        #             "merchant_id": 1,
        #             "platform": "facebook",
        #             "platform_sender_id": "1234567890",
        #             "status": "closed",
        #             "created_at": "2025-12-01T10:00:00",
        #             "updated_at": "2025-12-15T15:30:00",
        #             "days_since_update": 51
        #         },
        #         ...
        #     ]
        # }
        ```
    """
    service = DataRetentionService(
        voluntary_days=voluntary_days or 30
    )

    conversations = await service.get_conversations_to_delete(db, limit=limit)

    return {
        "count": len(conversations),
        "conversations": conversations,
    }
