#!/usr/bin/env python3
"""Generate realistic RAG query log data with varying frequencies.

This script creates more realistic test data where queries have different
frequencies (1-5 occurrences) instead of all being exactly 1 or 5.

Usage:
    python scripts/generate_realistic_query_data.py [--merchant-id ID] [--dry-run]
"""

import argparse
import asyncio
import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, ".")

from sqlalchemy import select
from app.core.database import get_session_factory
from app.models.rag_query_log import RAGQueryLog


# Sample realistic queries that users might ask
SAMPLE_QUERIES = [
    # Product questions (higher frequency)
    "What are your store hours?",
    "How much does shipping cost?",
    "What is your return policy?",
    "Do you offer free shipping?",
    "Where is my order?",
    "How can I track my package?",
    "What payment methods do you accept?",
    "Do you have a physical store location?",
    "Are you open on weekends?",
    "What's your phone number?",

    # Product-specific (medium frequency)
    "Do you have this in stock?",
    "When will this item be back in stock?",
    "Can I get a discount on bulk orders?",
    "Do you price match?",
    "Is this product available in different colors?",

    # Support questions (lower frequency)
    "How do I reset my password?",
    "I need to change my shipping address",
    "Can I cancel my order?",
    "How long does delivery take?",
    "Do you ship internationally?",

    # Knowledge base queries (varied frequency)
    "What is your warranty policy?",
    "How do I make a return?",
    "Where can I find product reviews?",
    "Do you offer gift cards?",
    "How do I use a promo code?",
]


async def get_existing_queries(session, merchant_id: int) -> set[str]:
    """Get existing queries for a merchant to avoid duplicates."""
    result = await session.execute(
        select(RAGQueryLog.query).where(RAGQueryLog.merchant_id == merchant_id)
    )
    return {row[0] for row in result.all()}


async def generate_realistic_data(
    merchant_id: int = 1,
    dry_run: bool = False,
) -> int:
    """Generate realistic RAG query log data with varying frequencies.

    Args:
        merchant_id: Merchant ID to generate data for
        dry_run: If True, show what would be created without inserting

    Returns:
        Number of log entries created
    """
    async with get_session_factory()() as session:
        # Get existing queries to avoid conflicts
        existing_queries = await get_existing_queries(session, merchant_id)

        # Generate query frequencies: some popular (4-5x), some medium (2-3x), some rare (1x)
        query_frequencies = []

        # High frequency queries (4-5 occurrences) - 20% of queries
        high_freq_queries = SAMPLE_QUERIES[:4]
        for query in high_freq_queries:
            if query not in existing_queries:
                freq = random.randint(4, 5)
                query_frequencies.append((query, freq))

        # Medium frequency queries (2-3 occurrences) - 30% of queries
        medium_freq_queries = SAMPLE_QUERIES[4:10]
        for query in medium_freq_queries:
            if query not in existing_queries:
                freq = random.randint(2, 3)
                query_frequencies.append((query, freq))

        # Low frequency queries (1 occurrence) - 50% of queries
        low_freq_queries = SAMPLE_QUERIES[10:]
        for query in low_freq_queries:
            if query not in existing_queries:
                query_frequencies.append((query, 1))

        if not query_frequencies:
            print("All sample queries already exist in database.")
            return 0

        # Calculate timestamps spread over the last 7 days
        now = datetime.now(UTC)
        logs_to_create = []

        for query, frequency in query_frequencies:
            # Spread occurrences over time for each query
            base_time = now - timedelta(
                days=random.uniform(0, 7),
                hours=random.uniform(0, 24),
                minutes=random.uniform(0, 60)
            )

            for i in range(frequency):
                # Add some randomness to each occurrence time
                time_offset = timedelta(
                    hours=random.uniform(0, 12),
                    minutes=random.uniform(0, 60)
                )
                created_at = base_time - time_offset

                # Randomly determine if matched (70% match rate)
                matched = random.random() < 0.70
                confidence = None
                sources = None

                if matched:
                    confidence = round(random.uniform(0.65, 0.95), 3)
                    sources = [
                        {
                            "document_id": random.randint(1, 10),
                            "document_name": f"Document {random.randint(1, 10)}",
                            "chunk_id": random.randint(1, 100),
                            "similarity": round(random.uniform(0.70, 0.95), 3),
                        }
                        for _ in range(random.randint(1, 3))
                    ]

                logs_to_create.append({
                    "query": query,
                    "frequency": i + 1,
                    "merchant_id": merchant_id,
                    "matched": matched,
                    "confidence": confidence,
                    "created_at": created_at,
                })

        if dry_run:
            print(f"\nDry run - would create {len(logs_to_create)} log entries:\n")
            for log in logs_to_create[:10]:  # Show first 10
                print(f"  - {log['query'][:50]}... "
                      f"(occurrence #{log['frequency']}, "
                      f"matched={log['matched']}, "
                      f"at {log['created_at'].strftime('%Y-%m-%d %H:%M')})")
            if len(logs_to_create) > 10:
                print(f"  ... and {len(logs_to_create) - 10} more")
            return len(logs_to_create)

        # Insert logs
        logs_created = 0
        for log_data in logs_to_create:
            log_entry = RAGQueryLog(
                merchant_id=log_data["merchant_id"],
                query=log_data["query"],
                matched=log_data["matched"],
                confidence=log_data["confidence"],
                sources=log_data.get("sources"),
                created_at=log_data["created_at"],
            )
            session.add(log_entry)
            logs_created += 1

        await session.commit()

        # Show summary statistics
        print(f"\n✓ Created {logs_created} RAG query log entries\n")

        # Show frequency distribution
        freq_distribution = {}
        for _, freq in query_frequencies:
            freq_distribution[freq] = freq_distribution.get(freq, 0) + 1

        print("Query Frequency Distribution:")
        for freq in sorted(freq_distribution.keys(), reverse=True):
            count = freq_distribution[freq]
            print(f"  {freq} occurrence(s): {count} queries")

        print(f"\nTotal unique queries: {len(query_frequencies)}")
        print(f"Total log entries: {logs_created}")
        print(f"Date range: Last 7 days\n")

        return logs_created


