# Story 11.3: Frontend Stream Consumer

**Workflow:** TEA Automate (BMad-Integrated Mode) + Implementation
**Story:** 11-3-frontend-stream-consumer (Beads: shop-gj8v)
**Coverage Target:** critical-paths
**Framework:** Playwright 1.58.2 (E2E)
**Status:** Complete (TDD + Implementation)

---

## Execution Summary

| Metric | Value |
|--------|-------|
| Total E2E tests | **10** |
| New test files | 2 |
| Support files | 1 (streaming-test-helpers.ts) |
| Modified source files | 6 |
| Created source files | 1 (StreamingIndicator.tsx) |
| Lint | Clean (0 new errors) |
| Typecheck | Clean (0 new errors) |

---

## Phase 1: TDD Contract Tests

### Frontend — E2E Tests (10 tests)

| File | Tests | Priority | Coverage |
|------|-------|----------|----------|
| `frontend/tests/e2e/story-11-3-streaming-message-flow.spec.ts` | 5 | P0/P1/P2 | Happy path streaming, field preservation, stream replacement, sequential streams, indicator visibility |
| `frontend/tests/e2e/story-11-3-streaming-error-fallback.spec.ts` | 5 | P1/P2 | Mid-stream error, REST fallback, REST field preservation, reconnect, multi-turn mixed streaming |

### Support Files

| File | Purpose |
|------|---------|
| `frontend/tests/helpers/streaming-test-helpers.ts` | Streaming test utilities: `StreamingMessageBuilder`, `mockStreamingWebSocket()`, `simulateStreamingResponse()`, `waitForStreamingStart/Token/End()`, `mockWebSocketStream()`, `mockWebSocketFailure()`, `mockWebSocketReconnect()`, `STREAM_EVENTS` constants |

### Modified Test Files

| File | Change |
|------|--------|
| `frontend/tests/helpers/widget-test-helpers.ts` | Added `sources` and `quick_replies` fields to `MockMessageResponse` interface |

---

## Phase 2: Implementation

### Source Files Modified

| File | Changes |
|------|---------|
| `frontend/src/widget/types/widget.ts` | Added `isStreaming`, `streamingMessageId`, `streamingContent`, `streamingError` to `WidgetState`; added `isStreaming?` to `WidgetMessage`; added 4 action types: `START_STREAMING`, `UPDATE_STREAMING_MESSAGE`, `FINISH_STREAMING_MESSAGE`, `STREAMING_ERROR` |
| `frontend/src/widget/api/widgetWsClient.ts` | Added `'bot_stream_start' \| 'bot_stream_token' \| 'bot_stream_end' \| 'bot_stream_error'` to `WSMessageEvent.type` union |
| `frontend/src/widget/context/WidgetContext.tsx` | Added streaming fields to `initialState`; added 4 streaming reducer cases; added streaming WS event handlers in `onMessage` callback; modified `sendMessage` to send `streaming: 'true'` when WS connected, falling back to REST otherwise |
| `frontend/src/widget/api/widgetClient.ts` | Updated `sendMessage` to accept optional `options?: { streaming?: string }` parameter |
| `frontend/src/widget/components/MessageList.tsx` | Restored corrupted `MessageBubbleInGroupProps` interface; added `data-testid="streaming-message"` with `data-streaming` attribute and streaming box-shadow styling |
| `frontend/src/widget/components/ChatWindow.tsx` | Added `isStreaming?` and `streamingError?` props; imported and rendered `StreamingIndicator` and `StreamErrorIndicator` |
| `frontend/src/widget/Widget.tsx` | Passed `state.isStreaming` and `state.streamingError` to `ChatWindow`; added `@keyframes streaming-pulse` CSS animation |

### Source Files Created

| File | Purpose |
|------|---------|
| `frontend/src/widget/components/StreamingIndicator.tsx` | `StreamingIndicator` (pulsing dot + "streaming..." text, `data-testid="streaming-indicator"`) and `StreamErrorIndicator` (error message, `data-testid="stream-error-indicator"`) |

---

## Data Flow

