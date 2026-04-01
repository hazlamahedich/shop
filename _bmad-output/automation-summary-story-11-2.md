# Test Automation Summary — Story 11.2: Multi-Turn Query Handling

**Workflow:** TEA Automate (BMad-Integrated Mode)
**Story:** 11-2-multi-turn-query-handling
**Coverage Target:** critical-paths
**Framework:** Playwright (E2E) + pytest (Backend)
**Status:** Complete (including P2 follow-ups)

---

## Execution Summary

| Metric | Value |
|--------|-------|
| Total new backend tests | **93** (all passing) |
| Total new E2E tests | **7** (require running frontend) |
| New test files | 10 |
| Support files | 1 (multi-turn-test-helpers.ts) |
| Backend validation | 93/93 passing |
| Existing test regression | 117/117 passing |
| Full multi-turn suite | **210 passing** (117 existing + 93 new) |
| Total including E2E | **217** |

---

## Files Created

### Backend — Unit Tests (66 tests)

| File | Tests | Priority | Coverage |
|------|-------|----------|----------|
| `backend/tests/unit/test_conversation_lock.py` | 15 | P0 | TTL cleanup, singleton, active_lock_count, concurrent access |
| `backend/tests/unit/test_state_machine_complete_transitions.py` | 13 | P1 | COMPLETE->IDLE, COMPLETE->CLARIFYING, full cycle |
| `backend/tests/unit/test_message_classifier_llm_success.py` | 16 | P1 | LLM high-confidence, threshold boundary, label mapping, exception handling |
| `backend/tests/unit/test_topic_change_edge_cases.py` | 22 | P2 | Empty/Unicode/emoji inputs, long messages, boundary conditions |

### Backend — API Tests (9 tests)

| File | Tests | Priority | Coverage |
|------|-------|----------|----------|
| `backend/tests/api/test_multi_turn_api_http.py` | 9 | P2 | HTTP-level GET/POST debug endpoints, auth, envelope, 404s |

### Backend — Integration Tests (18 tests)

| File | Tests | Priority | Coverage |
|------|-------|----------|----------|
| `backend/tests/integration/test_multi_turn_orchestration.py` | 11 | P0 | `_check_multi_turn_state()` orchestration path |
| `backend/tests/integration/test_concurrent_multi_turn.py` | 7 | P2 | Lock serialization, parallel conversations, high concurrency, state machine under lock |

### Frontend — E2E Tests (7 tests)

| File | Tests | Priority | Coverage |
|------|-------|----------|----------|
| `frontend/tests/e2e/story-11-2-multi-turn-clarification.spec.ts` | 5 | P0/P1/P2 | AC1: clarification flow, AC6: topic change, AC5: invalid re-prompt, AC4: turn limit |
| `frontend/tests/e2e/story-11-2-multi-turn-general-mode.spec.ts` | 2 | P2 | AC7: general mode flow, AC9: general mode topic change |

### Support Files

| File | Purpose |
|------|---------|
| `frontend/tests/helpers/multi-turn-test-helpers.ts` | Multi-turn mock helpers, conditional response routing, conversation handlers |

---

## Priority Breakdown

| Priority | Backend Tests | E2E Tests | Total |
|----------|--------------|-----------|-------|
| P0 (Critical) | 26 | 2 | 28 |
| P1 (High) | 29 | 2 | 31 |
| P2 (Medium) | 38 | 3 | 41 |
| **Total** | **93** | **7** | **100** |

---

## Acceptance Criteria Coverage

| AC | Description | Test Level | Status |
|----|-------------|------------|--------|
| AC1 | Multi-turn clarification flow | E2E + Integration | Covered |
| AC2 | Constraint accumulation | Unit (existing) | Covered |
| AC3 | Turn limit enforcement | E2E + Unit (existing) | Covered |
| AC4 | Max turns shows best-effort results | E2E + Integration | Covered |
| AC5 | Invalid response re-prompt | E2E + Integration | Covered |
| AC6 | Topic change resets state | E2E + Integration | Covered |
| AC7 | General mode clarification | E2E + Integration | Covered |
| AC8 | Mode-aware questions | Unit (existing) | Covered |
| AC9 | General mode topic change | E2E | Covered |
| AC10 | LLM + heuristic fallback | Unit (new + existing) | Covered |

---

## Coverage Gaps Filled

| Gap | Priority | Resolution |
|-----|----------|------------|
| Zero E2E tests | P0 | 7 E2E tests across ecommerce + general mode |
| No `_check_multi_turn_state()` orchestration test | P0 | 11 integration tests covering all branches |
| No `conversation_lock.py` unit tests | P0 | 15 unit tests covering TTL, singleton, concurrency |
| No COMPLETE state transition tests | P1 | 13 unit tests for COMPLETE->{IDLE, CLARIFYING} |
| No LLM success path tests | P1 | 16 unit tests for confidence threshold, label mapping |
| No general mode E2E flow | P2 | 2 E2E tests for general mode |
| No HTTP-level debug endpoint tests | P2 | 9 API tests through FastAPI ASGI transport |
| No edge case tests for `_is_topic_change()` | P2 | 22 unit tests for empty/Unicode/emoji/boundary |
| No concurrent state consistency tests | P2 | 7 integration tests for lock serialization + parallel |

