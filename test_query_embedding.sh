#!/bin/bash
# Test the embedding generation directly

echo "Testing embedding generation..."
echo ""

# Test if backend can generate embeddings
curl -s -X POST "http://localhost:8000/api/v1/widget/message" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "message": "where did he graduate"
  }' | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print(f'❌ Error: {data[\"error\"]}')
    else:
        content = data.get('data', {}).get('content', '')
        print(f'Response: {content[:200]}...')
except Exception as e:
    print(f'❌ Exception: {e}')
"
