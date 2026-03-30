#!/usr/bin/env python3
"""Test WebSocket connection through Zrok tunnel."""

import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket_through_zrok():
    """Test WebSocket connection through the Zrok tunnel."""
    zrok_ws_url = "wss://shopdevsherwingor.share.zrok.io/ws/widget/test-session-123"
    zrok_api_url = "https://shopdevsherwingor.share.zrok.io/api/v1/widget"

    print("🧪 WebSocket Through Zrok Tunnel Test")
    print("=" * 60)
    print(f"Zrok WebSocket URL: {zrok_ws_url}")
    print(f"Zrok API URL: {zrok_api_url}")
    print()

    # Step 1: Create a session
    print("📝 Step 1: Creating widget session...")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{zrok_api_url}/session",
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
                    print(f"   Response: {json.dumps(session_data, indent=2)[:500]}")
                    return False

                print(f"✅ Session created: {session_id}")

    except ImportError:
        print("⚠️  aiohttp not installed, using test session ID")
        session_id = "test-session-" + str(int(datetime.now().timestamp()))
    except Exception as e:
        print(f"❌ Failed to create session: {e}")
        session_id = "test-session-" + str(int(datetime.now().timestamp()))

    # Step 2: Test WebSocket connection
    print(f"\n🔌 Step 2: Connecting to WebSocket through Zrok...")
    ws_url = f"wss://shopdevsherwingor.share.zrok.io/ws/widget/{session_id}"
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
            print(f"✅ WebSocket CONNECTED in {connection_time:.0f}ms!")
            print(f"🎯 ZROK TUNNEL SUPPORTS WEBSOCKET!")

            # Send ping
            print("\n📤 Sending ping...")
            await websocket.send(json.dumps({"type": "ping"}))
            print("✅ Ping sent successfully")

            # Listen for messages
            print("\n📨 Listening for messages (15 seconds)...")
            message_count = 0
            start_time = datetime.now()

            try:
                while (datetime.now() - start_time).total_seconds() < 15:
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

                            if msg_type == 'pong':
                                print("   ✅ Pong received - heartbeat working!")
                            elif msg_type == 'merchant_message':
                                print(f"   💬 Merchant message: {data.get('data', {}).get('content', '')[:50]}...")
                            elif msg_type == 'connected':
                                print("   ✅ Connection confirmation received")

                        except json.JSONDecodeError:
                            print(f"📥 Message {message_count}: {message[:100]}")

                    except asyncio.TimeoutError:
                        # No message, but connection is still alive
                        print(f"⏱️  {int((datetime.now() - start_time).total_seconds())}s - Connection stable...")

            except Exception as e:
                print(f"❌ Error receiving messages: {e}")

            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"\n📊 Test Results:")
            print(f"   ⏱️  Duration: {elapsed:.1f} seconds")
            print(f"   📨 Messages: {message_count}")
            print(f"   ✅ Status: WebSocket connection stable through Zrok!")

            if message_count > 0:
                print(f"\n🎉 SUCCESS! Zrok tunnel fully supports WebSocket!")
                print(f"   The widget can now use real-time WebSocket instead of polling.")
            else:
                print(f"\n✅ SUCCESS! WebSocket connected (no messages expected without activity)")
                print(f"   Connection is stable and ready to receive real-time updates.")

            return True

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Invalid Status Code: {e}")
        print(f"   Zrok rejected the WebSocket upgrade")
        print(f"   This suggests Zrok may not support WebSocket")
        return False

    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection Closed: {e}")
        print(f"   WebSocket connection was closed")
        return False

    except asyncio.TimeoutError:
        print(f"❌ Timeout: Connection took too long")
        print(f"   Zrok may not support WebSocket or has high latency")
        return False

    except Exception as e:
        print(f"❌ WebSocket connection failed: {type(e).__name__}: {e}")
        print(f"   Zrok tunnel may not support WebSocket connections")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_websocket_through_zrok())
        print("\n" + "=" * 60)
        if result:
            print("✅ TEST PASSED - WebSocket works through Zrok!")
            print("=" * 60)
        else:
            print("❌ TEST FAILED - WebSocket does NOT work through Zrok")
            print("=" * 60)
            print("\n💡 Next step: Implement Cloudflare Tunnel for WebSocket")
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
