# Technical Debt: Story 11-2 Multi-Turn Query Handling

**Last Updated:** 2026-04-01
**Story:** 11-2 Multi-Turn Query Handling
**Status:** Implementation Complete, E2E Tests Reviewed & Improved

---

## Implementation Status

### Source Code (Complete)

- `backend/app/services/multi_turn/__init__.py` — Package init, exports all multi-turn components
- `backend/app/services/multi_turn/state_machine.py` — `ConversationStateMachine` (IDLE, CLARIFYING, REFINE_RESULTS, COMPLETE)
- `backend/app/services/multi_turn/constraint_accumulator.py` — `ConstraintAccumulator` with merge, dedup, contradiction detection
- `backend/app/services/multi_turn/message_classifier.py` — `MessageClassifier` with LLM fallback to heuristic
- `backend/app/services/multi_turn/conversation_lock.py` — `ConversationLockManager` with TTL cleanup, singleton
- `backend/app/services/multi_turn/schemas.py` — Pydantic schemas: `MultiTurnStateEnum`, `MessageType`, `MultiTurnConfig`, constraints
- `backend/app/api/multi_turn.py` — Debug API endpoints for state inspection/reset (admin only)
- `backend/app/services/clarification/clarification_service.py` — Extended with multi-turn + General mode
- `backend/app/services/clarification/question_generator.py` — Extended with mode-aware question generation
- `backend/app/services/conversation/unified_conversation_service.py` — Multi-turn integration at line 289, 2542+
- `backend/app/services/conversation/schemas.py` — Multi-turn state tracking fields (lines 68-101)
- `backend/app/core/errors.py` — Multi-turn error codes (line 232)

### Frontend E2E Tests (Reviewed & Improved — 2026-04-01)

**Test Review Score:** 98/100 (A - Excellent)

| File | Lines | Tests | Status |
|------|-------|-------|--------|
| `tests/e2e/story-11-2-multi-turn-clarification.spec.ts` | 130 | 6 | ✅ All passing |
| `tests/e2e/story-11-2-multi-turn-general-mode.spec.ts` | 78 | 2 | ✅ All passing |
| `tests/helpers/multi-turn-test-helpers.ts` | 203 | — | Shared helpers |

**Total:** 8 E2E tests across 2 spec files

### Backend Test Suite

| File | Lines | Tests | Status |
|------|-------|-------|--------|
| `tests/unit/test_multi_turn_state_machine.py` | — | — | ✅ All passing |
| `tests/unit/test_state_machine_complete_transitions.py` | 137 | — | ✅ All passing |
| `tests/unit/test_constraint_accumulator.py` | 173 | — | ✅ All passing |
| `tests/unit/test_multi_turn_schemas.py` | — | — | ✅ All passing |
| `tests/unit/test_conversation_lock.py` | 182 | — | ✅ All passing |
| `tests/unit/test_message_classifier.py` | — | — | ✅ All passing |
| `tests/unit/test_message_classifier_llm_success.py` | — | — | ✅ All passing |
| `tests/unit/test_topic_change_edge_cases.py` | — | — | ✅ All passing |
| `tests/api/test_multi_turn_api.py` | — | — | ✅ All passing |
| `tests/api/test_multi_turn_api_http.py` | — | — | ✅ All passing |
| `tests/integration/test_multi_turn_orchestration.py` | — | — | ✅ All passing |
| `tests/integration/test_multi_turn_ecommerce.py` | — | — | ✅ All passing |
| `tests/integration/test_multi_turn_general.py` | — | — | ✅ All passing |
| `tests/integration/test_concurrent_multi_turn.py` | — | — | ✅ All passing |

### Test Quality Improvements Applied (E2E — 2026-04-01)

- ✅ Replaced fragile CSS selectors (`[class*="user"]`, `[class*="bot"]`) with stable `data-testid` pattern (`[data-testid="message-bubble"].message-bubble--user/bot`)
- ✅ Added error scenario test: `[P1] 11.2-E2E-008` — network failure during multi-turn shows recovery
- ✅ Extracted `GENERAL_MODE_HANDLERS` to `multi-turn-test-helpers.ts` for consistency with `MULTI_TURN_HANDLERS`
- ✅ Extracted shared flow helpers: `sendAndWaitForResponse()`, `completeShoeClarification()` reducing duplication between E2E-001 and E2E-004
- ✅ Removed unused `CLARIFICATION_QUESTIONS` import from clarification spec

### Test Coverage (E2E)

| Test ID | Priority | AC | Description |
|---------|----------|----|-------------|
| 11.2-E2E-001 | P0 | AC1 | Multi-turn clarification conversation flow |
| 11.2-E2E-002 | P0 | AC6 | Topic change resets multi-turn state |
| 11.2-E2E-003 | P1 | AC5 | Invalid response triggers re-prompt |
| 11.2-E2E-004 | P1 | AC4 | Turn limit enforcement shows results |
| 11.2-E2E-005 | P2 | AC1 | Conversation shows user and bot messages |
| 11.2-E2E-006 | P2 | AC7 | General mode clarification flow |
| 11.2-E2E-007 | P2 | AC9 | General mode topic change resets |
| 11.2-E2E-008 | P1 | — | Network error during multi-turn shows recovery |

**Priority Distribution:** 2 P0, 3 P1, 3 P2

---

## Debt Items

### 1. SSE/WebSocket Streaming for Multi-Turn Responses ⚠️ HIGH Priority

**Current State:**
- Multi-turn responses delivered as complete HTTP responses
- User sees no progress during multi-turn clarification
- No streaming for accumulated constraint feedback

**Issue:**
- ❌ Users wait for full response during multi-step clarification
- ❌ No real-time feedback as constraints accumulate
- ❌ Perceived latency during complex multi-turn flows

**Tracking:** Beads issue `shop-r4nw` — P0, depends on `shop-xqdc` and `shop-obks`

**Implementation Effort:** 3-5 days

---

### 2. CI Workflow for Story 11-2 E2E Tests ⚠️ MEDIUM Priority

**Current State:**
- `story-11-1-e2e-tests.yml` exists but no equivalent for 11-2
- E2E tests only run locally

**Issue:**
- ❌ No CI automation for story 11-2 E2E tests
- ❌ Tests not gated on PR merge

**Recommended Solution:**
Create `.github/workflows/story-11-2-e2e-tests.yml` following the 11-1 pattern.

**Implementation Effort:** 0.5 day

---

## Priority Matrix

| Item | Priority | Effort | Impact | ROI |
|------|----------|--------|--------|-----|
| SSE Streaming Responses | HIGH | 3-5 days | HIGH | HIGH |
| CI Workflow for 11-2 E2E | MEDIUM | 0.5 day | MEDIUM | HIGH |

---

## Related Documentation

- Technical Debt: [11-1 Conversation Context Memory](./11-1-conversation-context.md)
- Test Review: `_bmad-output/test-artifacts/test-reviews/test-review-story-11-2.md`
- Beads: `shop-74w5`, `shop-r4nw`

---

## Questions?

Contact: @sherwing (Product Owner)
Created: 2026-04-01
