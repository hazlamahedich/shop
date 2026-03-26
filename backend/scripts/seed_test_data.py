#!/usr/bin/env python3
"""Seed test data for development.

This script populates the database with sample data for manual testing
and development. It uses the TEST_DATABASE_URL environment variable or defaults
to shop_test database.

Usage:
    # Seed all test data
    python scripts/seed_test_data.py

    # Seed only merchants
    python scripts/seed_test_data.py --merchants

    # Seed only conversations for merchant ID 1
    python scripts/seed_test_data.py --conversations --merchant-id 1

Environment Variables:
    TEST_DATABASE_URL: Database URL (default: shop_test)
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text

from app.core.database import async_session
from app.models.conversation import Conversation
from app.models.merchant import Merchant, PersonalityType
from app.models.message import Message


async def seed_merchant(
    merchant_id: int | None = None,
    business_name: str = "Test Shop",
    personality: PersonalityType = PersonalityType.FRIENDLY,
    platform: str = "widget",
):
    """Seed a test merchant with configuration.

    Args:
        merchant_id: Specific ID to use (optional, auto-generated if None)
        business_name: Shop name
        personality: Bot personality type
        platform: Platform type (widget/messenger)
    """
    async with async_session() as db:
        # Check if merchant exists
        if merchant_id:
            result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
            existing = result.scalars().first()
            if existing:
                print(f"✓ Merchant ID {merchant_id} already exists: {existing.business_name}")
                return existing

        merchant = Merchant(
            merchant_key=f"test_{datetime.now().timestamp()}",
            business_name=business_name,
            personality=personality,
            status="active",
            widget_config={
                "enabled": True,
                "theme_color": "#007bff",
                "position": "bottom-right",
                "greeting": f"Hello! Welcome to {business_name}. How can I help you today?",
            },
        )

        if merchant_id:
            # Force specific ID (only for new merchants)
            merchant.id = merchant_id

        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)

        print(f"✓ Created merchant ID {merchant.id}: {business_name}")
        return merchant


async def seed_conversations(
    merchant_id: int,
    count: int = 3,
    include_handoff: bool = True,
):
    """Seed test conversations with messages.

    Args:
        merchant_id: Merchant ID to create conversations for
        count: Number of conversations to create
        include_handoff: Include handoff conversations
    """
    async with async_session() as db:
        # Verify merchant exists
        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalars().first()
        if not merchant:
            print(f"✗ Merchant ID {merchant_id} not found")
            return

        print(f"\n→ Seeding {count} conversations for {merchant.business_name}")

        for i in range(count):
            # Create conversation
            status = "active"
            handoff_status = "none"

            if include_handoff and i == count - 1:
                # Last conversation is in handoff
                status = "handoff"
                handoff_status = "active"

            conversation = Conversation(
                merchant_id=merchant_id,
                platform="widget",
                platform_sender_id=f"test_customer_{i}_{datetime.now().timestamp()}",
                status=status,
                handoff_status=handoff_status,
                handoff_triggered_at=datetime.utcnow() if handoff_status == "active" else None,
                handoff_reason="customer_requested" if handoff_status == "active" else None,
            )

            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)

            # Add messages
            messages = [
                {
                    "sender": "customer",
                    "content": f"Hi, I have a question about order #{1000 + i}",
                },
                {
                    "sender": "bot",
                    "content": f"Hello! I'd be happy to help you with order #{1000 + i}. Let me look that up for you.",
                },
            ]

            if handoff_status == "active":
                messages.extend(
                    [
                        {
                            "sender": "customer",
                            "content": "I need to speak with someone about a refund.",
                        },
                        {
                            "sender": "bot",
                            "content": "I'll connect you with our team right away.",
                        },
                        {
                            "sender": "merchant",
                            "content": "Hello! I can help you with the refund. What's the issue?",
                        },
                    ]
                )

            for msg_data in messages:
                message = Message(
                    conversation_id=conversation.id,
                    sender=msg_data["sender"],
                    content=msg_data["content"],
                    message_type="text",
                )
                db.add(message)

            await db.commit()
            print(f"  ✓ Created conversation {conversation.id} ({status}/{handoff_status})")


async def seed_faqs(merchant_id: int):
    """Seed test FAQ pages.

    Args:
        merchant_id: Merchant ID to create FAQs for
    """
    async with async_session() as db:
        # Verify merchant exists
        result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
        merchant = result.scalars().first()
        if not merchant:
            print(f"✗ Merchant ID {merchant_id} not found")
            return

        print(f"\n→ Seeding FAQs for {merchant.business_name}")

        faqs = [
            {
                "question": "What are your business hours?",
                "answer": "We're open Monday-Friday -6pm, and Saturday 10am-4pm.",
            },
            {
                "question": "Do you offer refunds?",
                "answer": "Yes! We offer full refunds within 30 days of purchase.",
            },
            {
                "question": "How long does shipping take?",
                "answer": "Standard shipping takes 3-5 business days. Express shipping is 1-2 days.",
            },
        ]

        # Insert FAQs directly
        for index, faq_data in enumerate(faqs):
            await db.execute(
                text(
                    "INSERT INTO faqs (merchant_id, question, answer, order_index, created_at, updated_at) "
                    "VALUES (:merchant_id, :question, :answer, :order_index, NOW(), NOW())"
                ),
                {
                    "merchant_id": merchant_id,
                    "question": faq_data["question"],
                    "answer": faq_data["answer"],
                    "order_index": index + 1,
                },
            )

        print(f"  ✓ Created {len(faqs)} FAQs")


async def main():
    """Main entry point for seeding test data."""
    parser = argparse.ArgumentParser(description="Seed test data for development")
    parser.add_argument("--merchants", action="store_true", help="Seed only merchants")
    parser.add_argument("--conversations", action="store_true", help="Seed only conversations")
    parser.add_argument("--merchant-id", type=int, help="Specific merchant ID to seed data for")
    parser.add_argument("--count", type=int, default=3, help="Number of conversations to create")
    args = parser.parse_args()

    print("=" * 80)
    print("🌱 SEEDING TEST DATA")
    print("=" * 80)

    try:
        if args.merchants or (not args.merchants and not args.conversations):
            # Seed default test merchant
            merchant = await seed_merchant(
                merchant_id=args.merchant_id,
                business_name="Test Widget Shop",
                personality=PersonalityType.FRIENDLY,
                platform="widget",
            )

            if not args.conversations:
                # Seed all data for this merchant
                await seed_conversations(merchant.id, count=args.count)
                await seed_faqs(merchant.id)

        elif args.conversations and args.merchant_id:
            # Seed only conversations for specific merchant
            await seed_conversations(args.merchant_id, count=args.count)

        print("\n" + "=" * 80)
        print("✅ TEST DATA SEEDING COMPLETE")
        print("=" * 80)
        print("\nYou can now:")
        print("  • Test the widget with the seeded merchant")
        print("  • Test handoff resolution with the active handoff conversation")
        print("  • View FAQs and tutorials in the merchant dashboard")

    except Exception as e:
        print(f"\n✗ Error seeding test data: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
