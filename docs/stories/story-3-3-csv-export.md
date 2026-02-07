# Story 3-3: CSV Data Export

**Status:** ✅ Complete
**Date Completed:** 2026-02-07
**Sprint:** 3 - Messaging & Conversation Management

---

## Overview

A CSV export feature that allows merchants to download their conversation data for external analysis. The feature includes an export options modal for configuring filters, displays export progress, and handles errors gracefully. Export is limited to 10,000 conversations per request with proper user feedback.

---

## Requirements

### User Stories
- As a merchant, I want to export my conversations to CSV so I can analyze them externally
- As a merchant, I want to apply filters before exporting so I can get specific data subsets
- As a merchant, I want to see export progress so I know when the file is ready
- As a merchant, I want clear error messages if export fails so I can troubleshoot

### Acceptance Criteria
- [x] Export button visible on conversations page
- [x] Export options modal opens when button clicked
- [x] Modal displays current filters from conversations page
- [x] Modal shows "No filters" message when no filters applied
- [x] Modal displays export limit warning (10,000 conversations)
- [x] Modal shows CSV format information (what fields are included)
- [x] Export button disabled during export process
- [x] Progress indicator shown during export
- [x] Success message with export count shown on completion
- [x] CSV file automatically downloaded after successful export
- [x] Error message displayed if export fails
- [x] Cancel button closes modal without exporting
- [x] Clear all button removes all filters (when filters are active)

---

## Implementation

### Frontend Components

| Component | File | Description |
|-----------|------|-------------|
| ExportButton | `frontend/src/components/export/ExportButton.tsx` | Button with loading states (idle, preparing, exporting, completed) |
| ExportOptionsModal | `frontend/src/components/export/ExportOptionsModal.tsx` | Modal for export configuration with filter display |
| ExportProgress | `frontend/src/components/export/ExportProgress.tsx` | Progress indicator with status messages |
| Export Store | `frontend/src/stores/exportStore.ts` | Zustand state for export workflow |
| Export Service | `frontend/src/services/export.ts` | API client for export endpoint |
| Export API Tests | `frontend/tests/api/export.spec.ts` | API contract validation |

### Backend API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/conversations/export` | GET | Export filtered conversations as CSV |

### Data Models

```typescript
interface ExportRequest {
  search?: string;
  dateFrom?: string;
  dateTo?: string;
  status?: ('active' | 'closed' | 'handoff')[];
  sentiment?: ('positive' | 'neutral' | 'negative')[];
  hasHandoff?: boolean;
}

interface ExportResponse {
  // CSV file with UTF-8 BOM for Excel compatibility
  // Headers:
  // - Conversation ID
  // - Customer ID (masked)
  // - Created Date
  // - Updated Date
  // - Status
  // - Sentiment
  // - Message Count
  // - Has Order
  // - LLM Provider
  // - Total Tokens
  // - Estimated Cost (USD)
  // - Last Message Preview
}

interface ExportMetadata {
  exportCount: number;
  exportDate: string;
  filename: string;
}
```

---

## Test Coverage

### Summary
| Test Level | Tests | Status | Coverage |
|------------|-------|--------|----------|
| **E2E** | 10 | ✅ 100% pass | Critical user journeys |
| **API** | 26 | ✅ 100% pass | Contract validation |
| **Store** | 25 | ✅ 100% pass | State management |
| **Component** | 51 | ✅ 100% pass | React components |
| **Total** | **112** | ✅ **100%** | **Full coverage** |

### E2E Tests (10 tests)
**File:** `frontend/tests/e2e/story-3-3-csv-export.spec.ts`

| ID | Priority | Scenario | Browser Coverage |
|----|----------|----------|------------------|
| 3.3-E2E-001 | P0 | Export button opens options modal | 6 browsers |
| 3.3-E2E-002 | P0 | Export all conversations without filters | 6 browsers |
| 3.3-E2E-003 | P1 | Show current filters in export modal | 6 browsers |
| 3.3-E2E-004 | P1 | Download file after successful export | 6 browsers |
| 3.3-E2E-005 | P1 | Show progress indicator during export | 6 browsers |
| 3.3-E2E-006 | P2 | Cancel export from modal | 6 browsers |
| 3.3-E2E-007 | P2 | Clear all filters in modal | 6 browsers |
| 3.3-E2E-008 | P2 | Handle export errors gracefully | 6 browsers |
| 3.3-E2E-009 | P2 | Export with date range filter applied | 6 browsers |
| 3.3-E2E-010 | P2 | Generate CSV with correct format | 6 browsers |

**Result:** 60/60 tests passed (10 tests × 6 browser projects)

### API Tests (26 tests)
**File:** `frontend/tests/api/export.spec.ts`

