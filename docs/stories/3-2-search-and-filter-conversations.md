# Story 3-2: Search and Filter Conversations

## Overview
Enable merchants to efficiently search and filter their conversations by customer ID, message content, date range, status, sentiment, and handoff status. Includes URL-based filter sharing and saved filter management.

## Status: ✅ COMPLETED

**Test Results:** 72/72 passing (12 tests × 6 browsers)
- Last Verified: February 7, 2025
- Browsers: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari, Smoke Tests

---

## User Stories

### Primary [P0]
- As a merchant, I want to search conversations by customer ID so I can quickly find specific customer interactions
- As a merchant, I want to search conversations by message content so I can locate discussions about specific topics
- As a merchant, I want search to be case-insensitive so I don't have to worry about exact capitalization
- As a merchant, I want to filter conversations by date range so I can focus on recent or historical conversations

### High Priority [P1]
- As a merchant, I want to filter by multiple conversation statuses so I can view specific types of conversations
- As a merchant, I want to filter by sentiment so I can identify customer satisfaction trends
- As a merchant, I want to combine multiple filters so I can narrow down to specific conversation subsets
- As a merchant, I want to save frequently-used filter combinations for quick access

### Medium Priority [P2]
- As a merchant, I want to share filtered views via URL so I can collaborate with team members
- As a merchant, I want to quickly clear all filters so I can return to the full conversation list
- As a merchant, I want clear feedback when no results match my search criteria

---

## Implementation Summary

### Frontend Components

| Component | File | Description |
|-----------|------|-------------|
| Conversations Page | `src/pages/Conversations.tsx` | Main page with search, filters, and conversation list |
| Search Bar | `src/components/conversations/SearchBar.tsx` | Debounced search input with clear button |
| Filter Panel | `src/components/conversations/FilterPanel.tsx` | Expandable filter controls (status, sentiment, date, handoff) |
| Active Filters | `src/components/conversations/ActiveFilters.tsx` | Display and remove active filter chips |
| Saved Filters | `src/components/conversations/SavedFilters.tsx` | Save, manage, and apply saved filter combinations |

### State Management

**Zustand Store:** `src/stores/conversationStore.ts`

| Action | Description |
|--------|-------------|
| `fetchConversations` | Fetch conversations with filter parameters |
| `setSearchQuery` | Update search query and refetch |
| `setDateRange` | Update date range filter and refetch |
| `setStatusFilters` | Update status filters and refetch |
| `setSentimentFilters` | Update sentiment filters and refetch |
| `setHasHandoffFilter` | Update handoff filter and refetch |
| `clearAllFilters` | Reset all filters to initial state |
| `saveCurrentFilters` | Save current filter combination |
| `deleteSavedFilter` | Remove a saved filter |
| `applySavedFilter` | Apply a saved filter combination |
| `syncWithUrl` | Sync filters from URL query params on page load |
| `updateUrlFromState` | Write current filter state to URL (enables URL sharing) |

---

## API Integration

### Endpoint
```
GET /api/conversations
```

### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search by customer ID or message content |
| `date_from` | string ISO date | Filter conversations after this date |
| `date_to` | string ISO date | Filter conversations before this date |
| `status` | string[] | Filter by status: `active`, `handoff`, `closed` |
| `sentiment` | string[] | Filter by sentiment: `positive`, `neutral`, `negative` |
| `has_handoff` | boolean | Filter conversations with/without handoff |
| `page` | number | Page number for pagination |
| `per_page` | number | Items per page |
| `sort_by` | string | Sort field: `updated_at`, `created_at`, `status` |
| `sort_order` | string | Sort order: `asc`, `desc` |

