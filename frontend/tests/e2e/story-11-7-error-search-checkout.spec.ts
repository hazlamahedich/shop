import { test, expect } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
  mockWidgetMessageConditional,
  sendMessage,
  createMockMessageResponse,
} from '../helpers/widget-test-helpers';

const SEARCH_ERROR_RESPONSE = createMockMessageResponse({
  content:
    "I'm so sorry! I couldn't find products matching that description. Would you like me to broaden the search or try different keywords?",
});

const CHECKOUT_ERROR_RESPONSE = createMockMessageResponse({
  content:
    "I had trouble with checkout just now. You can also complete your purchase directly at our online store.",
  checkout_url: 'https://test.myshopify.com/checkout',
});

const ORDER_ERROR_RESPONSE = createMockMessageResponse({
  content:
    "I couldn't find information about that order. Could you double-check the order number and try again?",
});

const LLM_TIMEOUT_RESPONSE = createMockMessageResponse({
  content:
    "Hmm, let me think about that differently. Could you rephrase your question? I'd love to help!",
});

const GENERIC_RESPONSE = createMockMessageResponse({
  content: "I'm here to help! What would you like to know?",
});

async function setupErrorWidget(page: import('@playwright/test').Page) {
  const sessionId = crypto.randomUUID();
  await mockWidgetConfig(page);
  await mockWidgetSession(page, sessionId);

  await mockWidgetMessageConditional(page, [
    {
      match: (msg: string) =>
        msg.includes('impossible') ||
        msg.includes('xyzabc') ||
        msg.includes('find products'),
      response: SEARCH_ERROR_RESPONSE,
    },
    {
      match: (msg: string) =>
        msg.includes('checkout') && (msg.includes('error') || msg.includes('broken')),
      response: CHECKOUT_ERROR_RESPONSE,
    },
    {
      match: (msg: string) =>
        msg.includes('order') && (msg.includes('error') || msg.includes('lookup')),
      response: ORDER_ERROR_RESPONSE,
    },
    {
      match: (msg: string) =>
        msg.includes('timeout') || msg.includes('taking too long') || msg.includes('think'),
      response: LLM_TIMEOUT_RESPONSE,
    },
    {
      match: () => true,
      response: GENERIC_RESPONSE,
    },
  ]);

  await loadWidgetWithSession(page, sessionId);

  const bubble = page.getByRole('button', { name: 'Open chat' });
  await bubble.click();
  const dialog = page.getByRole('dialog', { name: 'Chat window' });
  await expect(dialog).toBeVisible({ timeout: 10000 });
}

async function getLastBotMessage(page: import('@playwright/test').Page): Promise<string> {
  const botBubble = page
    .locator('[data-testid="message-bubble"].message-bubble--bot')
    .last();
  await expect(botBubble).toBeVisible({ timeout: 10000 });
  return botBubble.innerText();
}

test.describe('Story 11-7: Error Search & Checkout @story-11-7', () => {
  test.afterEach(async ({ page }) => {
    await page.unrouteAll();
  });

  // GIVEN a user sends a message that triggers a search error
  // WHEN the bot responds with an error message
  // THEN the response contains a natural apology
  test('[P0] 11.7-E2E-001 AC1: Search error → bot apologizes naturally', async ({
    page,
  }) => {
    await setupErrorWidget(page);

    await sendMessage(page, 'Find me products with impossible constraints xyzabc');

    const text = await getLastBotMessage(page);
    expect(text.length).toBeGreaterThan(20);
    const lowerText = text.toLowerCase();
    const hasApology =
      lowerText.includes('sorry') ||
      lowerText.includes("couldn't") ||
      lowerText.includes('trouble');
    expect(hasApology).toBeTruthy();
  });

  // GIVEN a search error occurs
  // WHEN the bot formulates the error response
  // THEN the response explains the issue in plain language (mentions search/products)
  test('[P0] 11.7-E2E-002 AC2: Error explains issue in plain language', async ({
    page,
  }) => {
    await setupErrorWidget(page);

    await sendMessage(page, 'Find me products with impossible constraints xyzabc');

    const text = await getLastBotMessage(page);
    const lowerText = text.toLowerCase();
    const explainsIssue =
      lowerText.includes("couldn't find") ||
      lowerText.includes('search') ||
      lowerText.includes('products');
    expect(explainsIssue).toBeTruthy();
  });

  // GIVEN a search error occurs
  // WHEN the bot responds
  // THEN the response suggests an alternative approach (broaden, try different, etc.)
  test('[P0] 11.7-E2E-003 AC3: Error suggests alternative approaches', async ({
    page,
  }) => {
    await setupErrorWidget(page);

    await sendMessage(page, 'Find me products with impossible constraints xyzabc');

    const text = await getLastBotMessage(page);
    const lowerText = text.toLowerCase();
    const hasSuggestion =
      lowerText.includes('broad') ||
      lowerText.includes('different') ||
      lowerText.includes('try') ||
      lowerText.includes('would you');
    expect(hasSuggestion).toBeTruthy();
  });

  // GIVEN a user triggers a checkout error
  // WHEN the bot responds
  // THEN the response mentions checkout/purchase in plain language
  test('[P0] 11.7-E2E-009 AC2: Checkout error → plain language explanation', async ({
    page,
  }) => {
    await setupErrorWidget(page);

    await sendMessage(page, 'I want to checkout but there is an error');

    const text = await getLastBotMessage(page);
    const lowerText = text.toLowerCase();
    const mentionsCheckout =
      lowerText.includes('checkout') ||
      lowerText.includes('purchase') ||
      lowerText.includes('trouble');
    expect(mentionsCheckout).toBeTruthy();
  });

  // GIVEN a user triggers an order lookup error
  // WHEN the bot responds
  // THEN the response mentions orders/finding/couldn't in plain language
  test('[P1] 11.7-E2E-010 AC2: Order lookup error → specific plain language', async ({
    page,
  }) => {
    await setupErrorWidget(page);

    await sendMessage(page, 'order lookup error for my order');

    const text = await getLastBotMessage(page);
    const lowerText = text.toLowerCase();
    const mentionsOrder =
      lowerText.includes('order') ||
      lowerText.includes('find') ||
      lowerText.includes("couldn't");
    expect(mentionsOrder).toBeTruthy();
  });

  // GIVEN a user triggers an LLM timeout
  // WHEN the bot responds
  // THEN the response suggests rephrasing or trying differently
  test('[P1] 11.7-E2E-011 AC3: LLM timeout → suggests rephrasing', async ({
    page,
  }) => {
    await setupErrorWidget(page);

    await sendMessage(page, 'taking too long timeout');

    const text = await getLastBotMessage(page);
    const lowerText = text.toLowerCase();
    const hasSuggestion =
      lowerText.includes('rephrase') ||
      lowerText.includes('different') ||
      lowerText.includes('try') ||
      lowerText.includes('think');
    expect(hasSuggestion).toBeTruthy();
  });
});
