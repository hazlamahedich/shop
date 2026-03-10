# Story 4.8: Conversation History View

Status: done

## Story

As a merchant,
I want to see full conversation history including bot context,
so that I can understand exactly what happened before I step in.

## Acceptance Criteria

1. **AC1: Complete Message History** - Given a merchant opens a handoff conversation, When viewing conversation details, Then they see complete message history with all shopper and bot messages displayed in chronological order (oldest first).

2. **AC2: Bot Confidence Scores** - Given bot messages in the conversation, When viewing a bot message, Then the confidence score is displayed (e.g., "Confidence: 0.85") for each bot response.

3. **AC3: Bot Internal State** - Given a handoff conversation, When viewing conversation details, Then the bot's internal state is shown including: cart contents (items, quantities), extracted constraints (budget, size, category), and any other context the bot was tracking.

4. **AC4: User Info Display** - Given a handoff conversation, When viewing conversation details, Then user info is displayed including: masked customer ID, conversation status. Note: order history count returns 0 for MVP (requires Shopify integration from Stories 4-1/4-2).

5. **AC5: Handoff Context** - Given a handoff conversation, When viewing conversation details, Then handoff context is displayed including: time since handoff was triggered (e.g., "Waiting 15 min"), handoff trigger reason (keyword/low_confidence/clarification_loop), and urgency level.

6. **AC6: Visual Message Distinction** - Given messages from both shopper and bot, When viewing the conversation, Then bot messages are visually distinct from shopper messages (different styling, alignment, or color).

## Tasks / Subtasks

| Task | AC Coverage | Description |
|------|-------------|-------------|
| Task 1 | AC1,2,3,4,5 | Backend - Conversation History API |
| Task 2 | AC2 | Backend - Message Metadata for Confidence |
| Task 3 | All | Frontend - Conversation History Service |
| Task 4 | AC1,2,6 | Frontend - Conversation History Page |
| Task 5 | AC3,4,5 | Frontend - Context Sidebar |
| Task 6 | All | Frontend - Navigation Integration |
| Task 7 | All | Update Error Codes |
| Task 8 | All | Create E2E Tests |
| Task 9 | All | Create Unit Tests |
| Task 10 | All | Create API Contract Tests |

- [x] **Task 1: Backend - Conversation History API** (AC: 1, 2, 3, 4, 5)
  - [x] Create `GET /api/conversations/{conversation_id}/history` endpoint in `backend/app/api/conversations.py`
  - [x] Add route param `conversation_id: int` with validation
  - [x] Create `ConversationHistoryResponse` schema in `backend/app/schemas/conversation.py` with fields:
    - `messages: List[MessageHistoryItem]` (sender, content, created_at, confidence_score for bot)
    - `context: ConversationContext` (cart_state, extracted_constraints)
    - `handoff: HandoffContext` (trigger_reason, triggered_at, urgency_level, wait_time_seconds)
    - `customer: CustomerInfo` (masked_id, order_count - return 0 for MVP)
  - [x] Add `get_conversation_history()` method to `ConversationService` in `backend/app/services/conversation/conversation_service.py`
  - [x] Query: Load conversation with messages (ordered by created_at ASC)
  - [x] **CRITICAL**: Always use `message.decrypted_content` for response, never `message.content` (customer messages are encrypted)
  - [x] Extract cart_state and constraints from `Conversation.conversation_data` (JSONB field)
  - [x] Join with `HandoffAlert` to get urgency_level
  - [x] **Wait Time Calculation**: `wait_time_seconds = (datetime.utcnow() - conversation.handoff_triggered_at).total_seconds()` - use real-time calculation, NOT `HandoffAlert.wait_time_seconds` (which is a snapshot)
  - [x] Return 404 with error code 7001 if conversation not found or doesn't belong to merchant
  - [x] Add unit tests in `backend/app/api/test_conversations.py`

- [x] **Task 2: Backend - Message Metadata for Confidence Scores** (AC: 2)
  - [x] Extract `confidence_score` from `Message.message_metadata` JSONB field
  - [x] **Expected JSON structure** for bot messages:
    ```json
    {
      "confidence_score": 0.85,
      "intent": "product_search",
      "entities": {...}
    }
    ```
  - [x] Return `confidence_score` in `MessageHistoryItem` for bot messages only
  - [x] Customer messages have `confidenceScore: null`

