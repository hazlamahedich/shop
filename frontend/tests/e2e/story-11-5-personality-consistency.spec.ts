import { test, expect } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
  sendMessage,
} from '../helpers/widget-test-helpers';
import { sendAndWaitForResponse } from '../helpers/multi-turn-test-helpers';

function countEmojis(text: string): number {
  let count = 0;
  for (const char of text) {
    const cp = char.codePointAt(0);
    if (
      cp &&
      cp >= 0x2600 &&
      (cp <= 0x27b0 || (cp >= 0x1f300 && cp <= 0x1faff) || (cp >= 0xfe00 && cp <= 0xfe0f))
    ) {
      count++;
    }
  }
  return count;
}

const SLANG_WORDS = /\b(awesome|cool|gonna|wanna|yeah|yep|nope|omg|lol|brb|btw|tbh|yolo)\b/i;

function hasExclamation(text: string): boolean {
  return text.includes('!');
}

function hasSlang(text: string): boolean {
  return SLANG_WORDS.test(text);
}

async function waitForNthBotBubble(
  page: import('@playwright/test').Page,
  index: number,
  timeout = 10000
) {
  const botBubble = page
    .locator('[data-testid="message-bubble"].message-bubble--bot')
    .nth(index);
  await botBubble.waitFor({ state: 'attached', timeout });
}

async function sendAndWaitForBotResponse(
  page: import('@playwright/test').Page,
  message: string,
  botBubbleIndex: number
) {
  await sendAndWaitForResponse(page, message);
  await waitForNthBotBubble(page, botBubbleIndex);
}

async function getBotMessageTexts(page: import('@playwright/test').Page, expectedCount: number): Promise<string[]> {
  const botBubbles = page.locator('[data-testid="message-bubble"].message-bubble--bot');
  await expect(botBubbles).toHaveCount(expectedCount, { timeout: 10000 });
  const texts: string[] = [];
  for (let i = 0; i < expectedCount; i++) {
    const text = await botBubbles.nth(i).innerText();
    texts.push(text);
  }
  return texts;
}

const PROFESSIONAL_RESPONSES = [
  'Thank you for your inquiry. Our available products are listed below with current pricing.',
  'The item you selected is priced at $49.99. Would you like to proceed with the order?',
  'Your order #1234 has been confirmed. You will receive a confirmation email shortly.',
  'We offer free shipping on orders over $50. Standard delivery takes 3 to 5 business days.',
  'Our return policy allows returns within 30 days of purchase. Please retain your receipt.',
  'The product dimensions are 12 x 8 x 4 inches. Weight is approximately 2.5 pounds.',
];

const FRIENDLY_RESPONSES = [
  "Hey there! 👋 Great to see you! Let me help you find what you're looking for.",
  "Sure thing! We've got some really nice options for you to check out.",
  "That's a solid pick — it's one of our most popular items right now!",
  "No worries at all! I'm here to help with whatever you need.",
  "Great choice! That one usually ships pretty fast, too.",
  "Thanks for stopping by! Let me know if you need anything else.",
];

const ENTHUSIASTIC_RESPONSES = [
  "Hello!! 🎉 I'm SO excited to help you shop today!! Let's find something amazing!",
  "Oh wow, great taste!! That item is absolutely FABULOUS!! 🌟",
  "Fantastic choice!! You're going to LOVE it!! Order #5678 is all set!",
  "YES!! We have FREE shipping on this one!! How awesome is that!! 🚀",
  "This is one of our BEST sellers!! Customers can't get enough of it!! ✨",
  "Thank you SO much for shopping with us!! You're the best!! 🎊",
];

async function setupWidgetWithPersonality(
  page: import('@playwright/test').Page,
  personalityType: 'friendly' | 'professional' | 'enthusiastic',
  responses: string[],
  sessionId: string
) {
  await mockWidgetConfig(page, { personalityType });
  await mockWidgetSession(page, sessionId);

  let callIndex = 0;
  await page.route('**/api/v1/widget/message', async (route) => {
    const responseContent = responses[callIndex] || responses[responses.length - 1];
    callIndex++;
    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        data: {
          message_id: crypto.randomUUID(),
          sender: 'bot',
          created_at: new Date().toISOString(),
          content: responseContent,
        },
      }),
    });
  });

  await loadWidgetWithSession(page, sessionId);
}

