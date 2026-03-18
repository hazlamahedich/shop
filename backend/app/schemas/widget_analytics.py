"""Widget Analytics Pydantic Schemas

Story 9-10: Analytics & Performance Monitoring

API schemas for widget analytics endpoints.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WidgetAnalyticsEventPayload(BaseModel):
    """Single analytics event payload."""

    type: str
    timestamp: str
    session_id: str
    metadata: dict[str, Any] | None = None


class WidgetAnalyticsEventsRequest(BaseModel):
    """Batch request for analytics events."""

    merchant_id: int
    events: list[WidgetAnalyticsEventPayload]


class WidgetAnalyticsEventsResponse(BaseModel):
    """Response for analytics events endpoint."""

    accepted: int


class WidgetMetricsResponse(BaseModel):
    """Widget metrics response."""

    merchant_id: int
    period: dict[str, Any]
    metrics: dict[str, float]
    trends: dict[str, float]
    performance: dict[str, float]


class WidgetMetricsQuery(BaseModel):
    """Query params for widget metrics."""

    merchant_id: int = Field(...)
    days: int = Field(default=30)


class WidgetExportFilters(BaseModel):
    """Filters for CSV export."""

    start_date: str | None = Field(default=None)
    end_date: str | None = Field(default=None)
    merchant_id: int | None = Field(default=None)
    event_type: str | None = Field(default=None)
    limit: int | None = Field(default=1000)
    offset: int | None = Field(default=0)


class WidgetAnalyticsEventMetadata(BaseModel):
    """Metadata for analytics events."""

    product_id: str | None = None
    action: str | None = None
    duration_ms: int | None = None
    success: bool | None = None
    error: str | None = None
    button_label: str | None = None
    trigger_type: str | None = None
    carousel_action: str | None = None
