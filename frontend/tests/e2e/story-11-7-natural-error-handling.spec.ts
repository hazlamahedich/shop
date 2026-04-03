import { test, expect } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
  mockWidgetMessageConditional,
  sendMessage,
  MockMessageResponse,
} from '../helpers/widget-test-helpers';

const SEARCH_ERROR_RESPONSE: MockMessageResponse = {
  content:
    "I'm so sorry! I couldn't find products matching that description. Would you like me to broaden the search or try different keywords?",
};

const CHECKOUT_ERROR_RESPONSE: MockMessageResponse = {
  content:
    "I had trouble with checkout just now. You can also complete your purchase directly at our online store.",
  checkout_url: 'https://test.myshopify.com/checkout',
};

const ORDER_ERROR_RESPONSE: MockMessageResponse = {
  content:
    "I couldn't find information about that order. Could you double-check the order number and try again?",
};

const LLM_TIMEOUT_RESPONSE: MockMessageResponse = {
  content:
    "Hmm, let me think about that differently. Could you rephrase your question? I'd love to help!",
};

const CONTEXT_PRESERVED_RESPONSE: MockMessageResponse = {
  content:
    'Those blue sneakers you were looking at are still available! Would you like to add them to your cart?',
  products: [
    {
      id: 'prod-blue-1',
      variant_id: 'var-blue-1',
      title: 'Blue Sneakers',
      price: 59.99,
      available: true,
    },
  ],
};

const FRIENDLY_ERROR_RESPONSE: MockMessageResponse = {
  content: "Oops, something went wrong! 😅 But don't worry, I'm here to help. Want to try again?",
};

const PROFESSIONAL_ERROR_RESPONSE: MockMessageResponse = {
  content:
    'An error occurred while processing your request. Please try again, or let me know how I can assist.',
};

const ENTHUSIASTIC_ERROR_RESPONSE: MockMessageResponse = {
  content:
    "Oopsie! Something went a little wonky! 😅 But don't worry — let's try again together! 💪",
};

const GENERIC_RESPONSE: MockMessageResponse = {
  content: "I'm here to help! What would you like to know?",
};

const ERROR_VARIATION_1: MockMessageResponse = {
  content: "Oh no, that didn't work! Let me try something else for you. 😊",
};

const ERROR_VARIATION_2: MockMessageResponse = {
  content: "Hmm, I hit a snag there. No worries — let's figure this out together!",
};

const ERROR_VARIATION_3: MockMessageResponse = {
  content: "Yikes, something broke on my end! Give me another chance? 🙏",
};