async def show_current_stats():
    """Show current RAG query log statistics."""
    async with get_session_factory()() as session:
        result = await session.execute(
            select(
                RAGQueryLog.query,
                func.count(RAGQueryLog.id).label("count")
            )
            .group_by(RAGQueryLog.query)
            .order_by(func.count(RAGQueryLog.id).desc())
        )
        query_counts = result.all()

        if not query_counts:
            print("\nNo RAG query logs found.")
            return

        print(f"\nCurrent Query Statistics ({len(query_counts)} unique queries):\n")

        # Group by frequency
        freq_groups = {}
        for query, count in query_counts:
            freq_groups[count] = freq_groups.get(count, 0) + 1

        print("Frequency Distribution:")
        for freq in sorted(freq_groups.keys(), reverse=True):
            count = freq_groups[freq]
            bar = "█" * count
            print(f"  {freq}x: {count:2d} queries {bar}")

        print(f"\nTop 10 Queries:")
        for i, (query, count) in enumerate(query_counts[:10], 1):
            query_preview = query[:50] + "..." if len(query) > 50 else query
            print(f"  {i:2d}. [{count}x] {query_preview}")


from sqlalchemy import func


def main():
    parser = argparse.ArgumentParser(
        description="Generate realistic RAG query log data with varying frequencies"
    )
    parser.add_argument(
        "--merchant-id",
        type=int,
        default=1,
        help="Merchant ID (default: 1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without inserting",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show current statistics only",
    )

    args = parser.parse_args()

    if args.stats:
        asyncio.run(show_current_stats())
        return

    print("Generating realistic RAG query log data...\n")

    if args.dry_run:
        print("DRY RUN - no data will be inserted\n")

    async def run():
        await generate_realistic_data(
            merchant_id=args.merchant_id,
            dry_run=args.dry_run,
        )
        if not args.dry_run:
            await show_current_stats()

    asyncio.run(run())


if __name__ == "__main__":
    main()
