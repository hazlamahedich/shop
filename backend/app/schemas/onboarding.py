"""Pydantic schemas for onboarding prerequisite validation."""

from __future__ import annotations

from typing import Any, Optional
from datetime import datetime
from pydantic import Field

from app.schemas.base import BaseSchema, MetaData, MinimalEnvelope


class PrerequisiteCheckRequest(BaseSchema):
    """Request schema for prerequisite check.

    Uses camelCase aliases for API compatibility with frontend.
    """

    cloud_account: bool = Field(description="Cloud account ready")
    facebook_account: bool = Field(description="Facebook account ready")
    shopify_access: bool = Field(description="Shopify access ready")
    llm_provider_choice: bool = Field(description="LLM provider chosen")


class PrerequisiteCheckResponse(BaseSchema):
    """Response schema for prerequisite check.

    Returns completion status and list of missing prerequisites.
    """

    is_complete: bool = Field(description="Whether all prerequisites are complete")
    missing: list[str] = Field(default_factory=list, description="Missing prerequisite names")


class PrerequisiteStateCreate(BaseSchema):
    """Request schema for creating/updating prerequisite state.

    Maps to PrerequisiteChecklist ORM model for database storage.
    """

    has_cloud_account: bool = Field(description="Has cloud account")
    has_facebook_account: bool = Field(description="Has Facebook account")
    has_shopify_access: bool = Field(description="Has Shopify access")
    has_llm_provider_choice: bool = Field(description="Has chosen LLM provider")


class PrerequisiteStateResponse(BaseSchema):
    """Response schema for prerequisite state from database.

    Returns the stored prerequisite checklist state for a merchant.
    """

    id: int = Field(description="Database record ID")
    merchant_id: int = Field(description="Merchant ID")
    has_cloud_account: bool = Field(description="Has cloud account")
    has_facebook_account: bool = Field(description="Has Facebook account")
    has_shopify_access: bool = Field(description="Has Shopify access")
    has_llm_provider_choice: bool = Field(description="Has chosen LLM provider")
    is_complete: bool = Field(description="Whether all prerequisites are complete")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    created_at: datetime = Field(description="Record creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class PrerequisiteSyncRequest(BaseSchema):
    """Request schema for syncing localStorage state to backend.

    Used for migration from localStorage to PostgreSQL.
    """

    cloud_account: bool = Field(description="Cloud account status")
    facebook_account: bool = Field(description="Facebook account status")
    shopify_access: bool = Field(description="Shopify access status")
    llm_provider_choice: bool = Field(description="LLM provider choice status")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


__all__ = [
    "MinimalEnvelope",
    "MetaData",
    "PrerequisiteCheckRequest",
    "PrerequisiteCheckResponse",
    "PrerequisiteStateCreate",
    "PrerequisiteStateResponse",
    "PrerequisiteSyncRequest",
]
