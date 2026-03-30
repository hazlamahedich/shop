#!/bin/bash

# Simple RAG Test - Direct API Call
# This bypasses the session creation and tests a known working session

echo "🧪 Testing RAG with Direct API Call"
echo "===================================="
echo ""

# If you have a working widget session, use it
# Otherwise, we'll need to get one from your browser

echo "📝 To get a session ID:"
echo "   1. Open your widget in browser"
echo "   2. Open DevTools → Network tab"
echo "   3. Send a message through the widget"
echo "   4. Find the 'message' API call"
echo "   5. Copy the 'session_id' from the request payload"
echo ""
read -p "Enter your session ID (or press Enter to skip): " SESSION_ID

if [ -z "$SESSION_ID" ]; then
    echo "⏭️  Skipping API test"
    echo ""
    echo "💡 Instead, test in your browser widget:"
    echo "   1. Open the widget on your site"
    echo "   2. Ask: 'Where did he graduate?'"
    echo "   3. Check if the bot answers with graduation info"
    echo "   4. Open DevTools → Network tab"
    echo "   5. Look for the /api/v1/widget/message response"
    echo "   6. Check if it has a 'sources' array with document info"
    exit 0
fi

echo ""
echo "🔍 Testing with session: $SESSION_ID"
echo ""

# Test the message endpoint
RESPONSE=$(curl -s -X POST "http://localhost:8080/api/v1/widget/message" \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:5173" \
  -d "{
    \"session_id\": \"$SESSION_ID\",
    \"message\": \"Where did he graduate?\"
  }")

echo "Response:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Check for sources
if echo "$RESPONSE" | grep -q '"sources"'; then
    echo "✅ SUCCESS! RAG is working - sources were returned"
else
    echo "❌ No sources found - RAG may not be working"
fi
