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
- ⚠️ **Not yet completed**: Verify the fixes resolve the widget loading loop
- ⚠️ **Not yet completed**: Greenlet error not investigated (in backend services)
- ⚠️ **Not yet completed**: Quick reply chips not investigated fully
- ⚠️ **Not yet completed**: End-to-end testing in browser needed

## Relevant files / directories
### Frontend Files Modified:
- `frontend/src/widget/components/ChatWindow.tsx` - **FIXED corrupted code at lines 207-227**. The old broken code:
  ```javascript
  // BROKEN CODE (REMOVED):
  const [messages] = messages.filter(m => m.sender === 'user');
    if (userMessages.length > 0) {
      setShowFaqButtons(false);
    }
  }, [messages]);
  // ... more malformed blocks
  ```
  New fixed code:
  ```javascript
  // FIXED CODE:
  React.useEffect(() => {
    const userMessages = messages.filter((m) => m.sender === 'user');
    if (userMessages.length > 0 && showFaqButtons) {
      setShowFaqButtons(false);
    }
  }, [messages, showFaqButtons]);
  ```
- `frontend/src/widget/context/WidgetContext.tsx` - **FIXED initWidget guard clause** at lines 249-257:
  - Added missing `return` after `if (!mId)` check
  - Removed redundant `&& !state.isLoading` from initialization skip check

### Frontend Files (for reference):
- `frontend/src/widget/Widget.tsx` - Widget component, calls `initWidget(merchantId)` in useEffect
- `frontend/src/widget/loader.ts` - Widget loader script
- `frontend/src/widget/api/widgetClient.ts` - API client with `getConfig()`, `getFaqButtons()`, `sendMessage()`
- `frontend/src/widget/components/FAQQuickButtons.tsx` - FAQ button component
- `frontend/src/widget/components/QuickReplyButtons.tsx` - Quick reply component
- `frontend/src/widget/components/SuggestedReplies.tsx` - Suggested replies component
- `frontend/public/widget-test.html` - Widget test page

### Backend Files (need investigation):
- `backend/app/api/widget.py` - Widget API endpoints
- `backend/app/services/widget/widget_message_service.py` - WidgetMessageService.process_message()
- `backend/app/services/conversation/unified_conversation_service.py` - UnifiedConversationService (likely source of greenlet error)
### Backend APIs verified working:
- `GET /api/v1/widget/config/{merchantId}` - Returns widget config
- `GET /api/v1/widget/faq-buttons/{merchantId}` - Returns FAQ buttons

## Next Steps
1. **Test the fixes in browser** - Start frontend dev server and verify:
   - Widget loads without looping
   - Greeting appears once
   - FAQ buttons appear with greeting
   - FAQ buttons hide after first user message
2. **Investigate greenlet error** - Check backend services for lazy-loaded SQLAlchemy relationships accessed outside async context
3. **Investigate quick replies** - Check if backend returns `suggestedReplies` in message response and if frontend properly handles them
4. **Run end-to-end test** at `http://localhost:5174/widget-test.html?merchantId=1`