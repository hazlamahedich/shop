#!/usr/bin/env python
"""
WebSocket Connection Diagnostic Tool

This script checks the health of WebSocket connections and provides
detailed information about active connections and potential issues.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/diagnose_websocket.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog

from app.services.widget.connection_manager import get_connection_manager

logger = structlog.get_logger(__name__)


async def diagnose_websocket_connections():
    """Diagnose WebSocket connection issues."""

    print("=" * 80)
    print("🔍 WEBSOCKET CONNECTION DIAGNOSTIC")
    print("=" * 80)
    print()

    # Get connection manager
    manager = get_connection_manager()

    # Check active sessions
    print("📋 Active Sessions:")
    active_sessions = manager.get_all_active_sessions()

    if not active_sessions:
        print("   ❌ No active WebSocket connections")
        print()
        print("   Possible reasons:")
        print("   1. Widget is not open in browser")
        print("   2. WebSocket connection failed")
        print("   3. Widget session expired")
        print()
    else:
        total_connections = sum(active_sessions.values())
        print(
            f"   ✅ Found {len(active_sessions)} session(s) with {total_connections} total connection(s)"
        )
        print()

        for session_id, conn_count in active_sessions.items():
            print(f"   Session: {session_id[:40]}...")
            print(f"      Connections: {conn_count}")

            # Check if conversation exists for this session
            from sqlalchemy import select
            from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

            from app.models.conversation import Conversation

            engine = create_async_engine(
                "postgresql+asyncpg://developer:developer@localhost:5432/shop_dev"
            )
            async_session = async_sessionmaker(engine, expire_on_commit=False)

            async with async_session()() as db:
                result = await db.execute(
                    select(Conversation).where(Conversation.platform_sender_id == session_id)
                )
                conversation = result.scalars().first()

                if conversation:
                    print(f"      Conversation ID: {conversation.id}")
                    print(f"      Status: {conversation.status}")
                    print(f"      Handoff: {conversation.handoff_status}")
                    print(f"      Merchant ID: {conversation.merchant_id}")
                else:
                    print("      ⚠️  No conversation found in database")

            await engine.dispose()
            print()

    # Test specific session
    print("📋 Testing Your Shopify Widget Session:")
    your_session_id = "8865fc64-9a1d-413d-a91b-47fcc8d12da4"

    conn_count = manager.get_connection_count(your_session_id)
    print(f"   Session ID: {your_session_id}")
    print(f"   Active connections: {conn_count}")

    if conn_count == 0:
        print()
        print("   ❌ No active WebSocket connection for your session")
        print()
        print("   To fix this:")
        print("   1. Open your Shopify store in a browser")
        print("   2. Open the widget (click the chat bubble)")
        print("   3. Check browser console for WebSocket errors")
        print("   4. Look for: '[WS] Connecting to: wss://...'")
        print()
        print("   Common issues:")
        print("   - Widget not open (must be open to connect)")
        print("   - Cloudflare tunnel not working")
        print("   - CORS/CSRF blocking WebSocket upgrade")
        print("   - Browser blocking WebSocket connections")
    else:
        print()
        print("   ✅ WebSocket is connected!")
        print()
        print("   To test message delivery:")
        print("   1. Trigger handoff in your widget")
        print("   2. Resolve handoff in dashboard")
        print("   3. Message should appear in widget")

    print()
    print("=" * 80)
    print("📊 DIAGNOSTIC COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. If no connections: Open widget in browser and check console")
    print("2. If connections exist but no messages: Check backend logs for broadcast attempts")
    print("3. Run this script again after opening widget to see connection status")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(diagnose_websocket_connections())
