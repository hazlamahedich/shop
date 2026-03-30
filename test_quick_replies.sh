#!/bin/bash

# Test Quick Replies in Widget
# This script tests if the backend is sending quick_replies in the response

echo "Testing Quick Replies in Widget..."
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend is not running on port 8000"
    echo "Please start the backend with: cd backend && python -m uvicorn app.main:app --reload"
    exit 1
fi

echo "✅ Backend is running"
echo ""

# Get a widget config to find a merchant ID
echo "Fetching widget config..."
CONFIG_RESPONSE=$(curl -s http://localhost:8000/api/v1/widget/config/1)
echo "Config response: $CONFIG_RESPONSE"
echo ""

# Extract onboarding mode
ONBOARDING_MODE=$(echo $CONFIG_RESPONSE | jq -r '.data.onboarding_mode // .onboarding_mode // "ecommerce"')
echo "Onboarding mode: $ONBOARDING_MODE"
echo ""

# Create a session
echo "Creating session..."
SESSION_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/widget/session \
    -H "Content-Type: application/json" \
    -d '{"merchant_id": "1"}')
echo "Session response: $SESSION_RESPONSE"
echo ""

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.data.sessionId // .data.session_id // .session_id // .sessionId // ""')
echo "Session ID: $SESSION_ID"
echo ""

if [ -z "$SESSION_ID" ]; then
    echo "❌ Failed to get session ID"
    exit 1
fi

# Send a simple message that should trigger quick replies
echo "Sending message to trigger quick replies..."
MESSAGE_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/widget/message \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"hello\"}")
echo "Message response: $MESSAGE_RESPONSE"
echo ""

# Extract quick_replies from the response (check both camelCase and snake_case)
QUICK_REPLIES=$(echo $MESSAGE_RESPONSE | jq -r '.data.quickReplies // .data.quick_replies // "null"')
echo "Quick replies: $QUICK_REPLIES"
echo ""

if [ "$QUICK_REPLIES" = "null" ] || [ -z "$QUICK_REPLIES" ]; then
    echo "❌ No quickReplies or quick_replies found in response!"
    echo ""
    echo "Expected quick replies for greeting message but got none."
    echo ""
    echo "Full response:"
    echo $MESSAGE_RESPONSE | jq '.'
    exit 1
else
    echo "✅ Quick replies found!"
    echo ""
    echo "Quick replies content:"
    echo $QUICK_REPLIES | jq '.'
    exit 0
fi
