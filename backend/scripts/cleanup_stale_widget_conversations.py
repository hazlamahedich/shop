#!/usr/bin/env python3
"""
Immediately clean up stale widget conversations.

This script runs the conversation cleanup service once to close
all conversations with expired Redis sessions or conversations
older than 2 hours.

Run this to immediately clean up existing stale conversations.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.widget.widget_conversation_cleanup_service import (
    WidgetConversationCleanupService,
)


async def main():
    """Run conversation cleanup."""
    print("=== Widget Conversation Cleanup ===\n")

    service = WidgetConversationCleanupService()

    print("Scanning for stale conversations...")
    stats = await service.cleanup_stale_conversations()

    print(f"\nResults:")
    print(f"  Scanned:    {stats['scanned']}")
    print(f"  Found stale: {stats['stale']}")
    print(f"  Closed:     {stats['closed']}")
    print(f"  Errors:     {stats['errors']}")

    if stats["closed"] > 0:
        print(f"\n✓ Successfully closed {stats['closed']} stale conversations")
    elif stats["stale"] == 0:
        print("\n✓ No stale conversations found")
    else:
        print(f"\n⚠ Found {stats['stale']} stale but couldn't close them")

    if stats["errors"] > 0:
        print(f"\n⚠ Encountered {stats['errors']} errors")


if __name__ == "__main__":
    asyncio.run(main())
