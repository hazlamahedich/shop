import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.core.database import async_session
from app.services.handoff.detector import HandoffDetector
from app.services.handoff.handoff_flow_service import HandoffFlowService
from app.models.conversation import Conversation
from app.models.merchant import Merchant
from app.models.message import Message
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def main():
    print("Starting Handoff Verification Script...")

    async with async_session() as session:
        # 1. Get the demo merchant
        result = await session.execute(select(Merchant).where(Merchant.email == "demo@shopbot.ai"))
        merchant = result.scalars().first()

        if not merchant:
            print("❌ Demo merchant not found!")
            return

        print(f"✅ Found merchant: {merchant.email} (ID: {merchant.id})")

        # 2. Create a test conversation
        conversation = Conversation(
            merchant_id=merchant.id,
            platform="web",
            platform_sender_id="test_customer_e2e",
            customer_name="Test Customer E2E",
            status="active",
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        print(f"✅ Created conversation: {conversation.id}")

        # 3. Create a message
        msg_content = "I need to speak to a human"
        message = Message(
            conversation_id=conversation.id,
            content=msg_content,
            sender_type="customer",
            platform_message_id="msg_123",
        )
        session.add(message)
        await session.commit()

        # Reload conversation with messages
        result = await session.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation.id)
        )
        conversation = result.scalars().first()

        # 4. Process Handoff
        print(f"🔄 Processing handoff for message: '{msg_content}'")
        flow_service = HandoffFlowService(db=session)
        result = await flow_service.process_handoff(
            conversation=conversation, message=msg_content, confidence_score=0.99
        )

        print(f"ℹ️ Handoff Result: Should Handoff? {result.should_handoff}, Reason: {result.reason}")

        if result.should_handoff:
            print("✅ Handoff triggered successfully!")
        else:
            print("❌ Handoff NOT triggered.")


if __name__ == "__main__":
    asyncio.run(main())
