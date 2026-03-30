#!/bin/bash
# Test WebSocket Real-Time Updates for Knowledge Effectiveness Widget

echo "🧪 Testing WebSocket Real-Time Updates"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if backend is running
echo "1️⃣ Checking backend status..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Backend is running${NC}"
else
    echo -e "${RED}❌ Backend is not running${NC}"
    echo "Please start the backend first:"
    echo "  cd backend && python -m uvicorn app.main:app --reload"
    exit 1
fi

echo ""
echo "2️⃣ Checking WebSocket endpoint..."
WS_STATUS=$(curl -s "http://localhost:8000/api/v1/ws/dashboard/analytics/status?merchant_id=1")
echo "WebSocket status: $WS_STATUS"

echo ""
echo "3️⃣ Testing WebSocket connection..."
echo "   Opening WebSocket connection..."

# Use websocat if available, otherwise provide instructions
if command -v websocat &> /dev/null; then
    echo -e "${GREEN}✅ websocat found${NC}"
    echo "   Opening WebSocket (will timeout after 5 seconds)..."
    timeout 5 websocat "ws://localhost:8000/api/v1/ws/dashboard/analytics?merchant_id=1" 2>&1 || true
else
    echo -e "${YELLOW}⚠️  websocat not found${NC}"
    echo "   Install with: brew install websocat"
    echo ""
    echo "   Manual test: Open browser console and run:"
    echo "   const ws = new WebSocket('ws://localhost:8000/api/v1/ws/dashboard/analytics?merchant_id=1');"
    echo "   ws.onmessage = (e) => console.log('Received:', JSON.parse(e.data));"
fi

echo ""
echo "4️⃣ Testing RAG query broadcast..."
echo "   Creating test RAG query log..."

python3 - <<EOF
import asyncio
import sys
sys.path.insert(0, 'backend')

from app.core.database import get_db
from app.models.rag_query_log import RAGQueryLog
from datetime import datetime, UTC

async def create_test_log():
    async for db in get_db():
        log = RAGQueryLog(
            merchant_id=1,
            query=f'test query {datetime.now(UTC).isoformat()}',
            matched=True,
            confidence=0.92,
        )
        db.add(log)
        await db.commit()
        print(f"✅ Created RAG query log: {log.id}")
        print(f"   Query: {log.query}")
        print(f"   Matched: {log.matched}")
        print(f"   Confidence: {log.confidence}")
        break

asyncio.run(create_test_log())
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Test RAG query created${NC}"
    echo "   If WebSocket was connected, you should have received an update"
else
    echo -e "${RED}❌ Failed to create test RAG query${NC}"
fi

echo ""
echo "5️⃣ Testing HTTP API for comparison..."
API_RESPONSE=$(curl -s "http://localhost:8000/api/v1/analytics/knowledge-effectiveness?days=7" \
  -H "X-Merchant-Id: 1" \
  -H "X-Test-Mode: true")

echo "API Response:"
echo "$API_RESPONSE" | python3 -m json.tool | head -20

echo ""
echo "======================================"
echo -e "${GREEN}✅ Testing complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Open dashboard at http://localhost:5173/dashboard"
echo "2. Send a widget message to create a RAG query"
echo "3. Watch Knowledge Effectiveness Widget update instantly"
echo "4. Check for 'Live' indicator in widget"
