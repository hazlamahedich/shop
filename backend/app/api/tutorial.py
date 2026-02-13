"""Tutorial API endpoints.

API endpoints for managing tutorial progress:
- GET /api/tutorial/status - Get tutorial completion status
- POST /api/tutorial/start - Mark tutorial as started
- POST /api/tutorial/complete - Mark tutorial as complete
- POST /api/tutorial/skip - Mark tutorial as skipped
- POST /api/tutorial/reset - Reset tutorial progress (for replay)

SECURITY: All endpoints extract merchant_id from authenticated session (JWT)
instead of accepting it as a query parameter to prevent IDOR.
"""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_request_merchant_id
from app.models.tutorial import Tutorial

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tutorial"])


async def get_tutorial(
    db: AsyncSession,
    merchant_id: int,
) -> Tutorial:
    """Get tutorial record for merchant, creating if not exists.

    Args:
        db: Database session
        merchant_id: Merchant ID (extracted from authenticated session)

    Returns:
        Tutorial record
    """
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


@router.get("/status")
async def get_tutorial_status(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get tutorial completion status."""
    merchant_id = get_request_merchant_id(request)
    try:
        tutorial = await get_tutorial(db, merchant_id)

        return {
            "data": {
                "isStarted": tutorial.started_at is not None,
                "isCompleted": tutorial.completed_at is not None,
                "isSkipped": tutorial.skipped,
                "currentStep": tutorial.current_step,
                "completedSteps": tutorial.completed_steps,
                "stepsTotal": 8,
            },
            "meta": {
                "requestId": "status",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tutorial status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tutorial status: {str(e)}",
        )


@router.post("/start")
async def start_tutorial(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark tutorial as started."""
    merchant_id = get_request_merchant_id(request)
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
        await db.refresh(tutorial)

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start tutorial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start tutorial: {str(e)}",
        )


@router.post("/complete")
async def complete_tutorial(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark tutorial as complete."""
    merchant_id = get_request_merchant_id(request)
    try:
        tutorial = await get_tutorial(db, merchant_id)

        if tutorial.completed_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tutorial has already been completed",
            )

        # Mark all steps as completed
        all_steps = [f"step-{i}" for i in range(1, tutorial.steps_total + 1)]
        tutorial.completed_steps = all_steps
        tutorial.current_step = tutorial.steps_total
        tutorial.completed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(tutorial)

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete tutorial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete tutorial: {str(e)}",
        )


@router.post("/skip")
async def skip_tutorial(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark tutorial as skipped."""
    merchant_id = get_request_merchant_id(request)
    try:
        tutorial = await get_tutorial(db, merchant_id)

        tutorial.skipped = True
        tutorial.completed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(tutorial)

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to skip tutorial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to skip tutorial: {str(e)}",
        )


@router.post("/reset")
async def reset_tutorial(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Reset tutorial progress for replay."""
    merchant_id = get_request_merchant_id(request)
    try:
        tutorial = await get_tutorial(db, merchant_id)

        # Reset all progress
        tutorial.current_step = 1
        tutorial.completed_steps = []
        tutorial.started_at = None
        tutorial.completed_at = None
        tutorial.skipped = False
        await db.commit()
        await db.refresh(tutorial)

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset tutorial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset tutorial: {str(e)}",
        )
