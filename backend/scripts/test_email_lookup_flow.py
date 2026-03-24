#!/usr/bin/env python
"""Test email-based order lookup flow end-to-end.

Simulates the exact user flow:
1. Ask for order status
2. Get prompted for email
3. Provide email
4. Check if detailed response is returned
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import async_session
from app.services.conversation.schemas import Channel, ConversationContext
from app.services.conversation.unified_conversation_service import UnifiedConversationService


async def test_email_lookup_flow():
    """Test the complete email lookup flow."""
    async with async_session() as db:
        service = UnifiedConversationService()

        # Step 1: Ask for order status
        print("=" * 60)
        print("Step 1: User asks 'What's the status of my order?'")
        print("=" * 60)

        context1 = ConversationContext(
            session_id="test-session-email-lookup",
            merchant_id=6,
            channel=Channel.WIDGET,
        )

        response1 = await service.process_message(
            db=db,
            context=context1,
            message="What's the status of my order?",
        )

        print(f"\nBot Response:\n{response1.message}\n")
        print(f"Intent: {response1.intent}")
        print(f"Metadata: {response1.metadata}")

        # Check if pending flag is set
        if response1.metadata and response1.metadata.get("pending_cross_device_lookup"):
            print("✅ Pending cross-device lookup flag is set")
        else:
            print("❌ Pending cross-device lookup flag NOT set")

        # Step 2: Provide email
        print("\n" + "=" * 60)
        print("Step 2: User provides email 'hazlamahedich@gmail.com'")
        print("=" * 60)

        # Update context with metadata from previous response
        context2 = ConversationContext(
            session_id="test-session-email-lookup",
            merchant_id=6,
            channel=Channel.WIDGET,
            metadata=response1.metadata or {},
        )

        response2 = await service.process_message(
            db=db,
            context=context2,
            message="hazlamahedich@gmail.com",
        )

        print(f"\nBot Response:\n{response2.message[:500]}...\n")
        print(f"Intent: {response2.intent}")
        print(f"Order data: {response2.order}")

        # Check if response contains detailed order info
        if "📦 Order #" in response2.message:
            print("✅ Response contains detailed order status")
        else:
            print("❌ Response is a summary, not detailed status")

        if "📷 Image:" in response2.message:
            print("✅ Response contains product images")
        else:
            print("⚠️  Response does not contain product images")

        if "Estimated Delivery:" in response2.message:
            print("✅ Response contains estimated delivery")
        else:
            print("⚠️  Response does not contain estimated delivery")


if __name__ == "__main__":
    asyncio.run(test_email_lookup_flow())
