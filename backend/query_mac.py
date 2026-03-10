import asyncio
from sqlalchemy import select
from app.core.database import async_session
from app.models.order import Order
import json

async def main():
    async with async_session() as db:
        result = await db.execute(select(Order.items))
        items_lists = result.scalars().all()
        for items_str in items_lists:
            if isinstance(items_str, str):
                items = json.loads(items_str)
            else:
                items = items_str
            for item in items:
                title = item.get('title', '')
                if title and 'mac' in title.lower():
                    print("Found mac product:", item)

if __name__ == "__main__":
    asyncio.run(main())