- [x] **Task 3: Frontend - Conversation History Service** (AC: All)
  - [x] Add `getConversationHistory(conversationId: number)` method to `frontend/src/services/conversations.ts`
  - [x] **Follow existing URLSearchParams pattern** from `getConversations()` method
  - [x] Add types to `frontend/src/types/conversation.ts`:
    - `ConversationHistoryResponse`
    - `MessageHistoryItem` (sender, content, createdAt, confidenceScore?)
    - `ConversationContext` (cartState, extractedConstraints)
    - `HandoffContext` (triggerReason, triggeredAt, urgencyLevel, waitTimeSeconds)
    - `CustomerInfo` (maskedId, orderCount)

- [x] **Task 4: Frontend - Conversation History Page** (AC: 1, 2, 6)
  - [x] Create `frontend/src/pages/ConversationHistory.tsx` - Main page component
  - [x] Implement message list with visual distinction:
    - Shopper messages: right-aligned, blue background
    - Bot messages: left-aligned, gray background, confidence badge
  - [x] Display confidence score badge on bot messages (e.g., "85%" or "Confidence: 0.85")
  - [x] Add chronological ordering (oldest at top, scroll to bottom)
  - [x] Add loading and error states
  - [x] Add `data-testid` attributes for E2E testing:
    - `conversation-history-page`
    - `message-list`
    - `message-bubble` (with `data-sender="customer|bot"`)
    - `confidence-badge`
  - [x] Create co-located unit tests in `frontend/src/pages/ConversationHistory.test.tsx` (covered by E2E tests)

- [x] **Task 5: Frontend - Context Sidebar** (AC: 3, 4, 5)
  - [x] Create `frontend/src/components/conversations/ContextSidebar.tsx`
  - [x] Display Customer Info section (masked ID, order count - will be 0)
  - [x] Display Handoff Context section:
    - Wait time (e.g., "Waiting 15 min")
    - Trigger reason with label mapping
    - Urgency badge (🔴/🟡/🟢)
  - [x] Display Bot Internal State section:
    - Cart contents (items, quantities if present)
    - Extracted constraints (budget, size, category)
  - [x] Handle empty/missing state gracefully
  - [x] Add `data-testid` attributes for E2E testing:
    - `context-sidebar`
    - `customer-info-section`
    - `handoff-context-section`
    - `bot-state-section`

- [x] **Task 6: Frontend - Navigation Integration** (AC: All)
  - [x] Update `HandoffQueueItem` in `HandoffQueue.tsx` - Add click handler to navigate to history page with state `{ from: '/handoff-queue' }`
  - [x] Update `ConversationCard` in `Conversations.tsx` - Add click handler to navigate to history page with state `{ from: '/conversations' }`
  - [x] Add route `/conversations/:conversationId/history` in `frontend/src/components/App.tsx`
  - [x] Add dynamic back navigation based on referrer (returns to Handoff Queue OR Conversations)
  - [x] Update `ConversationHistory.tsx` to use `useLocation` for smart back button

- [x] **Task 7: Update Error Codes** (AC: All)
  - [x] Add error code `7001` for `CONVERSATION_NOT_FOUND` in `backend/app/core/errors.py` (Conversation/Session team range: 7000-7999)
  - [x] Document in `docs/error-code-governance.md`:
    ```
    | 7001 | CONVERSATION_NOT_FOUND | Conversation does not exist or merchant lacks access |
    ```

- [x] **Task 8: Create E2E Tests** (AC: All)
  - [x] Create `frontend/tests/e2e/story-4-8-conversation-history.spec.ts`
  - [x] Test: Page loads with conversation history
  - [x] Test: Messages display in chronological order
  - [x] Test: Bot messages show confidence score
  - [x] Test: Shopper vs bot messages are visually distinct
  - [x] Test: Context sidebar shows handoff info
  - [x] Test: Navigation from HandoffQueue to ConversationHistory
  - [x] Test: Navigation from Conversations page to ConversationHistory
  - [x] Test: Back navigation returns to HandoffQueue when coming from queue
  - [x] Test: Back navigation returns to Conversations when coming from conversations
  - [x] Test: 404 handling for non-existent conversation

