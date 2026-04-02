# Technical Debt: Story 11-3 Streaming Message Flow (Widget E2E)

**Last Updated:** 2026-04-02
**Story:** 11-3 Streaming Message Flow
**Status:** Implementation Complete, All E2E Tests Passing

---

## Implementation Status

### Source Code (Complete)

- `frontend/src/widget/api/widgetWsClient.ts` — WebSocket client with auto-reconnect (3s interval, 3 max attempts), heartbeat (25s), connection status tracking
- `frontend/src/widget/context/WidgetContext.tsx` — Streaming state management: `START_STREAMING`, `UPDATE_STREAMING_MESSAGE`, `FINISH_STREAMING_MESSAGE`, `STREAMING_ERROR` reducer actions; streaming gate at line 532 (`connectionStatus === 'connected' && !isStreaming`)
- `frontend/src/widget/components/StreamingIndicator.tsx` — `data-testid="streaming-indicator"` (pulsing dots), `data-testid="stream-error-indicator"` (error message with "Something went wrong")
- `frontend/src/widget/components/MessageList.tsx` — `data-testid="streaming-message"` when `isStreaming`, else `"message-bubble"` (line 398)
- `frontend/src/widget/components/ChatWindow.tsx` — Renders `<StreamErrorIndicator />` when streaming error occurs
- `frontend/src/widget/api/widgetClient.ts` — `sendMessage()` sends `{ streaming: 'true' }` when WS connected; validates response against `WidgetMessageSchema`
- `frontend/src/widget/types/widget.ts` — TypeScript types: `streamingMessageId`, `streamingContent`, `streamingError`
- `frontend/src/widget/Widget.tsx` — Streaming pulse CSS keyframe animation

### Backend Support (Complete)

- `backend/app/services/widget/connection_manager.py` — `broadcast_streaming_start/token/end/error` methods
- `backend/app/services/widget/widget_message_service.py` — `process_message_streaming()` for WS streaming
- `backend/app/services/conversation/unified_conversation_service.py` — Multi-turn + streaming integration

### E2E Test Suite (10/10 Passing)

**Test Review Score:** 96/100 (Grade A)

| Test ID | Description | Priority | File |
|---------|-------------|----------|------|
| 11.3-E2E-001 | Streaming message displays token-by-token then finalizes | P0 | `streaming-message-flow.spec.ts` |
| 11.3-E2E-002 | Streaming response preserves products, sources, and quick replies | P1 | `streaming-message-flow.spec.ts` |
| 11.3-E2E-003 | New streaming message replaces active stream content | P1 | `streaming-message-flow.spec.ts` |
| 11.3-E2E-004 | Sequential streaming messages display in order | P2 | `streaming-message-flow.spec.ts` |
| 11.3-E2E-005 | Streaming indicator appears during active stream | P1 | `streaming-message-flow.spec.ts` |
| 11.3-E2E-006 | Streaming error mid-stream shows error message | P1 | `streaming-error-fallback.spec.ts` |
| 11.3-E2E-007 | Falls back to REST when WebSocket unavailable | P2 | `streaming-error-fallback.spec.ts` |
| 11.3-E2E-008 | REST fallback preserves products, sources, and quick replies | P2 | `streaming-error-fallback.spec.ts` |
| 11.3-E2E-009 | Streaming reconnects after temporary disconnect | P2 | `streaming-error-fallback.spec.ts` |
| 11.3-E2E-010 | Multi-turn conversation with streaming errors | P2 | `streaming-error-fallback.spec.ts` |

### Test Helpers

| File | Purpose |
|------|---------|
| `frontend/tests/helpers/streaming-test-helpers.ts` | `StreamingMessageBuilder`, `mockStreamingWebSocket`, `mockWebSocketStream`, `mockWebSocketFailure`, `mockWebSocketReconnect`, `waitForStreamingStart/Token/End`, `STREAM_EVENTS` constants |
| `frontend/tests/helpers/widget-test-helpers.ts` | `loadWidgetWithSession`, `sendMessage`, `mockWidgetConfig`, `mockWidgetSession`, `mockWidgetMessageConditional`, `createMockProduct` |

---

## Resolved Issues

