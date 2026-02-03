"""Pydantic schemas for deployment API requests and responses.

All schemas use camelCase aliases for JSON serialization to follow
JavaScript conventions while using snake_case internally.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Platform(str, Enum):
    """Supported deployment platforms."""

    FLYIO = "flyio"
    RAILWAY = "railway"
    RENDER = "render"


class DeploymentStatus(str, Enum):
    """Deployment status values."""

    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LogLevel(str, Enum):
    """Log level values."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class DeploymentStep(str, Enum):
    """Deployment step values."""

    CHECK_CLI = "check_cli"
    AUTHENTICATION = "authentication"
    APP_SETUP = "app_setup"
    CONFIGURATION = "configuration"
    SECRETS = "secrets"
    DEPLOYMENT = "deploy"
    HEALTH_CHECK = "health_check"
    COMPLETE = "complete"


# Request Schemas


class StartDeploymentRequest(BaseModel):
    """Request to start a new deployment."""

    platform: Platform = Field(
        description="Deployment platform to use"
    )


# Response Schemas


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase.

    Args:
        string: The snake_case string to convert

    Returns:
        The camelCase version of the string
    """
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class MinimalEnvelope(BaseModel):
    """Minimal response envelope with metadata."""

    data: Any
    meta: MetaData

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class MetaData(BaseModel):
    """Metadata for API responses."""

    request_id: Optional[str] = Field(None, description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    pagination: Optional[dict[str, Any]] = Field(None, description="Pagination information")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class DeploymentLogEntry(BaseModel):
    """Single deployment log entry."""

    timestamp: datetime = Field(description="Log entry timestamp")
    level: LogLevel = Field(description="Log level (info, warning, error)")
    step: Optional[DeploymentStep] = Field(None, description="Deployment step for this log")
    message: str = Field(description="Log message")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class DeploymentState(BaseModel):
    """Current deployment state."""

    deployment_id: str = Field(description="Unique deployment identifier")
    merchant_key: str = Field(description="Unique merchant key")
    status: DeploymentStatus = Field(description="Current deployment status")
    platform: Platform = Field(description="Deployment platform")
    current_step: Optional[DeploymentStep] = Field(None, description="Current deployment step")
    progress: int = Field(default=0, ge=0, le=100, description="Progress percentage (0-100)")
    logs: list[DeploymentLogEntry] = Field(default_factory=list, description="Deployment logs")
    error_message: Optional[str] = Field(None, description="Error message if deployment failed")
    troubleshooting_url: Optional[str] = Field(None, description="Troubleshooting URL if deployment failed")
    created_at: datetime = Field(description="Deployment creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class StartDeploymentResponse(BaseModel):
    """Response when starting a deployment."""

    deployment_id: str = Field(description="Unique deployment identifier")
    merchant_key: str = Field(description="Unique merchant key")
    status: DeploymentStatus = Field(description="Initial deployment status")
    estimated_seconds: int = Field(default=900, description="Estimated deployment time in seconds")

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class DeploymentStatusResponse(DeploymentState):
    """Response for deployment status queries."""

    pass


# Export schemas for type generation
__all__ = [
    "Platform",
    "DeploymentStatus",
    "LogLevel",
    "DeploymentStep",
    "MinimalEnvelope",
    "MetaData",
    "StartDeploymentRequest",
    "DeploymentLogEntry",
    "DeploymentState",
    "StartDeploymentResponse",
    "DeploymentStatusResponse",
]
