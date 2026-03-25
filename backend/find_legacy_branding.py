
import asyncio
import sys
from pathlib import Path
from sqlalchemy import select

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import async_session
from app.models.merchant import Merchant

async def find_branding():
    async with async_session() as db:
        result = await db.execute(select(Merchant))
        merchants = result.scalars().all()
        
        print(f"Scanning {len(merchants)} merchants...")
        found = False
        for m in merchants:
            fields_to_check = {
                "bot_name": m.bot_name,
                "business_name": m.business_name,
                "business_description": m.business_description,
                "custom_greeting": m.custom_greeting,
            }
            
            for name, val in fields_to_check.items():
                if val and "Shopping Assistant" in val:
                    print(f"  [Found] ID {m.id}: {name} = \"{val}\"")
                    found = True
            
            if m.widget_config:
                for key, val in m.widget_config.items():
                    if isinstance(val, str) and "Shopping Assistant" in val:
                        print(f"  [Found] ID {m.id}: widget_config['{key}'] = \"{val}\"")
                        found = True
        
        if not found:
            print("No legacy branding found in merchant records.")

if __name__ == "__main__":
    asyncio.run(find_branding())
