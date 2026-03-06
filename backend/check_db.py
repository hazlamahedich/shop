import asyncio
from sqlalchemy import select
from app.core.database import TestingSessionLocal
from app.models.deletion_audit_log import DeletionAuditLog

async def check():
    async with TestingSessionLocal() as db:
        result = await db.execute(select(DeletionAuditLog))
        records = result.scalars().all()
        print(f'Total DeletionAuditLog records: {len(records)}')
        for r in records:
            print(f'  ID: {r.id}, Customer: {r.customer_id}, Merchant: {r.merchant_id}, Type: {r.request_type}')

asyncio.run(check())
