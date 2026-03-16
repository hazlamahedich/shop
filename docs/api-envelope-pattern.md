# API Envelope Pattern

## Overview

This document explains how to correctly handle API responses in the frontend, specifically the envelope pattern used by the `apiClient`.

## Response Structure

Backend API responses follow this envelope structure:

```json
{
  "data": { /* actual payload */ },
  "meta": {
    "request_id": "abc123",
    "timestamp": "2026-03-15T10:00:00Z"
  }
}
```

## apiClient Behavior

The `apiClient` (from `frontend/src/services/api.ts`) returns the **full envelope**, not the unwrapped data:

```typescript
// apiClient.request<T>() returns: ApiEnvelope<T>
interface ApiEnvelope<T> {
  data: T;
  meta: any;
}
```

## Correct Usage

### ✅ CORRECT: Use `response.data`

```typescript
const response = await apiClient.get<UserProfile>('/api/user/profile');
const user = response.data;  // This is the UserProfile object
```

### ❌ WRONG: Using `response.data.data`

```typescript
const response = await apiClient.get<UserProfile>('/api/user/profile');
const user = response.data.data;  // WRONG! UserProfile has no 'data' property
```

## Common Mistakes (Epic 8 Learnings)

### Story 8-7: Mode Service Bug

**Incorrect:**
```typescript
// frontend/src/services/merchant.ts (initial version)
async getMerchantMode(): Promise<OnboardingMode> {
  const response = await apiClient.get<{ onboardingMode: OnboardingMode }>('/api/merchant/mode');
  return response.data.data.onboardingMode;  // ❌ Double unwrap
}
```

**Correct:**
```typescript
async getMerchantMode(): Promise<OnboardingMode> {
  const response = await apiClient.get<{ onboardingMode: OnboardingMode }>('/api/merchant/mode');
  return response.data.onboardingMode;  // ✅ Single unwrap
}
```

## Quick Reference

| What You Want | Correct Access |
|---------------|----------------|
| The actual payload | `response.data` |
| The metadata | `response.meta` |
| Request ID (for logging) | `response.meta?.request_id` |

## Debugging Tips

If you see `undefined` when accessing response properties:

1. Check if you're using `response.data.data` (wrong)
2. Change to `response.data` (correct)
3. Use browser DevTools to inspect the actual response structure:
   ```javascript
   console.log('Full response:', response);
   console.log('Payload:', response.data);
   ```

## Related Files

- `frontend/src/services/api.ts` - apiClient implementation
- `backend/app/api/` - Backend endpoints that return envelope responses

## History

- **Epic 8**: Identified pattern of `response.data.data` mistakes in Stories 8-7 and 8-11
- **Root Cause**: Assumption that apiClient unwraps the envelope, but it doesn't
- **Fix**: Document pattern and use `response.data` consistently
