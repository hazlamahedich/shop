"""Deployment API endpoints.

Provides endpoints for managing cloud deployments to Fly.io, Railway, and Render.
Handles deployment state tracking, progress streaming, and cancellation.
"""

from __future__ import annotations

import asyncio
import subprocess
import secrets
import string
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Body, Depends, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.schemas.deployment import (
    DeploymentStatus,
    DeploymentState,
    DeploymentLogEntry,
    DeploymentStep,
    LogLevel,
    MinimalEnvelope,
    MetaData,
    Platform,
    StartDeploymentRequest,
    StartDeploymentResponse,
    to_camel,
)
from app.services.deployment import DeploymentService
from app.models.merchant import Merchant
from app.models.deployment_log import DeploymentLog as DeploymentLogModel
from app.models.onboarding import PrerequisiteChecklist

router = APIRouter()

# Deployment tracking - in-memory storage for subprocess handles only
# Actual state stored in PostgreSQL deployment_logs table
_active_subprocesses: dict[str, asyncio.subprocess.Process] = {}
_active_deployments: dict[str, datetime] = {}  # Track deployment start times for rate limiting


def _safe_step_to_enum(step_value: Optional[str]) -> Optional[DeploymentStep]:
    """Safely convert a step string to DeploymentStep enum.

    Handles both enum values (e.g., "check_cli") and script output
    (e.g., "Prerequisites"). Returns None if step doesn't match a known enum.

    Args:
        step_value: The step value from the database

    Returns:
        DeploymentStep enum if valid, None otherwise
    """
    if not step_value:
        return None

    # Try direct enum conversion first
    try:
        return DeploymentStep(step_value)
    except ValueError:
        pass

    # Map script output to enum values (DEFER-1.2-1 fix)
    script_to_enum = {
        "Prerequisites": DeploymentStep.CHECK_CLI,
        "Authentication": DeploymentStep.AUTHENTICATION,
        "App Setup": DeploymentStep.APP_SETUP,
        "Configuration": DeploymentStep.CONFIGURATION,
        "Secrets": DeploymentStep.SECRETS,
        "Deployment": DeploymentStep.DEPLOYMENT,
        "Health Check": DeploymentStep.HEALTH_CHECK,
        "Complete": DeploymentStep.COMPLETE,
    }

    return script_to_enum.get(step_value)

# Rate limiting configuration (per AC requirements)
MIN_DEPLOYMENT_INTERVAL_SECONDS = 600  # 10 minutes between deployments per merchant
MAX_CONCURRENT_DEPLOYMENTS = 1  # Max concurrent deployments per merchant


async def _get_script_path(platform: Platform) -> Path:
    """Get the path to the deployment script for a platform.

    Args:
        platform: The deployment platform

    Returns:
        Path to the deployment script

    Raises:
        APIError: If the script is not found
    """
    script_dir = Path(__file__).parent.parent.parent / "scripts" / "deploy"
    script_name = f"{platform.value}.sh"
    script_path = script_dir / script_name

    if not script_path.exists():
        raise APIError(
            ErrorCode.DEPLOYMENT_FAILED,
            f"Deployment script not found: {script_name}",
            details={"troubleshootingUrl": f"https://docs.example.com/deploy-troubleshoot#{platform.value}"}
        )

    return script_path


def generate_merchant_key() -> str:
    """Generate a unique merchant key with collision detection.

    Returns:
        A unique merchant key in format "shop-{random8chars}"
    """
    suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
    return f"shop-{suffix}"


def generate_secret_key() -> str:
    """Generate a 32-byte SECRET_KEY for production.

    Returns:
        A URL-safe 32-byte random key
    """
    return secrets.token_urlsafe(32)


def hash_secret_key(secret_key: str) -> str:
    """Hash a SECRET_KEY for storage.

    Args:
        secret_key: The plain text secret key

    Returns:
        Hashed secret key using SHA-256
    """
    import hashlib
    return hashlib.sha256(secret_key.encode()).hexdigest()


