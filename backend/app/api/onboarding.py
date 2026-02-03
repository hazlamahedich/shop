"""Onboarding API routes.

Handles prerequisite validation for merchant onboarding.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from app.core.errors import APIError, ErrorCode
from app.schemas.onboarding import (
    MinimalEnvelope,
    PrerequisiteCheckRequest,
    PrerequisiteCheckResponse,
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
