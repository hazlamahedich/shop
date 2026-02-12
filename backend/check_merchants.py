import asyncio
from app.core.database import engine
from sqlalchemy import text


async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, email FROM merchants"))
        merchants = result.all()
        print(f"Merchants in DB: {merchants}")


if __name__ == "__main__":
    asyncio.run(check())