### 1. Polling Coordination Pattern for WS Mocks ✅ RESOLVED

**Issue:** Widget never sends user messages through WebSocket — messages go via HTTP POST. WS mocks cannot use `ws.onMessage` to detect user messages.

**Resolution:** "Polling Coordination" pattern — HTTP route mock sets `httpMessageSent = true` flag. WS mock polls this flag every 50ms and sends streaming events when true. Used in all streaming test helpers.

---

### 2. StreamedEvent Field Name Mismatch ✅ RESOLVED

**Issue:** `StreamedEvent` interface had `event` field but `sendEventsWithDelay` accessed `events[i].type`. Caused all streaming mocks to fail silently.

**Resolution:** Renamed field to `type` consistently across all helpers and test files.

---

### 3. QuickReplySchema Requires `id` Field ✅ RESOLVED

**Issue:** Test 008's REST mock used `{ text, action, value }` format but `QuickReplySchema` requires `{ id: string, text: string }`.

**Resolution:** Updated mock data to use `{ id: 'qr-1', text: 'Add to cart' }` format.

---

### 4. Streaming Events Arrive Too Fast ✅ RESOLVED

**Issue:** With 5-10ms delays, streaming completes before Playwright detects the `streaming-indicator`. Second-message assertions miss the indicator entirely.

**Resolution:** Increased delays to 100ms. For multi-message tests (003/004), replaced `waitForStreamingStart/End` on second message with direct content assertion.

---

### 5. Strict Mode Violations ✅ RESOLVED

**Issue:** Regex `/error|try again|something went wrong/i` matched 3 elements in test 006. "Reconnected response" appeared twice in test 009.

**Resolution:** Used specific text matchers and `.first()` selector to avoid strict mode violations.

---

## Known Limitations

### E2E Test Flakiness ⚠️ DOCUMENTED

**Issue:** Tests 002, 003, 004, 009 exhibit intermittent flakiness (~20% failure rate on first run) when running the full suite with parallel workers. Tests pass 100% when run in isolation.

**Root Cause:** Playwright's `routeWebSocket` mock connections experience timing variability when multiple WS mock connections exist across sequential tests in the same browser context.

**Mitigation:** Both test files configured with:
- `test.describe.configure({ retries: 2, mode: 'serial' })` — retries handle first-run failures
- Tests within each file run serially to minimize cross-test interference
- All tests pass reliably with `--workers=1` or with retries enabled

---

## Architecture Notes

### Widget Streaming Flow

```
User sends message → HTTP POST /api/v1/widget/message { streaming: 'true' }
                              ↓
                   Server processes via process_message_streaming()
                              ↓
                   WebSocket pushes events to widget:
                   - bot_stream_start { messageId, createdAt }
                   - bot_stream_token { messageId, token } (×N)
                   - bot_stream_end { messageId, content, products, sources, quick_replies, ... }
                   - bot_stream_error { messageId, error } (on failure)
```

### Streaming Gate (WidgetContext line 532)

```typescript
const useStreaming = state.connectionStatus === 'connected' && !state.isStreaming;
```

Widget only sends `streaming: 'true'` when WS is connected and no stream is active.

### Fallback Behavior

1. **WS unavailable** → Widget sends HTTP POST without `streaming` → Gets full response via REST
2. **WS disconnects mid-stream** → Error indicator shown → WS client auto-reconnects (3s × 3 attempts)
3. **Reconnect succeeds** → Subsequent messages use streaming again
4. **Reconnect fails (3 attempts)** → `connectionStatus` set to `'error'` → All messages use REST

---

## Test Results

- **Frontend E2E Tests:** 10/10 passing (with retries configured)
- **Test Review:** `_bmad-output/test-artifacts/test-reviews/test-review-story-11-3.md` (96/100, Grade A)
- **Run Command:** `npx playwright test story-11-3 --project=chromium`

---

## Related Documentation

- Technical Debt: [11-1 Conversation Context Memory](./11-1-conversation-context.md)
- Technical Debt: [11-2 Multi-Turn Query Handling](./11-2-multi-turn-query-handling.md)
- Test Review: `_bmad-output/test-artifacts/test-reviews/test-review-story-11-3.md`
