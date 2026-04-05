import { test, expect } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
  mockWidgetMessageConditional,
  createMockMessageResponse,
  sendAndAwait,
  botMessages,
} from '../helpers/widget-test-helpers';

type SentimentType = 'empathetic' | 'escalation' | 'concise' | 'enthusiastic' | 'neutral' | 'product';

const SENTIMENT_CONTENT: Record<SentimentType, string> = {
  empathetic:
    "Oh no, I totally get the frustration! 😔 I'm sorry your order hasn't arrived yet. Let me look into this right away.\n\nWould you like me to connect you with someone who can help even more? 🤝",
  escalation:
    "It sounds like you could use some extra help. Let me connect you with a human agent who can assist you better. 🤝",
  concise: "Got it, let's get this sorted fast! ⚡ Your order #12345 shipped yesterday — tracking link: example.com/track",
  enthusiastic: "Awesome! 🎉 That's great to hear! Your order is confirmed and on its way!",
  neutral: 'Your store hours are Monday–Friday, 9 AM to 6 PM EST.',
  product: 'I found some great running shoes for you!',
};

function createSentimentResponse(
  sentiment: SentimentType,
  overrides: Record<string, unknown> = {}
) {
  return createMockMessageResponse({ content: SENTIMENT_CONTENT[sentiment], ...overrides });
}