### Response Format
```json
{
  "data": [
    {
      "id": 1,
      "platformSenderId": "customer_123",
      "platformSenderIdMasked": "cust****",
      "lastMessage": "Where is my order?",
      "status": "active",
      "sentiment": "neutral",
      "messageCount": 3,
      "hasHandoff": false,
      "updatedAt": "2025-01-15T10:30:00Z",
      "createdAt": "2025-01-15T09:00:00Z"
    }
  ],
  "meta": {
    "pagination": {
      "total": 42,
      "page": 1,
      "perPage": 20,
      "totalPages": 3
    }
  }
}
```

---

## URL Query Parameter Schema

Filters are synchronized with URL query params for shareability:

| URL Param | Filter | Example |
|-----------|--------|---------|
| `search` | Search query | `?search=order123` |
| `date_from` | Date range from | `?date_from=2025-01-01` |
| `date_to` | Date range to | `?date_to=2025-01-31` |
| `status` | Status filters | `?status=active&status=handoff` |
| `sentiment` | Sentiment filters | `?sentiment=positive` |
| `has_handoff` | Handoff filter | `?has_handoff=true` |

**Example URL:**
```
/conversations?status=active&sentiment=negative&search=refund&date_from=2025-01-01
```

---

## Test Coverage

### Test File
`tests/e2e/story-3-2-search-filters.spec.ts`

### Test Cases (12 tests, 72 assertions)

#### P0 - Critical/Smoke Tests (4)

| Test | Description | Assertion |
|------|-------------|-----------|
| `should search by customer ID` | Search returns matching conversations | Only matching conversation visible |
| `should search by message content` | Search finds conversations containing text | Conversation with matching content visible |
| `should perform case-insensitive search` | Search ignores case | Mixed-case search finds uppercase results |
| `should filter by date range` | Date range filters conversations | Conversations within range shown |

#### P1 - High Priority (4)

| Test | Description | Assertion |
|------|-------------|-----------|
| `should filter by multiple statuses` | Multiple status filters work | Only conversations with selected statuses visible |
| `should filter by multiple sentiments` | Multiple sentiment filters work | Only conversations with selected sentiments visible |
| `should apply combined filters` | Multiple filter types combine correctly | Results match all applied filters |
| `should save and apply saved filter` | Saved filters restore correctly | Saved filter produces same results |

#### P2 - Medium Priority (4)

| Test | Description | Assertion |
|------|-------------|-----------|
| `should sync filters from URL query params` | URL params sync on page load | Filters and search input reflect URL |
| `should clear all filters` | Clear button resets all filters | All conversations visible after clearing |
| `should show empty state for no search results` | No results shows empty state | Empty state message displayed |
| `should toggle filter panel visibility` | Filter panel toggles open/closed | Panel visibility changes on button click |

### Test Results
```
✓ 72 passed (37.6s)
```

**All tests passing across all browsers:**
- ✓ Chromium
- ✓ Firefox
- ✓ WebKit
- ✓ Mobile Chrome
- ✓ Mobile Safari
- ✓ Smoke Tests

---

## Implementation Details

### Debounced Search
Search input uses 350ms debounce to reduce API calls:
```typescript
const waitForDebounce = () => new Promise((resolve) => setTimeout(resolve, 350));
```

### Active Filter Chips
Each active filter displays as a removable chip with:
- Visual indicator (color coding by type)
- Remove button (× icon)
- Descriptive label

### Filter Persistence
Saved filters persist via Zustand persist middleware:
```typescript
persist(
  (set, get) => ({ /* store */ }),
  { name: 'conversation-store' }
)
```

### URL Sync on Page Load
Filters synchronize bidirectionally with URL params:
- **On mount:** Read filters from URL → State
- **On filter change:** Write filters from State → URL

```typescript
// On mount - read from URL
useEffect(() => {
  syncWithUrl();
}, []);

// On filter change - write to URL
setSearchQuery: async (query: string) => {
  set((state) => ({
    filters: { ...state.filters, searchQuery: query },
  }));
  updateUrlFromStateHelper(get());  // Update URL
  await get().fetchConversations({ page: 1 });
};
```

---

## Accessibility