```
User sends message
    │
    ▼
WidgetContext.sendMessage()
    │
    ├── connectionStatus === 'connected'?
    │   │
    │   ├── YES → widgetClient.sendMessage(content, sessionId, { streaming: 'true' })
    │   │           Backend routes to process_message_streaming()
    │   │           WebSocket events flow back:
    │   │
    │   │   bot_stream_start → dispatch START_STREAMING
    │   │   bot_stream_token → dispatch UPDATE_STREAMING_MESSAGE (×N)
    │   │   bot_stream_end   → dispatch FINISH_STREAMING_MESSAGE
    │   │   bot_stream_error → dispatch STREAMING_ERROR
    │   │
    │   └── NO  → widgetClient.sendMessage(content, sessionId) [REST fallback]
    │
    ▼
WidgetState
    │ isStreaming: boolean
    │ streamingMessageId: string | null
    │ streamingContent: string
    │ streamingError: string | null
    │
    ▼
Widget.tsx → ChatWindow.tsx
    │
    ├── StreamingIndicator (isStreaming=true → pulsing dot)
    ├── StreamErrorIndicator (streamingError → error banner)
    └── MessageList.tsx → MessageBubbleInGroup
        ├── data-testid="streaming-message" (when message.isStreaming)
        ├── data-testid="message-bubble" (when not streaming)
        └── data-streaming="true" attribute
```

---

## Test Case Inventory

### Happy Path (story-11-3-streaming-message-flow.spec.ts)

| Test ID | Priority | Description |
|---------|----------|-------------|
| 11.3-E2E-001 | P0 | Streaming message displays token-by-token then finalizes |
| 11.3-E2E-002 | P1 | Streaming response preserves products, sources, and quick replies |
| 11.3-E2E-003 | P1 | New streaming message replaces active stream content |
| 11.3-E2E-004 | P2 | Sequential streaming messages display in order |
| 11.3-E2E-005 | P1 | Streaming indicator appears during active stream |

### Error Handling & Fallback (story-11-3-streaming-error-fallback.spec.ts)

| Test ID | Priority | Description |
|---------|----------|-------------|
| 11.3-E2E-006 | P1 | Streaming error mid-stream shows error message |
| 11.3-E2E-007 | P1 | Fallback to REST when WebSocket unavailable |
| 11.3-E2E-008 | P1 | Fallback to REST preserves all message fields |
| 11.3-E2E-009 | P2 | Streaming reconnects after temporary disconnect |
| 11.3-E2E-010 | P2 | Multi-turn conversation with streaming errors |

---

## Priority Breakdown

| Priority | Tests | Total |
|----------|-------|-------|
| P0 (Critical) | 1 | 1 |
| P1 (High) | 6 | 6 |
| P2 (Medium) | 3 | 3 |
| **Total** | **10** | **10** |

---

## Backend Streaming Protocol Reference

```
bot_stream_start → { type, data: { messageId, sender: "bot", createdAt } }
bot_stream_token → { type, data: { messageId, token } }
bot_stream_end   → { type, data: { messageId, content, createdAt, products?, sources?, suggestedReplies?, quick_replies?, contactOptions?, consent_prompt_required?, cart?, checkout_url? } }
bot_stream_error → { type, data: { messageId, error } }
```

---

## Test Execution Commands

```bash
cd frontend

# Story 11.3 E2E tests
npx playwright test --grep "Story 11.3"

# Specific test files
npx playwright test tests/e2e/story-11-3-streaming-message-flow.spec.ts
npx playwright test tests/e2e/story-11-3-streaming-error-fallback.spec.ts

# P0 only
npx playwright test --grep "\[P0\].*11\.3"
```

---

## Key Design Decisions

