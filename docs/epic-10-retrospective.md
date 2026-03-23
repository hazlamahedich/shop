# Epic 10 Retrospective: General Mode Widgets

# Generated: 2026-03-22
# Team: team mantis b

## Executive Summary

# Sprint Completion: 2026-03-22
# Epic Status: DONE ✅

**Epic Goal:** Implement General Mode widgets for knowledge-based support merchants

**Stories Completed:** 10/10 (100%)

| Story | Title | Status | Test Score |
|-------|-------|--------|------------|
| 10-1 | Source Citations Widget | ✅ DONE | 95/100 (A) |
| 10-2 | FAQ Quick Buttons Widget | ✅ DONE | Code Review Complete |
| 10-3 | Quick Reply Chips Widget | ✅ DONE | 98/100 (A+) |
| 10-4 | Feedback Rating Widget | ✅ DONE | 95/100 (A) |
| 10-5 | Contact Card Widget | ✅ DONE | 100/100 (A+) |
| 10-6 | Enable Existing Widgets for General Mode | ✅ DONE | Code Review Complete |
| 10-7 | Knowledge Effectiveness Widget | ✅ DONE | Tests Passing |
| 10-8 | Top Topics Widget | ✅ DONE | 95/100 (A) |
| 10-9 | Response Time Distribution Widget | ✅ DONE | Tests Passing |
| 10-10 | FAQ Usage Widget | ✅ DONE | 85/100 (B) |

---

## What Went Well ✅

### Widget Consistency Across All Stories
- **Pattern Reuse:** Chip styling from Story 9-4 (Quick Reply Buttons) reused across all stories
- **Consistent Standards:** 44px touch targets, animation timing (150ms), reduced-motion support
- **UX Cohesion:** Source Citations, FAQ Quick Buttons, Quick Reply Chips, Feedback Rating, Contact Card all integrate seamlessly into MessageList
- **Impact:** Reduced bugs, faster implementation, consistent user experience

### Test Quality Improvements
- **High Scores:** A+ on multiple stories (10-3: 98/100, 10-5: 100/100)
- **Network-First Pattern:** Consistently applied across all stories
- **Data-testid Selectors:** Standard approach for E2E tests
- **Factory Functions:** TypeScript interfaces for better type safety
- **Test ID Format:** `10.x-E2E-XXX` pattern established

### Documentation Quality
- **Dev Notes Sections:** Code examples, previous story learnings, pre-development checklists
- **Usability:** Developers could implement without constant questions
- **Story References:** Clear cross-references to previous stories and patterns

### Component Pattern Consistency
- **MessageList Integration:** All widget components follow same integration pattern
- **Theme Support:** Dark mode support implemented consistently
- **Accessibility:** WCAG 2.1 AA compliance across all stories

---

## What Could Be Improved ⚠️

### Widget Client Field Extraction (CRITICAL - 5/10 Stories Affected)
**Problem:** When adding new response fields, `widgetClient.ts` extraction step is frequently missed, causing E2E test failures.

**Stories Affected:**
- 10-1: `sources` field not extracted
- 10-3: `suggestedReplies` field not extracted
- 10-4: `feedbackEnabled` and `userRating` fields not extracted
- 10-5: Custom contact option field not extracted
- 10-10: Various fields not extracted

**Root Cause:** Adding fields to `WidgetMessage` interface doesn't automatically update `widgetClient.ts` extraction logic.

**Impact:** ~15-20 hours total debugging time

**Recommendation:**
- Add checklist item to AGENTS.md for widget-affecting changes
- Consider pre-commit hook to verify field extraction

### E2E Test Syntax Errors (4/10 Stories Affected)
**Problem:** JSON syntax errors in E2E test files (missing commas, invalid quotes)

**Stories Affected:**
- 10-1: Missing commas in mock data
- 10-4: 5 locations with missing commas
- 10-5: Quote issues in mock setup
- 10-10: Multiple syntax errors

**Root Cause:** No linting/formatting checks on E2E test files