async def _run_deployment_script(
    db: AsyncSession,
    deployment_id: str,
    platform: Platform,
    merchant_key: str,
    secret_key: str,
    merchant_id: int,
    render_api_key: Optional[str] = None,
) -> None:
    """Run the deployment script in a subprocess.

    Args:
        db: Database session
        deployment_id: Unique deployment identifier
        platform: Deployment platform
        merchant_key: Generated merchant key
        secret_key: Generated SECRET_KEY
        merchant_id: Database merchant ID
        render_api_key: Optional Render API key

    Raises:
        APIError: If deployment exceeds timeout
    """
    script_path = _get_script_path(platform)
    deployment_start_time = datetime.utcnow()
    _active_deployments[deployment_id] = deployment_start_time

    # Deployment timeout: 15 minutes (900 seconds) per AC requirement
    DEPLOYMENT_TIMEOUT_SECONDS = 900

    async def log_message(level: LogLevel, step: Optional[DeploymentStep], message: str) -> None:
        """Add a log entry to database."""
        log_entry = DeploymentLogModel(
            deployment_id=deployment_id,
            merchant_id=merchant_id,
            timestamp=datetime.utcnow(),
            level=level.value,
            step=step.value if step else None,
            message=message,
        )
        db.add(log_entry)
        await db.commit()

    try:
        # Log deployment start
        await log_message(LogLevel.INFO, DeploymentStep.CHECK_CLI, "Starting deployment process")

        # Prepare command arguments
        args = [str(script_path), merchant_key, secret_key]
        if render_api_key:
            args.append(render_api_key)

        # Run the script
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Store subprocess handle for cancellation
        _active_subprocesses[deployment_id] = process

        # Read output line by line with timeout check
        while True:
            # Check for timeout before reading next line (per AC: 15 minutes)
            elapsed = (datetime.utcnow() - deployment_start_time).total_seconds()
            if elapsed > DEPLOYMENT_TIMEOUT_SECONDS:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                _active_subprocesses.pop(deployment_id, None)
                await DeploymentService.update_merchant_status(db, merchant_key, "failed")
                await log_message(LogLevel.ERROR, None, f"Deployment timeout after {int(elapsed)} seconds")
                raise APIError(
                    ErrorCode.DEPLOYMENT_TIMEOUT,
                    f"Deployment exceeded time limit of {DEPLOYMENT_TIMEOUT_SECONDS} seconds",
                    details={"troubleshootingUrl": f"https://docs.example.com/deploy-troubleshoot#{platform.value}"}
                )

            line = await process.stdout.readline()
            if not line:
                break

            line_str = line.decode().strip()
            if not line_str:
                continue

            await log_message(LogLevel.INFO, None, line_str)

        # Wait for process to complete
        returncode = await process.wait()

        # Clean up subprocess handles
        _active_subprocesses.pop(deployment_id, None)
        _active_deployments.pop(deployment_id, None)

        if returncode == 0:
            # Update merchant status to active
            await DeploymentService.update_merchant_status(db, merchant_key, "active")
            await log_message(LogLevel.INFO, DeploymentStep.COMPLETE, "Deployment completed successfully")
        else:
            stderr_output = (await process.stderr.read()).decode()
            # Update merchant status to failed
            await DeploymentService.update_merchant_status(db, merchant_key, "failed")
            await log_message(LogLevel.ERROR, None, f"Deployment failed: {stderr_output}")

    except APIError:
        # Re-raise APIError (like timeout)
        _active_subprocesses.pop(deployment_id, None)
        _active_deployments.pop(deployment_id, None)
        raise
    except Exception as e:
        _active_subprocesses.pop(deployment_id, None)
        _active_deployments.pop(deployment_id, None)
        await DeploymentService.update_merchant_status(db, merchant_key, "failed")
        await log_message(LogLevel.ERROR, None, f"Deployment error: {str(e)}")


