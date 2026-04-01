import { test, expect } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
  sendMessage,
  WIDGET_CONFIG_DEFAULTS,
} from '../helpers/widget-test-helpers';
import {
  mockMultiTurnConversation,
  GENERAL_MODE_HANDLERS,
} from '../helpers/multi-turn-test-helpers';

test.describe('Story 11.2 - Multi-Turn General Mode Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          data: {
            ...WIDGET_CONFIG_DEFAULTS,
            onboardingMode: 'general',
          },
        }),
      });
    });
    await mockWidgetSession(page, 'test-general-session');
    await mockMultiTurnConversation(page, [
      GENERAL_MODE_HANDLERS.accountProblem,
      GENERAL_MODE_HANDLERS.urgentSeverity,
      GENERAL_MODE_HANDLERS.timeframeResponse,
      GENERAL_MODE_HANDLERS.topicChange,
    ]);
    await loadWidgetWithSession(page, 'test-general-session');
  });

  test('[P2] 11.2-E2E-006 AC7: general mode clarification flow', async ({ page }) => {
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const responsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'I have a problem with my account');
    await responsePromise;

    await expect(page.getByText(/severe|severity/i)).toBeVisible();

    const severityResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'It is urgent');
    await severityResponsePromise;

    await expect(page.getByText(/when|started|timeframe/i)).toBeVisible();

    const timeResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'Started today');
    await timeResponsePromise;

    await expect(page.getByText(/urgent.*account|account.*today/i)).toBeVisible();
  });

  test('[P2] 11.2-E2E-007 AC9: general mode topic change resets', async ({ page }) => {
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const responsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'I have a problem with my account');
    await responsePromise;

    await expect(page.getByText(/severe/i)).toBeVisible();

    const topicResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'I want to buy some shoes');
    await topicResponsePromise;

    await expect(page.getByText("let's talk about that instead")).toBeVisible();
  });
});
