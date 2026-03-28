# CSAT Collection Implementation

## Summary of Changes

### 1. Backend: Updated Feedback API (`/api/v1/feedback`)

**File**: `backend/app/api/feedback.py`

The feedback API now updates the conversation's `customer_satisfied` field when message-level feedback is submitted:

- When **positive** feedback (`rating === "positive"`) is submitted → `conversation.customer_satisfied = true`
- When **negative** feedback (`rating === "negative"`) is submitted → `conversation.customer_satisfied = false`

This bridges the gap between message-level feedback and the conversation-level `customer_satisfied` field that the bot quality metrics query.

### 2. Current State

**Message-level feedback exists**: The widget already has thumbs up/down buttons on bot messages via the `FeedbackRating` component.

**Conversation-level satisfaction**: Now automatically updated when message feedback is submitted.

### 3. How it Works

```
User clicks thumbs up on a bot message
  ↓
Widget calls /api/v1/feedback with { messageId, rating: "positive", sessionId }
  ↓
Backend creates MessageFeedback record
  ↓
Backend ALSO updates conversation.customer_satisfied = true
  ↓
Bot Quality Widget now shows CSAT score based on this data
```

## Data Flow

### Message Feedback → Conversation Satisfaction

| Event | Message Rating | Conversation.customer_satisfied |
|-------|---------------|---------------------------------|
| User clicks thumbs up | positive | true |
| User clicks thumbs down | negative | false |
| No feedback | null | null (not counted in CSAT) |

### Bot Quality Metrics Calculation

The bot quality metrics query:
```sql
SELECT COUNT(*) WHERE customer_satisfied = true  -- satisfied_count
SELECT COUNT(*) WHERE customer_satisfied = false -- unsatisfied_count

CSAT score = 1 + (satisfied_count / total_rated) * 4
-- Returns 1.0 to 5.0 scale
```

## Next Steps (Optional Enhancements)

### Option A: Conversation-End CSAT Prompt

Add a dedicated prompt when the user closes the widget:

```typescript
// CsatPrompt.tsx (new component)
export function CsatPrompt({ onRating, theme }: CsatPromptProps) {
  return (
    <div className="csat-prompt">
      <p>How was your conversation?</p>
      <div className="rating-buttons">
        {[1, 2, 3, 4, 5].map(star => (
          <button onClick={() => onRating(star)}>{star}</button>
        ))}
      </div>
    </div>
  );
}
```

### Option B: Periodic CSAT Check

After every N messages, show a quick satisfaction check:
```typescript
const MESSAGE_THRESHOLD = 5;

if (userMessages.length % MESSAGE_THRESHOLD === 0) {
  setShowCsatPrompt(true);
}
```

### Option C: Current Implementation (Recommended)

**The current implementation is sufficient**:
- Message-level feedback is less intrusive
- Automatically updates conversation satisfaction
- Provides continuous feedback loop
- No additional UI changes needed

## Testing

### 1. Test Message Feedback Updates CSAT

```bash
# 1. Open the widget
# 2. Send a message
# 3. Click thumbs up on the bot's response
# 4. Check the database
```

```python
import asyncio
from app.core.database import get_db
from sqlalchemy import select
from app.models.conversation import Conversation

async def check_csat():
    async for db in get_db():
        result = await db.execute(
            select(Conversation.customer_satisfied)
            .order_by(Conversation.id.desc())
            .limit(5)
        )
        for row in result:
            print(f"customer_satisfied: {row[0]}")
        break

asyncio.run(check_csat())
```

### 2. Test Bot Quality Widget Updates

```bash
# 1. Submit feedback on a few messages (mix of positive/negative)
# 2. Wait 60 seconds for widget refresh
# 3. Check Neural Performance widget shows CSAT score
```

Expected result:
- GRID CSAT: ⭐⭐⭐⭐ X.X (should show a score now instead of N/A)
- RESP_LATENCY: Should still update
- FALLBACK_RATE: Based on conversation data
- RESOLVE_MESH: Based on conversation data

## Verification Commands

### Check conversation satisfaction data

```sql
SELECT
  id,
  customer_satisfied,
  status,
  handoff_status,
  created_at
FROM conversations
ORDER BY created_at DESC
LIMIT 10;
```

### Check message feedback data

```sql
SELECT
  mf.id,
  mf.rating,
  mf.comment,
  c.customer_satisfied,
  c.id as conversation_id
FROM message_feedback mf
JOIN conversations c ON mf.conversation_id = c.id
ORDER BY mf.created_at DESC
LIMIT 10;
```

### Verify bot quality metrics

```bash
# Check what the widget will receive
curl -X GET "http://localhost:8000/api/v1/analytics/bot-quality?days=30" \
  -H "X-Merchant-Id: 1"
```

## Database Schema

### Conversations Table

```sql
customer_satisfied BOOLEAN NULL,  -- Updated by feedback submission
```

### Message Feedback Table

```sql
CREATE TABLE message_feedback (
  id SERIAL PRIMARY KEY,
  message_id INTEGER,
  widget_message_id VARCHAR,
  conversation_id INTEGER,
  merchant_id INTEGER,
  rating VARCHAR(10),  -- 'positive' or 'negative'
  comment TEXT,
  session_id VARCHAR,
  created_at TIMESTAMP
);
```

## API Endpoints

### Submit Feedback (Existing, Enhanced)

```
POST /api/v1/feedback
{
  "messageId": "uuid-or-int",
  "rating": "positive|negative",
  "sessionId": "session-uuid",
  "merchantId": 1,
  "comment": "optional comment"
}
```

Now also updates `conversation.customer_satisfied`.

### Get Bot Quality Metrics (Existing)

```
GET /api/v1/analytics/bot-quality?days=30
```

Queries `conversation.customer_satisfied` for CSAT calculation.

## Frontend Components

### FeedbackRating (Existing)

Location: `frontend/src/widget/components/FeedbackRating.tsx`

- Thumbs up/down buttons on bot messages
- Already integrated into MessageList
- Calls `onFeedbackSubmit` prop

### WidgetClient (Existing)

Location: `frontend/src/widget/api/widgetClient.ts`

```typescript
async submitFeedback(
  messageId: string,
  rating: FeedbackRatingValue,
  sessionId: string,
  merchantId: string,
  comment?: string
)
```

### BotQualityWidget (Existing)

Location: `frontend/src/components/dashboard/BotQualityWidget.tsx`

- Displays CSAT score as star rating
- Refreshes every 60 seconds
- Queries `/api/v1/analytics/bot-quality`

## Conclusion

The CSAT collection is now **fully implemented** through the existing message feedback system:

✅ Users can rate bot responses with thumbs up/down
✅ Feedback automatically updates conversation satisfaction
✅ Bot Quality Widget displays CSAT score from this data
✅ No additional UI changes required

The widget will now show meaningful CSAT data instead of N/A as users interact with the bot and provide feedback.