1. **REST fallback**: `sendMessage()` checks `connectionStatus === 'connected'` before adding `streaming: 'true'` flag. When WS is unavailable, the existing REST flow is used unchanged.
2. **Streaming indicator placement**: Rendered in `ChatWindow` after `TypingIndicator`, separate from message bubbles. This avoids re-rendering the entire message list on each token.
3. **Streaming message styling**: Uses `data-testid="streaming-message"` with subtle inset box-shadow (`theme.primaryColor` at 40% opacity) to visually distinguish streaming messages.
4. **Animation**: `streaming-pulse` keyframe animates the indicator dot opacity (1 → 0.3 → 1) rather than scale, avoiding layout shifts.
5. **Message bubble corruption fix**: Restored `MessageBubbleInGroupProps` interface that had lost `onAddToCart`, `onProductClick`, `onRemoveFromCart`, `onCheckout`, `addingProductId`, `removingItemId`, `isCheckingOut` props from a failed previous edit.

---

## Validation Results

| Check | Result |
|-------|--------|
| TypeScript (`tsc --noEmit`) | 0 new errors (all widget errors pre-existing) |
| ESLint | 0 new errors (1 pre-existing: `ContactOption` unused import) |
| E2E tests compile | Clean |

### Pre-existing Issues (NOT from this story)
- `WidgetContext.tsx`: `getOrCreateVisitorId`, `getCachedMessages` unused imports; `getSession` unused; `getHistory` doesn't exist; `session` vs `sessionId` typo
- `MessageList.tsx`: `ContactOption` unused import
- `Widget.tsx`: `FAQQuickButton` type not imported (used in `handleFaqButtonClick`)

---

## Discoveries

1. **Previous session left MessageList.tsx corrupted**: A failed edit at the end of the previous conversation corrupted `MessageBubbleInGroup` (lines 398-432) with malformed CSS strings like `'box-shadow': 'inset 0 0px 3px dashed #1px solid...'`. Fixed by restoring from git history (`36365d8b`).
2. **`MessageBubbleInGroupProps` had lost 7 props**: The interface was missing `onAddToCart`, `onProductClick`, `onRemoveFromCart`, `onCheckout`, `addingProductId`, `removingItemId`, `isCheckingOut`. Restored from git history.
3. **`MockMessageResponse` was missing fields**: Added `sources` and `quick_replies` to support streaming end-event field verification.
4. **Streaming state already in types**: The previous session had already added `isStreaming`, `streamingMessageId`, `streamingContent`, `streamingError` to `WidgetState` and the 4 action types to `WidgetAction`.
5. **WS handlers already in WidgetContext**: The previous session had already added streaming reducer cases and WS event handlers in the `onMessage` callback.

---

## Change Log

| Date | Change | Files |
|------|--------|-------|
| 2026-04-01 | Phase 1: TDD contract tests — 10 E2E tests, streaming helpers | streaming-message-flow.spec.ts, streaming-error-fallback.spec.ts, streaming-test-helpers.ts, widget-test-helpers.ts |
| 2026-04-02 | Phase 2: Fixed corrupted MessageList.tsx, restored missing props | MessageList.tsx |
| 2026-04-02 | Phase 2: Created StreamingIndicator component | StreamingIndicator.tsx |
| 2026-04-02 | Phase 2: Updated ChatWindow with streaming indicators | ChatWindow.tsx |
| 2026-04-02 | Phase 2: Updated Widget to pass streaming state | Widget.tsx |
| 2026-04-02 | Phase 2: Added streaming-pulse CSS keyframe | Widget.tsx |
| 2026-04-02 | Party-mode review: Fixed messageId mismatch in 4 test files | streaming-error-fallback.spec.ts, streaming-message-flow.spec.ts |
| 2026-04-02 | Party-mode review: Replaced waitForTimeout with event-based waits in tests 009, 010 | streaming-error-fallback.spec.ts |
| 2026-04-02 | Party-mode review: Fixed STREAMING_ERROR reducer state leak | WidgetContext.tsx |
| 2026-04-02 | Party-mode review: Refactored test 010 to use mockMultiTurnConversation | streaming-error-fallback.spec.ts, streaming-test-helpers.ts |
| 2026-04-02 | Party-mode review: console.warn → console.debug in WS client | widgetWsClient.ts |
| 2026-04-02 | Party-mode review: Fixed refuseAfterTurnCount → refuseAfter parameter name | streaming-error-fallback.spec.ts |