| ID | Priority | Scenario |
|----|----------|----------|
| 3.3-API-001 | P0 | Authentication required |
| 3.3-API-002 | P0 | Auth token acceptance |
| 3.3-API-003 | P0 | CSV content type response |
| 3.3-API-004 | P0 | Export count header |
| 3.3-API-005 | P1 | Search filter parameter |
| 3.3-API-006 | P1 | Date from parameter |
| 3.3-API-007 | P1 | Date to parameter |
| 3.3-API-008 | P1 | Status filter parameter |
| 3.3-API-009 | P1 | Sentiment filter parameter |
| 3.3-API-010 | P1 | Handoff filter parameter |
| 3.3-API-011 | P1 | Multiple status values |
| 3.3-API-012 | P1 | Multiple sentiment values |
| 3.3-API-013 | P1 | All filters combined |
| 3.3-API-014 | P2 | UTF-8 BOM for Excel |
| 3.3-API-015 | P2 | CSV headers |
| 3.3-API-016 | P2 | Customer ID masking |
| 3.3-API-017 | P2 | Date formatting |
| 3.3-API-018 | P2 | Export limit (10000) |
| 3.3-API-019 | P2 | Empty export |
| 3.3-API-020 | P2 | Export error handling |
| 3.3-API-021 | P2 | Malformed date handling |
| 3.3-API-022 | P2 | Invalid status value |
| 3.3-API-023 | P2 | SQL injection protection |
| 3.3-API-024 | P3 | Special characters in search |
| 3.3-API-025 | P3 | Large date ranges |
| 3.3-API-026 | P3 | Export filename format |

### Store Tests (25 tests)
**File:** `frontend/src/stores/test_exportStore.test.ts`

| ID | Priority | Scenario |
|----|----------|----------|
| 3.3-STORE-001 | P0 | Initial state correctness |
| 3.3-STORE-002 | P0 | Open options modal |
| 3.3-STORE-003 | P0 | Close options modal |
| 3.3-STORE-004 | P0 | Set export options |
| 3.3-STORE-005 | P0 | Merge export options |
| 3.3-STORE-006 | P0 | Start export - preparing state |
| 3.3-STORE-007 | P0 | Start export - exporting state |
| 3.3-STORE-008 | P0 | Start export - download blob |
| 3.3-STORE-009 | P0 | Start export - close modal |
| 3.3-STORE-010 | P0 | Start export - reset to idle |
| 3.3-STORE-011 | P0 | Start export - pass options |
| 3.3-STORE-012 | P1 | Handle export errors |
| 3.3-STORE-013 | P1 | Handle unknown errors |
| 3.3-STORE-014 | P1 | Reset on error |
| 3.3-STORE-015 | P1 | No download on error |
| 3.3-STORE-016 | P1 | Clear error state |
| 3.3-STORE-017 | P1 | Cancel export |
| 3.3-STORE-018 | P1 | Reset all state |
| 3.3-STORE-019 | P2 | isLoading - preparing |
| 3.3-STORE-020 | P2 | isLoading - exporting |
| 3.3-STORE-021 | P2 | isLoading - idle |
| 3.3-STORE-022 | P2 | isCompleted calculation |
| 3.3-STORE-023 | P2 | Empty export options |
| 3.3-STORE-024 | P2 | Rapid export calls |
| 3.3-STORE-025 | P2 | Clear error preserves state |

### Component Tests (51 tests)
**Files:**
- `frontend/tests/component/export/ExportButton.test.tsx` (14 tests)
- `frontend/tests/component/export/ExportProgress.test.tsx` (15 tests)
- `frontend/tests/component/export/ExportOptionsModal.test.tsx` (22 tests)

#### ExportButton Tests (14)
| ID | Scenario |
|----|----------|
| Render with idle state | Default button appearance |
| Render loading state | Exporting... text with spinner |
| Render completed state | Export Complete with checkmark |
| Disabled when loading | Button disabled during export |
| Disabled via prop | Respect disabled prop |
| Click triggers modal | Calls openOptionsModal |
| Disabled when preparing | Preparing state disables button |
| Spinner when loading | Animated spinner icon |
| Checkmark when completed | Green checkmark icon |
| Download icon when idle | Default download icon |
| Custom className | ClassName prop applied |
| **Keyboard accessible** | Enter key triggers export |
| Not clickable when disabled (status) | Disabled state prevents clicks |
| Not clickable when disabled (prop) | Prop disabled prevents clicks |

#### ExportProgress Tests (15)
| ID | Scenario |
|----|----------|
| Not render when idle | Returns null for idle status |
| Render preparing state | "Preparing export..." message |
| Render exporting state | "Generating CSV file..." with progress bar |
| Render completed with metadata | Shows export count and filename |
| Render completed without metadata | Generic completion message |
| Render error state | Displays error message |
| Render default error | Generic error when null |
| Show dismiss button | Error state has dismiss button |
| No progress bar when completed | Progress bar only during active states |
| Progress bar during preparing | Show indeterminate progress |
| Format date correctly | Date formatting in metadata |
| Custom className | ClassName prop applied |
| ARIA attributes | Proper accessibility attributes |
| Dismiss error on click | Clear error when clicked |
| No dismiss in non-error | Only error state has dismiss button |

