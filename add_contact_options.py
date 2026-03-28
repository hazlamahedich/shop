#!/usr/bin/env python3
"""Add sample contact options to merchant."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy import select, update
from app.core.database import get_db_context
from app.models.merchant import Merchant


async def add_contact_options():
    """Add sample contact options to merchant."""
    db_gen = get_db_context()
    db = await db_gen.__anext__()

    try:
        # Get merchant ID 1
        result = await db.execute(
            select(Merchant).where(Merchant.id == 1)
        )
        merchant = result.scalars().first()

        if not merchant:
            print("❌ Merchant with ID 1 not found")
            return

        print(f"📊 Updating merchant: {merchant.business_name}")

        # Get current config
        config = merchant.config or {}
        widget_config = config.get("widget_config", {})

        # Add sample contact options
        contact_options = [
            {
                "type": "phone",
                "label": "Call Us",
                "value": "+1234567890",
                "icon": "phone"
            },
            {
                "type": "email",
                "label": "Email Support",
                "value": "support@example.com",
                "icon": "mail"
            },
            {
                "type": "custom",
                "label": "WhatsApp",
                "value": "https://wa.me/1234567890",
                "icon": "link"
            }
        ]

        widget_config["contact_options"] = contact_options
        config["widget_config"] = widget_config

        # Update merchant
        await db.execute(
            update(Merchant)
            .where(Merchant.id == 1)
            .values(config=config)
        )
        await db.commit()

        print("✅ Contact options added successfully!")
        print("\n📋 Configured contact options:")
        for i, opt in enumerate(contact_options, 1):
            print(f"   {i}. {opt['label']}: {opt['value']} ({opt['type']})")

        print("\n💡 The Contact Us button will now appear when:")
        print("   - A conversation triggers a handoff (human_handoff intent)")
        print("   - The bot message includes contact_options in the response")

        print("\n🧪 To test:")
        print("   1. Start a conversation in the widget")
        print("   2. Ask for something that requires human assistance")
        print("   3. The Contact Us buttons should appear in the bot's response")

    finally:
        try:
            await db_gen.aclose()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(add_contact_options())
