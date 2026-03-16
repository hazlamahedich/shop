"""Settings API endpoints.

Story 4-12: Business Hours Handling
Story 8-11: LLM Embedding Provider Integration & Re-embedding

Provides endpoints for:
- Getting business hours settings in API test format
- Getting/updating embedding provider settings
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import APIError, ErrorCode
from app.models.merchant import Merchant
from app.schemas.base import MinimalEnvelope, MetaData

router = APIRouter()


class DaySchedule(BaseModel):
    """Schedule for a single day."""

    is_open: bool = False
    open_time: str | None = None
    close_time: str | None = None


class BusinessHoursSettingsData(BaseModel):
    """Business hours settings data."""

    enabled: bool = False
    timezone: str = "America/Los_Angeles"
    schedule: dict[str, DaySchedule] = Field(default_factory=dict)


class BusinessHoursSettingsEnvelope(MinimalEnvelope):
    """Envelope for business hours settings response."""

    data: BusinessHoursSettingsData


# Story 8-11: Embedding Provider Settings
class EmbeddingProviderSettings(BaseModel):
    """Embedding provider settings."""

    provider: str = "openai"
    model: str = "text-embedding-3-small"


class EmbeddingProviderSettingsData(BaseModel):
    """Data for embedding provider settings."""

    provider: str
    model: str
    dimension: int
    re_embedding_required: bool = False
    document_count: int = 0


class EmbeddingProviderSettingsEnvelope(MinimalEnvelope):
    """Envelope for embedding provider settings response."""

    data: EmbeddingProviderSettingsData


def _get_merchant_id(request: Request) -> int:
    """Extract merchant ID from request state or headers."""
    merchant_id = getattr(request.state, "merchant_id", None)
    if not merchant_id:
        if settings()["DEBUG"]:
            merchant_id_header = request.headers.get("X-Merchant-Id")
            if merchant_id_header:
                return int(merchant_id_header)
            return 1
        raise APIError(
            ErrorCode.AUTH_FAILED,
            "Authentication required",
        )
    return merchant_id


@router.get(
    "/business-hours",
    response_model=BusinessHoursSettingsEnvelope,
)
async def get_business_hours_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> BusinessHoursSettingsEnvelope:
    """Get business hours settings.

    Story 4-12: Business Hours Handling
    AC1: Business Hours in Handoff Message

    Returns business hours configuration in the format expected by
    the API tests with day-by-day schedule.

    Args:
        request: FastAPI request
        db: Database session

    Returns:
        BusinessHoursSettingsEnvelope with schedule
    """
    merchant_id = _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            "Merchant not found",
        )

    config = merchant.business_hours_config or {}
    hours_list = config.get("hours", [])

    days_map = {
        "mon": "monday",
        "tue": "tuesday",
        "wed": "wednesday",
        "thu": "thursday",
        "fri": "friday",
        "sat": "saturday",
        "sun": "sunday",
    }

    schedule: dict[str, DaySchedule] = {}
    for day_abbr in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
        schedule[days_map[day_abbr]] = DaySchedule(is_open=False)

    for day_hours in hours_list:
        day_abbr = day_hours.get("day", "").lower()[:3]
        if day_abbr in days_map:
            schedule[days_map[day_abbr]] = DaySchedule(
                is_open=day_hours.get("is_open", False),
                open_time=day_hours.get("open_time"),
                close_time=day_hours.get("close_time"),
            )

    enabled = bool(hours_list)

    return BusinessHoursSettingsEnvelope(
        data=BusinessHoursSettingsData(
            enabled=enabled,
            timezone=config.get("timezone", "America/Los_Angeles"),
            schedule=schedule,
        ),
        meta=MetaData(
            request_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )


@router.get(
    "/embedding-provider",
    response_model=EmbeddingProviderSettingsEnvelope,
)
async def get_embedding_provider_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> EmbeddingProviderSettingsEnvelope:
    """Get embedding provider settings.

    Story 8-11: LLM Embedding Provider Integration

    Returns current embedding provider configuration.

    Args:
        request: FastAPI request
        db: Database session

    Returns:
        EmbeddingProviderSettingsEnvelope with settings
    """
    merchant_id = _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            "Merchant not found",
        )

    provider = getattr(merchant, "embedding_provider", "openai") or "openai"
    model = (
        getattr(merchant, "embedding_model", "text-embedding-3-small") or "text-embedding-3-small"
    )
    dimension = getattr(merchant, "embedding_dimension", 1536) or 1536

    return EmbeddingProviderSettingsEnvelope(
        data=EmbeddingProviderSettingsData(
            provider=provider,
            model=model,
            dimension=dimension,
            re_embedding_required=False,
            document_count=0,
        ),
        meta=MetaData(
            request_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )


@router.patch(
    "/embedding-provider",
    response_model=EmbeddingProviderSettingsEnvelope,
)
async def update_embedding_provider(
    request: Request,
    settings_data: EmbeddingProviderSettings,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> EmbeddingProviderSettingsEnvelope:
    """Update embedding provider settings.

    Story 8-11: LLM Embedding Provider Integration

    Updates the embedding provider configuration.
    If dimension changes, triggers re-embedding of all documents.

    Args:
        request: FastAPI request
        settings_data: New provider settings
        background_tasks: Background tasks for re-embedding
        db: Database session

    Returns:
        EmbeddingProviderSettingsEnvelope with updated settings
    """
    from app.services.rag.dimension_handler import DimensionHandler
    from app.services.rag.embedding_service import EMBEDDING_DIMENSIONS

    merchant_id = _get_merchant_id(request)

    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalars().first()

    if not merchant:
        raise APIError(
            ErrorCode.MERCHANT_NOT_FOUND,
            "Merchant not found",
        )

    old_dimension = getattr(merchant, "embedding_dimension", 1536) or 1536
    new_provider = settings_data.provider.lower()
    new_dimension = EMBEDDING_DIMENSIONS.get(new_provider, 1536)
    new_model = settings_data.model

    needs_reembedding = old_dimension != new_dimension

    merchant.embedding_provider = new_provider
    merchant.embedding_model = new_model
    merchant.embedding_dimension = new_dimension
    await db.commit()

    doc_count = 0
    if needs_reembedding:
        doc_count = await DimensionHandler.mark_documents_for_reembedding(
            db=db,
            merchant_id=merchant_id,
        )

        from app.services.rag.reembedding_worker import reembed_all_documents

        background_tasks.add_task(
            reembed_all_documents,
            merchant_id=merchant_id,
        )

    return EmbeddingProviderSettingsEnvelope(
        data=EmbeddingProviderSettingsData(
            provider=new_provider,
            model=new_model,
            dimension=new_dimension,
            re_embedding_required=needs_reembedding,
            document_count=doc_count,
        ),
        meta=MetaData(
            request_id=str(uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )
