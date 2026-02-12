import asyncio
from app.core.database import engine
from sqlalchemy import text


async def check():
    async with engine.connect() as conn:
        try:
            res = await conn.execute(text("SELECT id, config FROM merchants"))
            rows = res.all()
            print(f"Merchants found: {len(rows)}")
            for row in rows:
                print(f" - ID: {row[0]}, Config: {row[1]}")
        except Exception as e:
            print(f"Error reading merchants: {e}")


if __name__ == "__main__":
    asyncio.run(check())
