import asyncio
import sys
from pathlib import Path
from sqlalchemy import select

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import async_session
from app.models.merchant import Merchant


async def check_merchants():
    async with async_session() as db:
        result = await db.execute(select(Merchant))
        merchants = result.scalars().all()

        print(f"Found {len(merchants)} merchants:")
        for m in merchants:
            print(f"ID: {m.id}")
            print(f"  Business Name: {m.business_name}")
            print(f"  Bot Name: {m.bot_name}")
            print(f"  Widget Config: {m.widget_config}")
            print(f"  Config: {m.config}")
            print("-" * 20)


if __name__ == "__main__":
    asyncio.run(check_merchants())
