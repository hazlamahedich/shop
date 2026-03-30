# Widget Conversation Cleanup - Fix Summary

## Problem

**Issue**: Widget conversations were not being closed when their Redis sessions expired.

**Symptoms**:
- 13 active widget conversations in database
- Only 1 active session in Redis
- Conversations remained "active" for 37+ hours after sessions expired
- No automatic cleanup mechanism for stale conversations

## Root Cause

The existing cleanup system (`widget_cleanup_service.py`) only removed expired sessions from Redis but did **not** close the associated conversations in the database.

Conversations remained "active" when:
- Redis TTL expired (1 hour)
- WebSocket disconnected unexpectedly
- User closed browser without proper shutdown
- Network interruptions occurred

## Solution

### 1. Created Conversation Cleanup Service

**File**: `backend/app/services/widget/widget_conversation_cleanup_service.py`

A new service that:
- Scans all active widget conversations
- Checks if corresponding Redis session exists
- Closes conversations with expired/missing sessions
- Also closes conversations older than 2 hours (safety net)

### 2. Created Background Job Scheduler

**File**: `backend/app/background_jobs/widget_conversation_cleanup.py`

Background job that:
- Runs every 10 minutes
- Automatically closes stale conversations
- Prevents database bloat with orphaned conversations

### 3. Updated Application Startup

**File**: `backend/app/main.py`

Added conversation cleanup scheduler to application lifecycle:
- Starts with application (line 191)
- Shuts down gracefully (line 227)

### 4. Created Manual Cleanup Script

**File**: `backend/scripts/cleanup_stale_widget_conversations.py`

Script to immediately clean up existing stale conversations.

## Results

**Before**:
- 13 active widget conversations
- 12 stale (2-37 hours old)
- 1 active Redis session

**After**:
- 13 closed conversations
- 0 active stale conversations
- All orphaned conversations cleaned up

## Implementation Details

### Stale Conversation Criteria

A conversation is considered stale if ANY of:
1. No Redis session exists (expired or missing)
2. Redis session is past expiration time
3. Conversation is older than 2 hours (safety net)

### Cleanup Frequency

- **Background job**: Every 10 minutes
- **Manual cleanup**: Run `scripts/cleanup_stale_widget_conversations.py`

### Configuration

- Session TTL: 1 hour (Redis)
- Stale threshold: 2 hours (database)
- Cleanup interval: 10 minutes (background job)

## Files Modified

1. `backend/app/services/widget/widget_conversation_cleanup_service.py` (NEW)
2. `backend/app/background_jobs/widget_conversation_cleanup.py` (NEW)
3. `backend/app/main.py` (MODIFIED - added scheduler)
4. `backend/scripts/cleanup_stale_widget_conversations.py` (NEW)

## Future Improvements

1. Add metrics/monitoring for cleanup operations
2. Add alerting if cleanup fails repeatedly
3. Consider closing conversations on WebSocket disconnect (instead of background)
4. Add dashboard to view conversation lifecycle

## Testing

Run the cleanup script manually:
```bash
cd backend
python scripts/cleanup_stale_widget_conversations.py
```

Check active conversations:
```python
import asyncio
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.conversation import Conversation

async def check():
    async for db in get_db():
        result = await db.execute(
            select(Conversation.status, func.count(Conversation.id))
            .where(Conversation.platform == 'widget')
            .group_by(Conversation.status)
        )
        for row in result:
            print(f'{row[0]}: {row[1]}')
        break

asyncio.run(check())
```

## Deployment

The fix is self-deploying:
1. Application starts the scheduler automatically
2. Runs every 10 minutes without manual intervention
3. No configuration changes required
