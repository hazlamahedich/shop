import asyncio
import os
import sys
from datetime import datetime, timedelta
import httpx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add backend to path to import models
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.models.merchant import Merchant
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.database import Base

DATABASE_URL = "postgresql+asyncpg://developer:developer@localhost:5432/shop_dev"
API_URL = "http://localhost:8000/api/conversations/export"


async def setup_test_data():
    engine = create_async_engine(DATABASE_URL)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        # 1. Ensure test merchant exists
        result = await session.execute(select(Merchant).where(Merchant.id == 1))
        merchant = result.scalar_one_or_none()
        if not merchant:
            print("Creating test merchant...")
            merchant = Merchant(
                id=1, merchant_key="test-merchant-3-3", platform="facebook", status="active"
            )
            session.add(merchant)
            await session.commit()
            await session.refresh(merchant)

        # 2. Clear existing conversations for this merchant to have a clean slate
        print("Clearing existing conversations for merchant 1...")
        await session.execute(delete(Conversation).where(Conversation.merchant_id == 1))
        await session.commit()

        # 3. Create test conversations
        print("Creating test conversations...")

        # Conversation 1: Active, OpenAI, recent
        conv1 = Conversation(
            merchant_id=1,
            platform="facebook",
            platform_sender_id="cust_1234567890",
            status="active",
            created_at=datetime.utcnow() - timedelta(days=1),
        )
        session.add(conv1)
        await session.flush()

        msg1_1 = Message(
            conversation_id=conv1.id,
            sender="bot",
            content='Hello! How can I help you today with your "shoes"?',
            message_metadata={
                "llm_provider": "openai",
                "prompt_tokens": 500,
                "completion_tokens": 200,
            },
        )
        session.add(msg1_1)

        # Conversation 2: Handoff, Ollama, last week
        conv2 = Conversation(
            merchant_id=1,
            platform="facebook",
            platform_sender_id="cust_9876543210",
            status="handoff",
            created_at=datetime.utcnow() - timedelta(days=5),
        )
        session.add(conv2)
        await session.flush()

        msg2_1 = Message(
            conversation_id=conv2.id,
            sender="bot",
            content='I am passing you to a human agent because I cannot help with "refunds".',
            message_metadata={
                "llm_provider": "ollama",
                "prompt_tokens": 1000,
                "completion_tokens": 500,
            },
        )
        session.add(msg2_1)

        # Conversation 3: Closed, Anthropic, special characters
        conv3 = Conversation(
            merchant_id=1,
            platform="facebook",
            platform_sender_id="cust_abc123",
            status="closed",
            created_at=datetime.utcnow() - timedelta(days=10),
        )
        session.add(conv3)
        await session.flush()

        msg3_1 = Message(
            conversation_id=conv3.id,
            sender="bot",
            content="Your order #12345 has been confirmed. Thank you!",
            message_metadata={
                "llm_provider": "anthropic",
                "prompt_tokens": 800,
                "completion_tokens": 100,
                "order_reference": "ORDER-12345",
            },
        )
        session.add(msg3_1)

        await session.commit()
        print("Test data created successfully.")


async def verify_export():
    print("\n--- Verifying Export API ---")
    async with httpx.AsyncClient() as client:
        # Test 1: Export all
        print("Test 1: Export All")
        response = await client.post(API_URL, headers={"X-Merchant-ID": "1"}, json={})
        print(f"Status: {response.status_code}")
        print(f"X-Export-Count: {response.headers.get('X-Export-Count')}")
        print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")

        if response.status_code == 200:
            content = response.text
            print("CSV Header Preview (first 100 chars):")
            print(content[:100])

            # Verify BOM
            if content.startswith("\ufeff"):
                print("✓ UTF-8 BOM present")
            else:
                print("✗ UTF-8 BOM missing")

            # Verify CRLF
            if "\r\n" in content:
                print("✓ CRLF line endings present")
            else:
                print("✗ CRLF line endings missing")

            # Verify masked ID
            if "****7890" in content or "****3210" in content:
                print("✓ Masked Customer ID found")
            else:
                print("✗ Masked Customer ID NOT found")

            # Verify cost for OpenAI (700 tokens * 0.0015 / 1M = 0.00105 -> 0.0011?)
            # 700 / 1,000,000 * 0.0015 = 0.00000105
            # Wait, the cost calculator rounds to 4 decimal places.
            # 0.0000.
            if "0.0000" in content:
                print("✓ Cost column formatted correctly")
        else:
            print(f"Error: {response.text}")

        # Test 2: Filter by date (Last 3 days)
        print("\nTest 2: Filter by Date (Last 3 days)")
        date_from = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")
        response = await client.post(
            API_URL, headers={"X-Merchant-ID": "1"}, json={"dateFrom": date_from}
        )
        print(f"Status: {response.status_code}")
        print(f"X-Export-Count: {response.headers.get('X-Export-Count')} (Expected: 1)")

        # Test 3: Search
        print("\nTest 3: Search for 'refunds'")
        response = await client.post(
            API_URL, headers={"X-Merchant-ID": "1"}, json={"search": "refunds"}
        )
        print(f"Status: {response.status_code}")
        print(f"X-Export-Count: {response.headers.get('X-Export-Count')} (Expected: 1)")


async def main():
    await setup_test_data()
    await verify_export()


if __name__ == "__main__":
    asyncio.run(main())