- [x] **Task 9: Create Unit Tests** (AC: All)
  - [x] Create `frontend/src/components/conversations/test_ContextSidebar.test.tsx` (34 tests)
    - Customer info display
    - Urgency badges (high/medium/low)
    - formatWaitTime edge cases (0s, 59s, 60s, 3599s, 3600s, 24h+)
    - Trigger reason labels
    - Cart state display
    - Constraints display
  - [x] Create `frontend/src/pages/test_ConversationHistory.test.tsx` (25 tests)
    - formatConfidence edge cases (0, 1, decimals, null, undefined)
    - Loading state
    - Error states
    - Not found state
    - Message rendering (customer vs bot)
    - Back navigation

- [x] **Task 10: Create API Contract Tests** (AC: All)
  - [x] Create `frontend/tests/api/story-4-8-conversation-history.spec.ts` (22 tests)
  - [x] Test: Authentication required
  - [x] Test: Response structure validation
  - [x] Test: Chronological order
  - [x] Test: Confidence scores for bot messages
  - [x] Test: Null confidence for customer messages
  - [x] Test: Context data (cart, constraints, customer)
  - [x] Test: Error handling (404, validation)

## Dev Notes

### State Strategy

Use local `useState` for single-page data. Do NOT add to store - history view is transient and doesn't need global state.

### API Design

**GET /api/conversations/{conversation_id}/history**

<details>
<summary>Response Schema (click to expand)</summary>

```json
{
  "data": {
    "conversationId": 123,
    "messages": [
      {
        "id": 1,
        "sender": "customer",
        "content": "I'm looking for running shoes",
        "createdAt": "2026-02-15T10:00:00Z",
        "confidenceScore": null
      },
      {
        "id": 2,
        "sender": "bot",
        "content": "Great! What's your budget?",
        "createdAt": "2026-02-15T10:00:05Z",
        "confidenceScore": 0.92
      }
    ],
    "context": {
      "cartState": {
        "items": [
          { "productId": "abc123", "name": "Nike Air Max", "quantity": 1 }
        ]
      },
      "extractedConstraints": {
        "budget": "$100-150",
        "category": "running shoes",
        "size": "10"
      }
    },
    "handoff": {
      "triggerReason": "low_confidence",
      "triggeredAt": "2026-02-15T10:05:00Z",
      "urgencyLevel": "medium",
      "waitTimeSeconds": 300
    },
    "customer": {
      "maskedId": "1234****",
      "orderCount": 0
    }
  },
  "meta": {
    "requestId": "uuid",
    "timestamp": "ISO-8601"
  }
}
```
</details>

### Message Encryption Notes

**CRITICAL**: Customer messages are encrypted at rest. Always use `decrypted_content`:

```python
# In Message model
@property
def decrypted_content(self) -> str:
    if self.sender == "customer":
        return decrypt_conversation_content(self.content)
    return self.content  # Bot messages stored in plaintext
```

When building the history response, always use `message.decrypted_content` not `message.content`.

### Conversation Context Extraction

The `Conversation.conversation_data` JSONB field stores bot internal state:

```json
{
  "cart": { "items": [...], "total": 129.99 },
  "constraints": { "budget": "$100-150", "size": "10", "category": "running" },
  "last_intent": "product_search",
  "user_input": "encrypted..."
}
```

Use `conversation.decrypted_metadata` to get decrypted version.

### Handoff Reason Labels

```typescript
const HANDOFF_REASON_LABELS: Record<string, string> = {
  keyword: 'Customer requested human help',
  low_confidence: 'Bot needed assistance',
  clarification_loop: 'Multiple clarification attempts',
};
```

### Frontend Component Structure

```
ConversationHistory.tsx (page)
├── MessageList.tsx (new component)
│   └── MessageBubble.tsx (shopper vs bot styling)
└── ContextSidebar.tsx (new component)
    ├── CustomerInfoSection.tsx
    ├── HandoffContextSection.tsx
    └── BotStateSection.tsx
```

### Story 4-7 Learnings

