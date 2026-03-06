import asyncio
from app.core.database import async_session
from sqlalchemy import text


async def check_cols():
    async with async_session() as session:
        res = await session.execute(
            text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='deletion_audit_log'"
            )
        )
        cols = [r[0] for r in res.fetchall()]
        print(f"Columns in deletion_audit_log: {cols}")


if __name__ == "__main__":
    asyncio.run(check_cols())
