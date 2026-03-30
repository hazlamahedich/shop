# Story 12-13: Dead Code Cleanup

**Epic**: 12 - Security Hardening
**Priority**: P1 (High)
**Status**: backlog
**Estimate**: 2 hours
**Dependencies**: None

## Problem Statement

Dead code exists in `frontend/src/widget/api/llmProvider.ts:96-98` - unused `getAuthToken()` method reading from localStorage which could be a security concern.

## Acceptance Criteria

- [ ] Remove unused `getAuthToken()` method from llmProvider.ts
- [ ] Audit for other unused authentication code
- [ ] Verify no references to removed code
- [ ] Run linting and type checking
- [ ] Tests still pass

## Technical Design

### Code to Remove

```typescript
// frontend/src/widget/api/llmProvider.ts:96-98
// DELETE THIS:
const getAuthToken = (): string | null => {
    return localStorage.getItem('auth_token');
};
```

### Verification Steps

1. Search for `getAuthToken` references
2. Search for `localStorage.getItem('auth_token')` references
3. Remove the dead code
4. Run `npm run lint`
5. Run `npm run typecheck`
6. Run `npm test`

## Testing Strategy

1. Grep for all references
2. Verify build succeeds
3. Verify tests pass
4. Manual widget testing

## Related Files

- `frontend/src/widget/api/llmProvider.ts`
