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
  CLARIFICATION_QUESTIONS,
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

    const responsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'I am looking for shoes');
    await responsePromise;

    await expect(page.getByText("What's your budget range?")).toBeVisible();

    const budgetResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'under $100');
    await budgetResponsePromise;

    await expect(page.getByText('brand')).toBeVisible();

    const brandResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'Nike');
    await brandResponsePromise;

    await expect(page.getByText('size')).toBeVisible();

    const sizeResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'size L');
    await sizeResponsePromise;

    await expect(page.getByText('Nike running shoes under $100')).toBeVisible();
  });

  test('[P0] 11.2-E2E-002 AC6: topic change resets multi-turn state', async ({ page }) => {
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const responsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'I am looking for shoes');
    await responsePromise;

    await expect(page.getByText("budget")).toBeVisible();

    const topicResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'I want to order a pizza instead');
    await topicResponsePromise;

    await expect(page.getByText("let's talk about that instead")).toBeVisible();
  });

  test('[P1] 11.2-E2E-003 AC5: invalid response triggers re-prompt', async ({ page }) => {
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const responsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'I am looking for shoes');
    await responsePromise;

    const invalidResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'asdf');
    await invalidResponsePromise;

    await expect(
      page.getByText(/rephrasing|didn't quite catch|try rephrasing/i)
    ).toBeVisible();
  });

  test('[P1] 11.2-E2E-004 AC4: turn limit enforcement shows results', async ({ page }) => {
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const responsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'I am looking for shoes');
    await responsePromise;

    await expect(page.getByText("budget")).toBeVisible();

    const budgetResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'under $100');
    await budgetResponsePromise;

    await expect(page.getByText('brand')).toBeVisible();

    const brandResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'Nike');
    await brandResponsePromise;

    await expect(page.getByText('size')).toBeVisible();

    const sizeResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'size L');
    await sizeResponsePromise;

    await expect(
      page.getByText(/Nike.*shoes|results|found/i)
    ).toBeVisible();
  });

  test('[P2] 11.2-E2E-005 AC1: conversation shows user and bot messages', async ({ page }) => {
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const responsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'I am looking for shoes');
    await responsePromise;

    const userMessages = page.locator('[data-testid="user-message"], .user-bubble, [class*="user"]');
    const botMessages = page.locator('[data-testid="bot-message"], .bot-bubble, [class*="bot"]');

    const userCount = await userMessages.count();
    const botCount = await botMessages.count();
    expect(userCount).toBeGreaterThanOrEqual(1);
    expect(botCount).toBeGreaterThanOrEqual(1);
  });
});
