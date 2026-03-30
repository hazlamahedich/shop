#!/usr/bin/env python3
"""Test WebSocket connection for dashboard analytics."""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/ws/dashboard/analytics?merchant_id=1"

    print(f"🔌 Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")

            # Listen for messages for 5 seconds
            print("📨 Listening for messages (5 seconds)...")

            try:
                for i in range(5):
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    print(f"\n📩 Message {i+1}:")
                    print(f"   Type: {data.get('type')}")
                    print(f"   Data: {json.dumps(data.get('data'), indent=6)[:200]}...")

            except asyncio.TimeoutError:
                print("\n⏱️  No more messages (timeout)")

            print("\n✅ WebSocket connection test successful!")
            return True

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        print("\n💡 Tip: Install websockets with:")
        print("   pip install websockets")
        return False

if __name__ == "__main__":
    print("🧪 WebSocket Connection Test")
    print("=" * 50)
    asyncio.run(test_websocket())
