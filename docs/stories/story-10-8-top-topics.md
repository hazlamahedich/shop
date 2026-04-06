# Story 10-8: Top Topics Widget

Status: done

## Story

As a merchant using General mode,
I want to see the most frequently queried topics from my customers,
so that I can understand what my customers are asking about and prioritize content improvements.

## Acceptance Criteria

1. **AC1: Widget Visible in General Mode [P0]** - Given the merchant is in General mode, When viewing the "RAG Intel" dashboard tab, Then the Top Topics widget is visible
2. **AC2: Topics List Displayed [P0]** - Given topic data exists, When the widget renders, Then a list of topics is displayed
3. **AC3: Click Navigates to Conversations [P0]** - Given a topic is displayed, When the user clicks it, Then the app navigates to `/conversations?search=<topic>`
4. **AC4: "Semantic Clusters" Title [P0]** - Given the widget is visible, Then the title displays "Semantic Clusters"
5. **AC5: Topic Items Clickable [P1]** - Given topics are rendered, When hovered/focused, Then each topic shows interactive cursor and visual feedback
6. **AC6: Empty State [P1]** - Given no topics exist, When the widget renders, Then "No Patterns Detected" empty state is shown
7. **AC7: Loading Skeleton [P2]** - Given data is loading, Then a skeleton placeholder is shown
8. **AC8: WCAG 2.1 AA Accessibility [P2]** - Given the widget is visible, Then it meets WCAG 2.1 AA standards
9. **AC9: HTTP Cache-Control Header [P1]** - Given a valid API request, Then the response includes `Cache-Control: public, max-age=3600`
10. **AC10: ETag Header [P1]** - Given a valid API request, Then the response includes an ETag header
11. **AC11: Conditional 304 Response [P1]** - Given a valid If-None-Match header, When the ETag matches, Then a 304 Not Modified is returned
12. **AC12: Different Days = Different ETag [P1]** - Given different days parameters, Then different ETags are generated
13. **AC13: Vary Header [P1]** - Given a valid API request, Then the response includes `Vary: Accept-Encoding`
14. **AC14: Topic Structure [P1]** - Given topics exist, Then each has `name` (string), `queryCount` (int), and `trend` (one of: up/down/stable/new)
15. **AC15: Stop Words Filtered [P1]** - Given queries contain only stop words, Then they are excluded from results
16. **AC16: Empty Data Returns Empty Array [P1]** - Given no query data, Then the API returns `{ topics: [] }`

## Tasks / Subtasks

- [x] **Backend API** (AC: 9-16)
  - [x] `GET /api/v1/analytics/top-topics?days=7` in `backend/app/api/analytics.py`
  - [x] `AggregatedAnalyticsService.get_top_topics()` in `aggregated_analytics_service.py`
  - [x] HTTP caching: `Cache-Control`, `ETag`, `Vary` headers (1-hour max-age)
  - [x] Fernet decryption of encrypted queries with graceful fallback to `[Encrypted]`

- [x] **Topic Extractor Service** (AC: 15)
  - [x] `TopicExtractor` in `backend/app/services/analytics/topic_extractor.py` (365 lines)
  - [x] Stop word filtering (~140 English stop words + greetings)
  - [x] Trend calculation: period-over-period comparison (>10% = up/down, within +/-10% = stable, no prior = new)

- [x] **Frontend Component** (AC: 1-8)
  - [x] `TopTopicsWidget.tsx` — StatCard titled "Semantic Clusters", interactive BarChart (top 8)
  - [x] Click navigation to `/conversations?search=<topic>`
  - [x] Top 3 topics visible by default, remaining in Collapsible section
  - [x] Trend icons: arrow-up, arrow-down, sparkles (new), minus (stable)
  - [x] Encrypted topic handling: amber "Encrypted" badge with lock icon
  - [x] React Query key: `['analytics', 'top-topics', days]`
  - [x] `staleTime: 60_000` (1 minute), `refetchInterval: 120_000` (2 minutes)

- [x] **Testing**
  - [x] Backend API tests: `backend/tests/api/test_top_topics.py`
  - [x] Backend unit tests: `backend/tests/unit/test_topic_extractor.py`
  - [x] E2E P0: `story-10-8-top-topics-p0.spec.ts`
  - [x] E2E Features: `story-10-8-top-topics-features.spec.ts`
  - [x] API caching tests: `story-10-8-top-topics-caching.spec.ts`

## Dev Notes

### Files

| File | Role |
|------|------|
| `backend/app/api/analytics.py` (lines 324-355) | API endpoint with HTTP caching |
| `backend/app/services/analytics/aggregated_analytics_service.py` (lines 1577-1724) | Service logic with decryption |
| `backend/app/services/analytics/topic_extractor.py` | Topic extraction, stop words, trend calculation |
| `frontend/src/components/dashboard/TopTopicsWidget.tsx` | Widget component (242 lines) |
| `frontend/src/services/analyticsService.ts` (lines 388-392, 568-582) | API client + types |
| `frontend/src/config/dashboardWidgets.ts` (line 29) | Widget registration (General mode only) |

### API Response Structure

```typescript
interface TopTopic {
  name: string;           // decrypted query text (or "[Encrypted]")
  queryCount: number;     // count in current period
  trend: "up" | "down" | "stable" | "new";
}

interface TopTopicsResponse {
  topics: TopTopic[];
  lastUpdated: string;    // ISO-8601
  period: {
    days: number;
    startDate: string;
    endDate: string;
  };
}
```

### Trend Calculation Logic

```python
def calculate_trend(current_count: int, previous_count: int) -> str:
    if previous_count == 0:
        return "new"
    change = (current_count - previous_count) / previous_count * 100
    if change > 10:
        return "up"
    elif change < -10:
        return "down"
    else:
        return "stable"
```

### HTTP Caching Strategy

The API uses a 1-hour caching strategy (AC7):
- `Cache-Control: public, max-age=3600`
- `ETag` computed from response content hash
- `Vary: Accept-Encoding` for proper CDN/proxy caching
- Supports conditional requests via `If-None-Match` → 304 Not Modified

### Encrypted Query Handling

RAG query logs may contain Fernet-encrypted queries. The service attempts decryption for each topic and falls back to `[Encrypted]` if decryption fails. The frontend displays an amber "Encrypted" badge with a lock icon for these topics.

## Out of Scope

- Semantic clustering / NLP-based topic extraction (MVP uses frequency-based approach)
- Real-time WebSocket updates for topics (uses polling + HTTP caching instead)
- Topic sentiment analysis
- Topic comparison across merchants

## Related Stories

- Story 10-7: Knowledge Effectiveness Widget (shares `rag_query_logs` table)
- Story 9-10: Analytics & A/B Testing (dashboard infrastructure)

## Run Commands

```bash
# Backend API Tests
cd backend && source venv/bin/activate && python -m pytest tests/api/test_top_topics.py -v

# Backend Unit Tests
cd backend && source venv/bin/activate && python -m pytest tests/unit/test_topic_extractor.py -v

# E2E Tests
cd frontend && npx playwright test story-10-8

# API Caching Tests
cd frontend && npx playwright test story-10-8-top-topics-caching --project=api-tests
```
