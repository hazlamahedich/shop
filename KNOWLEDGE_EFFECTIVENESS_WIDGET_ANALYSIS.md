# Knowledge Effectiveness Widget - Data Staleness Analysis

**Date:** 2026-03-28
**Issue:** Widget data appears stale and not updating

## 🔍 Investigation Summary

### Backend Status: ✅ WORKING CORRECTLY

The backend API is returning **fresh, live data**:

```bash
curl "http://localhost:8000/api/v1/analytics/knowledge-effectiveness?days=7" \
  -H "X-Merchant-Id: 1" -H "X-Test-Mode: true"
```

**Response:**
```json
{
  "data": {
    "totalQueries": 153,
    "successfulMatches": 110,
    "noMatchRate": 28.1,
    "avgConfidence": 0.8,
    "trend": [0.79, 0.82],
    "lastUpdated": "2026-03-28T07:27:59.196960+00:00"  // TODAY!
  }
}
```

### Database Status: ✅ WORKING CORRECTLY

- **Total RAG query logs:** 153
- **Latest entry:** 2026-03-27 05:50:47 UTC
- **Data is being actively logged**

## ⚠️ Root Cause: Frontend Caching Configuration

### Problem 1: React Query Aggressive Caching

**Location:** `frontend/src/components/dashboard/KnowledgeEffectivenessWidget.tsx:16-21`

```typescript
const { data, isLoading, isError } = useQuery({
  queryKey: ['analytics', 'knowledge-effectiveness'],
  queryFn: () => analyticsService.getKnowledgeEffectiveness(),
  staleTime: 30_000,        // ❌ ISSUE: Data cached for 30 seconds
  refetchInterval: 60_000,  // Only refetches every 60 seconds
});
```

**Impact:**
- Data is considered "fresh" for 30 seconds after fetch
- Within that window, even manual refreshes won't trigger a refetch
- Users see old data for up to 60 seconds

### Problem 2: Global React Query Defaults

**Location:** `frontend/src/main.tsx:14-21`

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,  // ❌ ISSUE: Global 30-second cache
    },
  },
});
```

**Impact:**
- All analytics queries inherit this 30-second stale time
- Creates perception of stale data across the dashboard

### Problem 3: No Manual Refresh Mechanism

The widget has:
- ❌ No refresh button
- ❌ No "last updated" display
- ❌ No refetch on window focus
- ❌ No refetch on reconnect

## 🔧 Recommended Fixes

### Option 1: Reduce Cache Time (Quick Fix)

**File:** `frontend/src/components/dashboard/KnowledgeEffectivenessWidget.tsx`

```typescript
const { data, isLoading, isError } = useQuery({
  queryKey: ['analytics', 'knowledge-effectiveness'],
  queryFn: () => analyticsService.getKnowledgeEffectiveness(),
  staleTime: 5_000,        // ✅ Only cache for 5 seconds
  refetchInterval: 30_000,  // ✅ Refetch every 30 seconds
});
```

### Option 2: Add Refetch Triggers (Better UX)

```typescript
const { data, isLoading, isError, refetch } = useQuery({
  queryKey: ['analytics', 'knowledge-effectiveness'],
  queryFn: () => analyticsService.getKnowledgeEffectiveness(),
  staleTime: 10_000,           // 10-second cache
  refetchInterval: 30_000,     // Auto-refresh every 30s
  refetchOnWindowFocus: true,  // ✅ Refresh when user returns to tab
  refetchOnReconnect: true,    // ✅ Refresh after network issues
});

// Add refresh button to widget UI
<button onClick={() => refetch()}>Refresh</button>
```

### Option 3: Display Last Updated Time (Transparent)

```typescript
// In the widget JSX
<div className="text-xs text-gray-500">
  Last updated: {new Date(effectivenessData?.lastUpdated).toLocaleTimeString()}
</div>
```

### Option 4: Disable Caching for Live Data (Aggressive)

```typescript
const { data, isLoading, isError } = useQuery({
  queryKey: ['analytics', 'knowledge-effectiveness'],
  queryFn: () => analyticsService.getKnowledgeEffectiveness(),
  staleTime: 0,               // ✅ Never consider data fresh
  refetchInterval: 15_000,    // Refresh every 15 seconds
  refetchOnWindowFocus: true,
});
```

## 📊 Current Behavior vs Expected

| Metric | Current | Expected |
|--------|---------|----------|
| Initial Load | ✅ Works | ✅ Works |
| Auto Refresh | Every 60s | Every 15-30s |
| Manual Refresh | ❌ Blocked for 30s | ✅ Immediate |
| Window Focus | ❌ No refresh | ✅ Should refresh |
| Network Reconnect | ❌ No refresh | ✅ Should refresh |
| Last Updated Display | ❌ Hidden | ✅ Visible |

## 🚀 Recommended Action Plan

1. **Immediate (Hotfix):**
   - Reduce `staleTime` from 30s to 5s
   - Reduce `refetchInterval` from 60s to 30s
   - Enable `refetchOnWindowFocus: true`

2. **Short-term (UX Improvement):**
   - Add visible "Refresh" button
   - Display "Last updated" timestamp
   - Add loading indicator during refresh

3. **Long-term (Architecture):**
   - Consider WebSocket for real-time updates
   - Implement optimistic UI updates
   - Add dashboard-wide refresh controls

## 🧪 Testing Steps

After applying fixes, verify:

```bash
# 1. Check backend returns fresh data
curl "http://localhost:8000/api/v1/analytics/knowledge-effectiveness?days=7" \
  -H "X-Merchant-Id: 1" -H "X-Test-Mode: true"

# 2. Check frontend fetches latest data
# - Open dashboard
# - Wait for initial load
# - Create new RAG query (send widget message)
# - Verify widget updates within 30 seconds
# - Switch browser tab and back
# - Verify widget refreshes
```

## 📝 Additional Notes

- Backend is working correctly (no changes needed)
- Database is being actively updated
- Issue is purely frontend caching configuration
- Consider applying similar fixes to other analytics widgets

---

**Files to Modify:**
- `frontend/src/components/dashboard/KnowledgeEffectivenessWidget.tsx`
- `frontend/src/main.tsx` (optional - global defaults)
