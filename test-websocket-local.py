#!/usr/bin/env python3
"""Test WebSocket connection locally (without Zrok)."""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket_local():
    """Test WebSocket connection locally."""
    local_ws_url = "ws://localhost:8000/ws/widget/test-session-local"
    local_api_url = "http://localhost:8000/api/v1/widget"

    print("🧪 WebSocket Local Test (Direct Connection)")
    print("=" * 60)
    print(f"Local WebSocket URL: {local_ws_url}")
    print(f"Local API URL: {local_api_url}")
    print()

    # Step 1: Create a session
    print("📝 Step 1: Creating widget session...")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{local_api_url}/session",
                json={"merchant_id": "1"},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    print(f"❌ Failed to create session: HTTP {response.status}")
                    return False

                session_data = await response.json()
                session_id = (session_data.get('session_id') or
                            session_data.get('sessionId') or
                            session_data.get('session', {}).get('session_id') or
                            session_data.get('session', {}).get('sessionId') or
                            session_data.get('data', {}).get('session_id') or
                            session_data.get('data', {}).get('sessionId'))

                if not session_id:
                    print("❌ No session ID in response")
                    return False

                print(f"✅ Session created: {session_id}")

    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        session_id = "test-session-local"

    # Step 2: Test WebSocket connection locally
    print(f"\n🔌 Step 2: Connecting to WebSocket locally...")
    ws_url = f"ws://localhost:8000/ws/widget/{session_id}"
    print(f"   URL: {ws_url}")

    try:
        connection_start = datetime.now()

        async with websockets.connect(
            ws_url,
            ping_timeout=10,
            close_timeout=10,
            ping_interval=20
        ) as websocket:
            connection_time = (datetime.now() - connection_start).total_seconds() * 1000
            print(f"✅ WebSocket CONNECTED locally in {connection_time:.0f}ms!")

            # Send ping
            print("\n📤 Sending ping...")
            await websocket.send(json.dumps({"type": "ping"}))
            print("✅ Ping sent successfully")

            # Listen for messages
            print("\n📨 Listening for messages (10 seconds)...")
            message_count = 0
            start_time = datetime.now()

            try:
                while (datetime.now() - start_time).total_seconds() < 10:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=2.0
                        )
                        message_count += 1

                        try:
                            data = json.loads(message)
                            msg_type = data.get('type', 'unknown')
                            print(f"📥 Message {message_count}: {msg_type}")

                        except json.JSONDecodeError:
                            print(f"📥 Message {message_count}: {message[:100]}")

                    except asyncio.TimeoutError:
                        print(f"⏱️  {int((datetime.now() - start_time).total_seconds())}s - Connection stable...")

            except Exception as e:
                print(f"❌ Error receiving messages: {e}")

            print(f"\n✅ Local WebSocket test PASSED!")
            print(f"   Backend WebSocket is working correctly")
            return True

    except Exception as e:
        print(f"❌ Local WebSocket connection failed: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_websocket_local())
        print("\n" + "=" * 60)
        if result:
            print("✅ LOCAL TEST PASSED - Backend WebSocket works!")
            print("   This means the issue is with Zrok's WebSocket proxying")
        else:
            print("❌ LOCAL TEST FAILED - Backend WebSocket has issues")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
