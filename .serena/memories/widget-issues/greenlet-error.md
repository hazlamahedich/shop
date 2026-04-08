# Widget Issues - Current Progress

## Goal
The user is experiencing **five issues** in their e-commerce chat widget application:

1. **Greenlet Error**: A SQLAlchemy async error: `greenlet_spawn has not been called; can't call await_only() here` - occurs in backend when processing messages
2. **Greeting not showing**: Custom greeting message not appearing when widget opens (or appearing twice)
3. **FAQ buttons not showing**: FAQ quick buttons not appearing below the chat on initial load
4. **Quick reply chips not showing**: Suggested replies/quick reply chips not appearing after bot messages
5. **Widget loading loop** (NEW): Widget is continuously looping/reloading when embedded on a portfolio page

## Instructions
- Investigate and fix all five issues
- Merchant ID 1 is logged in and has data in PostgreSQL database on Docker port 5433
- Test the widget at `http://localhost:5174/widget-test.html?merchantId=1`
- **Important clarification from user**: Quick reply buttons should only appear AFTER user provides a response or bot responds from FAQ/knowledge base. FAQ buttons should appear on initial chat TOgether with the greeting.
- **Do NOT commit code** unless explicitly asked by user

## Discoveries

**Database Configuration (verified correct):**
- Merchant 1: `onboarding_mode = 'general'`, `use_custom_greeting = true`
- Custom greeting: "Hi I am Sherms! I can help ypu answer questions about Sherwin G. Mante"
- 4 FAQs exist in `faqs` table for merchant 1

**Backend APIs (verified working):**
- `GET /api/v1/widget/config/1` returns correct config with `onboardingMode: "general"`, `welcomeMessage` set
- `GET /api/v1/widget/faq-buttons/1` returns 4 FAQ buttons correctly
- Backend health check passes

**Root Causes Identified:**
1. **ChatWindow.tsx CORRUPTED CODE (FIXED)**: Lines 207-227 had severely corrupted/malformed code with:
   - Broken `useEffect` blocks (missing `React.useEffect` wrapper)
   - References to non-existent `state` variable (ChatWindow uses props, not state)
   - Malformed JavaScript causing syntax errors
   - Multiple duplicate/broken useEffect blocks
   - This was likely causing infinite re-renders and the widget loading loop

2. **initWidget guard clause bug (FIXED)**: Missing `return` statement after checking if merchantId is empty, and redundant `!state.isLoading` check in the initialization guard
3. **Greeting showing twice**: Race condition in `WidgetContext.tsx` lines 603-620 where `greetingShownRef.current` logic may allow duplicate greetings
4. **FAQ buttons not appearing**: The corrupted code in ChatWindow.tsx was preventing proper rendering; also the `showFaqButtons` state logic needs to be verified after the fix
5. **Quick reply chips**: Backend may not be returning `suggestedReplies` in message responses - needs investigation
6. **Greenlet error**: Lazy-loaded SQLAlchemy relationships accessed after session commit/flush in backend services - needs investigation

## Accomplished
- ✅ Verified database configuration is correct
- ✅ Verified backend APIs return correct data (config, FAQ buttons)
- ✅ **FIXED corrupted ChatWindow.tsx code** (lines 207-227) - replaced broken code with proper React.useEffect for hiding FAQ buttons after user message
- ✅ **FIXED initWidget guard clause** - added missing `return` and removed redundant `!state.isLoading` check
- ✅ **FIXED greenlet error** in `widget_message_service.py` by caching merchant attributes before async operations
- ✅ **FIXED message persistence** - Added 3 missing GET endpoints to `backend/app/api/widget.py`:
  - `GET /widget/session/{session_id}` - Retrieve session data for restoration
  - `GET /widget/session/{session_id}/messages` - Retrieve message history from Redis
  - `GET /widget/session/by-visitor/{merchant_id}/{visitor_id}` - Look up session by visitor ID
- ✅ **FIXED TTL bug** in `widget_session_service.py` `refresh_session()` - message history TTL was being reset from 7 days to 1 hour on every message exchange

## Next Steps
1. Test end-to-end: session restore, message persistence across refresh, cart/order operations
2. Start backend + frontend and verify at `http://localhost:5174/widget-test.html?merchantId=1`