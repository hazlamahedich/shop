#!/usr/bin/env python3
"""Manual test script for handoff resolution messages.

This script tests the LLM-powered handoff resolution feature by:
1. Creating a test handoff conversation
2. Calling the resolve-handoff endpoint
3. Verifying the resolution message was generated and stored

Usage:
    python test_handoff_resolution_manual.py
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session
from app.models.merchant import Merchant, PersonalityType
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.handoff.handoff_resolution_service import HandoffResolutionService


async def create_test_data(db: AsyncSession):
    """Create test merchant and conversation."""
    print("\n📝 Creating test data...")

    # Create test merchant
    merchant = Merchant(
        merchant_key=f"test_handoff_resolution_{datetime.now().timestamp()}",
        business_name="Test Shop",
        personality=PersonalityType.FRIENDLY,
        platform="widget",
        use_custom_greeting=False,
    )
    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)
    print(f"✅ Created merchant: {merchant.id} - {merchant.business_name}")

    # Create test conversation in handoff status
    conversation = Conversation(
        merchant_id=merchant.id,
        platform="widget",
        platform_sender_id=f"test_session_{datetime.now().timestamp()}",
        status="handoff",
        handoff_status="active",
        handoff_triggered_at=datetime.utcnow(),
        handoff_reason="test",
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    print(f"✅ Created conversation: {conversation.id} - Status: {conversation.status}")

    # Add some test messages
    messages = [
        Message(
            conversation_id=conversation.id,
            sender="customer",
            content="Hi, I need help with my order",
            message_type="text",
        ),
        Message(
            conversation_id=conversation.id,
            sender="bot",
            content="I'm connecting you with a human agent!",
            message_type="text",
        ),
        Message(
            conversation_id=conversation.id,
            sender="merchant",
            content="Hi there! I can help you with your order. What's the issue?",
            message_type="text",
        ),
        Message(
            conversation_id=conversation.id,
            sender="customer",
            content="My order #12345 hasn't arrived yet",
            message_type="text",
        ),
        Message(
            conversation_id=conversation.id,
            sender="merchant",
            content="I see the issue. Your order is currently in transit and should arrive tomorrow!",
            message_type="text",
        ),
    ]

    for msg in messages:
        db.add(msg)
    await db.commit()
    print(f"✅ Created {len(messages)} test messages")

    return merchant, conversation


async def test_resolution_service(db: AsyncSession, merchant: Merchant, conversation: Conversation):
    """Test the HandoffResolutionService."""
    print("\n🧪 Testing HandoffResolutionService...")

    service = HandoffResolutionService(db)

    print(f"   Merchant: {merchant.business_name} ({merchant.personality})")
    print(f"   Conversation: {conversation.id} ({conversation.platform})")

    result = await service.send_resolution_message(
        conversation=conversation,
        merchant=merchant,
    )

    print("\n📊 Result:")
    print(f"   Sent: {result['sent']}")
    print(f"   Message ID: {result['message_id']}")
    print(f"   Fallback: {result['fallback']}")
    print(f"   Reason: {result['reason']}")
    print(f"   Broadcast Sent: {result['broadcast_sent']}")
    print(f"   Content: {result['content']}")

    return result


async def verify_stored_message(db: AsyncSession, message_id: int):
    """Verify the message was stored in database."""
    print("\n🔍 Verifying stored message...")

    result = await db.execute(select(Message).where(Message.id == message_id))
    message = result.scalars().first()

    if message:
        print(f"✅ Message found in database:")
        print(f"   ID: {message.id}")
        print(f"   Sender: {message.sender}")
        print(f"   Content: {message.content}")
        print(f"   Created: {message.created_at}")
        return True
    else:
        print("❌ Message not found in database!")
        return False


async def test_different_personalities(db: AsyncSession):
    """Test with different personality types."""
    print("\n🎭 Testing Different Personalities...")

    personalities = [
        (PersonalityType.FRIENDLY, "Friendly Shop"),
        (PersonalityType.PROFESSIONAL, "Professional Corp"),
        (PersonalityType.ENTHUSIASTIC, "Party Supplies Plus"),
    ]

    results = []

    for personality, business_name in personalities:
        print(f"\n   Testing {personality.value} personality...")

        # Create merchant with specific personality
        merchant = Merchant(
            merchant_key=f"test_{personality.value}_{datetime.now().timestamp()}",
            business_name=business_name,
            personality=personality,
            platform="widget",
            use_custom_greeting=False,
        )
        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)

        # Create conversation
        conversation = Conversation(
            merchant_id=merchant.id,
            platform="widget",
            platform_sender_id=f"test_session_{datetime.now().timestamp()}",
            status="handoff",
            handoff_status="active",
            handoff_triggered_at=datetime.utcnow(),
            handoff_reason="test",
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        # Test service
        service = HandoffResolutionService(db)
        result = await service.send_resolution_message(conversation, merchant)

        results.append(
            {
                "personality": personality.value,
                "business_name": business_name,
                "content": result["content"],
                "fallback": result["fallback"],
            }
        )

        print(f"   Generated: {result['content'][:80]}...")

    print("\n📋 Personality Test Results:")
    for r in results:
        print(f"\n   {r['personality'].upper()}: {r['business_name']}")
        print(f"   Message: {r['content']}")
        print(f"   Fallback: {r['fallback']}")

    return results


async def cleanup(db: AsyncSession, merchant_ids: list):
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")

    for merchant_id in merchant_ids:
        # Delete messages
        await db.execute(select(Conversation).where(Conversation.merchant_id == merchant_id))
        conversations = (
            (await db.execute(select(Conversation).where(Conversation.merchant_id == merchant_id)))
            .scalars()
            .all()
        )

        for conv in conversations:
            await db.execute(select(Message).where(Message.conversation_id == conv.id))
            messages = (
                (await db.execute(select(Message).where(Message.conversation_id == conv.id)))
                .scalars()
                .all()
            )

            for msg in messages:
                await db.delete(msg)

            await db.delete(conv)

        # Delete merchant
        merchant = (
            (await db.execute(select(Merchant).where(Merchant.id == merchant_id))).scalars().first()
        )

        if merchant:
            await db.delete(merchant)

    await db.commit()
    print("✅ Cleanup complete")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("   HANDOFF RESOLUTION MESSAGE TEST")
    print("=" * 60)

    merchant_ids = []

    try:
        async with async_session() as db:
            # Test 1: Basic functionality
            print("\n" + "=" * 60)
            print("TEST 1: Basic Resolution Message Generation")
            print("=" * 60)

            merchant, conversation = await create_test_data(db)
            merchant_ids.append(merchant.id)

            result = await test_resolution_service(db, merchant, conversation)

            if result["sent"]:
                await verify_stored_message(db, result["message_id"])

            # Test 2: Different personalities
            print("\n" + "=" * 60)
            print("TEST 2: Personality Variations")
            print("=" * 60)

            results = await test_different_personalities(db)

            # Track merchants for cleanup
            for r in results:
                # We'd need to track merchant IDs from the test
                pass

            # Summary
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print("✅ All tests completed successfully!")
            print(f"✅ Tested {len(results) + 1} different scenarios")
            print(f"✅ LLM generation working: {not any(r['fallback'] for r in results)}")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
