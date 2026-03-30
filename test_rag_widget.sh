#!/bin/bash

# Test RAG Widget Script
# This script tests if the widget can answer questions from the knowledge base

# Configuration
MERCHANT_ID=1
BACKEND_URL="http://localhost:8080"

echo "🔍 Testing RAG Widget for Merchant $MERCHANT_ID"
echo "================================================"
echo ""

# Step 1: Create a session
echo "📝 Step 1: Creating widget session..."
SESSION_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/widget/session" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": '$MERCHANT_ID',
    "visitor_id": "test-visitor-'$(date +%s)'"
  }')

echo "Response: $SESSION_RESPONSE"
echo ""

# Extract session_id from response
SESSION_ID=$(echo $SESSION_RESPONSE | grep -o '"session_id":"[^"]*' | cut -d'"' -f4)

if [ -z "$SESSION_ID" ]; then
  echo "❌ Failed to create session"
  echo "Full response: $SESSION_RESPONSE"
  exit 1
fi

echo "✅ Session created: $SESSION_ID"
echo ""

# Step 2: Send a test question
echo "💬 Step 2: Sending question: 'Where did he graduate?'"
MESSAGE_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/widget/message" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Where did he graduate?\"
  }")

echo "Response:"
echo "$MESSAGE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$MESSAGE_RESPONSE"
echo ""

# Step 3: Check if sources were returned
echo "📚 Step 3: Checking if RAG sources were returned..."
if echo "$MESSAGE_RESPONSE" | grep -q '"sources"'; then
  echo "✅ RAG is working! Sources were returned."
  echo ""
  echo "Sources found:"
  echo "$MESSAGE_RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'data' in data and 'sources' in data['data']:
    sources = data['data']['sources']
    for i, source in enumerate(sources, 1):
        print(f\"  {i}. Document: {source.get('filename', 'N/A')}\")
        print(f\"     Type: {source.get('documentType', 'N/A')}\")
        print(f\"     Relevance: {source.get('relevanceScore', 'N/A')}\")
        print()
else:
    print('  No sources found in response')
"
else
  echo "❌ RAG may not be working - no sources in response"
fi

echo ""
echo "================================================"
echo "Test complete!"
echo ""
echo "💡 To test in browser:"
echo "   1. Open your widget URL"
echo "   2. Ask: 'Where did he graduate?'"
echo "   3. Check if the bot answers with information from the resume"