Apply these fixes from previous story implementation:
- **Python 3.9/3.11 Compatibility**: Use `datetime.timezone.utc` not `datetime.UTC`
- **Model Registration**: `HandoffAlert` already registered in `models/__init__.py`
- **Component Navigation**: Use `HandoffQueueItem` in `HandoffQueue.tsx`, not `ConversationCard.tsx` (doesn't exist)

### Testing Patterns

Follow existing test patterns from Story 4-7:
- Unit tests co-located with source files
- API tests in `frontend/tests/api/`
- E2E tests in `frontend/tests/e2e/`
- Use `data-testid` attributes for E2E selectors

### Source Tree Components to Touch

```
backend/
├── app/
│   ├── api/
│   │   └── conversations.py            # MODIFIED: Add GET /{id}/history
│   │   └── test_conversations.py       # MODIFIED: Add history endpoint tests
│   ├── core/
│   │   └── errors.py                   # MODIFIED: Add error code 7001
│   ├── schemas/
│   │   └── conversation.py             # MODIFIED: Add history response schemas
│   └── services/conversation/
│       └── conversation_service.py     # MODIFIED: Add get_conversation_history()

frontend/
├── src/
│   ├── pages/
│   │   └── ConversationHistory.tsx     # NEW: History page
│   │   └── test_ConversationHistory.test.tsx # NEW: Unit tests (25 tests)
│   ├── components/conversations/
│   │   └── ContextSidebar.tsx          # NEW: Context display component
│   │   └── test_ContextSidebar.test.tsx # NEW: Unit tests (34 tests)
│   ├── pages/
│   │   └── HandoffQueue.tsx            # MODIFIED: Add click handler to HandoffQueueItem
│   ├── services/
│   │   └── conversations.ts            # MODIFIED: Add getConversationHistory
│   ├── types/
│   │   └── conversation.ts             # MODIFIED: Add history types
│   └── components/
│       └── App.tsx                     # MODIFIED: Add route
├── tests/
│   ├── e2e/
│   │   └── story-4-8-conversation-history.spec.ts  # NEW: E2E tests (10 tests)
│   └── api/
│       └── story-4-8-conversation-history.spec.ts  # NEW: API tests (22 tests)

docs/
└── error-code-governance.md             # MODIFIED: Document error code 7001
```

### Testing Standards

| Test Type | Location | Tests | Coverage Target |
|-----------|----------|-------|-----------------|
| Backend Unit | `backend/app/api/test_conversations.py` | 9 | History endpoint, 404 handling, encryption |
| Frontend Unit | `frontend/src/pages/test_ConversationHistory.test.tsx` | 25 | Page rendering, loading states, formatConfidence |
| Frontend Unit | `frontend/src/components/conversations/test_ContextSidebar.test.tsx` | 34 | Sidebar rendering, formatWaitTime edge cases |
| API | `frontend/tests/api/story-4-8-conversation-history.spec.ts` | 22 | API contract tests |
| E2E | `frontend/tests/e2e/story-4-8-conversation-history.spec.ts` | 10 | AC 1-6 |

### Dependencies

| Dependency | Story | Status |
|------------|-------|--------|
| Human Assistance Detection | Story 4-5 | ✅ Done |
| Handoff Queue with Urgency | Story 4-7 | ✅ Done |
| Conversation Model | Epic 1 | ✅ Done |
| Message Model | Epic 1 | ✅ Done |

### Project Structure Notes

- Follow existing API patterns from `handoff_alerts.py` for response envelope
- Use Pydantic `alias_generator=to_camel` for API field naming
- Co-locate unit tests with components

### References

- `backend/app/models/conversation.py` - Conversation model with conversation_data
- `backend/app/models/message.py` - Message model with decrypted_content
- `backend/app/models/handoff_alert.py` - HandoffAlert model
- `backend/app/services/conversation/conversation_service.py` - Service patterns
- `frontend/src/services/conversations.ts` - URLSearchParams pattern
- `frontend/src/pages/HandoffQueue.tsx` - Page patterns, HandoffQueueItem component

## Dev Agent Record

### Agent Model Used

zai-coding-plan/glm-5

### Debug Log References

None

### Completion Notes List

- Backend API implemented with 9/9 tests passing
- Frontend types, service, and components created
- Navigation from HandoffQueue to ConversationHistory working
- **Navigation from Conversations page to ConversationHistory working** (added 2026-02-15)
- **Dynamic back navigation** - returns to referrer page (HandoffQueue or Conversations) (added 2026-02-15)
- Error code 7001 documented in governance file
- E2E tests created with 11 test cases (updated 2026-02-15)
- Unit tests added for ContextSidebar (34 tests) - edge cases for formatting functions
- Unit tests added for ConversationHistory (25 tests) - formatConfidence edge cases, states
- API contract tests added (22 tests) - endpoint validation, error handling

### File List

**Backend (Modified):**
- `backend/app/api/conversations.py` - Added GET /{conversation_id}/history endpoint
- `backend/app/schemas/conversation.py` - Added history response schemas
- `backend/app/services/conversation/conversation_service.py` - Added get_conversation_history()
- `backend/app/api/test_conversations.py` - Added 9 new tests for history endpoint
- `backend/app/conftest.py` - Added fixtures for conversation history tests
- `backend/tests/conftest.py` - Fixed duplicate fixtures
- `docs/error-code-governance.md` - Updated error code 7001 description

**Frontend (New/Modified):**
- `frontend/src/pages/ConversationHistory.tsx` - NEW: History page with dynamic back navigation
- `frontend/src/components/conversations/ContextSidebar.tsx` - NEW: Context sidebar
- `frontend/src/components/conversations/ConversationCard.tsx` - MODIFIED: Added data-testid and click handler
- `frontend/src/services/conversations.ts` - MODIFIED: Added getConversationHistory
- `frontend/src/types/conversation.ts` - MODIFIED: Added history types
- `frontend/src/pages/HandoffQueue.tsx` - MODIFIED: Added click to navigate to history with state
- `frontend/src/pages/Conversations.tsx` - MODIFIED: Added click handler to navigate to history with state
- `frontend/src/components/App.tsx` - MODIFIED: Added route for history page
- `frontend/tests/e2e/story-4-8-conversation-history.spec.ts` - NEW: E2E tests (11 tests)

**Frontend Tests (Added 2026-02-15):**
- `frontend/src/components/conversations/test_ContextSidebar.test.tsx` - NEW: Unit tests (34 tests)
- `frontend/src/pages/test_ConversationHistory.test.tsx` - NEW: Unit tests (25 tests)
- `frontend/tests/api/story-4-8-conversation-history.spec.ts` - NEW: API contract tests (22 tests)

## Test Coverage Summary

| Test Level | File | Count | Status |
|------------|------|-------|--------|
| Backend Unit | `test_conversations.py` | 9 | ✅ Passing |
| Frontend Unit | `test_ContextSidebar.test.tsx` | 34 | ✅ Passing |
| Frontend Unit | `test_ConversationHistory.test.tsx` | 25 | ✅ Passing |
| API Contract | `tests/api/story-4-8-*.spec.ts` | 22 | ✅ Created |
| E2E | `tests/e2e/story-4-8-*.spec.ts` | 11 | ✅ Passing |
| **Total** | | **101** | ✅ |

## Changelog

### 2026-02-15 - Extended Navigation Support
- **Feature**: Added ability to view conversation history from Conversations page (not just Handoff Queue)
- **UX**: Dynamic back button returns to referrer page (Handoff Queue or Conversations)
- **Tests**: Added 2 new E2E tests for navigation from Conversations page and back button behavior
- **Files Modified**:
  - `Conversations.tsx` - Added navigate with state
  - `ConversationHistory.tsx` - Added useLocation for dynamic back destination
  - `HandoffQueue.tsx` - Pass location state on navigate
  - `ConversationCard.tsx` - Added data-testid

### 2026-03-10 - Dynamic Updates for Conversation History
- **Feature**: Added a 10-second background polling mechanism via `setInterval` in `ConversationHistory.tsx`.
- **UX**: Customer information, handoff context, and bot state update dynamically without a hard page refresh, allowing merchants to observe real-time changes without losing their current place or typing focus.
- **Fix**: Resolved `no-unsafe-finally` and `no-useless-catch` TypeScript linter errors within the data fetching logic to ensure clean unmounting.
