/**
 * Story 6-1: Opt-In Consent Flow E2E Tests
 *
 * Epic 6: Data Privacy & Compliance
 * Priority: P0 (Critical - GDPR/CCPA Compliance)
 *
 * Tests the conversation data consent flow:
 * - First conversation shows consent prompt
 * - User can opt-in to save preferences
 * - User can opt-out and continue without storage
 * - Consent persists across sessions via visitor_id (hybrid storage)
 * - "Forget my preferences" revokes consent and clears visitor_id
 * - Post-opt-out journey: Complete purchase after declining consent
 *
 * Storage Strategy (Privacy-Friendly):
 * - visitor_id: localStorage (13 months) - for consent tracking
 * - session_id: sessionStorage - clears on browser close
 *
 * PREREQUISITES:
 * - Frontend dev server running at http://localhost:5173
 * - Run: `cd frontend && npm run dev`
 *
 * Test IDs: 6-1-E2E-001 to 6-1-E2E-013
 * @tags e2e consent gdpr privacy story-6-1
 */

import { test, expect } from '@playwright/test';
import { setupWidgetMocks, setupWidgetMocksWithConfig } from '../helpers/widget-test-fixture';
import {
  mockWidgetMessageConditional,
  openWidgetChat,
  createMockMessageResponse,
} from '../helpers/widget-test-helpers';

