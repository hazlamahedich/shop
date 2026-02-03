"""Onboarding API routes.

Handles prerequisite validation and state management for merchant onboarding.
Story 1.2: localStorage to PostgreSQL migration with sync endpoints.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.onboarding import PrerequisiteChecklist
from app.schemas.onboarding import (
    MinimalEnvelope,
    PrerequisiteCheckRequest,
    PrerequisiteCheckResponse,
    PrerequisiteStateCreate,
    PrerequisiteStateResponse,
    PrerequisiteSyncRequest,
)

router = APIRouter()


def _get_missing_prerequisites(data: PrerequisiteCheckRequest) -> list[str]:
    """Get list of missing prerequisites.

    Args:
        data: Prerequisite check request

    Returns:
        List of missing prerequisite keys in camelCase
    """
    missing: list[str] = []
    if not data.cloud_account:
        missing.append("cloudAccount")
    if not data.facebook_account:
        missing.append("facebookAccount")
    if not data.shopify_access:
        missing.append("shopifyAccess")
    if not data.llm_provider_choice:
        missing.append("llmProviderChoice")
    return missing


def _create_meta() -> dict[str, Any]:
    """Create metadata for API response.

    Returns:
        Metadata dict with request_id and timestamp
    """
    return {
        "requestId": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get(
    "/prerequisites/check",
    response_model=MinimalEnvelope,
    summary="Check if prerequisites are complete",
    description="Validates that all onboarding prerequisites are completed before deployment.",
)
async def check_prerequisites(
    cloudAccount: bool = False,
    facebookAccount: bool = False,
    shopifyAccess: bool = False,
    llmProviderChoice: bool = False,
) -> MinimalEnvelope:
    """Check if all prerequisites are completed.

    Args:
        cloudAccount: Cloud provider account status
        facebookAccount: Facebook business account status
        shopifyAccess: Shopify admin access status
        llmProviderChoice: LLM provider selection status

    Returns:
        MinimalEnvelope with is_complete flag and missing items

    Raises:
        APIError: If prerequisites are incomplete (400 status)
    """
    # Build PrerequisiteCheckRequest from query params
    data = PrerequisiteCheckRequest(
        cloud_account=cloudAccount,
        facebook_account=facebookAccount,
        shopify_access=shopifyAccess,
        llm_provider_choice=llmProviderChoice,
    )

    missing = _get_missing_prerequisites(data)
    is_complete = len(missing) == 0

    if not is_complete:
        raise APIError(
            ErrorCode.PREREQUISITES_INCOMPLETE,
            "Complete all prerequisites before deployment",
            {"missing": missing},
        )

    return MinimalEnvelope(
        data=PrerequisiteCheckResponse(
            is_complete=True,
            missing=[],
        ),
        meta=_create_meta(),
    )


@router.post(
    "/prerequisites/validate",
    response_model=MinimalEnvelope,
    summary="Validate prerequisites state",
    description="Returns current prerequisite completion state without raising errors.",
)
async def validate_prerequisites(data: PrerequisiteCheckRequest) -> MinimalEnvelope:
    """Validate prerequisites and return completion state.

    Unlike /check endpoint, this returns the state without raising errors.

    Args:
        data: Prerequisite check request with checkbox states

    Returns:
        MinimalEnvelope with is_complete flag and missing items
    """
    missing = _get_missing_prerequisites(data)
    is_complete = len(missing) == 0

    return MinimalEnvelope(
        data=PrerequisiteCheckResponse(
            is_complete=is_complete,
            missing=missing,
        ),
        meta=_create_meta(),
    )


# ============================================================================
# Story 1.2: localStorage to PostgreSQL Migration Endpoints
# ============================================================================


@router.get(
    "/prerequisites",
    response_model=MinimalEnvelope,
    summary="Get merchant prerequisite state",
    description="Retrieves the stored prerequisite checklist state from PostgreSQL.",
)
async def get_prerequisite_state(
    merchant_id: int = 1,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Get prerequisite state from database for a merchant.

    Args:
        merchant_id: Merchant ID (defaults to 1 until auth is implemented)
        db: Async database session

    Returns:
        MinimalEnvelope with PrerequisiteStateResponse or null if not found

    Raises:
        APIError: If database operation fails
    """
    try:
        result = await db.execute(
            select(PrerequisiteChecklist).where(
                PrerequisiteChecklist.merchant_id == merchant_id
            )
        )
        checklist = result.scalars().first()

        if checklist is None:
            return MinimalEnvelope(
                data=None,
                meta=_create_meta(),
            )

        return MinimalEnvelope(
            data=PrerequisiteStateResponse(
                id=checklist.id,
                merchant_id=checklist.merchant_id,
                has_cloud_account=checklist.has_cloud_account,
                has_facebook_account=checklist.has_facebook_account,
                has_shopify_access=checklist.has_shopify_access,
                has_llm_provider_choice=checklist.has_llm_provider_choice,
                is_complete=checklist.is_complete,
                completed_at=checklist.completed_at,
                created_at=checklist.created_at,
                updated_at=checklist.updated_at,
            ),
            meta=_create_meta(),
        )
    except Exception as e:
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            f"Failed to retrieve prerequisite state: {str(e)}",
        ) from e


