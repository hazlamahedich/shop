# Neural Performance Widget Stale Data - Diagnosis

## Issue
The Neural Performance widget shows data that appears stale and not updating:
- STATUS_ARRAY: OPTIMAL
- GRID CSAT: N/A
- RESP_LATENCY: 1.3s
- FALLBACK_RATE: 0.0%
- RESOLVE_MESH: 0.0%

## Root Cause Analysis

### 1. Insufficient Data
```
Total LLM cost entries: 75 (65 in last 24h)
Total conversations: 3
CSAT ratings: 0
```

### 2. Missing Customer Satisfaction Data
- No conversations have `customer_satisfied` field populated
- This causes GRID CSAT to display as "N/A"
- Without CSAT data, the widget appears incomplete

### 3. Limited Conversation Activity
- Only 3 conversations total means metrics won't change frequently
- Fallback rate and resolution rate require more conversation data to show meaningful trends

## Widget Configuration (✓ Correct)
```typescript
refetchInterval: 60_000,  // Fetches every 60 seconds
staleTime: 30_000,        // Data stale after 30 seconds
```

## Backend Endpoint (✓ Correct)
- No caching on `/api/v1/analytics/bot-quality` endpoint
- Queries database directly each time
- Logs confirm metrics are being retrieved

## Solutions

### Option 1: Add Test Conversations
```sql
-- Insert conversations with varied outcomes
INSERT INTO conversations (
  merchant_id,
  customer_satisfied,
  status,
  handoff_status,
  consecutive_low_confidence_count,
  created_at
) VALUES
(1, TRUE, 'closed', 'resolved', 0, NOW()),
(1, FALSE, 'closed', 'escalated', 2, NOW()),
(1, TRUE, 'closed', 'none', 0, NOW() - INTERVAL '1 day');
```

### Option 2: Implement CSAT Collection
```typescript
// Add feedback collection in widget
const handleFeedback = async (satisfied: boolean) => {
  await apiClient.post('/api/v1/conversations/{id}/feedback', {
    customer_satisfied: satisfied
  });
};
```

### Option 3: Check Conversation Creation Flow
Verify that:
1. Conversations are being created properly
2. Conversations are being closed
3. Feedback collection is implemented
4. LLM cost tracking is working

## Testing Commands

### Check Widget Refresh Rate
```bash
# Open browser console and watch network requests
grep -i "bot-quality" backend/logs/app.log | tail -20
```

### Verify Data is Being Created
```python
# Run in backend directory
source .venv/bin/activate
python3 << 'EOF'
import asyncio
from app.core.database import get_db
from sqlalchemy import select, func
from app.models.llm_conversation_cost import LLMConversationCost
from app.models.conversation import Conversation
from datetime import datetime, timedelta

async def main():
    async for db in get_db():
        # Recent LLM entries
        cutoff = datetime.utcnow() - timedelta(hours=1)
        recent = await db.execute(
            select(func.count(LLMConversationCost.id))
            .where(LLMConversationCost.request_timestamp >= cutoff)
        )

        # Conversations by status
        by_status = await db.execute(
            select(Conversation.status, func.count(Conversation.id))
            .group_by(Conversation.status)
        )

        print(f"LLM entries (last hour): {recent.scalar()}")
        for status, count in by_status:
            print(f"Conversations with status '{status}': {count}")
        break

asyncio.run(main())
EOF
```

### Monitor Widget API Calls
```bash
# Watch the bot-quality endpoint logs
tail -f backend/logs/app.log | grep "bot_quality"
```

## Expected Behavior After Fix

Once sufficient data exists, the widget should show:
- **GRID CSAT**: ⭐⭐⭐⭐ score (e.g., 4.2)
- **RESP_LATENCY**: Updating based on recent LLM processing times
- **FALLBACK_RATE**: % of conversations with low confidence
- **RESOLVE_MESH**: % of conversations resolved without handoff
- **STATUS_ARRAY**: Changes based on health thresholds:
  - OPTIMAL: response time < 3s, fallback rate < 5%, resolution rate > 70%
  - DEGRADED: response time 3-5s, fallback rate 5-10%, resolution rate 50-70%
  - CRITICAL: response time > 5s, fallback rate > 10%, resolution rate < 50%
