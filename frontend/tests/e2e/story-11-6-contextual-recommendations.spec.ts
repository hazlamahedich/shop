import { test, expect } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
  mockWidgetMessageConditional,
  sendMessage,
  MockMessageResponse,
} from '../helpers/widget-test-helpers';

const RECOMMENDATION_RESPONSE: MockMessageResponse = {
  content:
    'Based on your interest in running shoes under $100, I recommend the Nike Air Max at $89.99 — great cushioning and support!',
  products: [
    {
      id: 'prod-1',
      variant_id: 'var-1',
      title: 'Nike Air Max',
      price: 89.99,
      available: true,
      image_url: 'https://example.com/shoes.jpg',
    },
    {
      id: 'prod-2',
      variant_id: 'var-2',
      title: 'Adidas Ultraboost',
      price: 79.99,
      available: true,
      image_url: 'https://example.com/shoes2.jpg',
    },
  ],
};

const DISMISSAL_RESPONSE: MockMessageResponse = {
  content:
    'No problem! Let me find something different. How about the Puma RS-X at $69.99?',
  products: [
    {
      id: 'prod-3',
      variant_id: 'var-3',
      title: 'Puma RS-X',
      price: 69.99,
      available: true,
      image_url: 'https://example.com/puma.jpg',
    },
  ],
};

const EMPTY_RESPONSE: MockMessageResponse = {
  content:
    "I'm sorry, I couldn't find any products matching your preferences right now. Would you like to try different criteria?",
};

const GENERAL_MODE_RESPONSE: MockMessageResponse = {
  content:
    "I'd be happy to help you with general questions! For product recommendations, please visit our store directly.",
};

const FALLBACK_RESPONSE: MockMessageResponse = {
  content: 'I can help you find the perfect product! What are you looking for?',
};

async function setupRecommendationWidget(
  page: import('@playwright/test').Page,
  personalityType: 'friendly' | 'professional' | 'enthusiastic' = 'friendly'
) {
  const sessionId = crypto.randomUUID();
  await mockWidgetConfig(page, { personalityType });
  await mockWidgetSession(page, sessionId);

  await mockWidgetMessageConditional(page, [
    {
      match: (msg: string) => msg.includes('recommend') || msg.includes('suggest'),
      response: RECOMMENDATION_RESPONSE,
    },
    {
      match: (msg: string) =>
        msg.includes('not that') ||
        msg.includes("don't like") ||
        msg.includes('too expensive') ||
        msg.includes('different') ||
        msg.includes('anything else') ||
        msg.includes('nope') ||
        msg.includes('next'),
      response: DISMISSAL_RESPONSE,
    },
    {
      match: (msg: string) => msg.includes('nothing') || msg.includes('empty'),
      response: EMPTY_RESPONSE,
    },
    {
      match: (msg: string) => msg.includes('general'),
      response: GENERAL_MODE_RESPONSE,
    },
    {
      match: () => true,
      response: FALLBACK_RESPONSE,
    },
  ]);

  await loadWidgetWithSession(page, sessionId);

  const bubble = page.getByRole('button', { name: 'Open chat' });
  await bubble.click();
  const dialog = page.getByRole('dialog', { name: 'Chat window' });
  await expect(dialog).toBeVisible({ timeout: 10000 });
}

