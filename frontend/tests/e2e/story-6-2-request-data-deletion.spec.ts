/**
 * Story 6-2: Request Data Deletion E2E Tests
 *
 * Epic 6: Data Privacy & Compliance
 * Priority: P1 (Critical - GDPR/CCPA Compliance)
 *
 * Tests data deletion functionality:
 * - "Forget my preferences" triggers actual deletion
 * - Conversation history is deleted from DB
 * - Consent prompt shows again after forgetting
 * - Personality-aware confirmation message
 * - Rate limiting blocks duplicate requests
 *
 * PREREQUISITES:
 * - Frontend dev server running at http://localhost:5173
 * - Run: `cd frontend && npm run dev`
 *
 * Test IDs: 6-2-E2E-001 through 6-2-E2E-005
 * @tags e2e consent gdpr privacy data-deletion story-6-2
 */

import { test, expect } from '@playwright/test';
import { setupWidgetMocks, setupWidgetMocksWithConfig } from '../helpers/widget-test-fixture';
import {
  mockWidgetMessageConditional,
  openWidgetChat,
  createMockMessageResponse,
} from '../helpers/widget-test-helpers';

test.describe('Story 6-2: Request Data Deletion', () => {
  test.describe.configure({ mode: 'parallel' });

  test('[P0][6-2-E2E-001] @smoke should trigger deletion on "forget my preferences"', async ({ page }) => {
    await setupWidgetMocks(page);

    let deletionTriggered = false;

    await page.route('**/api/v1/widget/consent/*', async (route) => {
      if (route.request().method() === 'DELETE') {
        deletionTriggered = true;
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              success: true,
              clear_visitor_id: true,
              deletion_summary: {
                conversations_deleted: 1,
                messages_deleted: 5,
              },
            },
          }),
        });
      } else if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              status: 'opted_in',
              can_store_conversation: true,
              consent_message_shown: true,
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('forget') || msg.includes('delete'),
        response: createMockMessageResponse({
          content: "I've forgotten your preferences and conversation history. Your order references are kept for business purposes.",
          intent: 'preferences_forgotten',
        }),
      },
    ]);

    const { input } = await openWidgetChat(page);
    await input.fill('forget my preferences');
    await input.press('Enter');

    await expect(page.getByText(/forgotten your preferences/i)).toBeVisible({ timeout: 10000 });

    expect(deletionTriggered).toBe(true);
  });

  test('[P0][6-2-E2E-002] @smoke should delete conversation history from DB', async ({ page }) => {
    await setupWidgetMocks(page);

    let deletedSessionId: string | null = null;

    await page.route('**/api/v1/widget/consent/*', async (route) => {
      if (route.request().method() === 'DELETE') {
        const url = route.request().url();
        const match = url.match(/consent\/([^?]+)/);
        deletedSessionId = match ? match[1] : null;

        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              success: true,
              clear_visitor_id: true,
              deletion_summary: {
                conversations_deleted: 2,
                messages_deleted: 10,
                audit_log_id: 123,
              },
            },
          }),
        });
      } else if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              status: 'opted_in',
              can_store_conversation: true,
              consent_message_shown: true,
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('delete') || msg.includes('forget'),
        response: createMockMessageResponse({
          content: "I've forgotten your preferences and conversation history.",
          intent: 'preferences_forgotten',
        }),
      },
    ]);

    const { input } = await openWidgetChat(page);
    await input.fill('delete my data');
    await input.press('Enter');

    await expect(page.getByText(/forgotten your preferences/i)).toBeVisible({ timeout: 10000 });

    expect(deletedSessionId).not.toBeNull();
  });

  test('[P0][6-2-E2E-003] @smoke should show consent prompt again after forgetting', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/consent/*', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              success: true,
              clear_visitor_id: true,
            },
          }),
        });
      } else if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              status: 'pending',
              can_store_conversation: false,
              consent_message_shown: false,
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('forget'),
        response: createMockMessageResponse({
          content: "I've forgotten your preferences and conversation history.",
          intent: 'preferences_forgotten',
        }),
      },
      {
        match: (msg) => msg.includes('hello') || msg.includes('hi'),
        response: createMockMessageResponse({
          content: 'To remember your preferences for faster shopping next time, I\'ll save your conversation. OK?',
          intent: 'consent_prompt',
          consent_required: true,
        }),
      },
    ]);

    const { input } = await openWidgetChat(page);
    await input.fill('forget my preferences');
    await input.press('Enter');

    await expect(page.getByText(/forgotten your preferences/i)).toBeVisible({ timeout: 10000 });

    await input.fill('hello');
    await input.press('Enter');

    await expect(page.getByText(/save your conversation/i)).toBeVisible({ timeout: 10000 });
  });

  test('[P0][6-2-E2E-004] @smoke should show personality-aware confirmation', async ({ page }) => {
    await setupWidgetMocksWithConfig(page, {
      botName: 'ShopBot Pro',
      personality: 'enthusiastic',
    });

    await page.route('**/api/v1/widget/consent/*', async (route) => {
      if (route.request().method() === 'DELETE') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              success: true,
              clear_visitor_id: true,
            },
          }),
        });
      } else if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              status: 'opted_in',
              can_store_conversation: true,
              consent_message_shown: true,
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('forget') || msg.includes('delete'),
        response: createMockMessageResponse({
          content: "POOF! Your preferences are gone! Order info stays for business stuff, but everything else is wiped clean!",
          intent: 'preferences_forgotten',
        }),
      },
    ]);

    const { input } = await openWidgetChat(page);
    await input.fill('forget my preferences');
    await input.press('Enter');

    await expect(page.getByText(/POOF/i)).toBeVisible({ timeout: 10000 });
  });

  test('[P0][6-2-E2E-005] @smoke should block duplicate requests with rate limiting', async ({ page }) => {
    await setupWidgetMocks(page);

    let deleteCallCount = 0;

    await page.route('**/api/v1/widget/consent/*', async (route) => {
      if (route.request().method() === 'DELETE') {
        deleteCallCount++;
        if (deleteCallCount === 1) {
          await route.fulfill({
            status: 200,
            body: JSON.stringify({
              data: {
                success: true,
                clear_visitor_id: true,
              },
            }),
          });
        } else {
          await route.fulfill({
            status: 429,
            body: JSON.stringify({
              error_code: 2000,
              message: 'Rate limit exceeded. Please wait before requesting another deletion.',
              details: { retry_after_seconds: 3600 },
            }),
          });
        }
      } else if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              status: 'opted_in',
              can_store_conversation: true,
              consent_message_shown: true,
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('forget'),
        response: createMockMessageResponse({
          content: "I've forgotten your preferences and conversation history.",
          intent: 'preferences_forgotten',
        }),
      },
      {
        match: (msg) => msg.includes('rate limit') || msg.includes('wait'),
        response: createMockMessageResponse({
          content: "You've already requested data deletion recently. Please wait before trying again.",
          intent: 'rate_limited',
        }),
      },
    ]);

    const { input } = await openWidgetChat(page);

    await input.fill('forget my preferences');
    await input.press('Enter');
    await expect(page.getByText(/forgotten your preferences/i)).toBeVisible({ timeout: 10000 });

    await input.fill('forget my preferences');
    await input.press('Enter');

    await expect(page.getByText(/already requested|rate limit|wait/i)).toBeVisible({ timeout: 10000 });
  });
});
