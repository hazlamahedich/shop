"""Pydantic schemas for onboarding prerequisite validation."""

from __future__ import annotations

from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PrerequisiteCheckRequest(BaseModel):
    """Request schema for prerequisite check.

    Uses camelCase aliases for API compatibility with frontend.
    """

    cloud_account: bool = Field(alias="cloudAccount")
    facebook_account: bool = Field(alias="facebookAccount")
    shopify_access: bool = Field(alias="shopifyAccess")
    llm_provider_choice: bool = Field(alias="llmProviderChoice")

    class Config:
        """Pydantic config."""

        populate_by_name = True


class PrerequisiteCheckResponse(BaseModel):
    """Response schema for prerequisite check.

    Returns completion status and list of missing prerequisites.
    """

    is_complete: bool = Field(alias="isComplete")
    missing: list[str] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        populate_by_name = True


class PrerequisiteStateCreate(BaseModel):
    """Request schema for creating/updating prerequisite state.

    Maps to PrerequisiteChecklist ORM model for database storage.
    """

    has_cloud_account: bool = Field(alias="hasCloudAccount")
    has_facebook_account: bool = Field(alias="hasFacebookAccount")
    has_shopify_access: bool = Field(alias="hasShopifyAccess")
    has_llm_provider_choice: bool = Field(alias="hasLlmProviderChoice")

    class Config:
        """Pydantic config."""

        populate_by_name = True


class PrerequisiteStateResponse(BaseModel):
    """Response schema for prerequisite state from database.

    Returns the stored prerequisite checklist state for a merchant.
    """

    id: int
    merchant_id: int = Field(alias="merchantId")
    has_cloud_account: bool = Field(alias="hasCloudAccount")
    has_facebook_account: bool = Field(alias="hasFacebookAccount")
    has_shopify_access: bool = Field(alias="hasShopifyAccess")
    has_llm_provider_choice: bool = Field(alias="hasLlmProviderChoice")
    is_complete: bool = Field(alias="isComplete")
    completed_at: Optional[datetime] = Field(None, alias="completedAt")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    class Config:
        """Pydantic config."""

        populate_by_name = True


class PrerequisiteSyncRequest(BaseModel):
    """Request schema for syncing localStorage state to backend.

    Used for migration from localStorage to PostgreSQL.
    """

    cloud_account: bool = Field(alias="cloudAccount")
    facebook_account: bool = Field(alias="facebookAccount")
    shopify_access: bool = Field(alias="shopifyAccess")
    llm_provider_choice: bool = Field(alias="llmProviderChoice")
    updated_at: Optional[str] = Field(None, alias="updatedAt")

    class Config:
        """Pydantic config."""

        populate_by_name = True


class MetaData(BaseModel):
    """Metadata for API responses following Minimal Envelope pattern.

    Includes request_id for tracing and ISO-8601 timestamp.
    """

    request_id: str = Field(alias="requestId")
    timestamp: str

    class Config:
        """Pydantic config."""

        populate_by_name = True


class MinimalEnvelope(BaseModel):
    """Minimal envelope pattern for API responses.

    Structure: {data: {...}, meta: {requestId, timestamp}}
    Follows project architecture pattern for consistent API responses.
    """

    data: Any
    meta: MetaData
