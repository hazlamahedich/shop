"""Tutorial API endpoints.

API endpoints for managing tutorial progress:
- GET /api/tutorial/status - Get tutorial completion status
- POST /api/tutorial/start - Mark tutorial as started
- POST /api/tutorial/complete - Mark tutorial as complete
- POST /api/tutorial/skip - Mark tutorial as skipped
- POST /api/tutorial/reset - Reset tutorial progress (for replay)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.merchant import Merchant
from app.models.tutorial import Tutorial
from app.schemas.tutorial import (
    TutorialStatusResponse,
    TutorialStartResponse,
    TutorialCompleteResponse,
    TutorialSkipResponse,
    TutorialResetResponse,
)

router = APIRouter(prefix="/tutorial", tags=["tutorial"])


async def get_tutorial(
    db: AsyncSession,
    merchant_id: int,
) -> Tutorial:
    """Get tutorial record for merchant, creating if not exists.

    Args:
        db: Database session
        merchant_id: Merchant ID

    Returns:
        Tutorial record

    Raises:
        APIError: If merchant not found
    """
    # Verify merchant exists
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant with ID {merchant_id} not found",
        )

    # Get or create tutorial
    result = await db.execute(
        select(Tutorial).where(Tutorial.merchant_id == merchant_id)
    )
    tutorial = result.scalar_one_or_none()

    if not tutorial:
        tutorial = Tutorial(
            merchant_id=merchant_id,
            current_step=1,
            completed_steps=[],
            skipped=False,
        )
        db.add(tutorial)
        await db.commit()
        await db.refresh(tutorial)

    return tutorial


@router.get("/status", response_model=dict)
async def get_tutorial_status(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get tutorial completion status.

    Args:
        merchant_id: Merchant ID
        db: Database session

    Returns:
        Tutorial status with isStarted, isCompleted, currentStep, etc.
    """
    try:
        tutorial = await get_tutorial(db, merchant_id)

        return {
            "data": {
                "isStarted": tutorial.started_at is not None,
                "isCompleted": tutorial.completed_at is not None,
                "isSkipped": tutorial.skipped,
                "currentStep": tutorial.current_step,
                "completedSteps": tutorial.completed_steps,
                "stepsTotal": tutorial.steps_total,
            },
            "meta": {
                "requestId": "status",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except APIError as e:
        raise e
    except Exception as e:
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            f"Failed to get tutorial status: {str(e)}",
        ) from e


@router.post("/start", response_model=dict)
async def start_tutorial(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark tutorial as started.

    Args:
        merchant_id: Merchant ID
        db: Database session

    Returns:
        Started timestamp and current step
    """
    try:
        tutorial = await get_tutorial(db, merchant_id)

        if tutorial.started_at:
            # Tutorial already started - return existing state
            return {
                "data": {
                    "startedAt": tutorial.started_at.isoformat(),
                    "currentStep": tutorial.current_step,
                },
                "meta": {
                    "requestId": "start",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

        tutorial.started_at = datetime.utcnow()
        tutorial.current_step = 1
        await db.commit()

        return {
            "data": {
                "startedAt": tutorial.started_at.isoformat(),
                "currentStep": tutorial.current_step,
            },
            "meta": {
                "requestId": "start",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except APIError as e:
        raise e
    except Exception as e:
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            f"Failed to start tutorial: {str(e)}",
        ) from e


@router.post("/complete", response_model=dict)
async def complete_tutorial(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark tutorial as complete.

    Args:
        merchant_id: Merchant ID
        db: Database session

    Returns:
        Completed timestamp and all completed steps
    """
    try:
        tutorial = await get_tutorial(db, merchant_id)

        if tutorial.completed_at:
            # Tutorial already completed
            raise APIError(
                ErrorCode.TUTORIAL_ALREADY_COMPLETED,
                "Tutorial has already been completed",
            )

        # Mark all steps as completed
        all_steps = [f"step-{i}" for i in range(1, tutorial.steps_total + 1)]
        tutorial.completed_steps = all_steps
        tutorial.current_step = tutorial.steps_total
        tutorial.completed_at = datetime.utcnow()
        await db.commit()

        return {
            "data": {
                "completedAt": tutorial.completed_at.isoformat(),
                "completedSteps": tutorial.completed_steps,
            },
            "meta": {
                "requestId": "complete",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except APIError as e:
        raise e
    except Exception as e:
        raise APIError(
            ErrorCode.TUTORIAL_COMPLETION_FAILED,
            f"Failed to complete tutorial: {str(e)}",
        ) from e


@router.post("/skip", response_model=dict)
async def skip_tutorial(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark tutorial as skipped.

    Args:
        merchant_id: Merchant ID
        db: Database session

    Returns:
        Skip status and timestamp
    """
    try:
        tutorial = await get_tutorial(db, merchant_id)

        tutorial.skipped = True
        tutorial.completed_at = datetime.utcnow()
        await db.commit()

        return {
            "data": {
                "skipped": True,
                "skippedAt": tutorial.completed_at.isoformat(),
            },
            "meta": {
                "requestId": "skip",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except APIError as e:
        raise e
    except Exception as e:
        raise APIError(
            ErrorCode.UNKNOWN_ERROR,
            f"Failed to skip tutorial: {str(e)}",
        ) from e


@router.post("/reset", response_model=dict)
async def reset_tutorial(
    merchant_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reset tutorial progress for replay.

    Args:
        merchant_id: Merchant ID
        db: Database session

    Returns:
        Reset confirmation
    """
    try:
        tutorial = await get_tutorial(db, merchant_id)

        # Reset all progress
        tutorial.current_step = 1
        tutorial.completed_steps = []
        tutorial.started_at = None
        tutorial.completed_at = None
        tutorial.skipped = False
        await db.commit()

        return {
            "data": {
                "reset": True,
                "message": "Tutorial progress has been reset",
            },
            "meta": {
                "requestId": "reset",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except APIError as e:
        raise e
    except Exception as e:
        raise APIError(
            ErrorCode.TUTORIAL_STATE_CORRUPT,
            f"Failed to reset tutorial: {str(e)}",
        ) from e
