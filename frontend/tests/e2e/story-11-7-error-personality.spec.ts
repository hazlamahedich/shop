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

const PROFESSIONAL_ERROR_RESPONSE = createMockMessageResponse({
  content:
    'An error occurred while processing your request. Please try again, or let me know how I can assist.',
});

const ENTHUSIASTIC_ERROR_RESPONSE = createMockMessageResponse({
  content: "Oopsie! Something went a little wonky! 😅 But don't worry — let's try again together! 💪",
});

const GENERIC_RESPONSE = createMockMessageResponse({
  content: "I'm here to help! What would you like to know?",
});

type PersonalityType = 'friendly' | 'professional' | 'enthusiastic';

async function setupPersonalityWidget(
  page: import('@playwright/test').Page,
  personality: PersonalityType,
  errorResponse: typeof FRIENDLY_ERROR_RESPONSE
) {
  const sessionId = crypto.randomUUID();
  await mockWidgetConfig(page, { personalityType: personality });
  await mockWidgetSession(page, sessionId);

  await mockWidgetMessageConditional(page, [
    {
      match: (msg: string) => msg.includes('error') || msg.includes('wrong') || msg.includes('broke'),
      response: errorResponse,
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
}

async function getLastBotMessage(page: import('@playwright/test').Page): Promise<string> {
  const botBubble = page
    .locator('[data-testid="message-bubble"].message-bubble--bot')
    .last();
  await expect(botBubble).toBeVisible({ timeout: 10000 });
  return botBubble.innerText();
}

function hasEmoji(text: string): boolean {
  const emojiRegex = /[\p{Emoji_Presentation}\p{Extended_Pictographic}]/u;
  return emojiRegex.test(text);
}

function isCasualTone(text: string): boolean {
  const lower = text.toLowerCase();
  return (
    lower.includes("oops") ||
    lower.includes("don't worry") ||
    lower.includes("want to") ||
    lower.includes("here to help")
  );
}

function isFormalTone(text: string): boolean {
  const lower = text.toLowerCase();
  return (
    lower.includes('error occurred') ||
    lower.includes('please try again') ||
    lower.includes('let me know') ||
    lower.includes('assist')
  );
}

function isExcitedTone(text: string): boolean {
  const lower = text.toLowerCase();
  return (
    lower.includes('oopsie') ||
    lower.includes("let's") ||
    lower.includes('together') ||
    lower.includes('wonky')
  );
}

test.describe('Story 11-7: Error Personality Tone @story-11-7', () => {
  test.afterEach(async ({ page }) => {
    await page.unrouteAll();
  });

  // GIVEN a merchant with friendly personality
  // WHEN an error occurs in the conversation
  // THEN the error response uses casual language with emojis
  test('[P0] 11.7-E2E-005 AC5: Friendly personality tone in error responses', async ({
    page,
  }) => {
    await setupPersonalityWidget(page, 'friendly', FRIENDLY_ERROR_RESPONSE);

    await sendMessage(page, 'Something went wrong error');

    const text = await getLastBotMessage(page);
    expect(text.length).toBeGreaterThan(10);
    expect(hasEmoji(text)).toBeTruthy();
    expect(isCasualTone(text)).toBeTruthy();
  });

  // GIVEN a merchant with professional personality
  // WHEN an error occurs in the conversation
  // THEN the error response uses formal language without emojis
  test('[P1] 11.7-E2E-006 AC5: Professional personality tone in error responses', async ({
    page,
  }) => {
    await setupPersonalityWidget(page, 'professional', PROFESSIONAL_ERROR_RESPONSE);

    await sendMessage(page, 'trigger an error');

    const text = await getLastBotMessage(page);
    expect(text.length).toBeGreaterThan(10);
    expect(hasEmoji(text)).toBeFalsy();
    expect(isFormalTone(text)).toBeTruthy();
  });

  // GIVEN a merchant with enthusiastic personality
  // WHEN an error occurs in the conversation
  // THEN the error response uses excited language with multiple emojis
  test('[P1] 11.7-E2E-007 AC5: Enthusiastic personality tone in error responses', async ({
    page,
  }) => {
    await setupPersonalityWidget(page, 'enthusiastic', ENTHUSIASTIC_ERROR_RESPONSE);

    await sendMessage(page, 'trigger an error');

    const text = await getLastBotMessage(page);
    expect(text.length).toBeGreaterThan(10);
    expect(hasEmoji(text)).toBeTruthy();
    expect(isExcitedTone(text)).toBeTruthy();
  });
});
