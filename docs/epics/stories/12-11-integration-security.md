# Story 12-11: Integration Security Tests

**Epic**: 12 - Security Hardening
**Priority**: P2 (Medium)
**Status**: backlog
**Estimate**: 6 hours
**Dependencies**: 12-9

## Problem Statement

Integration tests don't cover security scenarios. Need end-to-end security validation.

## Acceptance Criteria

- [ ] E2E authentication flow tests
- [ ] E2E authorization tests
- [ ] E2E CSRF protection tests
- [ ] E2E rate limiting tests
- [ ] E2E session management tests
- [ ] E2E data isolation tests (multi-tenant)
- [ ] Test fixtures for security scenarios
- [ ] CI integration for security E2E tests

## Technical Design

### E2E Security Test Structure

```
frontend/tests/e2e/security/
├── authentication.spec.ts
├── authorization.spec.ts
├── csrf.spec.ts
├── rate-limiting.spec.ts
├── session-management.spec.ts
└── data-isolation.spec.ts
```

### Example Tests

```typescript
// frontend/tests/e2e/security/authentication.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication Security', () => {
    test('brute force protection', async ({ page }) => {
        // Attempt 6 failed logins
        for (let i = 0; i < 6; i++) {
            await page.goto('/login');
            await page.fill('[name="email"]', 'test@example.com');
            await page.fill('[name="password"]', 'wrongpassword');
            await page.click('button[type="submit"]');
        }
        
        // Should be rate limited
        await expect(page.locator('.error')).toContainText('Too many attempts');
    });
    
    test('session expires after inactivity', async ({ page }) => {
        // Login
        await login(page, 'user@example.com', 'password');
        
        // Wait for session timeout
        await page.waitForTimeout(31 * 60 * 1000); // 31 minutes
        
        // Try to access protected resource
        await page.goto('/dashboard');
        
        // Should redirect to login
        await expect(page).toHaveURL(/\/login/);
    });
});
```

## Testing Strategy

1. Run E2E security tests in CI
2. Schedule periodic security E2E runs
3. Test across browsers
4. Test mobile security flows

## Related Files

- `frontend/tests/e2e/security/` (new)
- `frontend/tests/helpers/security-helpers.ts` (new)
- `playwright.config.ts`
