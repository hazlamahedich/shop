/**
 * @fileoverview Shared fixtures for Story 6-5 E2E tests
 * @description Reusable fixtures for authentication and API mocking
 */

import { test as base, APIRequestContext } from '@playwright/test';
import { createAuthState, createSchedulerHealth, createAuditLogResponse } from '../test-utils/factories/retention-factories';

type RetentionTestFixtures = {
  authenticatedPage: import('@playwright/test').Page;
  apiContext: APIRequestContext;
};

export const test = base.extend<RetentionTestFixtures>({
  apiContext: async ({ playwright }, use) => {
    const context = await playwright.request.newContext({
      baseURL: process.env.API_URL || 'http://localhost:8000',
    });
    await use(context);
  },

  authenticatedPage: async ({ page }, use) => {
    const authState = createAuthState({
      merchant: {
        id: 'test-merchant-retention',
        email: 'retention-test@test.com',
        name: 'Retention Test Merchant',
        hasStoreConnected: true,
      },
    });

    const schedulerHealth = createSchedulerHealth();
    const auditLogResponse = createAuditLogResponse({
      logs: [
        {
          id: 1,
          sessionId: 'test-session-1',
          merchantId: 1,
          retentionPeriodDays: 30,
          deletionTrigger: 'auto',
          requestedAt: new Date(Date.now() - 7200000).toISOString(),
          completedAt: new Date(Date.now() - 7100000).toISOString(),
          conversationsDeleted: 5,
          messagesDeleted: 23,
          redisKeysCleared: 3,
          errorMessage: null,
        },
      ],
      total: 1,
    });

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: authState.merchant,
          meta: {
            sessionExpiresAt: authState.sessionExpiresAt,
          },
        }),
      });
    });

    await page.route('**/api/v1/health/scheduler', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(schedulerHealth),
      });
    });

    await page.route('**/api/v1/audit/retention-logs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(auditLogResponse),
      });
    });

    await page.addInitScript(() => {
      const mockAuthState = {
        isAuthenticated: true,
        merchant: {
          id: 'test-merchant-retention',
          email: 'retention-test@test.com',
          name: 'Retention Test Merchant',
          hasStoreConnected: true,
        },
        sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
        isLoading: false,
        error: null,
      };

      localStorage.setItem('shop_auth_state', JSON.stringify(mockAuthState));
    });

    await use(page);
  },
});

export { expect } from '@playwright/test';