### ARIA Labels
- Search input: `aria-label="Search conversations"`
- Clear search button: `aria-label="Clear search"`
- Filter buttons: Proper role and labels
- Filter chips: Descriptive labels with remove actions

### Keyboard Navigation
- Enter key saves filter name
- Escape key closes dialogs
- Tab navigation through filter controls
- Space/Enter toggles filter options

---

## Code Review Improvements (February 7, 2026)

### Item 1: Validation Duplication - Fixed ✅
**Issue:** Validation for status and sentiment existed in both `ConversationFilterParams` Pydantic model and the API endpoint function.

**Fix:** Refactored API endpoint to use the Pydantic model for validation instead of manual validation.

**Files Changed:**
- `backend/app/api/conversations.py` - Now uses `ConversationFilterParams` for validation

**Before:**
```python
# Manual validation duplicated Pydantic logic (81-97)
if status:
    invalid_status = [s for s in status if s not in VALID_STATUS_VALUES]
    # ... duplicate validation code
```

**After:**
```python
# Clean Pydantic validation
try:
    filter_params = ConversationFilterParams(
        search=search,
        date_from=date_from,
        date_to=date_to,
        status=status,
        sentiment=sentiment,
        has_handoff=has_handoff,
    )
except ValueError as e:
    raise ValidationError(str(e))
```

### Item 3: URL Bidirectional Sync - Fixed ✅
**Issue:** URL sync was one-way only (URL → State). Filter changes via UI didn't update the URL.

**Fix:** Added `updateUrlFromStateHelper()` function and `updateUrlFromState` action that writes filter state to URL after every change.

**Files Changed:**
- `frontend/src/stores/conversationStore.ts` - Added bidirectional URL sync

**Implementation:**
```typescript
const updateUrlFromStateHelper = (state: Pick<ConversationsState, 'filters'>): void => {
  if (typeof window === 'undefined') return;

  const url = new URL(window.location.href);
  const params = url.searchParams;

  // Clear existing filter params
  params.delete('search');
  params.delete('date_from');
  params.delete('date_to');
  params.delete('status');
  params.delete('sentiment');
  params.delete('has_handoff');

  // Add current filter state to URL
  if (state.filters.searchQuery) {
    params.set('search', state.filters.searchQuery);
  }
  // ... (other filters)

  // Update URL without triggering a page reload
  window.history.replaceState({}, '', url.toString());
};
```

**Benefits:**
- Users can bookmark/share filtered conversation views
- Browser back/forward navigation preserves filter state
- Filter state is reflected in URL for copy-paste sharing

---

## Known Issues & Limitations

### None
All functionality is working as expected. All tests passing.

---

## Future Enhancements (Out of Scope)

- Export filtered conversation results
- Advanced search operators (AND, OR, NOT)
- Filter usage analytics
- Share saved filters across users
- Filter presets based on common use cases

---

## Related Stories

- **Story 3-1:** Conversation List with Pagination (Prerequisite)
- **Story 3-3:** Conversation Detail View

---

## Deployment Notes

### Environment Variables
No new environment variables required.

### Database Changes
None - uses existing conversation data.

### API Changes
Backend must support query parameters listed in API Integration section.

---

## Verification Steps

1. ✅ Search by customer ID returns correct results
2. ✅ Search by message content returns correct results
3. ✅ Search is case-insensitive
4. ✅ Date range filtering works correctly
5. ✅ Multiple status filters can be applied
6. ✅ Multiple sentiment filters can be applied
7. ✅ Combined filters work together
8. ✅ Filters can be saved and applied
9. ✅ URL query params sync filters on page load
10. ✅ Clear all filters button works
11. ✅ Empty state displays when no results
12. ✅ Filter panel toggles visibility

---

## Sign-off

| Role | Name | Date | Status |
|------|------|------|--------|
| Developer | Claude | 2025-02-07 | ✅ Complete |
| QA | Automated E2E Tests | 2025-02-07 | ✅ All Passing |
