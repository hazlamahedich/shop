#!/usr/bin/env python3
"""
One-time script to create missing HandoffAlert records for existing handoff conversations.

This script finds all conversations with status='handoff' that don't have a corresponding
HandoffAlert record and creates them.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.core.database import async_session
from app.models.conversation import Conversation
from app.models.handoff_alert import HandoffAlert
from app.models.message import Message


async def create_missing_alerts():
    """Create missing HandoffAlert records for handoff conversations."""
    async with async_session() as db:
        # Find all handoff conversations without alerts
        result = await db.execute(
            select(Conversation).where(
                Conversation.status == "handoff",
                Conversation.handoff_status.in_(["pending", "active"]),
            )
        )
        handoff_conversations = result.scalars().all()

        print(f"Found {len(handoff_conversations)} handoff conversations")

        created_count = 0
        skipped_count = 0

        for conv in handoff_conversations:
            # Check if alert already exists
            existing_alert = await db.execute(
                select(HandoffAlert).where(HandoffAlert.conversation_id == conv.id)
            )
            if existing_alert.scalars().first():
                skipped_count += 1
                print(f"  [SKIP] Conversation {conv.id} already has alert")
                continue

            # Get last customer message for preview
            msg_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conv.id)
                .where(Message.sender == "customer")
                .order_by(Message.created_at.desc())
                .limit(1)
            )
            last_msg = msg_result.scalars().first()

            # Determine urgency
            urgency_level = "low"
            if last_msg and last_msg.content:
                msg_lower = last_msg.content.lower()
                high_priority = ["checkout", "payment", "charged", "refund", "cancel"]
                medium_priority = ["order", "delivery", "shipping", "track", "where is"]

                if any(kw in msg_lower for kw in high_priority):
                    urgency_level = "high"
                elif conv.handoff_reason in ("low_confidence", "clarification_loop"):
                    urgency_level = "medium"
                elif any(kw in msg_lower for kw in medium_priority):
                    urgency_level = "medium"

            # Get customer ID (masked)
            customer_id = None
            if conv.platform_sender_id:
                if len(conv.platform_sender_id) > 4:
                    customer_id = f"{conv.platform_sender_id[:4]}****"
                else:
                    customer_id = conv.platform_sender_id

            # Get conversation preview (decrypted)
            conversation_preview = None
            if last_msg:
                try:
                    decrypted = last_msg.decrypted_content
                    if decrypted:
                        conversation_preview = decrypted[:500]
                except Exception:
                    # Fall back to encrypted content if decryption fails
                    if last_msg.content:
                        conversation_preview = last_msg.content[:500]

            # Calculate wait time
            wait_time_seconds = 0
            if conv.handoff_triggered_at:
                from datetime import datetime

                elapsed = datetime.utcnow() - conv.handoff_triggered_at
                wait_time_seconds = int(elapsed.total_seconds())

            # Create alert
            alert = HandoffAlert(
                conversation_id=conv.id,
                merchant_id=conv.merchant_id,
                urgency_level=urgency_level,
                customer_name=None,
                customer_id=customer_id,
                conversation_preview=conversation_preview,
                wait_time_seconds=wait_time_seconds,
                is_read=False,
                is_offline=False,  # Can't determine retroactively
            )
            db.add(alert)
            created_count += 1
            print(f"  [CREATE] Alert for conversation {conv.id} (urgency={urgency_level})")

        if created_count > 0:
            await db.commit()
            print(f"\n✓ Created {created_count} handoff alerts")
        else:
            print("\n✓ No missing alerts found")

        print(f"  Skipped: {skipped_count}")


if __name__ == "__main__":
    print("Creating missing HandoffAlert records...\n")
    asyncio.run(create_missing_alerts())
