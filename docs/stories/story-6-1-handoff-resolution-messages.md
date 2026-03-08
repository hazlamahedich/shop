# Story 6-1: Handoff Resolution Messages

## Status: ✅ COMPLETE

## Goal

Implement LLM-powered handoff resolution messages that appear in the Shopify widget when merchants resolve handoffs from the queue. The system generates personalized, context-aware messages (1-3 sentences) and delivers them in real-time via WebSocket to the customer's widget.

## Requirements

- Generate personalized messages when merchants resolve handoffs
- Use last 5 messages for context, temperature 0.7
- Fallback to generic "Welcome back!" on LLM failure
- Naturally mention the business name in generated messages
- Track metrics: success rate, response time, fallback usage
- Platform-aware: Only send WebSocket messages to widget conversations (not messenger)
- Retroactive consent save: When consent is granted, save all previous messages from Redis to PostgreSQL
- Better UX approach: Bot responds immediately, then when consent is granted, retroactively save conversation history

## Implementation Details

### Backend Changes

| File | Changes |
|------|---------|
| `backend/app/services/handoff/handoff_resolution_service.py` | Orchestrates resolution flow, generates LLM message, broadcasts via WebSocket |
| `backend/app/services/widget/widget_message_service.py` | Added `retroactively_save_conversation_history()` method |
| `backend/app/services/widget/connection_manager.py` | Fixed singleton pattern, added extensive logging |
| `backend/app/api/widget.py` | Integrated retroactive save on consent grant |
| `backend/app/api/widget_ws.py` | Added connection logging |
| `backend/app/main.py` | Strengthened `/widget/{filename}` cache headers to `no-cache, no-store, must-revalidate` |

### Frontend Changes

| File | Changes |
|------|---------|
| `frontend/src/widget/api/widgetWsClient.ts` | Added comprehensive diagnostic logging in `ws.onmessage` handler |
| `frontend/src/widget/context/WidgetContext.tsx` | Added handler for `handoff_resolved` message type |
| `frontend/src/components/widget/EmbedCodePreview.tsx` | Changed all embed code generators to use `/widget/widget.umd.js` instead of `/static/widget/widget.umd.js` |

## Bugs Fixed

### Bug: Handoff Resolution Message Not Appearing in Widget

**Root Cause:** The Shopify-embedded widget was loading a **stale cached version** of `widget.umd.js` that didn't contain the `handoff_resolved` WebSocket handler.

This happened because the embed code pointed to `/static/widget/widget.umd.js`, which is served by FastAPI's built-in `StaticFiles` middleware with **default 2-week browser cache headers**. Even after rebuilding the widget with the handler, the browser kept serving the old cached JS file.

**Fixes Applied:**
1. Changed all embed code generators to use `/widget/widget.umd.js` instead of `/static/widget/widget.umd.js` — this route has explicit no-cache headers
2. Strengthened the `/widget/{filename}` route's cache headers to `Cache-Control: no-cache, no-store, must-revalidate`
3. Updated Shopify `theme.liquid` script tag URL from `/static/widget/` to `/widget/` path

**Why It Was Tricky to Debug:**
- The **backend was correctly sending** the `handoff_resolved` message via WebSocket
- The **frontend code was correct** — the WidgetContext.tsx handler properly dispatches `ADD_MESSAGE` for `handoff_resolved` events
- The actual issue was invisible at the code level — it was a **deployment/caching problem** where the browser never loaded the latest JS build

## Test Commands

```bash
# Check WebSocket connections log
tail -30 /tmp/ws_connections.log

# Rebuild widget
cd frontend && npm run build:widget && cp -r dist/widget/* ../backend/app/static/widget/

# Test handoff resolution
cd backend && source venv/bin/activate && python scripts/test_handoff_resolution_flow.py
```

## Embed Code (Current)

```html
<script>
  window.ShopBotConfig = {
    merchantId: '6',
    theme: { primaryColor: '#6366f1' },
    apiBaseUrl: 'https://your-domain.com/api/v1/widget'
  };
</script>
<script src="https://your-domain.com/widget/widget.umd.js"></script>
```

## Key Learnings

1. **Widget caching is critical**: Always use no-cache headers for widget JavaScript files
2. **Use `/widget/` route, not `/static/widget/`**: The `/widget/` route has proper cache headers
3. **Diagnostic logging is essential**: Version identifiers in console logs help verify correct build is loaded
4. **Singleton patterns in Python**: Use dict-based state (`_manager_state = {"manager": None}`) instead of module-level variables for proper singleton behavior

## Tasks Completed

- [x] Retroactive conversation save on consent grant
- [x] Handoff resolution message generation (LLM working)
- [x] Message storage in PostgreSQL
- [x] WebSocket broadcast implementation
- [x] Singleton fix for connection manager
- [x] Frontend handler for `handoff_resolved` message type
- [x] Widget caching fix for proper build loading
