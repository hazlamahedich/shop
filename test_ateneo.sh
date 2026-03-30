#!/bin/bash
API_BASE="http://localhost:8000/api/v1/widget"

echo "Testing: Ask about Ateneo"
echo "=========================="
echo ""

# Create session
SESSION=$(curl -s -X POST "$API_BASE/session" \
  -H "Content-Type: application/json" \
  -d '{"merchant_id": "1"}')

SESSION_ID=$(echo $SESSION | grep -o '"sessionId":"[^"]*"' | cut -d'"' -f4)
echo "Session: $SESSION_ID"
echo ""

# Ask about Ateneo
RESPONSE=$(curl -s -X POST "$API_BASE/message" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"where did he go to college\"}")

echo "$RESPONSE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
content = d['data']['content']
print('Bot Response:')
print(content[:500])
print()

if 'ateneo' in content.lower():
    print('✅ SUCCESS: Found Ateneo')
else:
    print('❌ FAILED: Did not find Ateneo')
"
