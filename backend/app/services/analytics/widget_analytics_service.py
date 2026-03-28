"""Widget Analytics Service.

Story 9-10: Analytics & Performance Monitoring

Service for processing and aggregating widget analytics events.
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.widget_analytics_event import WidgetAnalyticsEvent

logger = structlog.get_logger(__name__)

EVENT_TYPES = {
    "widget_open",
    "message_send",
    "quick_reply_click",
    "voice_input",
    "proactive_trigger",
    "carousel_engagement",
    "faq_click",
}


class WidgetAnalyticsService:
    """Service for widget analytics events.

    Story 9-10: Handles event ingestion, aggregation, and export.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest_events(
        self,
        merchant_id: int,
        events: list[dict[str, Any]],
    ) -> int:
        """Ingest a batch of widget analytics events.

        Args:
            merchant_id: Merchant ID
            events: List of event payloads

        Returns:
            Number of events accepted
        """
        accepted = 0

        for event in events:
            event_type = event.get("type", "")
            if event_type not in EVENT_TYPES:
                logger.warning(
                    "Unknown event type",
                    event_type=event_type,
                    merchant_id=merchant_id,
                )
                continue

            try:
                timestamp_str = event.get("timestamp", "")
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                else:
                    timestamp = datetime.now(UTC)

                db_event = WidgetAnalyticsEvent(
                    merchant_id=merchant_id,
                    session_id=event.get("session_id", ""),
                    event_type=event_type,
                    timestamp=timestamp,
                    event_metadata=event.get("metadata", {}) or {},
                )
                self.db.add(db_event)
                accepted += 1
            except Exception as e:
                logger.error(
                    "Failed to ingest event",
                    error=str(e),
                    event=event,
                )
                continue

        await self.db.commit()
        return accepted

    async def get_metrics(
        self,
        merchant_id: int,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get aggregated widget metrics for a merchant.

        Args:
            merchant_id: Merchant ID
            days: Number of days to look back

        Returns:
            Dict with metrics, trends, and performance data
        """
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)
        prev_start = start_date - timedelta(days=days)

        events = await self._get_events_in_range(merchant_id, start_date, end_date)
        prev_events = await self._get_events_in_range(merchant_id, prev_start, start_date)

        metrics = self._calculate_metrics(events)
        prev_metrics = self._calculate_metrics(prev_events)

        trends = self._calc_trends(metrics, prev_metrics)

        performance = {
            "avg_load_time_ms": self._calc_avg_load_time(events),
            "p95_load_time_ms": self._calc_p95_load_time(events),
            "bundle_size_kb": self._calc_bundle_size(events),
        }

        return {
            "merchant_id": merchant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days,
            },
            "metrics": metrics,
            "trends": trends,
            "performance": performance,
        }

    async def export_csv(
        self,
        merchant_id: int,
        start_date: str | None = None,
        end_date: str | None = None,
        event_type: str | None = None,
    ) -> str:
        """Export widget analytics as CSV.

        Args:
            merchant_id: Merchant ID
            start_date: ISO date string for start of range
            end_date: ISO date string for end of range
            event_type: Optional filter by event type

        Returns:
            CSV string
        """
        query = select(WidgetAnalyticsEvent).where(WidgetAnalyticsEvent.merchant_id == merchant_id)

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.where(WidgetAnalyticsEvent.timestamp >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.where(WidgetAnalyticsEvent.timestamp <= end_dt)

        if event_type:
            query = query.where(WidgetAnalyticsEvent.event_type == event_type)

        query = query.order_by(WidgetAnalyticsEvent.timestamp.desc())

        result = await self.db.execute(query)
        events = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "timestamp",
                "event_type",
                "session_id",
                "metadata",
            ]
        )

        for event in events:
            writer.writerow(
                [
                    event.timestamp.isoformat(),
                    event.event_type,
                    event.session_id,
                    str(event.event_metadata) if event.event_metadata else "",
                ]
            )

        return output.getvalue()

    async def cleanup_old_events(self, days: int = 30) -> int:
        """Delete events older than specified days (GDPR compliance).

        Args:
            days: Number of days to retain

        Returns:
            Number of deleted events
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        stmt = (
            delete(WidgetAnalyticsEvent)
            .where(WidgetAnalyticsEvent.timestamp < cutoff)
            .returning(WidgetAnalyticsEvent.id)
        )

        result = await self.db.execute(stmt)
        deleted_ids = result.fetchall()
        await self.db.commit()

        deleted = len(deleted_ids)
        logger.info(
            "Cleaned up old widget analytics events", deleted=deleted, cutoff=cutoff.isoformat()
        )
        return deleted

    async def _get_events_in_range(
        self,
        merchant_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> list[WidgetAnalyticsEvent]:
        """Get events in a date range."""
        result = await self.db.execute(
            select(WidgetAnalyticsEvent).where(
                and_(
                    WidgetAnalyticsEvent.merchant_id == merchant_id,
                    WidgetAnalyticsEvent.timestamp >= start_date,
                    WidgetAnalyticsEvent.timestamp < end_date,
                )
            )
        )
        return list(result.scalars().all())

    def _calculate_metrics(self, events: list[WidgetAnalyticsEvent]) -> dict[str, float]:
        """Calculate metrics from events."""
        if not events:
            return {
                "open_rate": 0.0,
                "message_rate": 0.0,
                "quick_reply_rate": 0.0,
                "voice_input_rate": 0.0,
                "proactive_conversion_rate": 0.0,
                "carousel_engagement_rate": 0.0,
            }

        counts: dict[str, int] = {et: 0 for et in EVENT_TYPES}
        for event in events:
            if event.event_type in counts:
                counts[event.event_type] += 1

        total_opens = counts.get("widget_open", 0)
        total_sessions = len(set(e.session_id for e in events)) or 1

        return {
            "open_rate": round(total_opens / total_sessions * 100, 2)
            if total_sessions > 0
            else 0.0,
            "message_rate": round(counts.get("message_send", 0) / max(total_opens, 1) * 100, 2),
            "quick_reply_rate": round(
                counts.get("quick_reply_click", 0) / max(total_opens, 1) * 100, 2
            ),
            "voice_input_rate": round(counts.get("voice_input", 0) / max(total_opens, 1) * 100, 2),
            "proactive_conversion_rate": round(
                counts.get("proactive_trigger", 0) / max(total_sessions, 1) * 100, 2
            ),
            "carousel_engagement_rate": round(
                counts.get("carousel_engagement", 0) / max(total_opens, 1) * 100, 2
            ),
        }

    def _calc_change(self, current: float, previous: float) -> float:
        """Calculate percentage change."""
        if previous == 0:
            return 0.0
        return round((current - previous) / previous * 100, 2)

    def _calc_trends(
        self, current_metrics: dict[str, float], prev_metrics: dict[str, float]
    ) -> dict[str, float]:
        """Calculate trends between current and previous periods."""
        return {
            "open_rate_change": self._calc_change(
                current_metrics.get("open_rate", 0.0), prev_metrics.get("open_rate", 0.0)
            ),
            "message_rate_change": self._calc_change(
                current_metrics.get("message_rate", 0.0), prev_metrics.get("message_rate", 0.0)
            ),
        }

    def _calc_avg_load_time(self, events: list[WidgetAnalyticsEvent]) -> float:
        """Calculate average load time from event metadata."""
        if not events:
            return 0.0

        load_times = []
        for event in events:
            if event.event_metadata and "load_time_ms" in event.event_metadata:
                load_time = event.event_metadata["load_time_ms"]
                if isinstance(load_time, (int, float)):
                    load_times.append(load_time)

        return round(sum(load_times) / len(load_times), 2) if load_times else 0.0

    def _calc_p95_load_time(self, events: list[WidgetAnalyticsEvent]) -> float:
        """Calculate p95 load time from event metadata."""
        if not events:
            return 0.0

        load_times = []
        for event in events:
            if event.event_metadata and "load_time_ms" in event.event_metadata:
                load_time = event.event_metadata["load_time_ms"]
                if isinstance(load_time, (int, float)):
                    load_times.append(load_time)

        if not load_times:
            return 0.0

        load_times.sort()
        p95_index = int(len(load_times) * 0.95)
        return load_times[min(p95_index, len(load_times) - 1)]

    def _calc_bundle_size(self, events: list[WidgetAnalyticsEvent]) -> float:
        """Calculate average bundle size from event metadata."""
        if not events:
            return 0.0

        bundle_sizes = []
        for event in events:
            if event.event_metadata and "bundle_size_kb" in event.event_metadata:
                bundle_size = event.event_metadata["bundle_size_kb"]
                if isinstance(bundle_size, (int, float)):
                    bundle_sizes.append(bundle_size)

        return round(sum(bundle_sizes) / len(bundle_sizes), 2) if bundle_sizes else 0.0
