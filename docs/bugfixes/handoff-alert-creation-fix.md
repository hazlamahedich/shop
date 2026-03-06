# Bug Fix: Handoff Alert Creation for Widget Conversations

**Date:** 2026-03-06  
**Priority:** High  
**Status:** Fixed

## Problem Description

Widget conversations that triggered handoff were not appearing in the Handoff Queue page. The conversations were correctly marked with `status='handoff'` and `handoff_status='pending'`, but they were missing from the handoff queue UI.

## Root Cause

When handoff was triggered through the unified conversation service (`unified_conversation_service.py`), the system:

1. ✅ Created/updated `Conversation` records with handoff status
2. ✅ Persisted messages to the database
3. ❌ **Did NOT create `HandoffAlert` records**

The Handoff Queue page queries the `handoff_alerts` table, not the `conversations` table. Without a corresponding `HandoffAlert` record, conversations would not appear in the queue.

## Additional Issues Found

1. **Encrypted Message Display**: The `conversation_preview` field in `HandoffAlert` was storing encrypted message content instead of decrypted text, making the queue unreadable.

2. **Missing Alerts for Existing Conversations**: Historical handoff conversations lacked `HandoffAlert` records.

## Solution Implemented

### 1. Added HandoffAlert Creation to Unified Service

**File:** `backend/app/services/conversation/unified_conversation_service.py`

Added logic in `_update_conversation_handoff_status()` to:
- Create `HandoffAlert` record when handoff is triggered
- Determine urgency level (high/medium/low) based on message content
- Store decrypted conversation preview
- Mask customer ID for privacy
- Check for existing alerts to avoid duplicates

**Urgency Logic:**
- **High**: Checkout/payment/refund/cancel mentioned
- **Medium**: Low confidence, clarification loop, or order/delivery/shipping mentioned
- **Low**: Keyword trigger (routine request)

### 2. Created Migration Script

**File:** `backend/scripts/create_missing_handoff_alerts.py`

One-time migration to:
- Find existing handoff conversations without alerts
- Create missing `HandoffAlert` records
- Use decrypted message content for preview
- Calculate wait time from handoff trigger

**Results:**
- Created 2 missing alerts for merchant 4
- Skipped 1 conversation that already had alert

### 3. Fixed Encrypted Preview Issue

Updated migration script to use `message.decrypted_content` property instead of encrypted `message.content` field.

## Files Changed

1. `backend/app/services/conversation/unified_conversation_service.py` - Added HandoffAlert creation logic
2. `backend/scripts/create_missing_handoff_alerts.py` - New migration script

## Testing

### Before Fix
```
handoff_alerts for merchant 4: 4 records
- All for Facebook conversations (fb-user-*)
- No widget conversation alerts
```

### After Fix
```
handoff_alerts for merchant 4: 6 records
- Includes widget conversation 975 (3929ca93-a7c2-4b3b-ab46-f5dd00c3224f)
- Includes test conversation 976 (test-session-123)
- All previews now show decrypted text
```

### Verification Steps

1. Send handoff message through Shopify widget (e.g., "I need to talk to someone")
2. Check `handoff_alerts` table - new alert should be created automatically
3. View Handoff Queue page - conversation should appear immediately
4. Verify conversation preview shows readable text (not encrypted)

## Impact

- **User Impact:** High - Merchants can now see all handoff requests in queue
- **Data Impact:** Medium - Historical conversations migrated, future alerts auto-created
- **Performance Impact:** Minimal - One additional database insert per handoff

## Related Stories

- Story 4-6: Handoff Notifications
- Story 4-7: Handoff Queue with Urgency
- Story 5-11: Messenger Unified Service Migration

## Deployment Notes

1. Deploy backend changes
2. Run migration script: `python backend/scripts/create_missing_handoff_alerts.py`
3. Verify alerts appear in Handoff Queue UI
4. No frontend changes required

## Prevention

The unified service now creates `HandoffAlert` records automatically, preventing this issue from recurring. The code includes:
- Duplicate detection (skips if alert exists)
- Proper decryption of message content
- Error handling and logging
- Urgency level determination