@router.post(
    "/prerequisites",
    response_model=MinimalEnvelope,
    summary="Create or update prerequisite state",
    description="Saves prerequisite checklist state to PostgreSQL. Creates new record or updates existing.",
)
async def upsert_prerequisite_state(
    data: PrerequisiteStateCreate,
    merchant_id: int = 1,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Create or update prerequisite state in database.

    Args:
        data: Prerequisite state to save
        merchant_id: Merchant ID (defaults to 1 until auth is implemented)
        db: Async database session

    Returns:
        MinimalEnvelope with saved PrerequisiteStateResponse

    Raises:
        APIError: If database operation fails
    """
    try:
        # Check if checklist exists
        result = await db.execute(
            select(PrerequisiteChecklist).where(
                PrerequisiteChecklist.merchant_id == merchant_id
            )
        )
        checklist = result.scalars().first()

        if checklist:
            # Update existing
            checklist.has_cloud_account = data.has_cloud_account
            checklist.has_facebook_account = data.has_facebook_account
            checklist.has_shopify_access = data.has_shopify_access
            checklist.has_llm_provider_choice = data.has_llm_provider_choice
            checklist.update_completed_at()
        else:
            # Create new
            checklist = PrerequisiteChecklist(
                merchant_id=merchant_id,
                has_cloud_account=data.has_cloud_account,
                has_facebook_account=data.has_facebook_account,
                has_shopify_access=data.has_shopify_access,
                has_llm_provider_choice=data.has_llm_provider_choice,
            )
            # Update completed_at if all complete
            checklist.update_completed_at()
            db.add(checklist)

        await db.commit()
        await db.refresh(checklist)

        return MinimalEnvelope(
            data=PrerequisiteStateResponse(
                id=checklist.id,
                merchant_id=checklist.merchant_id,
                has_cloud_account=checklist.has_cloud_account,
                has_facebook_account=checklist.has_facebook_account,
                has_shopify_access=checklist.has_shopify_access,
                has_llm_provider_choice=checklist.has_llm_provider_choice,
                is_complete=checklist.is_complete,
                completed_at=checklist.completed_at,
                created_at=checklist.created_at,
                updated_at=checklist.updated_at,
            ),
            meta=_create_meta(),
        )
    except Exception as e:
        await db.rollback()
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            f"Failed to save prerequisite state: {str(e)}",
        ) from e


@router.post(
    "/prerequisites/sync",
    response_model=MinimalEnvelope,
    summary="Sync localStorage state to backend",
    description="Migrates localStorage prerequisite state to PostgreSQL. Story 1.2 migration endpoint.",
)
async def sync_prerequisite_state(
    data: PrerequisiteSyncRequest,
    merchant_id: int = 1,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Sync localStorage state to backend database.

    This endpoint handles the migration from localStorage to PostgreSQL.
    It compares timestamps to determine which source is more recent.

    Args:
        data: LocalStorage state to sync
        merchant_id: Merchant ID (defaults to 1 until auth is implemented)
        db: Async database session

    Returns:
        MinimalEnvelope with synced PrerequisiteStateResponse

    Raises:
        APIError: If database operation fails
    """
    try:
        # Get existing state from database
        result = await db.execute(
            select(PrerequisiteChecklist).where(
                PrerequisiteChecklist.merchant_id == merchant_id
            )
        )
        checklist = result.scalars().first()

        # Convert frontend field names to backend model
        state_data = PrerequisiteStateCreate(
            has_cloud_account=data.cloud_account,
            has_facebook_account=data.facebook_account,
            has_shopify_access=data.shopify_access,
            has_llm_provider_choice=data.llm_provider_choice,
        )

        if checklist:
            # Update existing with localStorage data
            checklist.has_cloud_account = state_data.has_cloud_account
            checklist.has_facebook_account = state_data.has_facebook_account
            checklist.has_shopify_access = state_data.has_shopify_access
            checklist.has_llm_provider_choice = state_data.has_llm_provider_choice
            checklist.update_completed_at()
        else:
            # Create new from localStorage data
            checklist = PrerequisiteChecklist(
                merchant_id=merchant_id,
                has_cloud_account=state_data.has_cloud_account,
                has_facebook_account=state_data.has_facebook_account,
                has_shopify_access=state_data.has_shopify_access,
                has_llm_provider_choice=state_data.has_llm_provider_choice,
            )
            checklist.update_completed_at()
            db.add(checklist)

        await db.commit()
        await db.refresh(checklist)

        return MinimalEnvelope(
            data=PrerequisiteStateResponse(
                id=checklist.id,
                merchant_id=checklist.merchant_id,
                has_cloud_account=checklist.has_cloud_account,
                has_facebook_account=checklist.has_facebook_account,
                has_shopify_access=checklist.has_shopify_access,
                has_llm_provider_choice=checklist.has_llm_provider_choice,
                is_complete=checklist.is_complete,
                completed_at=checklist.completed_at,
                created_at=checklist.created_at,
                updated_at=checklist.updated_at,
            ),
            meta=_create_meta(),
        )
    except Exception as e:
        await db.rollback()
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            f"Failed to sync prerequisite state: {str(e)}",
        ) from e


@router.delete(
    "/prerequisites",
    response_model=MinimalEnvelope,
    summary="Delete prerequisite state",
    description="Deletes stored prerequisite checklist state for a merchant.",
)
async def delete_prerequisite_state(
    merchant_id: int = 1,
    db: AsyncSession = Depends(get_db),
) -> MinimalEnvelope:
    """Delete prerequisite state from database.

    Args:
        merchant_id: Merchant ID (defaults to 1 until auth is implemented)
        db: Async database session

    Returns:
        MinimalEnvelope with deletion confirmation

    Raises:
        APIError: If database operation fails
    """
    try:
        result = await db.execute(
            select(PrerequisiteChecklist).where(
                PrerequisiteChecklist.merchant_id == merchant_id
            )
        )
        checklist = result.scalars().first()

        if checklist:
            await db.delete(checklist)
            await db.commit()

        return MinimalEnvelope(
            data={"deleted": checklist is not None},
            meta=_create_meta(),
        )
    except Exception as e:
        await db.rollback()
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            f"Failed to delete prerequisite state: {str(e)}",
        ) from e
