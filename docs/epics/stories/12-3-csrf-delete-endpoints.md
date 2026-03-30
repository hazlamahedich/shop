# Story 12-3: CSRF Delete Endpoints

**Epic**: 12 - Security Hardening
**Priority**: P1 (High)
**Status**: backlog
**Estimate**: 4 hours
**Dependencies**: None

## Problem Statement

DELETE endpoints may not be properly covered by CSRF protection. Need to verify all mutation endpoints have CSRF validation.

## Acceptance Criteria

- [ ] Audit all DELETE endpoints in backend
- [ ] Verify CSRF middleware covers DELETE method
- [ ] Add CSRF token to frontend DELETE requests
- [ ] Tests for CSRF protection on DELETE endpoints
- [ ] Documentation updated

## Technical Design

### Backend CSRF Middleware Check

```python
# backend/app/middleware/csrf.py
# Ensure DELETE is in protected methods
PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
```

### Frontend API Client Update

```typescript
// frontend/src/api/client.ts
async delete<T>(url: string): Promise<T> {
    const csrfToken = getCsrfToken();
    return this.request<T>('DELETE', url, {
        headers: { 'X-CSRF-Token': csrfToken }
    });
}
```

## Testing Strategy

1. Test DELETE without CSRF token (should fail)
2. Test DELETE with valid CSRF token (should succeed)
3. Test CSRF token expiration on DELETE

## Related Files

- `backend/app/middleware/csrf.py`
- `frontend/src/api/client.ts`
- `backend/tests/api/test_csrf.py`
