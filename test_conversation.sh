#!/bin/bash
# Test RAG and Quick Replies in conversation flow

API_BASE="http://localhost:8000/api/v1/widget"

echo "=========================================="
echo "TESTING: Graduation Question with Context"
echo "=========================================="
echo ""

# Create session
echo "Step 1: Creating session..."
SESSION=$(curl -s -X POST "$API_BASE/session" \
  -H "Content-Type: application/json" \
  -d '{"merchant_id": "1"}')

SESSION_ID=$(echo $SESSION | grep -o '"sessionId":"[^"]*"' | cut -d'"' -f4)
echo "✓ Session: $SESSION_ID"
echo ""

# Send greeting
echo "Step 2: Sending greeting..."
GREETING=$(curl -s -X POST "$API_BASE/message" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"hello\"}")

echo "$GREETING" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Bot: ' + d['data']['content'][:150] + '...')
qr = d['data'].get('quickReplies', d['data'].get('quick_replies'))
if qr:
    print('Quick Replies:')
    for r in qr:
        print(f'  - {r[\"text\"]} {r.get(\"icon\", \"\")}')
else:
    print('Quick Replies: NONE')
"
echo ""

sleep 1

# Ask about graduation
echo "Step 3: Asking 'where did he graduate'..."
RESPONSE=$(curl -s -X POST "$API_BASE/message" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"where did he graduate\"}")

echo "$RESPONSE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
content = d['data']['content']
print('Bot: ' + content[:400])
print()

# Check RAG
if 'santo tomas' in content.lower() or 'university of santo tomas' in content.lower():
    print('✅ RAG: Found University of Santo Tomas')
elif 'university' in content.lower():
    print('⚠️  RAG: Found university but not specific')
    print('   Expected: University of Santo Tomas')
else:
    print('❌ RAG: No graduation info found')

print()

# Check quick replies
qr = d['data'].get('quickReplies', d['data'].get('quick_replies'))
if qr:
    print(f'Quick Replies: {len(qr)} chips')
    for r in qr:
        print(f'  - {r[\"text\"]} {r.get(\"icon\", \"\")}')

    texts = [r['text'].lower() for r in qr]
    if 'yes' in texts or 'no' in texts:
        print('❌ ISSUE: Yes/No replies not contextual')
        print('   Expected: Learn more, Contact us, etc.')
    else:
        print('✅ Quick replies are contextual')
else:
    print('❌ Quick Replies: NONE')

print()

# Check sources
sources = d['data'].get('sources')
if sources:
    print(f'Sources: {len(sources)} citations')
    for s in sources:
        print(f'  - {s.get(\"title\", \"Unknown\")}')
else:
    print('Sources: NONE')
"
echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
