# Story 10-7: Knowledge Effectiveness Widget

Status: done

## Story

As a merchant using General mode,
I want to see how effectively my knowledge base answers customer queries,
so that I can identify gaps and improve my documentation.

## Acceptance Criteria

1. **AC1: Widget Visible in General Mode [P0]** - Given the merchant is in General mode, When viewing the dashboard, Then the Knowledge Effectiveness widget is visible
2. **AC2: View Details Button [P0]** - Given the widget is visible, When rendered, Then a "View details" button is present
3. **AC3: Metrics Displayed Correctly [P1]** - Given effectiveness data exists, When the widget loads, Then totalQueries and successfulMatches are displayed
4. **AC4: Warning When No-Match Rate > 20% [P1]** - Given the no-match rate exceeds 20%, When the widget renders, Then a warning is shown
5. **AC5: Hidden in E-commerce Mode [P1]** - Given the merchant is in E-commerce mode, When viewing the dashboard, Then the widget is not displayed
6. **AC6: 7-Day Trend Chart [P1]** - Given effectiveness data exists, When the widget renders, Then a sparkline trend chart is displayed
7. **AC7: WCAG 2.1 AA Accessibility [P1]** - Given the widget is visible, Then it meets WCAG 2.1 AA accessibility standards
8. **AC8: Empty State [P2]** - Given no queries exist, When the widget renders, Then an empty state with "Add Knowledge" link is shown
9. **AC9: Error State [P2]** - Given the API fails, When the widget renders, Then an error state is displayed
10. **AC10: Loading Skeleton [P2]** - Given data is loading, Then a skeleton placeholder is shown
11. **AC11: Last Updated Timestamp [P2]** - Given effectiveness data exists, When the widget renders, Then a last-updated timestamp is displayed
12. **AC12: Average Confidence [P2]** - Given matched queries exist, When the widget renders, Then average confidence percentage is shown
13. **AC13: Retry After Failure [P2]** - Given an error occurred, When the user clicks retry, Then data is re-fetched
14. **AC14: API Returns Correct Structure [P1]** - Given a valid request, Then the API returns all required fields (totalQueries, successfulMatches, noMatchRate, avgConfidence, trend, lastUpdated)
15. **AC15: Days Parameter [P1]** - Given a days parameter (1-30), Then the API filters data for that period
16. **AC16: Invalid Days Rejected [P1]** - Given an invalid days parameter, Then the API returns 422

## Tasks / Subtasks

- [x] **Database Model**
  - [x] Create `rag_query_logs` table in `backend/app/models/rag_query_log.py`
  - [x] Alembic migration: `20260320_1435-a1b2c3d4e5f6_add_rag_query_logs_table.py`
  - [x] Indexes: `ix_rag_query_logs_merchant_id`, `idx_rag_logs_merchant_date`

- [x] **Backend API** (AC: 14, 15, 16)
  - [x] `GET /api/v1/analytics/knowledge-effectiveness?days=7` in `backend/app/api/analytics.py`
  - [x] `AggregatedAnalyticsService.get_knowledge_effectiveness()` in `aggregated_analytics_service.py`

- [x] **Real-Time Updates** (WebSocket)
  - [x] `RAGQueryBroadcaster` in `backend/app/services/analytics/rag_query_broadcaster.py`
  - [x] WebSocket handler in `backend/app/api/dashboard_ws.py`
  - [x] Frontend WS handler in `dashboardWebSocketService.ts`

- [x] **Frontend Component** (AC: 1-13)
  - [x] `KnowledgeEffectivenessWidget.tsx` — StatCard with match rate, DonutGauge, MiniAreaChart sparkline
  - [x] Mode restriction: visible only in General mode (widget config `mode: ['general']`)
  - [x] WebSocket Live/Offline connection status indicator
  - [x] React Query key: `['analytics', 'knowledge-effectiveness']`

- [x] **Backfill Script**
  - [x] `backend/scripts/backfill_rag_query_logs.py` — populate from historical messages

- [x] **Testing**
  - [x] Backend API tests: `backend/tests/api/test_knowledge_effectiveness.py`
  - [x] E2E P0: `story-10-7-knowledge-effectiveness-p0.spec.ts`
  - [x] E2E Features: `story-10-7-knowledge-effectiveness-features.spec.ts`
  - [x] API integration: `story-10-7-knowledge-effectiveness-api.spec.ts`
  - [x] Unit tests: `KnowledgeEffectivenessWidget.test.tsx`

## Dev Notes

### Files

| File | Role |
|------|------|
| `backend/app/models/rag_query_log.py` | Database model — `rag_query_logs` table |
| `backend/app/api/analytics.py` (lines 301-321) | API endpoint |
| `backend/app/services/analytics/aggregated_analytics_service.py` (lines 1474-1575) | Service logic |
| `backend/app/services/analytics/rag_query_broadcaster.py` | WebSocket broadcaster |
| `backend/app/api/dashboard_ws.py` (lines 311-333) | WS handler |
| `frontend/src/components/dashboard/KnowledgeEffectivenessWidget.tsx` | Widget component (222 lines) |
| `frontend/src/services/analyticsService.ts` (lines 374-378, 559-566) | API client + types |
| `frontend/src/services/dashboardWebSocketService.ts` (lines 197-228) | WS message handler |
| `frontend/src/config/dashboardWidgets.ts` (line 28) | Widget registration (General mode only) |

### Data Staleness Resolution

Initially used aggressive React Query caching (`staleTime: 30s`, `refetchInterval: 60s`) which caused data staleness. Resolved by switching to WebSocket-based real-time updates with `staleTime: 10s` and disabled polling. See `KNOWLEDGE_EFFECTIVENESS_WIDGET_ANALYSIS.md`.

### API Response Structure

```typescript
interface KnowledgeEffectivenessResponse {
  totalQueries: number;
  successfulMatches: number;
  noMatchRate: number;       // 0-100, rounded to 1 decimal
  avgConfidence: number | null;  // 0-1, null if no matched queries
  trend: number[];           // daily avg confidence for sparkline
  lastUpdated: string;       // ISO-8601
}
```

### Database Schema

```sql
CREATE TABLE rag_query_logs (
  id SERIAL PRIMARY KEY,
  merchant_id INTEGER NOT NULL,
  query TEXT NOT NULL,
  matched BOOLEAN DEFAULT FALSE,
  confidence FLOAT,
  sources JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Out of Scope

- Per-document effectiveness breakdown
- Automated knowledge gap suggestions
- Export to CSV/PDF
- Comparison across time periods (beyond trend sparkline)

## Related Stories

- Story 10-8: Top Topics Widget (shares `rag_query_logs` table)
- Story 9-10: Analytics & A/B Testing (dashboard infrastructure)

## Run Commands

```bash
# Backend API Tests
cd backend && source venv/bin/activate && python -m pytest tests/api/test_knowledge_effectiveness.py -v

# E2E Tests
cd frontend && npx playwright test story-10-7

# API Integration Tests
cd frontend && npx playwright test story-10-7-knowledge-effectiveness-api --project=api-tests

# Unit Tests
cd frontend && npm run test KnowledgeEffectivenessWidget.test.tsx -- --run
```
