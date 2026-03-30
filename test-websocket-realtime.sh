#!/bin/bash
# Quick Test: WebSocket Real-Time Updates
#
# This script tests the WebSocket real-time implementation
# for the Knowledge Effectiveness Widget.

set -e

echo "🚀 Testing WebSocket Real-Time Updates"
echo "======================================"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ python3 not found"
    exit 1
fi

if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Backend not running at http://localhost:8000"
    echo ""
    echo "Start the backend first:"
    echo "  cd backend && python -m uvicorn app.main:app --reload"
    exit 1
fi

echo "✅ All prerequisites met"
echo ""

# Test 1: WebSocket endpoint availability
echo "🧪 Test 1: WebSocket Endpoint Status"
echo "-------------------------------------"
WS_STATUS=$(curl -s "http://localhost:8000/api/v1/ws/dashboard/analytics/status?merchant_id=1")
echo "$WS_STATUS" | python3 -m json.tool
echo ""

# Test 2: Create RAG query log
echo "🧪 Test 2: Create RAG Query Log (triggers broadcast)"
echo "-----------------------------------------------------"
python3 <<'PYEOF'
import asyncio
import sys
sys.path.insert(0, 'backend')

from app.core.database import get_db
from app.models.rag_query_log import RAGQueryLog
from datetime import datetime, UTC

async def main():
    async for db in get_db():
        log = RAGQueryLog(
            merchant_id=1,
            query=f'websocket_test_{datetime.now(UTC).timestamp()}',
            matched=True,
            confidence=0.91,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)

        print(f"✅ RAG query log created")
        print(f"   ID: {log.id}")
        print(f"   Query: {log.query}")
        print(f"   Matched: {log.matched}")
        print(f"   Confidence: {log.confidence}")
        print(f"   Created: {log.created_at}")
        print("")
        print("   If WebSocket is connected, dashboard clients received update instantly")
        break

asyncio.run(main())
PYEOF

echo ""

# Test 3: Verify metrics updated
echo "🧪 Test 3: Verify Knowledge Effectiveness API"
echo "----------------------------------------------"
API_RESPONSE=$(curl -s "http://localhost:8000/api/v1/analytics/knowledge-effectiveness?days=7" \
  -H "X-Merchant-Id: 1" \
  -H "X-Test-Mode: true")

echo "$API_RESPONSE" | python3 -m json.tool
echo ""

# Test 4: WebSocket connection (if websocat available)
if command -v websocat &> /dev/null; then
    echo "🧪 Test 4: WebSocket Connection (5 second test)"
    echo "------------------------------------------------"
    echo "Opening WebSocket connection..."
    echo "Look for 'connected' message below:"
    echo ""

    timeout 5 websocat "ws://localhost:8000/api/v1/ws/dashboard/analytics?merchant_id=1" 2>&1 || true

    echo ""
    echo "✅ WebSocket connection test complete"
else
    echo "🧪 Test 4: WebSocket Connection (skipped)"
    echo "-----------------------------------------"
    echo "websocat not found. Install with:"
    echo "  brew install websocat"
    echo ""
    echo "Manual test in browser console:"
    echo "  const ws = new WebSocket('ws://localhost:8000/api/v1/ws/dashboard/analytics?merchant_id=1');"
    echo "  ws.onmessage = (e) => console.log(JSON.parse(e.data));"
    echo ""
fi

echo "======================================"
echo "✅ All tests complete!"
echo ""
echo "🎯 Next Steps:"
echo "1. Open http://localhost:5173/dashboard"
echo "2. Look for 'Live' indicator in Knowledge Effectiveness Widget"
echo "3. Send a widget message"
echo "4. Watch widget update instantly"
echo ""
echo "📚 Documentation:"
echo "  - WEBSOCKET_REALTIME_SUMMARY.md (overview)"
echo "  - WEBSOCKET_REALTIME_IMPLEMENTATION.md (details)"
