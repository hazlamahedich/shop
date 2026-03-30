#!/bin/bash
API_BASE="http://localhost:8000/api/v1/widget"

# Create session
SESSION=$(curl -s -X POST "$API_BASE/session" \
  -H "Content-Type: application/json" \
  -d '{"merchant_id": "1"}')

SESSION_ID=$(echo $SESSION | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['sessionId'])")
echo "Session: $SESSION_ID"
echo ""

# Send greeting
echo "Sending greeting..."
curl -s -X POST "$API_BASE/message" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"hello\"}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d['data']['content'][:100])
"
echo ""

# Ask about graduation
echo "Asking: where did he graduate"
RESPONSE=$(curl -s -X POST "$API_BASE/message" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"where did he graduate\"}")

echo "$RESPONSE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
content = d['data']['content']
sources = d['data'].get('sources')

print(f'Bot: {content}')
print()
if sources:
    print(f'Sources: {len(sources)} documents')
    for s in sources:
        print(f'  - {s.get(\"title\", \"Unknown\")}')
else:
    print('Sources: NONE')
"
