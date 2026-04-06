#!/usr/bin/env python3
"""Monitor RAG query logs for real-time analytics.

This script provides monitoring and alerting for new RAG query logs.
Useful for tracking widget usage and knowledge base effectiveness.

Usage:
    # Watch for new logs (real-time)
    python scripts/monitor_rag_logs.py --watch

    # Show statistics
    python scripts/monitor_rag_logs.py --stats

    # Show recent activity
    python scripts/monitor_rag_logs.py --recent

    # Continuous monitoring with alerts
    python scripts/monitor_rag_logs.py --monitor --interval 60
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta, UTC
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from app.core.database import get_session_factory
from app.models.rag_query_log import RAGQueryLog


async def show_stats() -> None:
    """Show current RAG query log statistics."""
    async with get_session_factory()() as session:
        # Total counts
        result = await session.execute(select(func.count(RAGQueryLog.id)))
        total = result.scalar()

        result = await session.execute(
            select(func.count(RAGQueryLog.id)).where(RAGQueryLog.matched == True)
        )
        matched = result.scalar()

        result = await session.execute(
            select(func.avg(RAGQueryLog.confidence)).where(RAGQueryLog.matched == True)
        )
        avg_confidence = result.scalar()

        # Unique queries
        result = await session.execute(select(func.count(func.distinct(RAGQueryLog.query))))
        unique_queries = result.scalar()

        # Top merchants
        result = await session.execute(
            select(RAGQueryLog.merchant_id, func.count(RAGQueryLog.id).label("count"))
            .group_by(RAGQueryLog.merchant_id)
            .order_by(func.count(RAGQueryLog.id).desc())
            .limit(5)
        )
        top_merchants = result.all()

        # Recent activity (last 24h)
        result = await session.execute(
            select(func.count(RAGQueryLog.id)).where(
                RAGQueryLog.created_at >= datetime.now(UTC) - timedelta(hours=24)
            )
        )
        last_24h = result.scalar()

        # Date range
        result = await session.execute(
            select(func.min(RAGQueryLog.created_at), func.max(RAGQueryLog.created_at))
        )
        min_date, max_date = result.first()

        print("\n" + "=" * 60)
        print("RAG Query Log Statistics")
        print("=" * 60)
        print(f"\nTotal Queries: {total}")
        print(f"Unique Queries: {unique_queries}")
        print(f"Matched: {matched} ({matched / total * 100 if total > 0 else 0:.1f}%)")
        print(
            f"No Match: {total - matched} ({(total - matched) / total * 100 if total > 0 else 0:.1f}%)"
        )
        print(
            f"Average Confidence: {avg_confidence:.3f}"
            if avg_confidence
            else "Average Confidence: N/A"
        )
        print(f"\nLast 24 Hours: {last_24h} queries")
        print(f"\nDate Range:")
        print(f"  Earliest: {min_date}" if min_date else "  Earliest: N/A")
        print(f"  Latest: {max_date}" if max_date else "  Latest: N/A")

        if top_merchants:
            print(f"\nTop Merchants:")
            for merchant_id, count in top_merchants:
                print(f"  Merchant {merchant_id}: {count} queries")

        print("\n" + "=" * 60 + "\n")


async def show_recent(limit: int = 20) -> None:
    """Show recent RAG query logs."""
    async with get_session_factory()() as session:
        result = await session.execute(
            select(RAGQueryLog).order_by(RAGQueryLog.created_at.desc()).limit(limit)
        )
        logs = result.scalars().all()

        if not logs:
            print("No recent RAG query logs found.")
            return

        print(f"\nRecent {len(logs)} RAG Query Logs:")
        print("=" * 80)

        for log in logs:
            query_preview = log.query[:60] + "..." if len(log.query) > 60 else log.query
            status = "✓ MATCH" if log.matched else "✗ NO MATCH"
            confidence = f"{log.confidence:.2f}" if log.confidence else "N/A"

            print(
                f"\n[{log.created_at.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"Merchant {log.merchant_id} - {status}"
            )
            print(f"  Confidence: {confidence}")
            print(f"  Query: {query_preview}")

            if log.sources:
                print(f"  Sources: {len(log.sources)} document(s)")

        print("\n" + "=" * 80 + "\n")


async def show_top_queries(days: int = 7, limit: int = 10) -> None:
    """Show top queries over time period."""
    async with get_session_factory()() as session:
        cutoff = datetime.now(UTC) - timedelta(days=days)

        result = await session.execute(
            select(
                RAGQueryLog.query,
                func.count(RAGQueryLog.id).label("count"),
                func.avg(RAGQueryLog.confidence).label("avg_confidence"),
            )
            .where(RAGQueryLog.created_at >= cutoff)
            .group_by(RAGQueryLog.query)
            .order_by(func.count(RAGQueryLog.id).desc())
            .limit(limit)
        )
        queries = result.all()

        if not queries:
            print(f"No queries found in the last {days} days.")
            return

        print(f"\nTop {len(queries)} Queries (Last {days} days):")
        print("=" * 80)

        for query, count, avg_conf in queries:
            query_preview = query[:50] + "..." if len(query) > 50 else query
            conf_str = f"{avg_conf:.2f}" if avg_conf else "N/A"
            print(f"\n[{count}x] {query_preview}")
            print(f"  Avg Confidence: {conf_str}")

        print("\n" + "=" * 80 + "\n")


async def watch_new_logs(interval: int = 30) -> None:
    """Watch for new RAG query logs in real-time."""
    print(f"\nWatching for new RAG query logs (checking every {interval}s)...")
    print("Press Ctrl+C to stop.\n")

    last_id = 0
    async with get_session_factory()() as session:
        result = await session.execute(select(func.max(RAGQueryLog.id)))
        last_id = result.scalar() or 0

    try:
        while True:
            async with get_session_factory()() as session:
                result = await session.execute(
                    select(RAGQueryLog)
                    .where(RAGQueryLog.id > last_id)
                    .order_by(RAGQueryLog.created_at.asc())
                )
                new_logs = result.scalars().all()

                if new_logs:
                    print(f"\n🆕 {len(new_logs)} new query log(s):\n")

                    for log in new_logs:
                        query_preview = log.query[:60] + "..." if len(log.query) > 60 else log.query
                        status = "✓" if log.matched else "✗"
                        confidence = f"{log.confidence:.2f}" if log.confidence else "N/A"

                        print(
                            f"[{log.created_at.strftime('%H:%M:%S')}] "
                            f"Merchant {log.merchant_id} {status} "
                            f"(conf: {confidence})"
                        )
                        print(f"  Query: {query_preview}")

                        last_id = max(last_id, log.id)

                await asyncio.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")


async def check_alerts(threshold_hours: int = 24) -> None:
    """Check for alerts based on inactivity."""
    async with get_session_factory()() as session:
        # Check last log time
        result = await session.execute(select(func.max(RAGQueryLog.created_at)))
        last_log_time = result.scalar()

        print("\n" + "=" * 60)
        print("RAG Query Log Alerts")
        print("=" * 60)

        if not last_log_time:
            print("\n⚠️  WARNING: No RAG query logs found in database!")
            print("   The widget may not be logging queries properly.")
            print("\nRecommendations:")
            print("  1. Test the widget by sending a message")
            print("  2. Check RAG configuration for merchant")
            print("  3. Review backend logs for errors")
        else:
            time_since_last = datetime.now(UTC) - last_log_time
            hours_since = time_since_last.total_seconds() / 3600

            print(f"\nLast Query Log: {last_log_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"Time Since: {hours_since:.1f} hours ago")

            if hours_since > threshold_hours:
                print(f"\n⚠️  WARNING: No queries logged for {hours_since:.1f} hours!")
                print("   This may indicate:")
                print("   - No widget usage")
                print("   - RAG logging is disabled")
                print("   - Backend issues")
            else:
                print("\n✓ RAG logging is active")

        print("\n" + "=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Monitor RAG query logs for real-time analytics")
    parser.add_argument("--stats", action="store_true", help="Show current statistics")
    parser.add_argument("--recent", action="store_true", help="Show recent query logs")
    parser.add_argument("--top", action="store_true", help="Show top queries")
    parser.add_argument(
        "--days", type=int, default=7, help="Number of days for top queries (default: 7)"
    )
    parser.add_argument("--watch", action="store_true", help="Watch for new logs in real-time")
    parser.add_argument(
        "--monitor", action="store_true", help="Run continuous monitoring with alerts"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds for monitor mode (default: 60)",
    )
    parser.add_argument(
        "--alerts", action="store_true", help="Check for alerts (inactivity warnings)"
    )

    args = parser.parse_args()

    if args.stats:
        asyncio.run(show_stats())
    elif args.recent:
        asyncio.run(show_recent())
    elif args.top:
        asyncio.run(show_top_queries(days=args.days))
    elif args.watch:
        asyncio.run(watch_new_logs(interval=args.interval))
    elif args.monitor:
        asyncio.run(watch_new_logs(interval=args.interval))
    elif args.alerts:
        asyncio.run(check_alerts())
    else:
        # Default: show stats and recent activity
        asyncio.run(show_stats())
        asyncio.run(show_recent(limit=10))


if __name__ == "__main__":
    main()