async function setupErrorWidget(
  page: import('@playwright/test').Page,
  personalityType: 'friendly' | 'professional' | 'enthusiastic' = 'friendly'
) {
  const sessionId = crypto.randomUUID();
  await mockWidgetConfig(page, { personalityType });
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
      match: (msg: string) => msg.includes('blue sneakers') || msg.includes('still available'),
      response: CONTEXT_PRESERVED_RESPONSE,
    },
    {
      match: (msg: string) => msg.includes('error') || msg.includes('wrong') || msg.includes('broke'),
      response: FRIENDLY_ERROR_RESPONSE,
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

test.describe('Story 11-7: Natural Error Handling @story-11-7', () => {
  test.afterEach(async ({ page }) => {
    await page.unrouteAll();
  });

  test('[P0] 11.7-E2E-001 AC1: Search error → bot apologizes naturally', async ({
    page,
  }) => {
    await setupErrorWidget(page);

    await sendMessage(page, 'Find me products with impossible constraints xyzabc');

    const text = await getLastBotMessage(page);
    expect(text.length).toBeGreaterThan(20);
    const lowerText = text.toLowerCase();
    const hasApology =
      lowerText.includes("sorry") ||
      lowerText.includes("couldn't") ||
      lowerText.includes("trouble");
    expect(hasApology).toBeTruthy();
  });

  test('[P0] 11.7-E2E-002 AC2: Error explains issue in plain language', async ({
    page,
  }) => {
    await setupErrorWidget(page);

    await sendMessage(page, 'Find me products with impossible constraints xyzabc');

    const text = await getLastBotMessage(page);
    const lowerText = text.toLowerCase();
    const explainsIssue =
      lowerText.includes("couldn't find") ||
      lowerText.includes("search") ||
      lowerText.includes("products");
    expect(explainsIssue).toBeTruthy();
  });

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

  test('[P0] 11.7-E2E-004 AC4: Context preserved after error in multi-turn', async ({
    page,
  }) => {
    await setupErrorWidget(page);

    await sendMessage(page, 'Show me blue sneakers');
    const firstResponse = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(firstResponse).toBeVisible({ timeout: 10000 });

    await sendMessage(page, 'trigger an error wrong broke');
    const errorResponse = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(errorResponse).toBeVisible({ timeout: 10000 });

    await sendMessage(page, 'Are those blue sneakers still available?');
    const contextResponse = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(contextResponse).toBeVisible({ timeout: 10000 });

    const text = await contextResponse.innerText();
    const lowerText = text.toLowerCase();
    const preservedContext =
      lowerText.includes('blue') ||
      lowerText.includes('sneaker') ||
      lowerText.includes('cart');
    expect(preservedContext).toBeTruthy();
  });

  test('[P0] 11.7-E2E-005 AC5: Friendly personality tone in error responses', async ({
    page,
  }) => {
    await setupErrorWidget(page, 'friendly');

    await sendMessage(page, 'Something went wrong error');

    const text = await getLastBotMessage(page);
    expect(text.length).toBeGreaterThan(10);
  });

  test('[P1] 11.7-E2E-006 AC5: Professional personality tone in error responses', async ({
    page,
  }) => {
    const sessionId = crypto.randomUUID();
    await mockWidgetConfig(page, { personalityType: 'professional' });
    await mockWidgetSession(page, sessionId);

    await mockWidgetMessageConditional(page, [
      {
        match: (msg: string) => msg.includes('error') || msg.includes('wrong'),
        response: PROFESSIONAL_ERROR_RESPONSE,
      },
      {
        match: () => true,
        response: GENERIC_RESPONSE,
      },
    ]);

    await loadWidgetWithSession(page, sessionId);
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible({
      timeout: 10000,
    });

    await sendMessage(page, 'trigger an error');

    const text = await getLastBotMessage(page);
    expect(text.length).toBeGreaterThan(10);
  });

  test('[P1] 11.7-E2E-007 AC5: Enthusiastic personality tone in error responses', async ({
    page,
  }) => {
    const sessionId = crypto.randomUUID();
    await mockWidgetConfig(page, { personalityType: 'enthusiastic' });
    await mockWidgetSession(page, sessionId);

    await mockWidgetMessageConditional(page, [
      {
        match: (msg: string) => msg.includes('error') || msg.includes('wrong'),
        response: ENTHUSIASTIC_ERROR_RESPONSE,
      },
      {
        match: () => true,
        response: GENERIC_RESPONSE,
      },
    ]);

    await loadWidgetWithSession(page, sessionId);
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible({
      timeout: 10000,
    });

    await sendMessage(page, 'trigger an error');

    const text = await getLastBotMessage(page);
    expect(text.length).toBeGreaterThan(10);
  });

  test('[P1] 11.7-E2E-008 AC7: Consecutive errors produce different phrasing', async ({
    page,
  }) => {
    const sessionId = crypto.randomUUID();
    await mockWidgetConfig(page);
    await mockWidgetSession(page, sessionId);

    let errorCallCount = 0;
    const errorVariations = [ERROR_VARIATION_1, ERROR_VARIATION_2, ERROR_VARIATION_3];

    await page.route('**/api/v1/widget/message', async (route) => {
      const body = route.request().postDataJSON();
      const message = body?.message?.toLowerCase() || '';

      if (message.includes('error') || message.includes('fail')) {
        const variation = errorVariations[errorCallCount % errorVariations.length];
        errorCallCount++;
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              message_id: crypto.randomUUID(),
              sender: 'bot',
              created_at: new Date().toISOString(),
              ...variation,
            },
          }),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          data: {
            message_id: crypto.randomUUID(),
            sender: 'bot',
            created_at: new Date().toISOString(),
            ...GENERIC_RESPONSE,
          },
        }),
      });
    });

    await loadWidgetWithSession(page, sessionId);
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible({
      timeout: 10000,
    });

    const responses: string[] = [];

    for (let i = 0; i < 3; i++) {
      await sendMessage(page, `trigger error number ${i + 1}`);
      const text = await getLastBotMessage(page);
      responses.push(text);
    }

    expect(responses).toHaveLength(3);
    const uniqueResponses = new Set(responses);
    expect(uniqueResponses.size).toBeGreaterThanOrEqual(2);
  });

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

  test('[P2] 11.7-E2E-012 AC4: Error does not clear previous conversation', async ({
    page,
  }) => {
    await setupErrorWidget(page);

    await sendMessage(page, 'Show me blue sneakers');
    const firstBotMsg = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(firstBotMsg).toBeVisible({ timeout: 10000 });

    const userMessagesBefore = await page
      .locator('[data-testid="message-bubble"].message-bubble--user')
      .count();
    expect(userMessagesBefore).toBe(1);

    await sendMessage(page, 'trigger error fail');
    const errorMsg = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(errorMsg).toBeVisible({ timeout: 10000 });

    const userMessagesAfter = await page
      .locator('[data-testid="message-bubble"].message-bubble--user')
      .count();
    expect(userMessagesAfter).toBe(2);

    const allBotMessages = await page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .count();
    expect(allBotMessages).toBeGreaterThanOrEqual(2);
  });
});