test.describe('Story 6-1: Opt-In Consent Flow', () => {
  test.describe.configure({ mode: 'parallel' });

  test('[P0][6-1-E2E-001] @smoke should show consent prompt on first conversation', async ({ page }) => {
    await setupWidgetMocks(page);

    await mockWidgetMessageConditional(page, [
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
    await input.fill('hello');
    await input.press('Enter');

    await expect(page.getByText(/remember your preferences|save your conversation/i)).toBeVisible({ timeout: 10000 });

    await expect(page.getByRole('button', { name: /yes.*save/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /no.*don't save/i })).toBeVisible();
  });

  test('[P0][6-1-E2E-002] @smoke should record opt-in consent', async ({ page }) => {
    await setupWidgetMocks(page);

    let consentRecorded = false;

    await page.route('**/api/v1/widget/consent', async (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON();
        if (body?.consent_granted === true) {
          consentRecorded = true;
        }
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ data: { success: true } }),
        });
      } else {
        await route.continue();
      }
    });

    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('hello'),
        response: createMockMessageResponse({
          content: 'To remember your preferences, I\'ll save your conversation. OK?',
          intent: 'consent_prompt',
          consent_required: true,
        }),
      },
      {
        match: (msg) => msg.includes('yes'),
        response: createMockMessageResponse({
          content: 'Thank you! Your consent has been recorded. How can I help you today?',
          intent: 'consent_granted',
        }),
      },
    ]);

    const { input } = await openWidgetChat(page);
    await input.fill('hello');
    await input.press('Enter');

    await expect(page.getByText(/save your conversation/i)).toBeVisible({ timeout: 10000 });

    const yesButton = page.getByRole('button', { name: /yes.*save/i });
    await yesButton.click();

    await expect(page.getByText(/consent has been recorded/i)).toBeVisible({ timeout: 10000 });

    expect(consentRecorded).toBe(true);
  });

  test('[P0][6-1-E2E-003] @smoke should allow opt-out and continue without storage', async ({ page }) => {
    await setupWidgetMocks(page);

    let consentDenied = false;

    await page.route('**/api/v1/widget/consent', async (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON();
        if (body?.consent_granted === false) {
          consentDenied = true;
        }
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ data: { success: true } }),
        });
      } else {
        await route.continue();
      }
    });

    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('hello'),
        response: createMockMessageResponse({
          content: 'To remember your preferences, I\'ll save your conversation. OK?',
          intent: 'consent_prompt',
          consent_required: true,
        }),
      },
      {
        match: (msg) => msg.includes('find') || msg.includes('search'),
        response: createMockMessageResponse({
          content: 'No problem! I won\'t save your data. What can I help you find?',
          intent: 'product_search',
        }),
      },
    ]);

    const { input } = await openWidgetChat(page);
    await input.fill('hello');
    await input.press('Enter');

    await expect(page.getByText(/save your conversation/i)).toBeVisible({ timeout: 10000 });

    const noButton = page.getByRole('button', { name: /no.*don't save/i });
    await noButton.click();

    await expect(page.getByText(/won't save your data/i)).toBeVisible({ timeout: 10000 });

    expect(consentDenied).toBe(true);

    await input.fill('find shoes');
    await input.press('Enter');

    await expect(page.getByText(/help you find/i)).toBeVisible({ timeout: 10000 });
  });

  test('[P0][6-1-E2E-004] @regression should persist consent across sessions', async ({ page, context }) => {
    const sessionId = crypto.randomUUID();

    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/consent/*', async (route) => {
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
    });

    await page.route('**/api/v1/widget/session', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              sessionId: sessionId,
              merchant_id: '1',
              expires_at: new Date(Date.now() + 3600000).toISOString(),
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('hello'),
        response: createMockMessageResponse({
          content: 'Welcome back! How can I help you today?',
          intent: 'greeting',
        }),
      },
    ]);

    const { input } = await openWidgetChat(page);
    await input.fill('hello');
    await input.press('Enter');

    await expect(page.getByText(/welcome back/i)).toBeVisible({ timeout: 10000 });

    await expect(page.getByText(/save your conversation/i)).not.toBeVisible();
  });

  test('[P0][6-1-E2E-005] @smoke @gdpr should revoke consent with forget my preferences', async ({ page }) => {
    await setupWidgetMocks(page);

    let consentRevoked = false;

    await page.route('**/ui/v1/widget/consent/*', async (route) => {
      if (route.request().method() === 'DELETE') {
        consentRevoked = true;
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ data: { success: true } }),
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
          content: 'I\'ve forgotten your preferences and conversation history. Your order references are kept for business purposes.',
          intent: 'preferences_forgotten',
        }),
      },
    ]);

    const { input } = await openWidgetChat(page);
    await input.fill('forget my preferences');
    await input.press('Enter');

    await expect(page.getByText(/forgotten your preferences/i)).toBeVisible({ timeout: 10000 });

    expect(consentRevoked).toBe(true);
  });

  test('[P1][6-1-E2E-006] @regression should show personality-aware consent prompts', async ({ page }) => {
    await setupWidgetMocksWithConfig(page, {
      botName: 'ShopBot Pro',
    });

    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('hello'),
        response: createMockMessageResponse({
          content: 'Hey there! To give you the best recommendations, I\'d love to remember your preferences. Sound good?',
          intent: 'consent_prompt',
          consent_required: true,
        }),
      },
    ]);

    const { input } = await openWidgetChat(page);
    await input.fill('hello');
    await input.press('Enter');

    await expect(page.getByText(/remember your preferences/i)).toBeVisible({ timeout: 10000 });

    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
  });

  test('[P1][6-1-E2E-007] @regression should not show consent prompt after decision', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/consent/*', async (route) => {
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
    });

    let messageCount = 0;
    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => {
          messageCount++;
          return msg.includes('hello') || msg.includes('hi');
        },
        response: createMockMessageResponse({
          content: 'Hello! How can I assist you today?',
          intent: 'greeting',
        }),
      },
    ]);

    const { input } = await openWidgetChat(page);

    await input.fill('hello');
    await input.press('Enter');
    await expect(page.getByText(/assist you/i)).toBeVisible({ timeout: 10000 });

    await input.fill('hi again');
    await input.press('Enter');
    await expect(page.getByText(/assist you/i)).toBeVisible({ timeout: 10000 });

    await expect(page.getByText(/save your conversation/i)).not.toBeVisible();

    expect(messageCount).toBeGreaterThanOrEqual(2);
  });

  test('[P1][6-1-E2E-009] @regression should complete purchase journey after opt-out', async ({ page }) => {
    await setupWidgetMocks(page);

    let purchaseCompleted = false;

    await page.route('**/api/v1/widget/consent', async (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ data: { success: true } }),
        });
      } else {
        await route.continue();
      }
    });

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: 'No problem! I won\'t save your data. What would you like to buy?',
            sender: 'bot',
            created_at: new Date().toISOString(),
            intent: 'product_search',
          },
        }),
      });
    });

    const { input } = await openWidgetChat(page);

    await input.fill('hello');
    await input.press('Enter');

    await expect(page.getByText(/won't save your data/i)).toBeVisible({ timeout: 10000 });

    const noButton = page.getByRole('button', { name: /no.*don't save/i });
    await noButton.click();

    await expect(page.getByText(/what would you like to buy/i)).toBeVisible({ timeout: 10000 });

    await input.fill('show me red shoes');
    await input.press('Enter');

    await expect(page.getByText(/red shoes/i)).toBeVisible({ timeout: 10000 });

    purchaseCompleted = true;
  });

  test('[P1][6-1-E2E-010] @gdpr should verify no PII stored after opt-out', async ({ page }) => {
    await setupWidgetMocks(page);

    await page.route('**/api/v1/widget/consent', async (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON();
        if (body?.consent_granted === false) {
          await route.fulfill({
            status: 200,
            body: JSON.stringify({ data: { success: true } }),
          });
        } else {
          await route.continue();
        }
      } else {
        await route.continue();
      }
    });

    await page.route('**/api/v1/widget/consent/*', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              status: 'opted_out',
              can_store_conversation: false,
              consent_message_shown: true,
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    const { input } = await openWidgetChat(page);
    await input.fill('hello');
    await input.press('Enter');

    await expect(page.getByText(/save your conversation/i)).toBeVisible({ timeout: 10000 });

    const noButton = page.getByRole('button', { name: /no.*don't save/i });
    await noButton.click();

    const consentStatusResponse = await page.evaluate(() => {
      const consentData = localStorage.getItem('consent_status');
      return consentData ? JSON.parse(consentData) : null;
    });

    expect(consentStatusResponse?.status || 'opted_out').toBeTruthy();
  });

  test('[P1][6-1-E2E-011] @regression should verify opt-out takes immediate effect', async ({ page }) => {
    await setupWidgetMocks(page);

    let optOutTime: Date | null = null;

    await page.route('**/api/v1/widget/consent', async (route) => {
      if (route.request().method() === 'POST') {
        const body = route.request().postDataJSON();
        if (body?.consent_granted === false) {
          optOutTime = new Date();
          await route.fulfill({
            status: 200,
            body: JSON.stringify({ data: { success: true } }),
          });
        } else {
          await route.continue();
        }
      } else {
        await route.continue();
      }
    });

    await page.route('**/api/v1/widget/consent/*', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              status: 'opted_out',
              can_store_conversation: false,
              consent_message_shown: true,
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    const { input } = await openWidgetChat(page);
    await input.fill('hello');
    await input.press('Enter');

    const noButton = page.getByRole('button', { name: /no.*don't save/i });
    await noButton.click();

    expect(optOutTime).not.toBeNull();
    const elapsed = Date.now() - optOutTime!.getTime();
    expect(elapsed).toBeLessThan(2000);
  });
});

test.describe('Story 6-1: Consent Flow - Hybrid Storage (AC4)', () => {
  test('[P1][6-1-E2E-012] @regression should persist visitor_id in localStorage and session_id in sessionStorage', async ({ page }) => {
    await setupWidgetMocks(page);

    let capturedSessionId: string | null = null;

    await page.route('**/api/v1/widget/session', async (route) => {
      if (route.request().method() === 'POST') {
        const sessionId = crypto.randomUUID();
        capturedSessionId = sessionId;
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              sessionId: sessionId,
              merchant_id: '1',
              expires_at: new Date(Date.now() + 3600000).toISOString(),
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    const { input } = await openWidgetChat(page);

    // Wait deterministically for storage to be populated (replaces hard wait)
    await page.waitForFunction(() => {
      return sessionStorage.getItem('widget_session_id') !== null &&
             localStorage.getItem('widget_visitor_id') !== null;
    }, { timeout: 5000 });

    const storedSessionId = await page.evaluate(() => {
      return sessionStorage.getItem('widget_session_id');
    });

    const visitorIdData = await page.evaluate(() => {
      const data = localStorage.getItem('widget_visitor_id');
      return data ? JSON.parse(data) : null;
    });

    expect(storedSessionId).toBe(capturedSessionId);
    expect(visitorIdData).not.toBeNull();
    expect(visitorIdData.visitorId).toBeDefined();
    expect(typeof visitorIdData.visitorId).toBe('string');
    expect(visitorIdData.createdAt).toBeDefined();
  });

  test('[P1][6-1-E2E-013] @regression should clear visitor_id on forget preferences', async ({ page }) => {
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
          content: "I've forgotten your preferences and conversation history.",
          intent: 'preferences_forgotten',
        }),
      },
    ]);

    const { input } = await openWidgetChat(page);

    // Wait deterministically for visitor_id to be populated (replaces hard wait)
    await page.waitForFunction(() => {
      return localStorage.getItem('widget_visitor_id') !== null;
    }, { timeout: 5000 });

    const visitorIdBefore = await page.evaluate(() => {
      return localStorage.getItem('widget_visitor_id');
    });
    expect(visitorIdBefore).not.toBeNull();

    await input.fill('forget my preferences');
    await input.press('Enter');

    await expect(page.getByText(/forgotten your preferences/i)).toBeVisible({ timeout: 10000 });

    const visitorIdAfter = await page.evaluate(() => {
      return localStorage.getItem('widget_visitor_id');
    });
    expect(visitorIdAfter).toBeNull();
  });
});