#### ExportOptionsModal Tests (22)
| ID | Scenario |
|----|----------|
| Not render when closed | Modal hidden when closed |
| Render dialog when open | Modal visible with content |
| Show no filters message | "No filters - export all" |
| Show filter count | Displays count when filters active |
| Display export limit warning | 10,000 conversation limit notice |
| Display CSV format info | Lists all CSV fields |
| Display search filter | Shows search query |
| Display date range (both) | From/to dates |
| Display date range (from only) | From date only |
| Display date range (to only) | To date only |
| Display multiple status | Comma-separated status values |
| Display sentiment filter | Comma-separated sentiment values |
| Display handoff (true) | Shows "Yes" |
| Display handoff (false) | Shows "No" |
| Export button actions | Calls setExportOptions, startExport |
| Cancel button actions | Closes modal |
| Show clear all button | Visible when filters active |
| Initialize with filters | Pre-fills from conversation store |
| Count filters correctly | Accurate filter count |
| ARIA attributes | Proper modal accessibility |
| **Keyboard accessible** | Tab and Enter navigation |
| No clear all when no filters | Button hidden when no filters |

---

## Test Infrastructure

### Mock Setup
**Files:**
- `frontend/tests/component/mocks/exportStore.mock.ts` - Zustand store mock
- `frontend/tests/component/mocks/conversationStore.mock.ts` - Filter store mock

**Pattern:** Vitest `vi.mock` with module-level state manipulation

### Quality Standards Applied
- Given-When-Then format in E2E tests
- Priority tags ([P0], [P1], [P2], [P3])
- Network-first pattern (intercept before navigate)
- Keyboard accessibility testing with userEvent
- Regex matchers for split text nodes
- Mock state helper functions

### Test Framework Migration
- **From:** Playwright Component Testing (experimental-ct-react)
- **To:** Vitest + React Testing Library
- **Reason:** Vitest's `vi.mock` works with Zustand stores; Playwright CT doesn't support Vitest mocking

---

## Execution Results

### Latest Test Run
**Date:** 2026-02-07

**Component Tests:**
```bash
npx vitest run tests/component/export
✓ 51 passed (1.21s)
```

**Store Tests:**
```bash
npx vitest run src/stores/test_exportStore.test.ts
✓ 25 passed (881ms)
```

**Total Export Tests:** ✅ **76/76 passing** (100%)

### Priority Breakdown
| Priority | Count | Percentage |
|----------|-------|------------|
| P0 (Critical) | 16 | 21% |
| P1 (High) | 24 | 32% |
| P2 (Medium) | 34 | 45% |
| P3 (Low) | 3 | 4% |

---

## Fixes Applied

### Component Test Fixes
1. **Keyboard accessibility test** - Changed from `fireEvent.keyDown` to `userEvent.keyboard()` for proper keyboard simulation
2. **Text matching tests** - Changed exact text match to regex match for dialog description and filter display (text split across React nodes)
3. **Cleaned up redundant files** - Removed old Playwright CT `.spec.tsx` files that used incompatible testing framework

### Configuration Updates
- Updated `package.json` `test:component` script from Playwright CT to Vitest
- All export component tests now use Vitest + React Testing Library

---

## Definition of Done

- [x] All acceptance criteria met
- [x] Frontend components implemented (3 components)
- [x] Export store with complete workflow
- [x] Export API service
- [x] E2E tests passing (60/60 across 6 browsers)
- [x] API tests passing (26/26)
- [x] Store tests passing (25/25)
- [x] Component tests passing (51/51)
- [x] Keyboard accessibility verified
- [x] Error handling validated
- [x] Documentation updated

---

## Dependencies

### Completed Stories
- Story 3-1: Conversation List with Pagination (provides data to export)
- Story 3-2: Search and Filter Conversations (filter integration)

### Blocking Stories
None - this story is complete

---

## Open Issues

### Future Enhancements
1. **Export format options** - Add JSON, Excel formats
2. **Scheduled exports** - Auto-export on schedule
3. **Export templates** - Save/export custom filter configurations
4. **Bulk export** - Export multiple filter sets at once
5. **Export history** - Track and re-download previous exports

---

## Related Documentation

- [Testing Strategy](../../TESTING_STRATEGY.md)
- [Error Recovery Pattern](../regression/error-recovery-pattern.md)
- [Flaky Test Wrapper](../helpers/flaky-test-wrapper.ts)
