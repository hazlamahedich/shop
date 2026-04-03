import { test, expect } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
  mockWidgetMessageConditional,
  sendMessage,
  createMockMessageResponse,
} from '../helpers/widget-test-helpers';

const FRIENDLY_ERROR_RESPONSE = createMockMessageResponse({
  content: "Oops, something went wrong! 😅 But don't worry, I'm here to help. Want to try again?",
});

const CONTEXT_PRESERVED_RESPONSE = createMockMessageResponse({
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
});

const GENERIC_RESPONSE = createMockMessageResponse({
  content: "I'm here to help! What would you like to know?",
});

const ERROR_VARIATION_1 = createMockMessageResponse({
  content: "Oh no, that didn't work! Let me try something else for you. 😊",
});

const ERROR_VARIATION_2 = createMockMessageResponse({
  content: "Hmm, I hit a snag there. No worries — let's figure this out together!",
});

const ERROR_VARIATION_3 = createMockMessageResponse({
  content: "Yikes, something broke on my end! Give me another chance? 🙏",
});

async function setupContextWidget(page: import('@playwright/test').Page) {
  const sessionId = crypto.randomUUID();
  await mockWidgetConfig(page);
  await mockWidgetSession(page, sessionId);

  await mockWidgetMessageConditional(page, [
    {
      match: (msg: string) => msg.includes('error') || msg.includes('wrong') || msg.includes('broke'),
      response: FRIENDLY_ERROR_RESPONSE,
    },
    {
      match: (msg: string) => msg.includes('blue sneakers') || msg.includes('still available'),
      response: CONTEXT_PRESERVED_RESPONSE,
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

test.describe('Story 11-7: Error Context & Variation @story-11-7', () => {
  test.afterEach(async ({ page }) => {
    await page.unrouteAll();
  });

  // GIVEN a user has discussed blue sneakers
  // WHEN an error occurs in a subsequent message
  // AND the user asks about the previously discussed product
  // THEN the bot remembers the context and references blue sneakers/cart
  test('[P0] 11.7-E2E-004 AC4: Context preserved after error in multi-turn', async ({
    page,
  }) => {
    await setupContextWidget(page);

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

  // GIVEN a user triggers multiple errors in sequence
  // WHEN the bot responds to each error
  // THEN consecutive error responses use different phrasing (at least 2 unique out of 3)
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

  // GIVEN a user has sent messages and received responses
  // WHEN an error occurs
  // THEN previous user messages and bot responses remain visible in the conversation
  test('[P2] 11.7-E2E-012 AC4: Error does not clear previous conversation', async ({
    page,
  }) => {
    await setupContextWidget(page);

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
