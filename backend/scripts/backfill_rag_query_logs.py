#!/usr/bin/env python3
"""Backfill RAG query logs from historical conversation data.

Story 10-7: Knowledge Effectiveness Widget

This script creates sample RAG query log entries from past user messages
to populate the Knowledge Effectiveness widget with realistic data.

Usage:
    python scripts/backfill_rag_query_logs.py [--merchant-id ID] [--match-rate RATE] [--dry-run]

Options:
    --merchant-id ID   Only backfill for specific merchant (default: all)
    --match-rate RATE  Percentage of queries that matched (0.0-1.0, default: 0.75)
    --dry-run          Show what would be created without actually inserting
"""

import argparse
import asyncio
import random
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text

sys.path.insert(0, ".")

from app.core.database import async_session
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.rag_query_log import RAGQueryLog


async def get_user_messages(
    session,
    merchant_id: int | None = None,
) -> list[tuple[int, int, str, datetime]]:
    """Get all user messages from conversations.

    Returns list of (merchant_id, conversation_id, content, created_at) tuples.
    """
    query = (
        select(
            Conversation.merchant_id,
            Message.conversation_id,
            Message.content,
            Message.created_at,
        )
        .select_from(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Message.sender == "customer")
        .where(Message.content.isnot(None))
        .where(Message.content != "")
        .order_by(Message.created_at.asc())
    )

    if merchant_id:
        query = query.where(Conversation.merchant_id == merchant_id)

    result = await session.execute(query)
    return result.fetchall()


def generate_fake_sources() -> list[dict]:
    """Generate fake source attribution for matched queries."""
    document_names = [
        "FAQ - Shipping",
        "Product Catalog",
        "Return Policy",
        "Store Hours",
        "Contact Info",
        "Size Guide",
        "Payment Methods",
    ]

    sources = []
    num_sources = random.randint(1, 3)

    for i in range(num_sources):
        sources.append(
            {
                "document_id": random.randint(1, 100),
                "document_name": random.choice(document_names),
                "chunk_id": random.randint(1, 500),
                "similarity": round(random.uniform(0.7, 0.95), 3),
            }
        )

    return sorted(sources, key=lambda x: x["similarity"], reverse=True)


async def backfill_logs(
    match_rate: float = 0.75,
    merchant_id: int | None = None,
    dry_run: bool = False,
) -> int:
    """Backfill RAG query logs from historical user messages.

    Args:
        match_rate: Percentage of queries that should show as matched (0.0-1.0)
        merchant_id: Optional specific merchant to backfill
        dry_run: If True, don't actually insert records

    Returns:
        Number of log entries created
    """
    async with async_session()() as session:
        messages = await get_user_messages(session, merchant_id)

        if not messages:
            print("No user messages found to backfill.")
            return 0

        print(f"Found {len(messages)} user messages to process.")

        logs_created = 0

        for msg_merchant_id, conv_id, content, created_at in messages:
            if not content or len(content.strip()) < 5:
                continue

            matched = random.random() < match_rate
            confidence = None
            sources = None

            if matched:
                confidence = round(random.uniform(0.65, 0.95), 3)
                sources = generate_fake_sources()

            if dry_run:
                print(
                    f"  Would create: merchant={msg_merchant_id}, "
                    f"matched={matched}, confidence={confidence}, "
                    f"query='{content[:50]}...'"
                )
                logs_created += 1
            else:
                log_entry = RAGQueryLog(
                    merchant_id=msg_merchant_id,
                    query=content[:1000],
                    matched=matched,
                    confidence=confidence,
                    sources=sources,
                    created_at=created_at,
                )
                session.add(log_entry)
                logs_created += 1

        if not dry_run:
            await session.commit()
            print(f"Created {logs_created} RAG query log entries.")
        else:
            print(f"Dry run: would create {logs_created} entries.")

        return logs_created


async def show_stats() -> None:
    """Show current RAG query log statistics."""
    async with async_session()() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM rag_query_logs"))
        total = result.scalar()

        result = await session.execute(
            text("SELECT COUNT(*) FROM rag_query_logs WHERE matched = true")
        )
        matched = result.scalar()

        result = await session.execute(
            text("SELECT AVG(confidence) FROM rag_query_logs WHERE matched = true")
        )
        avg_confidence = result.scalar()

        print("\nCurrent RAG Query Log Statistics:")
        print(f"  Total queries: {total}")
        print(f"  Matched: {matched}")
        print(f"  No match: {total - matched}")
        if total > 0:
            rate = (matched / total) * 100
            print(f"  Match rate: {rate:.1f}%")
        if avg_confidence:
            print(f"  Avg confidence: {avg_confidence:.3f}")


def main():
    parser = argparse.ArgumentParser(
        description="Backfill RAG query logs from historical conversations"
    )
    parser.add_argument(
        "--merchant-id",
        type=int,
        help="Only backfill for specific merchant",
    )
    parser.add_argument(
        "--match-rate",
        type=float,
        default=0.75,
        help="Percentage of queries that matched (0.0-1.0, default: 0.75)",
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
        asyncio.run(show_stats())
        return

    if not 0.0 <= args.match_rate <= 1.0:
        print("Error: match-rate must be between 0.0 and 1.0")
        sys.exit(1)

    print(f"Backfilling RAG query logs (match_rate={args.match_rate})...")
    if args.dry_run:
        print("DRY RUN - no data will be inserted")

    async def run_backfill():
        await backfill_logs(
            match_rate=args.match_rate,
            merchant_id=args.merchant_id,
            dry_run=args.dry_run,
        )
        if not args.dry_run:
            await show_stats()

    asyncio.run(run_backfill())


if __name__ == "__main__":
    main()