const USER_MESSAGES = [
  'Hello, what products do you have?',
  'Tell me about the blue one',
  'I would like to order that',
  'What about shipping options?',
  'Can you tell me the dimensions?',
  'Thank you, that is all',
];

test.describe('Story 11.5 - Personality Consistency', () => {
  test('[P0] 11.5-E2E-001 AC1: professional personality remains consistent across all turns', async ({
    page,
  }) => {
    await setupWidgetWithPersonality(page, 'professional', PROFESSIONAL_RESPONSES, 'test-prof-session');

    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    for (let i = 0; i < USER_MESSAGES.length; i++) {
      await sendAndWaitForBotResponse(page, USER_MESSAGES[i], i);
    }

    const botTexts = await getBotMessageTexts(page, USER_MESSAGES.length);

    for (let i = 0; i < botTexts.length; i++) {
      const text = botTexts[i];
      expect(countEmojis(text), `Professional turn ${i}: no emojis expected`).toBe(0);
      expect(hasSlang(text), `Professional turn ${i}: no slang expected`).toBe(false);
    }
  });

  test('[P0] 11.5-E2E-002 AC1: friendly personality remains consistent across all turns', async ({
    page,
  }) => {
    await setupWidgetWithPersonality(page, 'friendly', FRIENDLY_RESPONSES, 'test-friend-session');

    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    for (let i = 0; i < USER_MESSAGES.length; i++) {
      await sendAndWaitForBotResponse(page, USER_MESSAGES[i], i);
    }

    const botTexts = await getBotMessageTexts(page, USER_MESSAGES.length);

    for (let i = 0; i < botTexts.length; i++) {
      const text = botTexts[i];
      expect(countEmojis(text), `Friendly turn ${i}: max 2 emojis allowed`).toBeLessThanOrEqual(2);
    }
  });

  test('[P0] 11.5-E2E-003 AC1: enthusiastic personality remains consistent across all turns', async ({
    page,
  }) => {
    await setupWidgetWithPersonality(page, 'enthusiastic', ENTHUSIASTIC_RESPONSES, 'test-enth-session');

    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    for (let i = 0; i < USER_MESSAGES.length; i++) {
      await sendAndWaitForBotResponse(page, USER_MESSAGES[i], i);
    }

    const botTexts = await getBotMessageTexts(page, USER_MESSAGES.length);

    for (let i = 0; i < botTexts.length; i++) {
      const text = botTexts[i];
      expect(hasExclamation(text), `Enthusiastic turn ${i}: at least 1 exclamation expected`).toBe(true);
      expect(countEmojis(text), `Enthusiastic turn ${i}: max 10 emojis allowed`).toBeLessThanOrEqual(10);
    }
  });

  test('[P1] 11.5-E2E-004 AC2: personality persists through clarification loops', async ({ page }) => {
    const clarificationResponses = [
      "I'd be happy to assist. Could you please specify the product category you are interested in?",
      'Understood. Electronics are available in our catalog. What is your preferred price range?',
      'We have several options between $50 and $100. Here are the matching results.',
      'Thank you for your patience. Is there anything else I can assist you with?',
    ];
    const clarificationMessages = [
      'I need help finding something',
      'Electronics',
      'Between 50 and 100 dollars',
      'That is all, thanks',
    ];

    await setupWidgetWithPersonality(
      page,
      'professional',
      clarificationResponses,
      'test-clarify-session'
    );

    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    for (let i = 0; i < clarificationMessages.length; i++) {
      await sendAndWaitForBotResponse(page, clarificationMessages[i], i);
    }

    const botTexts = await getBotMessageTexts(page, clarificationMessages.length);

    for (let i = 0; i < botTexts.length; i++) {
      expect(countEmojis(botTexts[i]), `Clarification turn ${i}: no emojis`).toBe(0);
      expect(hasSlang(botTexts[i]), `Clarification turn ${i}: no slang`).toBe(false);
    }
  });

  test('[P1] 11.5-E2E-005 AC3: personality does not conflict with clarity', async ({ page }) => {
    const clarityResponses = [
      'The total for your order is $149.99, including tax and shipping. Would you like to proceed?',
      'Your order #9876 has been placed. Estimated delivery is March 15, 2026.',
      'The refund of $29.99 will be processed within 5 to 7 business days to your original payment method.',
    ];
    const clarityMessages = ['What is the total?', 'Place the order', 'I want a refund'];

    await setupWidgetWithPersonality(page, 'professional', clarityResponses, 'test-clarity-session');

    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    for (let i = 0; i < clarityMessages.length; i++) {
      await sendAndWaitForBotResponse(page, clarityMessages[i], i);
    }

    const botTexts = await getBotMessageTexts(page, clarityMessages.length);

    for (const text of botTexts) {
      expect(countEmojis(text), 'Clarity: no emojis in professional responses').toBe(0);
      expect(hasSlang(text), 'Clarity: no slang in professional responses').toBe(false);
    }

    expect(botTexts[0]).toContain('$149.99');
    expect(botTexts[1]).toContain('#9876');
  });

  test('[P1] 11.5-E2E-006 AC4: bot introduction is consistent with personality', async ({ page }) => {
    const introResponses = [
      'Good day. I am your shopping assistant. How may I help you today?',
    ];

    await setupWidgetWithPersonality(page, 'professional', introResponses, 'test-intro-session');

    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForBotResponse(page, 'Hello', 0);

    const botTexts = await getBotMessageTexts(page, 1);

    const intro = botTexts[0];
    expect(countEmojis(intro), 'Intro: no emojis for professional').toBe(0);
    expect(hasSlang(intro), 'Intro: no slang for professional').toBe(false);
    expect(intro.length).toBeGreaterThan(10);
  });

  test('[P2] 11.5-E2E-007 AC11: error response maintains personality', async ({ page }) => {
    let callIndex = 0;
    const initialResponse = 'Thank you for your inquiry. How may I assist you today?';
    await mockWidgetConfig(page, { personalityType: 'professional' });
    await mockWidgetSession(page, 'test-error-session');
    await page.route('**/api/v1/widget/message', async (route) => {
      if (callIndex === 0) {
        callIndex++;
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              message_id: crypto.randomUUID(),
              sender: 'bot',
              created_at: new Date().toISOString(),
              content: initialResponse,
            },
          }),
        });
      } else {
        await route.fulfill({
          status: 500,
          body: JSON.stringify({ error: 'Internal Server Error' }),
        });
      }
    });
    await loadWidgetWithSession(page, 'test-error-session');

    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForBotResponse(page, 'Hello there', 0);

    const errorResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'This should fail');
    await errorResponsePromise;

    const errorAlert = page.locator('[role="alert"]').first();
    await expect(errorAlert).toBeVisible({ timeout: 5000 });

    const errorTitle = errorAlert.locator('.error-toast__title');
    const errorDetail = errorAlert.locator('.error-toast__detail');
    const titleText = await errorTitle.innerText();
    const detailText = (await errorDetail.isVisible()) ? await errorDetail.innerText() : '';
    const errorText = `${titleText} ${detailText}`;
    expect(countEmojis(errorText), 'Error toast: no emojis for professional').toBe(0);
    expect(hasSlang(errorText), 'Error toast: no slang for professional').toBe(false);
  });

  test('[P2] 11.5-E2E-008 AC2: enthusiastic personality persists through extended conversation', async ({
    page,
  }) => {
    const extendedResponses = [
      "Hey!! Welcome!! 🎉 I'm thrilled to help you today!!",
      "Oh awesome!! Great question!! Let me check that for you!!",
      "Here it is!! This is a PERFECT match!! 🌟",
      "You bet!! Anything else you need!! I'm here all day!!",
      "Wonderful!! Thanks for chatting!! Come back soon!! 💫",
    ];
    const extendedMessages = ['Hi there', 'Show me options', 'I like that one', 'One more thing', 'Goodbye'];

    await setupWidgetWithPersonality(page, 'enthusiastic', extendedResponses, 'test-extended-session');

    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    for (let i = 0; i < extendedMessages.length; i++) {
      await sendAndWaitForBotResponse(page, extendedMessages[i], i);
    }

    const botTexts = await getBotMessageTexts(page, extendedMessages.length);

    for (let i = 0; i < botTexts.length; i++) {
      expect(hasExclamation(botTexts[i]), `Extended turn ${i}: exclamation expected`).toBe(true);
      expect(countEmojis(botTexts[i]), `Extended turn ${i}: max 10 emojis`).toBeLessThanOrEqual(10);
    }
  });
});
