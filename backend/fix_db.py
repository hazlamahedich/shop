
import asyncio
import sys
from pathlib import Path
from sqlalchemy import select, update

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import async_session
from app.models.merchant import Merchant

async def fix_merchants():
    async with async_session() as db:
        result = await db.execute(select(Merchant))
        merchants = result.scalars().all()
        
        print(f"Checking {len(merchants)} merchants...")
        updated_count = 0
        for m in merchants:
            needs_update = False
            
            # Check main bot_name column
            if m.bot_name == "Shopping Assistant":
                m.bot_name = "Mantisbot"
                needs_update = True
                print(f"  ID {m.id}: Updating bot_name column to Mantisbot")
            
            # Check widget_config JSONB column
            if m.widget_config and m.widget_config.get("bot_name") == "Shopping Assistant":
                new_config = dict(m.widget_config)
                new_config["bot_name"] = "Mantisbot"
                m.widget_config = new_config
                needs_update = True
                print(f"  ID {m.id}: Updating widget_config.bot_name to Mantisbot")
            
            if needs_update:
                db.add(m)
                updated_count += 1
        
        if updated_count > 0:
            await db.commit()
            print(f"✓ Successfully updated {updated_count} merchants.")
        else:
            print("No merchants needed updates.")

if __name__ == "__main__":
    asyncio.run(fix_merchants())