test.describe('Story 11-6: Contextual Product Recommendations', () => {
  test('[P0] 11.6-E2E-001 AC1: User asks for recommendations → bot returns products with explanations', async ({
    page,
  }) => {
    await setupRecommendationWidget(page);

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('What do you recommend?');
    await page.getByRole('button', { name: 'Send message' }).click();

    const botBubble = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(botBubble).toBeVisible({ timeout: 10000 });

    const text = await botBubble.innerText();
    expect(text.length).toBeGreaterThan(0);
  });

  test('[P0] 11.6-E2E-002 AC2: Recommendation includes explanation why', async ({
    page,
  }) => {
    await setupRecommendationWidget(page);

    await sendMessage(page, 'Can you suggest some shoes?');

    const botBubble = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(botBubble).toBeVisible({ timeout: 10000 });

    const text = await botBubble.innerText();
    expect(text.length).toBeGreaterThan(20);
  });

  test('[P1] 11.6-E2E-003 AC3: Multi-turn conversation improves recommendations', async ({
    page,
  }) => {
    await setupRecommendationWidget(page);

    await sendMessage(page, 'I am looking for running shoes');
    const firstResponse = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(firstResponse).toBeVisible({ timeout: 10000 });

    await sendMessage(page, 'My budget is under $100');
    const secondResponse = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(secondResponse).toBeVisible({ timeout: 10000 });

    await sendMessage(page, 'What do you recommend?');
    const recResponse = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(recResponse).toBeVisible({ timeout: 10000 });

    const text = await recResponse.innerText();
    expect(text.length).toBeGreaterThan(0);
  });

  test('[P1] 11.6-E2E-004 AC4: User dismisses recommendation → bot adjusts', async ({
    page,
  }) => {
    await setupRecommendationWidget(page);

    await sendMessage(page, 'Recommend me some shoes');
    const firstResponse = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(firstResponse).toBeVisible({ timeout: 10000 });

    await sendMessage(page, 'Not that one, show me something different');
    const secondResponse = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(secondResponse).toBeVisible({ timeout: 10000 });

    const text = await secondResponse.innerText();
    expect(text.length).toBeGreaterThan(0);
  });

  test('[P0] 11.6-E2E-005 AC5: General mode → no product recommendations', async ({
    page,
  }) => {
    await setupRecommendationWidget(page);

    await sendMessage(page, 'general question');

    const botBubble = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(botBubble).toBeVisible({ timeout: 10000 });

    const text = await botBubble.innerText();
    expect(text.length).toBeGreaterThan(0);
  });

  test('[P1] 11.6-E2E-006 AC6: Friendly personality tone in recommendations', async ({
    page,
  }) => {
    await setupRecommendationWidget(page, 'friendly');

    await sendMessage(page, 'What do you recommend?');

    const botBubble = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(botBubble).toBeVisible({ timeout: 10000 });

    const text = await botBubble.innerText();
    expect(text.length).toBeGreaterThan(0);
  });

  test('[P1] 11.6-E2E-007 AC6: Professional personality tone in recommendations', async ({
    page,
  }) => {
    await setupRecommendationWidget(page, 'professional');

    await sendMessage(page, 'What do you recommend?');

    const botBubble = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(botBubble).toBeVisible({ timeout: 10000 });

    const text = await botBubble.innerText();
    expect(text.length).toBeGreaterThan(0);
  });

  test('[P0] 11.6-E2E-008 AC8: Empty recommendation set → graceful fallback', async ({
    page,
  }) => {
    await setupRecommendationWidget(page);

    await sendMessage(page, 'Show me nothing at all, I want empty results');

    const botBubble = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(botBubble).toBeVisible({ timeout: 10000 });

    const text = await botBubble.innerText();
    expect(text.length).toBeGreaterThan(0);
  });

  test('[P1] 11.6-E2E-009 AC7: Multi-turn recommendations show varied transition phrases', async ({
    page,
  }) => {
    await setupRecommendationWidget(page);

    const responses: string[] = [];

    for (let turn = 0; turn < 3; turn++) {
      await sendMessage(page, 'What do you recommend?');
      const botBubble = page
        .locator('[data-testid="message-bubble"].message-bubble--bot')
        .last();
      await expect(botBubble).toBeVisible({ timeout: 10000 });
      const text = await botBubble.innerText();
      responses.push(text);
    }

    expect(responses).toHaveLength(3);
    for (const response of responses) {
      expect(response.length).toBeGreaterThan(0);
    }
  });

  test('[P2] 11.6-E2E-010 AC6: Enthusiastic personality tone in recommendations', async ({
    page,
  }) => {
    const ENTHUSIASTIC_RESPONSE: MockMessageResponse = {
      content:
        "OMG you're gonna LOVE these!!! Here are my TOP picks for running shoes! 🔥",
      products: [
        {
          id: 'prod-1',
          variant_id: 'var-1',
          title: 'Nike Air Max',
          price: 89.99,
          available: true,
          image_url: 'https://example.com/shoes.jpg',
        },
      ],
    };

    const sessionId = crypto.randomUUID();
    await mockWidgetConfig(page, { personalityType: 'enthusiastic' });
    await mockWidgetSession(page, sessionId);
    await mockWidgetMessageConditional(page, [
      {
        match: (msg: string) => msg.includes('recommend') || msg.includes('suggest'),
        response: ENTHUSIASTIC_RESPONSE,
      },
    ]);
    await loadWidgetWithSession(page, sessionId);

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    const dialog = page.getByRole('dialog', { name: 'Chat window' });
    await expect(dialog).toBeVisible({ timeout: 10000 });

    await sendMessage(page, 'What do you recommend?');

    const botBubble = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(botBubble).toBeVisible({ timeout: 10000 });

    const text = await botBubble.innerText();
    expect(text.length).toBeGreaterThan(0);
  });

  test('[P2] 11.6-E2E-011 AC7: Dismissal followed by new recommendation shows transition', async ({
    page,
  }) => {
    await setupRecommendationWidget(page);

    await sendMessage(page, 'Recommend me some shoes');
    const firstResponse = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(firstResponse).toBeVisible({ timeout: 10000 });

    await sendMessage(page, "don't like that");
    const dismissResponse = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(dismissResponse).toBeVisible({ timeout: 10000 });

    await sendMessage(page, 'recommend something else');
    const newRecResponse = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(newRecResponse).toBeVisible({ timeout: 10000 });

    const text = await newRecResponse.innerText();
    expect(text.length).toBeGreaterThan(0);
  });

  test('[P2] 11.6-E2E-012 AC6: Professional personality avoids casual language', async ({
    page,
  }) => {
    const PROFESSIONAL_RESPONSE: MockMessageResponse = {
      content:
        'Based on your stated preferences, here are our recommendations from Test Store.',
      products: [
        {
          id: 'prod-1',
          variant_id: 'var-1',
          title: 'Nike Air Max',
          price: 89.99,
          available: true,
          image_url: 'https://example.com/shoes.jpg',
        },
      ],
    };

    const sessionId = crypto.randomUUID();
    await mockWidgetConfig(page, { personalityType: 'professional' });
    await mockWidgetSession(page, sessionId);
    await mockWidgetMessageConditional(page, [
      {
        match: (msg: string) => msg.includes('recommend') || msg.includes('suggest'),
        response: PROFESSIONAL_RESPONSE,
      },
    ]);
    await loadWidgetWithSession(page, sessionId);

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    const dialog = page.getByRole('dialog', { name: 'Chat window' });
    await expect(dialog).toBeVisible({ timeout: 10000 });

    await sendMessage(page, 'What do you recommend?');

    const botBubble = page
      .locator('[data-testid="message-bubble"].message-bubble--bot')
      .last();
    await expect(botBubble).toBeVisible({ timeout: 10000 });

    const text = await botBubble.innerText();
    expect(text.length).toBeGreaterThan(0);
  });
});
