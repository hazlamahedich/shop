#!/usr/bin/env python3
"""Check knowledge base status for merchant 1."""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select
from app.core.database import get_db
from app.db.models import KnowledgeBase

async def check_kb():
    async for db in get_db():
        result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.merchant_id == 1))
        docs = result.scalars().all()
        print(f'Found {len(docs)} knowledge base documents for merchant 1:')
        for doc in docs:
            print(f'  - {doc.filename} (ID: {doc.id}, Status: {doc.indexing_status})')

        resume_docs = [d for d in docs if 'resume' in d.filename.lower()]
        print(f'\nResume documents: {len(resume_docs)}')
        for doc in resume_docs:
            print(f'  - {doc.filename} (Indexed: {doc.indexing_status})')

if __name__ == '__main__':
    asyncio.run(check_kb())