**Recommendation:**
- Add ESLint rule to catch JSON syntax errors
- Run `eslint --fix` on E2E files before test execution

### Mock Data Incomplete (2/10 Stories Affected)
**Problem:** Mock data didn't match test expectations

**Stories Affected:**
- 10-5: Mock only provided phone/email, tests expected custom option
- 10-6: Test artifacts in wrong location

**Root Cause:** Mock setup not verified against test assertions

**Recommendation:**
- Create mock data validation guide
- Ensure mocks match test expectations before running tests

### Hard Waits Still Used Initially (3/10 Stories Affected)
**Problem:** `waitForTimeout()` used instead of deterministic waits

**Stories Affected:**
- 10-1: Hard waits for scroll settling
- 10-4: 9 hard waits before refactoring
- 10-3: Hard waits removed during review

**Root Cause:** Quick debugging approach that became technical debt

**Resolution:** Replaced with deterministic patterns during test quality reviews

### E2E Test Files Too Large (1/10 Stories Affected)
**Problem:** Story 10-6 had 475-line E2E test file

**Impact:** Reduced maintainability, slower test execution

**Resolution:** Split into 4 focused files (162 total lines), improved readability

---

## Testing Pain Points Summary

| Story | Issues | Time Impact |
|------|-------|-------------|
| 10-1 | Viewport fix, `sources` field not extracted | ~2 hours |
| 10-4 | E2E syntax errors, hard waits, widget client fields, backend integration | ~3 hours |
| 10-5 | Mock incomplete (missing custom contact option) | ~1 hour |
| 10-6 | E2E file too large, test artifacts in wrong location | ~1 hour |
| 10-10 | Backend mock issues, API syntax errors, integration errors | ~2 hours |

**Total Testing Friction:** ~9-10 hours across epic

---

## Communication & Coordination

### Cross-Story Coordination
- **Widget Client Updates:** Stories 10-1, 10-3, 10-4, 10-5, 10-10 all needed `widgetClient.ts` updates
- **Integration Gap:** Changes not communicated across stories upfront
- **Impact:** Discovered during testing phase rather than implementation

### Documentation Gaps
- **Pattern Reference:** No central documentation for widget patterns
- **Story References:** Each story referenced previous learnings, but no shared guide

---

## Process Improvements for Future Epics

### Recommended Action Items
1. **Create Widget Client Update Checklist** - Add to AGENTS.md
2. **Add Pre-Commit Hook for Field Extraction** - Automated verification
3. **Create Shared Widget Pattern Documentation** - Central reference
4. **Add ESLint Rule for JSON Syntax** - Catch missing commas in E2E tests
5. **Create Network-First Pattern Guide** - Document standard approach for mocking
6. **Create Mock Data Validation Guide** - Ensure mocks match test expectations

### Estimated Impact
- **Testing Friction Reduction:** 50-70% (from ~10 hours to ~3-4 hours)
- **Bug Prevention:** Earlier detection during implementation
- **Developer Experience:** Faster onboarding for widget stories

---

## Key Learnings
1. **Pattern Reuse Works:** Chip styling consistency reduced bugs and accelerated development
2. **Field Extraction is a Common Pitfall:** Widget client updates are easily missed
3. **E2E Tests Need Linting:** JSON syntax errors could be caught automatically
4. **Documentation Quality Matters:** Good Dev Notes sections improved developer productivity
5. **Test Quality Reviews Add Value:** Hard waits and syntax issues caught and fixed

---

## Team Feedback
- **Alice (PO):** "Stories were well-scoped, but widget client coordination could be improved"
- **Charlie (Dev):** "Widget client field extraction is a common pitfall - we need a checklist"
- **Dana (QA):** "Test quality scores improved across epic, but initial tests had recurring issues"
- **Elena (Junior Dev):** "Dev Notes sections were incredibly helpful for implementation"

---

## Retrospective Participants
- Bob (Scrum Master)
- Alice (Product Owner)
- Charlie (Senior Dev)
- Dana (QA Engineer)
- Elena (Junior Dev)
- team mantis b (Project Lead)
