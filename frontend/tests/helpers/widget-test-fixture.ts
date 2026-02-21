/**
 * Widget Test Fixture
 *
 * Shared Playwright fixture setup for Story 5-10 E2E tests.
 * Provides common mocks for config, session, and Shopify blocking.
 *
 * @see tests/helpers/widget-test-helpers.ts for additional helpers
 */

import { Page } from '@playwright/test';
import { WIDGET_CONFIG_DEFAULTS } from './widget-test-helpers';

export async function setupWidgetMocks(page: Page, options: { blockShopify?: boolean } = {}) {
  const { blockShopify = true } = options;

  if (blockShopify) {
    await page.route('**/*.myshopify.com/**', (route) => route.abort());
  }

  await page.route('**/api/v1/widget/config/*', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        config: WIDGET_CONFIG_DEFAULTS,
      }),
    });
  });

  await page.route('**/api/v1/widget/session', async (route) => {
    if (route.request().method() === 'POST') {
      const now = new Date();
      const expiresAt = new Date(now.getTime() + 60 * 60 * 1000);
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          session: {
            session_id: crypto.randomUUID(),
            merchant_id: '1',
            expires_at: expiresAt.toISOString(),
            created_at: now.toISOString(),
            last_activity_at: now.toISOString(),
          },
        }),
      });
    } else {
      await route.continue();
    }
  });
}

export async function setupWidgetMocksWithConfig(
  page: Page,
  configOverrides: Partial<typeof WIDGET_CONFIG_DEFAULTS> = {}
) {
  await page.route('**/*.myshopify.com/**', (route) => route.abort());

  const config = {
    ...WIDGET_CONFIG_DEFAULTS,
    ...configOverrides,
    theme: {
      ...WIDGET_CONFIG_DEFAULTS.theme,
      ...configOverrides.theme,
    },
  };

  await page.route('**/api/v1/widget/config/*', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({ config }),
    });
  });

  await page.route('**/api/v1/widget/session', async (route) => {
    if (route.request().method() === 'POST') {
      const now = new Date();
      const expiresAt = new Date(now.getTime() + 60 * 60 * 1000);
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          session: {
            session_id: crypto.randomUUID(),
            merchant_id: '1',
            expires_at: expiresAt.toISOString(),
            created_at: now.toISOString(),
            last_activity_at: now.toISOString(),
          },
        }),
      });
    } else {
      await route.continue();
    }
  });

  return config;
}