test.describe('Story 11-10: Sentiment-Adaptive Responses @p1', () => {
  test.describe.configure({ retries: 2 });

  test('[P0] 11.10-E2E-001: frustrated message gets empathetic response with pre/post phrases (AC1, AC2)', async ({
    page,
  }) => {
    // Given: widget is loaded with sentiment-adaptive response routing
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-empathetic-session');
    await mockWidgetMessageConditional(page, [
      {
        match: (msg) =>
          ['frustrated', 'angry', 'upset', 'terrible', 'awful'].some((w) => msg.includes(w)),
        response: createSentimentResponse('empathetic'),
      },
    ]);
    await loadWidgetWithSession(page, 'test-empathetic-session');

    // When: user sends a frustrated message
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const { send, response } = sendAndAwait(page, 'I am so frustrated with my order!');
    await send();
    await response;

    // Then: response contains empathetic phrases and escalation offer
    await expect(botMessages(page).last()).toContainText(/frustration|totally get/i);
    await expect(botMessages(page).last()).toContainText(/connect you|help even more/i);
  });

  test('[P0] 11.10-E2E-002: consecutive frustration triggers escalation handoff (AC3)', async ({ page }) => {
    // Given: widget is loaded with escalation routing for repeated frustration
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-escalation-session');
    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('unacceptable') || msg.includes('escalation'),
        response: createSentimentResponse('escalation'),
      },
      {
        match: (msg) =>
          (msg.includes('where is my order') && !msg.includes('unacceptable')) ||
          msg.includes('still waiting'),
        response: createSentimentResponse('empathetic', {
          content:
            "Oh no, I totally get the frustration! 😔 I understand this is still not resolved.\n\nWould you like me to connect you with someone who can help even more? 🤝",
        }),
      },
      {
        match: (msg) =>
          ['frustrated', 'angry', 'upset', 'terrible'].some((w) => msg.includes(w)),
        response: createSentimentResponse('empathetic'),
      },
    ]);
    await loadWidgetWithSession(page, 'test-escalation-session');

    // When: user sends two consecutive frustrated messages
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const msg1 = sendAndAwait(page, 'I am frustrated with this service');
    await msg1.send();
    await msg1.response;
    await expect(botMessages(page).last()).toContainText(/frustration|totally get/i);

    const msg2 = sendAndAwait(page, 'This is unacceptable, where is my order?!');
    await msg2.send();
    await msg2.response;

    // Then: escalation handoff is triggered
    await expect(botMessages(page).last()).toContainText(/human agent|extra help/i);
  });

  test('[P1] 11.10-E2E-003: neutral message gets no adaptation — passthrough (AC5)', async ({ page }) => {
    // Given: widget is loaded with neutral response routing
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-neutral-session');
    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('hours') || msg.includes('store'),
        response: createSentimentResponse('neutral'),
      },
    ]);
    await loadWidgetWithSession(page, 'test-neutral-session');

    // When: user sends a neutral question
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const { send, response } = sendAndAwait(page, 'What are your store hours?');
    await send();
    await response;

    // Then: response is factual with no sentiment adaptation phrases
    await expect(botMessages(page).last()).toContainText('Monday–Friday');

    const chatDialog = page.getByRole('dialog', { name: 'Chat window' });
    await expect(chatDialog).not.toContainText('totally get the frustration');
    await expect(chatDialog).not.toContainText("let's get this sorted fast");
    await expect(chatDialog).not.toContainText('Awesome!');
  });

  test('[P1] 11.10-E2E-004: urgent message gets concise response (AC1)', async ({ page }) => {
    // Given: widget is loaded with concise response routing for urgent messages
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-concise-session');
    await mockWidgetMessageConditional(page, [
      {
        match: (msg) =>
          ['urgent', 'asap', 'quickly', 'right now', 'fast', 'hurry'].some((w) =>
            msg.includes(w)
          ),
        response: createSentimentResponse('concise'),
      },
    ]);
    await loadWidgetWithSession(page, 'test-concise-session');

    // When: user sends an urgent message
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const { send, response } = sendAndAwait(page, 'I need my order status ASAP!');
    await send();
    await response;

    // Then: response is concise and action-oriented
    await expect(botMessages(page).last()).toContainText(/sorted fast|Got it/i);
  });

  test('[P1] 11.10-E2E-005: happy message gets enthusiastic response (AC1)', async ({ page }) => {
    // Given: widget is loaded with enthusiastic response routing for positive messages
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-enthusiastic-session');
    await mockWidgetMessageConditional(page, [
      {
        match: (msg) =>
          ['love it', 'great', 'awesome', 'amazing', 'happy', 'excited'].some((w) =>
            msg.includes(w)
          ),
        response: createSentimentResponse('enthusiastic'),
      },
    ]);
    await loadWidgetWithSession(page, 'test-enthusiastic-session');

    // When: user sends a happy message
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const { send, response } = sendAndAwait(page, 'I love it! This is amazing!');
    await send();
    await response;

    // Then: response is enthusiastic and celebratory
    await expect(botMessages(page).last()).toContainText(/Awesome|🎉/i);
  });

  test('[P2] 11.10-E2E-006: multi-turn sentiment accumulation across conversation (AC4)', async ({
    page,
  }) => {
    // Given: widget is loaded with sentiment accumulation routing
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-accumulation-session');
    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('shoes') || msg.includes('running'),
        response: createSentimentResponse('product'),
      },
      {
        match: (msg) => msg.includes('wrong') || msg.includes('size'),
        response: createSentimentResponse('empathetic', {
          content:
            "Oh no, I totally get the frustration! 😔 I'm sorry to hear about the sizing issue.\n\nWould you like me to connect you with someone who can help even more? 🤝",
        }),
      },
      {
        match: (msg) => msg.includes('still') || msg.includes('frustrated'),
        response: createSentimentResponse('empathetic'),
      },
    ]);
    await loadWidgetWithSession(page, 'test-accumulation-session');

    // When: user progresses from neutral to frustrated across multiple turns
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const msg1 = sendAndAwait(page, 'Show me running shoes');
    await msg1.send();
    await msg1.response;
    await expect(botMessages(page).last()).toContainText('running shoes');

    const msg2 = sendAndAwait(page, 'The size is wrong on these');
    await msg2.send();
    await msg2.response;
    await expect(botMessages(page).last()).toContainText(/frustration|sorry to hear|totally get/i);

    // Then: continued frustration triggers empathetic escalation
    const msg3 = sendAndAwait(page, 'I am still frustrated about this');
    await msg3.send();
    await msg3.response;
    await expect(botMessages(page).last()).toContainText(/connect you|help even more/i);
  });
});