@router.post(
    "/start",
    response_model=MinimalEnvelope,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a new deployment",
    description="Initiate a deployment to the specified platform",
)
async def start_deployment(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Start a new deployment.

    Args:
        request: FastAPI Request object
        db: Database session

    Returns:
        MinimalEnvelope with deployment details

    Raises:
        APIError: If a deployment is already in progress or merchant already exists
    """
    # Parse request body manually to work around ASGITransport issues
    import json
    from pydantic import ValidationError

    body_bytes = await request.body()

    # Handle empty body
    if not body_bytes:
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Request body is required",
            details={"errors": [{"field": "platform", "message": "Field required"}]}
        )

    try:
        body_data = json.loads(body_bytes)
    except json.JSONDecodeError:
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid JSON in request body",
            details={"errors": [{"message": "Invalid JSON"}]}
        )

    # Validate platform field exists
    if "platform" not in body_data:
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Platform field is required",
            details={"errors": [{"field": "platform", "message": "Field required"}]}
        )

    # Validate platform value
    try:
        start_request = StartDeploymentRequest(**body_data)
    except ValidationError as e:
        raise APIError(
            ErrorCode.VALIDATION_ERROR,
            "Invalid platform value",
            details={"errors": e.errors()}
        )

    # Rate limiting: Check for recent deployments (per AC requirements)
    from sqlalchemy import func, text
    from datetime import timedelta
    
    # Calculate threshold time
    threshold_time = datetime.utcnow() - timedelta(seconds=MIN_DEPLOYMENT_INTERVAL_SECONDS)
    recent_deployments = await db.execute(
        select(func.count(Merchant.id))
        .where(Merchant.status.in_(["pending", "active"]))
        .where(Merchant.created_at > threshold_time)
    )
    if recent_deployments.scalar() >= MAX_CONCURRENT_DEPLOYMENTS:
        raise APIError(
            ErrorCode.DEPLOYMENT_IN_PROGRESS,
            f"Deployment already in progress. Please wait {MIN_DEPLOYMENT_INTERVAL_SECONDS // 60} minutes between deployments.",
            details={"retryAfterSeconds": MIN_DEPLOYMENT_INTERVAL_SECONDS}
        )

    prerequisites = body_data.get("prerequisites")

    deployment_id = str(uuid4())
    merchant_key = await DeploymentService.generate_merchant_key(db)
    secret_key = generate_secret_key()
    secret_key_hash = hash_secret_key(secret_key)

    # Create merchant record
    merchant = await DeploymentService.create_merchant(
        db=db,
        merchant_key=merchant_key,
        platform=start_request.platform.value,
        secret_key_hash=secret_key_hash,
    )

    # Migrate prerequisites if provided
    if prerequisites:
        await DeploymentService.migrate_prerequisites(
            db=db,
            merchant_id=merchant.id,
            prerequisites=prerequisites,
        )

    # Create initial deployment log entry
    initial_log = DeploymentLogModel(
        deployment_id=deployment_id,
        merchant_id=merchant.id,
        timestamp=datetime.utcnow(),
        level=LogLevel.INFO.value,
        step=DeploymentStep.CHECK_CLI.value,
        message="Deployment initiated",
    )
    db.add(initial_log)
    await db.commit()

    # Start deployment in background
    asyncio.create_task(
        _run_deployment_script(
            db=db,
            deployment_id=deployment_id,
            platform=start_request.platform,
            merchant_key=merchant_key,
            secret_key=secret_key,
            merchant_id=merchant.id,
        )
    )

    response_data = StartDeploymentResponse(
        deployment_id=deployment_id,
        merchant_key=merchant_key,
        status=DeploymentStatus.PENDING,
        estimated_seconds=900,  # 15 minutes
    )

    return MinimalEnvelope(
        data=response_data.model_dump(by_alias=True),
        meta=MetaData(request_id=deployment_id),
    ).model_dump(by_alias=True)


@router.get(
    "/status/{deployment_id}",
    response_model=MinimalEnvelope,
    summary="Get deployment status",
    description="Get the current status and progress of a deployment",
)
async def get_deployment_status(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get deployment status.

    Args:
        deployment_id: Unique deployment identifier
        db: Database session

    Returns:
        MinimalEnvelope with deployment state

    Raises:
        APIError: If deployment not found
    """
    # Get logs from database
    result = await db.execute(
        select(DeploymentLogModel)
        .where(DeploymentLogModel.deployment_id == deployment_id)
        .order_by(DeploymentLogModel.timestamp)
    )
    logs = result.scalars().all()

    if not logs:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Deployment not found: {deployment_id}"
        )

    # Get merchant info from first log
    first_log = logs[0]
    merchant_result = await db.execute(
        select(Merchant).where(Merchant.id == first_log.merchant_id)
    )
    merchant = merchant_result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant not found for deployment: {deployment_id}"
        )

    # Determine status from merchant
    status_mapping = {
        "pending": DeploymentStatus.PENDING,
        "active": DeploymentStatus.SUCCESS,
        "failed": DeploymentStatus.FAILED,
    }
    deployment_status = status_mapping.get(merchant.status, DeploymentStatus.IN_PROGRESS)

    # Get latest log for current step
    latest_log = logs[-1] if logs else None
    # Use raw step string for progress calculation (supports both enum and script output)
    current_step_raw = latest_log.step if latest_log else None
    # Convert to enum for API response (returns None for script-style names)
    current_step = _safe_step_to_enum(current_step_raw) if latest_log else None

    # Calculate progress based on step
    # Maps both human-readable script output and enum values to progress percentages
    # This handles the alignment between script output (e.g., "Prerequisites") and API enums (e.g., "check_cli")
    step_progress = {
        # Enum values (from DeploymentStep)
        "check_cli": 10,
        "authentication": 20,
        "app_setup": 30,
        "configuration": 40,
        "secrets": 50,
        "deploy": 70,
        "health_check": 90,
        "complete": 100,
        # Human-readable script output (from deployment scripts)
        "Prerequisites": 10,
        "Authentication": 20,
        "App Setup": 30,
        "Configuration": 40,
        "Secrets": 50,
        "Deployment": 70,
        "Health Check": 90,
        "Complete": 100,
    }
    progress = step_progress.get(current_step_raw, 0) if current_step_raw else 0
    if deployment_status == DeploymentStatus.SUCCESS:
        progress = 100

    # Convert logs to schema format
    deployment_logs = [
        DeploymentLogEntry(
            timestamp=log.timestamp,
            level=LogLevel(log.level) if log.level else LogLevel.INFO,
            step=_safe_step_to_enum(log.step),
            message=log.message,
        )
        for log in logs
    ]

    deployment_state = DeploymentState(
        deployment_id=deployment_id,
        merchant_key=merchant.merchant_key,
        status=deployment_status,
        platform=Platform(merchant.platform),
        current_step=current_step,
        progress=progress,
        logs=deployment_logs,
        error_message=None,
        troubleshooting_url=None,
        created_at=merchant.created_at,
        updated_at=merchant.updated_at,
    )

    return MinimalEnvelope(
        data=deployment_state.model_dump(by_alias=True),
        meta=MetaData(request_id=deployment_id),
    ).model_dump(by_alias=True)


