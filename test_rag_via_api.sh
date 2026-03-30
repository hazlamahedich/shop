#!/bin/bash
# Test RAG via actual backend API with detailed logging

API_BASE="http://localhost:8000/api/v1/widget"

echo "=========================================="
echo "Testing RAG via Backend API"
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

# Test different queries
queries=(
    "where did he go to college"
    "what university did he attend"
    "education background"
    "ateneo"
)

for query in "${queries[@]}"; do
    echo "Testing query: '$query'"
    echo "---"

    RESPONSE=$(curl -s -X POST "$API_BASE/message" \
      -H "Content-Type: application/json" \
      -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"$query\"}")

    echo "$RESPONSE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
content = d['data']['content']

# Check for Ateneo or education keywords
content_lower = content.lower()
if 'ateneo' in content_lower:
    print('✅ SUCCESS: Found Ateneo')
elif 'university' in content_lower and 'education' in content_lower:
    print('⚠️  PARTIAL: Found education/university keywords')
elif \"don't have\" in content or \"doesn't contain\" in content or \"doesn't mention\" in content:
    print('❌ FAILED: Bot says info not available')
else:
    print('❓ UNCLEAR: Check response')

print(f'Bot: {content[:200]}...')
"

    # Check sources
    SOURCES=$(echo "$RESPONSE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
sources = d['data'].get('sources', [])
if sources:
    print(f'Sources: {len(sources)} documents')
    for s in sources:
        print(f'  - {s.get(\"title\", \"Unknown\")}')
else:
    print('Sources: NONE (RAG not used)')
")
    echo ""
    sleep 1
done

echo "=========================================="
echo "Summary"
echo "=========================================="
echo "If all queries fail with 'info not available',"
echo "then RAG embedding generation is failing."
echo ""
echo "Possible causes:"
echo "1. Gemini API key not configured/invalid"
echo "2. Embedding service not responding"
echo "3. Vector similarity threshold too high"
