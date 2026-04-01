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
  MULTI_TURN_HANDLERS,
  sendAndWaitForResponse,
  completeShoeClarification,
} from '../helpers/multi-turn-test-helpers';

test.describe('Story 11.2 - Multi-Turn Clarification Flow', () => {
  test.beforeEach(async ({ page }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-multi-turn-session');
    await mockMultiTurnConversation(page, [
      MULTI_TURN_HANDLERS.ambiguousQuery,
      MULTI_TURN_HANDLERS.budgetResponse,
      MULTI_TURN_HANDLERS.brandResponse,
      MULTI_TURN_HANDLERS.sizeResponse,
      MULTI_TURN_HANDLERS.topicChange,
      MULTI_TURN_HANDLERS.invalidResponse,
    ]);
    await loadWidgetWithSession(page, 'test-multi-turn-session');
  });

  test('[P0] 11.2-E2E-001 AC1: multi-turn clarification conversation flow', async ({ page }) => {
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await completeShoeClarification(page);

    await expect(page.getByText('Nike running shoes under $100')).toBeVisible();
  });

  test('[P0] 11.2-E2E-002 AC6: topic change resets multi-turn state', async ({ page }) => {
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForResponse(page, 'I am looking for shoes');

    await expect(page.getByText("budget")).toBeVisible();

    await sendAndWaitForResponse(page, 'I want to order a pizza instead');

    await expect(page.getByText("let's talk about that instead")).toBeVisible();
  });

  test('[P1] 11.2-E2E-003 AC5: invalid response triggers re-prompt', async ({ page }) => {
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForResponse(page, 'I am looking for shoes');
    await sendAndWaitForResponse(page, 'asdf');

    await expect(
      page.getByText(/rephrasing|didn't quite catch|try rephrasing/i)
    ).toBeVisible();
  });

  test('[P1] 11.2-E2E-004 AC4: turn limit enforcement shows results', async ({ page }) => {
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await completeShoeClarification(page);

    await expect(
      page.getByText(/Nike.*shoes|results|found/i)
    ).toBeVisible();
  });

  test('[P2] 11.2-E2E-005 AC1: conversation shows user and bot messages', async ({ page }) => {
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForResponse(page, 'I am looking for shoes');

    const userMessages = page.locator('[data-testid="message-bubble"].message-bubble--user');
    const botMessages = page.locator('[data-testid="message-bubble"].message-bubble--bot');

    const userCount = await userMessages.count();
    const botCount = await botMessages.count();
    expect(userCount).toBeGreaterThanOrEqual(1);
    expect(botCount).toBeGreaterThanOrEqual(1);
  });

  test('[P1] 11.2-E2E-008: network error during multi-turn shows recovery', async ({ page }) => {
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForResponse(page, 'I am looking for shoes');

    await expect(page.getByText('budget')).toBeVisible();

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 500,
        body: JSON.stringify({ error: 'Internal Server Error' }),
      });
    });

    const errorResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'under $100');
    await errorResponsePromise;

    await expect(
      page.getByText(/error|try again|something went wrong/i)
    ).toBeVisible();
  });
});