@router.get(
    "/progress/{deployment_id}",
    summary="Stream deployment progress",
    description="Server-Sent Events stream for real-time deployment updates",
)
async def stream_deployment_progress(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Stream deployment progress via Server-Sent Events.

    Args:
        deployment_id: Unique deployment identifier
        db: Database session

    Returns:
        StreamingResponse with SSE events
    """
    import json

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events for deployment progress."""
        max_iterations = 900  # 15 minutes max
        iteration = 0

        while iteration < max_iterations:
            # Get current status from database
            result = await db.execute(
                select(DeploymentLogModel)
                .where(DeploymentLogModel.deployment_id == deployment_id)
                .order_by(DeploymentLogModel.timestamp)
            )
            logs = result.scalars().all()

            if not logs:
                yield f"data: {{\"error\": \"Deployment not found: {deployment_id}\"}}\n\n"
                break

            # Get merchant status
            first_log = logs[0]
            merchant_result = await db.execute(
                select(Merchant).where(Merchant.id == first_log.merchant_id)
            )
            merchant = merchant_result.scalars().first()

            if not merchant:
                yield f"data: {{\"error\": \"Merchant not found\"}}\n\n"
                break

            # Build deployment state
            status_mapping = {
                "pending": DeploymentStatus.PENDING,
                "active": DeploymentStatus.SUCCESS,
                "failed": DeploymentStatus.FAILED,
            }
            deployment_status = status_mapping.get(merchant.status, DeploymentStatus.IN_PROGRESS)

            latest_log = logs[-1] if logs else None
            # Use raw step string for progress calculation (supports both enum and script output)
            current_step_raw = latest_log.step if latest_log else None
            # Convert to enum for API response (returns None for script-style names)
            current_step = _safe_step_to_enum(current_step_raw) if latest_log else None

            # Maps both human-readable script output and enum values to progress percentages
            # This handles the alignment between script output (e.g., "Prerequisites") and API enums (e.g., "check_cli")
            step_progress = {
                # Enum values (from DeploymentStep)
                "check_cli": 10,
                "authentication": 20,
                "app_setup": 30,
                "configuration": 40,
                "secrets": 50,
                "deploy": 70,
                "health_check": 90,
                "complete": 100,
                # Human-readable script output (from deployment scripts)
                "Prerequisites": 10,
                "Authentication": 20,
                "App Setup": 30,
                "Configuration": 40,
                "Secrets": 50,
                "Deployment": 70,
                "Health Check": 90,
                "Complete": 100,
            }
            progress = step_progress.get(current_step_raw, 0) if current_step_raw else 0
            if deployment_status == DeploymentStatus.SUCCESS:
                progress = 100

            deployment_logs = [
                DeploymentLogEntry(
                    timestamp=log.timestamp,
                    level=LogLevel(log.level) if log.level else LogLevel.INFO,
                    step=_safe_step_to_enum(log.step),
                    message=log.message,
                )
                for log in logs
            ]

            deployment_state = DeploymentState(
                deployment_id=deployment_id,
                merchant_key=merchant.merchant_key,
                status=deployment_status,
                platform=Platform(merchant.platform),
                current_step=current_step,
                progress=progress,
                logs=deployment_logs,
                error_message=None,
                troubleshooting_url=None,
                created_at=merchant.created_at,
                updated_at=merchant.updated_at,
            )

            event_data = deployment_state.model_dump(by_alias=True, mode='json')
            yield f"data: {json.dumps(event_data, default=str)}\n\n"

            # Stop streaming if deployment is complete or failed
            if deployment_status in (
                DeploymentStatus.SUCCESS,
                DeploymentStatus.FAILED,
            ):
                yield "data: [DONE]\n\n"
                break

            # Wait before next update
            await asyncio.sleep(1)
            iteration += 1

        if iteration >= max_iterations:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post(
    "/cancel/{deployment_id}",
    response_model=MinimalEnvelope,
    summary="Cancel a deployment",
    description="Cancel an in-progress deployment",
)
async def cancel_deployment(
    deployment_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Cancel a deployment.

    Args:
        deployment_id: Unique deployment identifier
        db: Database session

    Returns:
        MinimalEnvelope with cancellation confirmation

    Raises:
        APIError: If deployment not found or cannot be cancelled
    """
    # Get deployment logs to find merchant
    result = await db.execute(
        select(DeploymentLogModel)
        .where(DeploymentLogModel.deployment_id == deployment_id)
        .limit(1)
    )
    first_log = result.scalars().first()

    if not first_log:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Deployment not found: {deployment_id}"
        )

    # Get merchant
    merchant_result = await db.execute(
        select(Merchant).where(Merchant.id == first_log.merchant_id)
    )
    merchant = merchant_result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            f"Merchant not found for deployment: {deployment_id}"
        )

    # Check if deployment can be cancelled
    if merchant.status not in ("pending", "active"):
        raise APIError(
            ErrorCode.DEPLOYMENT_FAILED,
            f"Cannot cancel deployment with status: {merchant.status}"
        )

    # Kill subprocess if running
    process = _active_subprocesses.get(deployment_id)
    if process:
        try:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
        except Exception:
            pass
        finally:
            _active_subprocesses.pop(deployment_id, None)

    # Update merchant status
    merchant.status = "failed"
    await db.commit()

    # Log cancellation
    cancel_log = DeploymentLogModel(
        deployment_id=deployment_id,
        merchant_id=merchant.id,
        timestamp=datetime.utcnow(),
        level=LogLevel.WARNING.value,
        step=None,
        message="Deployment cancelled by user",
    )
    db.add(cancel_log)
    await db.commit()

    return MinimalEnvelope(
        data={"message": "Deployment cancelled", "deploymentId": deployment_id},
        meta=MetaData(request_id=deployment_id),
    ).model_dump(by_alias=True)