---

## Test Execution Commands

### Backend (all passing)
```bash
cd backend
source venv/bin/activate

# All new tests
python -m pytest tests/unit/test_conversation_lock.py \
  tests/unit/test_state_machine_complete_transitions.py \
  tests/unit/test_message_classifier_llm_success.py \
  tests/unit/test_topic_change_edge_cases.py \
  tests/api/test_multi_turn_api_http.py \
  tests/integration/test_multi_turn_orchestration.py \
  tests/integration/test_concurrent_multi_turn.py -v

# All multi-turn tests (existing + new) — 210 total
python -m pytest tests/unit/test_multi_turn*.py \
  tests/unit/test_constraint_accumulator.py \
  tests/unit/test_message_classifier*.py \
  tests/unit/test_topic_change_edge_cases.py \
  tests/unit/test_conversation_lock.py \
  tests/api/test_multi_turn_api.py \
  tests/api/test_multi_turn_api_http.py \
  tests/integration/test_multi_turn*.py \
  tests/integration/test_concurrent_multi_turn.py -v
```

### Frontend E2E (requires running frontend)
```bash
cd frontend

# Story 11.2 E2E tests
npx playwright test --grep "Story 11.2"

# Specific test files
npx playwright test tests/e2e/story-11-2-multi-turn-clarification.spec.ts
npx playwright test tests/e2e/story-11-2-multi-turn-general-mode.spec.ts
```

---

## Key Assumptions and Risks

1. **E2E tests require running frontend/backend**: Tests use `page.route()` to mock API responses, so they don't need real backend, but need the frontend dev server running.
2. **Widget selectors**: E2E tests use `getByRole('button', { name: 'Open chat' })` and `getByRole('dialog', { name: 'Chat window' })` — if widget component changes these labels, tests will need updating.
3. **Orchestration tests use mock objects**: The `_check_multi_turn_state()` integration tests mock the service instance directly rather than going through HTTP. This tests the logic path but not the HTTP layer.
4. **LLM classifier tests use mock LLM**: No real LLM calls are made in tests — the mock returns configurable results to test classification logic.
5. **HTTP API tests note**: The `Conversation` model has no `context` field; the multi-turn debug API uses `hasattr(conversation, "context")` which is always False for real DB conversations. The HTTP tests verify the actual behavior (returns IDLE defaults, no crash).
6. **Streaming tests**: WebSocket streaming uses simulated character-by-character chunking (30ms intervals). No real WS connection in unit tests; streaming behavior tested via mock broadcast methods.

---

## Discoveries During Testing

1. **API envelope uses camelCase**: The `MinimalEnvelope` meta field serializes as `requestId` (not `request_id`). HTTP tests use the correct camelCase key.
2. **`_is_topic_change()` stop word list**: Limited to English stop words; Unicode/emoji inputs fall through keyword analysis gracefully.
3. **ConversationLockManager with `ttl_seconds=0`**: Expired locks are cleaned up on the next `get_lock()` call; held (locked) locks are never cleaned even if TTL expired.

---

## Tech Debt Resolution Additions (2026-04-01)

The following infrastructure was added after the initial automation pass to address tech debt from a Party Mode review:

### New Infrastructure

| Component | File | Purpose |
|-----------|------|---------|
| `process_message_streaming()` | `backend/app/services/widget/widget_message_service.py` | WebSocket streaming for multi-turn responses |
| Streaming broadcast methods | `backend/app/services/widget/connection_manager.py` | `broadcast_streaming_start/token/end/error` |
| `streaming` field | `backend/app/schemas/widget.py` | `SendMessageRequest` streaming flag |
| Streaming API route | `backend/app/api/widget.py` | Routes to streaming handler when `streaming=true` |
| `MultiTurnStateAdapter` | `backend/app/services/multi_turn/state_persistence.py` | Decouples state machine from JSONB persistence |
| CI workflow | `.github/workflows/story-11-2-e2e-tests.yml` | Automated test pipeline |
| Streaming WS actions | `frontend/src/widget/types/widget.ts` | `UPDATE_STREAMING_MESSAGE`, `FINISH_STREAMING_MESSAGE`, `UPDATE_MESSAGE` |
| Streaming WS handlers | `frontend/src/widget/context/WidgetContext.tsx` | `bot_stream_start/token/end/error` event handlers |

### Multi-Currency Regex Improvements

| Before | After |
|--------|-------|
| `$` only | 30+ currency symbols, 35+ currency codes, country-dollar prefixes |
| Case-sensitive (broken against `lower_msg`) | `re.IGNORECASE` flag added |
| 10 brands | Extended international brand list |
| XS-XXL sizes | Extended sizes + numeric EU sizes |

### Validation
- All 114 backend unit tests passing post-changes
- No regressions introduced
- Tech debt doc: `docs/technical-debt/11-2-multi-turn-query-handling.md`
