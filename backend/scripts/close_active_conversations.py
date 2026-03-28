#!/usr/bin/env python3
"""
Close all active widget conversations.

This script updates all active widget conversations to 'closed' status.
Run this after deploying the conversation lifecycle fix to clean up legacy data.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from app.core.database import get_db
from app.models.conversation import Conversation


async def close_active_conversations():
    """Close all active widget conversations."""
    async for db in get_db():
        # Get count of active conversations
        active_result = await db.execute(
            select(func.count(Conversation.id))
            .where(Conversation.status == "active")
            .where(Conversation.platform == "widget")
        )
        active_count = active_result.scalar() or 0

        print(f"Found {active_count} active widget conversations")

        if active_count == 0:
            print("No active conversations to close.")
            return

        # Get all active widget conversations
        result = await db.execute(
            select(Conversation)
            .where(Conversation.status == "active")
            .where(Conversation.platform == "widget")
        )
        conversations = result.scalars().all()

        # Close each conversation
        closed_count = 0
        for conv in conversations:
            conv.status = "closed"
            conv.handoff_status = "resolved"
            closed_count += 1
            print(f"  - Closed conversation {conv.id} (session: {conv.platform_sender_id})")

        await db.commit()

        print(f"\n✓ Successfully closed {closed_count} conversations")

        # Verify the changes
        verify_result = await db.execute(
            select(Conversation.status, func.count(Conversation.id))
            .where(Conversation.platform == "widget")
            .group_by(Conversation.status)
        )

        print("\nUpdated conversation status distribution:")
        print("STATUS  | COUNT")
        print("-" * 20)
        for row in verify_result:
            status, count = row
            print(f"{status:8} | {count}")

        break


if __name__ == "__main__":
    print("=== Closing Active Widget Conversations ===\n")
    asyncio.run(close_active_conversations())
