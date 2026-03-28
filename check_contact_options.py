#!/usr/bin/env python3
"""Check if contact options are configured for merchants."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import select
from app.core.database import get_db_context
from app.models.merchant import Merchant


async def check_contact_options():
    """Check merchant contact options configuration."""
    db_gen = get_db_context()
    db = await db_gen.__anext__()

    try:
        # Get all merchants
        result = await db.execute(select(Merchant))
        merchants = result.scalars().all()

        if not merchants:
            print("❌ No merchants found in database")
            return

        print(f"Found {len(merchants)} merchant(s):\n")

        for merchant in merchants:
            print(f"📊 Merchant ID: {merchant.id}")
            print(f"   Business Name: {merchant.business_name}")

            # Check contact_options column
            contact_options = getattr(merchant, "contact_options", [])
            if contact_options:
                print(f"   ✅ contact_options column: {len(contact_options)} options")
                for i, opt in enumerate(contact_options, 1):
                    print(f"      {i}. Type: {opt.get('type')}, Label: {opt.get('label')}, Value: {opt.get('value')}")
            else:
                print(f"   ❌ contact_options column: empty")

            # Check widget_config
            if merchant.widget_config:
                widget_contact_options = merchant.widget_config.get("contactOptions", [])
                if widget_contact_options:
                    print(f"   ✅ widget_config.contactOptions: {len(widget_contact_options)} options")
                    for i, opt in enumerate(widget_contact_options, 1):
                        print(f"      {i}. Type: {opt.get('type')}, Label: {opt.get('label')}, Value: {opt.get('value')}")
                else:
                    print(f"   ❌ widget_config.contactOptions: empty")
            else:
                print(f"   ❌ widget_config: null")

            # Check config (this is where we saved it!)
            if merchant.config:
                config_contact_options = merchant.config.get("contact_options", [])
                if config_contact_options:
                    print(f"   ✅ merchant.config.contact_options: {len(config_contact_options)} options")
                    for i, opt in enumerate(config_contact_options, 1):
                        print(f"      {i}. Type: {opt.get('type')}, Label: {opt.get('label')}, Value: {opt.get('value')}")
                else:
                    print(f"   ❌ merchant.config.contact_options: empty")
            else:
                print(f"   ❌ merchant.config: null")

            print()
    finally:
        try:
            await db_gen.aclose()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(check_contact_options())
