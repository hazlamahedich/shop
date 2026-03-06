import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add the backend directory to sys.path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.core.config import settings
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.deletion_audit_log import DeletionAuditLog, DeletionTrigger
from app.services.privacy.data_tier_service import DataTier
from app.services.privacy.retention_service import RetentionPolicy

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://developer:@localhost:5432/shop")


async def verify_retention():
    print(f"Connecting to {DATABASE_URL}...")
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Setup Test Data
        merchant_id = 1
        now = datetime.now(timezone.utc)
        expired_date = datetime.utcnow() - timedelta(days=35)
        recent_date = datetime.utcnow() - timedelta(days=10)

        print("\n--- Setting up test data ---")

        # Create an expired voluntary conversation
        expired_conv = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="exp-vol-1",
            data_tier=DataTier.VOLUNTARY,
            created_at=expired_date,
            updated_at=expired_date,
        )
        session.add(expired_conv)

        # Create a recent voluntary conversation (should NOT be deleted)
        recent_conv = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="rec-vol-1",
            data_tier=DataTier.VOLUNTARY,
            created_at=recent_date,
            updated_at=recent_date,
        )
        session.add(recent_conv)

        # Create an expired operational conversation (should NOT be deleted)
        op_conv = Conversation(
            merchant_id=merchant_id,
            platform="facebook",
            platform_sender_id="exp-op-1",
            data_tier=DataTier.OPERATIONAL,
            created_at=expired_date,
            updated_at=expired_date,
        )
        session.add(op_conv)

        await session.commit()
        await session.refresh(expired_conv)
        await session.refresh(recent_conv)
        await session.refresh(op_conv)

        print(f"Created expired voluntary conv: {expired_conv.id}")
        print(f"Created recent voluntary conv: {recent_conv.id}")
        print(f"Created expired operational conv: {op_conv.id}")

        # Add messages to the expired conversation
        msg1 = Message(
            conversation_id=expired_conv.id,
            sender="customer",
            content="Expired msg",
            data_tier=DataTier.VOLUNTARY,
            created_at=expired_date,
        )
        session.add(msg1)
        await session.commit()

        # 2. Run Retention Policy
        print("\n--- Running retention policy ---")
        deleted_count = await RetentionPolicy.delete_expired_voluntary_data(session, days=30)

        print(f"Retention result: {deleted_count}")

        # 3. Verify Deletions
        print("\n--- Verifying deletions ---")

        # Check expired conv (should be gone)
        res = await session.execute(select(Conversation).where(Conversation.id == expired_conv.id))
        if res.scalar_one_or_none() is None:
            print(f"SUCCESS: Expired voluntary conversation {expired_conv.id} deleted.")
        else:
            print(f"FAILURE: Expired voluntary conversation {expired_conv.id} still exists.")

        # Check recent conv (should remain)
        res = await session.execute(select(Conversation).where(Conversation.id == recent_conv.id))
        if res.scalar_one_or_none() is not None:
            print(f"SUCCESS: Recent voluntary conversation {recent_conv.id} preserved.")
        else:
            print(f"FAILURE: Recent voluntary conversation {recent_conv.id} was deleted.")

        # Check operational conv (should remain)
        res = await session.execute(select(Conversation).where(Conversation.id == op_conv.id))
        if res.scalar_one_or_none() is not None:
            print(f"SUCCESS: Expired operational conversation {op_conv.id} preserved.")
        else:
            print(f"FAILURE: Expired operational conversation {op_conv.id} was deleted.")

        # 4. Verify Audit Log
        print("\n--- Verifying audit log ---")
        res = await session.execute(
            select(DeletionAuditLog)
            .where(DeletionAuditLog.deletion_trigger == "auto")
            .order_by(DeletionAuditLog.requested_at.desc())
            .limit(1)
        )
        audit_log = res.scalar_one_or_none()
        if audit_log:
            print(f"SUCCESS: Audit log found (ID: {audit_log.id})")
            print(f"  Trigger: {audit_log.deletion_trigger}")
            print(f"  Conversations deleted: {audit_log.conversations_deleted}")
            print(f"  Retention period: {audit_log.retention_period_days} days")
        else:
            print("FAILURE: No automated deletion audit log found.")

        # Cleanup (optional, but good for repeatability)
        await session.execute(delete(Conversation).where(Conversation.id == recent_conv.id))
        await session.execute(delete(Conversation).where(Conversation.id == op_conv.id))
        await session.commit()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(verify_retention())
