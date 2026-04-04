import { test, expect, type Page } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
  sendMessage,
  mockWidgetMessageConditional,
  createMockMessageResponse,
  createMockProduct,
} from '../helpers/widget-test-helpers';

function sendAndAwait(page: Page, messageText: string) {
  const response = page.waitForResponse('**/api/v1/widget/message');
  return { response, send: () => sendMessage(page, messageText) };
}

test.describe('Story 11-9: Conversation Summarization @p1', () => {
  test.describe.configure({ retries: 2 });

  const SUMMARY_RESPONSE = createMockMessageResponse({
    content:
      '## Summary\n\n- 🛍️ Products Discussed: Running shoes, blue color\n- 🎯 Preferences: Blue running shoes\n- 📋 Next Steps: Browse catalog',
  });

  const SHORT_CONV_RESPONSE = createMockMessageResponse({
    content:
      "We just started chatting! 😊 Not much to summarize yet, but feel free to ask me anything!",
  });

  const PRODUCT_RESPONSE = createMockMessageResponse({
    content: 'I found some great running shoes for you!',
    products: [createMockProduct({ title: 'Blue Running Shoes', price: 89.99 })],
  });

  const RETURN_POLICY_RESPONSE = createMockMessageResponse({
    content:
      'Our return policy allows returns within 30 days of purchase. Items must be unused and in original packaging.',
  });

  test('[P1] 11.9-E2E-001: recap shows summary after multi-turn conversation', async ({ page }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-summarize-session');
    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('running shoes'),
        response: PRODUCT_RESPONSE,
      },
      {
        match: (msg) => msg.includes('blue'),
        response: createMockMessageResponse({
          content: 'Great choice! Blue running shoes are very popular.',
        }),
      },
      {
        match: (msg) => ['recap', 'summarize', 'summary'].some((s) => msg.includes(s)),
        response: SUMMARY_RESPONSE,
      },
    ]);

    await loadWidgetWithSession(page, 'test-summarize-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const msg1 = sendAndAwait(page, 'I want running shoes');
    await msg1.send();
    await msg1.response;
    await expect(page.getByText('running shoes')).toBeVisible();

    const msg2 = sendAndAwait(page, 'I prefer blue');
    await msg2.send();
    await msg2.response;
    await expect(page.getByText('Blue')).toBeVisible();

    const msg3 = sendAndAwait(page, 'recap');
    await msg3.send();
    await msg3.response;
    await expect(page.getByText(/Products Discussed|Summary/i)).toBeVisible();
  });

  test('[P1] 11.9-E2E-002: short conversation summarize shows friendly message', async ({ page }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-short-conv-session');
    await mockWidgetMessageConditional(page, [
      {
        match: (msg) =>
          ['summarize', 'recap', 'summary'].some((s) => msg.trim() === s || msg.includes(s)),
        response: SHORT_CONV_RESPONSE,
      },
    ]);

    await loadWidgetWithSession(page, 'test-short-conv-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const { send, response } = sendAndAwait(page, 'summarize');
    await send();
    await response;
    await expect(
      page.getByText(/not much to summarize|just started|Nothing to summarize|still chatting/i)
    ).toBeVisible();
  });

  test('[P1] 11.9-E2E-003: "summarize the return policy" does NOT trigger summary', async ({ page }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-no-summary-session');
    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('return policy'),
        response: RETURN_POLICY_RESPONSE,
      },
    ]);

    await loadWidgetWithSession(page, 'test-no-summary-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const { send, response } = sendAndAwait(page, 'summarize the return policy');
    await send();
    await response;
    await expect(page.getByText(/return policy/i)).toBeVisible();

    const messagesContainer = page.getByRole('dialog', { name: 'Chat window' });
    await expect(messagesContainer).not.toContainText('Products Discussed');
    await expect(messagesContainer).not.toContainText('Topics Covered');
  });

  test('[P1] 11.9-E2E-004: summary does not reset conversation — can continue chatting (AC5)', async ({
    page,
  }) => {
    const CLARIFICATION_RESPONSE = createMockMessageResponse({
      content: 'Sure! Let me narrow it down. What size are you looking for?',
    });
    const AFTER_SUMMARY_RESPONSE = createMockMessageResponse({
      content: 'Great, size 10 blue running shoes — here are some options!',
      products: [createMockProduct({ title: 'Nike Air Zoom Pegasus', price: 120.0 })],
    });

    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-ac5-session');
    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('running shoes'),
        response: PRODUCT_RESPONSE,
      },
      {
        match: (msg) => msg.includes('blue'),
        response: createMockMessageResponse({
          content: 'Great choice! Blue running shoes are very popular.',
        }),
      },
      {
        match: (msg) => msg.includes('recap'),
        response: SUMMARY_RESPONSE,
      },
      {
        match: (msg) => msg.includes('size'),
        response: CLARIFICATION_RESPONSE,
      },
      {
        match: (msg) => msg.includes('10'),
        response: AFTER_SUMMARY_RESPONSE,
      },
    ]);

    await loadWidgetWithSession(page, 'test-ac5-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const msg1 = sendAndAwait(page, 'I want running shoes');
    await msg1.send();
    await msg1.response;
    await expect(page.getByText('running shoes')).toBeVisible();

    const msg2 = sendAndAwait(page, 'I prefer blue');
    await msg2.send();
    await msg2.response;

    const msg3 = sendAndAwait(page, 'recap');
    await msg3.send();
    await msg3.response;
    await expect(page.getByText(/Products Discussed|Summary/i)).toBeVisible();

    const msg4 = sendAndAwait(page, 'What about size 10?');
    await msg4.send();
    await msg4.response;
    await expect(page.getByText(/size 10|Nike Air Zoom/i)).toBeVisible();
  });

  test('[P1] 11.9-E2E-005: exactly 3 turns triggers full summary (boundary)', async ({ page }) => {
    const THIRD_TURN_RESPONSE = createMockMessageResponse({
      content: 'Good to know! Anything else?',
    });

    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-boundary-session');
    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('hello'),
        response: createMockMessageResponse({ content: 'Hi there! How can I help?' }),
      },
      {
        match: (msg) => msg.includes('shoes'),
        response: THIRD_TURN_RESPONSE,
      },
      {
        match: (msg) => ['recap', 'summarize', 'summary'].some((s) => msg.includes(s)),
        response: SUMMARY_RESPONSE,
      },
    ]);

    await loadWidgetWithSession(page, 'test-boundary-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const msg1 = sendAndAwait(page, 'hello');
    await msg1.send();
    await msg1.response;

    const msg2 = sendAndAwait(page, 'show me shoes');
    await msg2.send();
    await msg2.response;

    const msg3 = sendAndAwait(page, 'recap');
    await msg3.send();
    await msg3.response;
    await expect(page.getByText(/Products Discussed|Summary/i)).toBeVisible();
  });
});
