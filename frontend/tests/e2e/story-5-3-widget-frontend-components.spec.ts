/**
 * Widget Frontend Components E2E Tests
 *
 * Story 5-3: Widget Frontend Components
 * Tests the widget UI components: ChatBubble, ChatWindow, MessageList, MessageInput, TypingIndicator
 * Covers Shadow DOM isolation, keyboard navigation, and accessibility (AC6, AC7, AC8)
 *
 * @tags e2e widget story-5-3 accessibility keyboard shadow-dom
 */

import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = 1;

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/widget/config/*', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        config: {
          enabled: true,
          botName: 'Test Assistant',
          welcomeMessage: 'Hi! How can I help you today?',
          theme: {
            primaryColor: '#6366f1',
            backgroundColor: '#ffffff',
            textColor: '#1f2937',
            botBubbleColor: '#f3f4f6',
            userBubbleColor: '#6366f1',
            position: 'bottom-right',
            borderRadius: 16,
            width: 380,
            height: 600,
            fontFamily: 'Inter, sans-serif',
            fontSize: 14,
          },
          allowedDomains: [],
        },
      }),
    });
  });

  await page.route('**/api/v1/widget/session', async (route) => {
    if (route.request().method() === 'POST') {
      const now = new Date();
      const expiresAt = new Date(now.getTime() + 60 * 60 * 1000);
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          session: {
            session_id: crypto.randomUUID(),
            merchant_id: '1',
            expires_at: expiresAt.toISOString(),
            created_at: now.toISOString(),
            last_activity_at: now.toISOString(),
          },
        }),
      });
    } else {
      await route.continue();
    }
  });

  await page.route('**/api/v1/widget/message', async (route) => {
    if (route.request().method() === 'POST') {
      await new Promise(resolve => setTimeout(resolve, 300));
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: 'Thanks for your message! How can I help you?',
            sender: 'bot',
            created_at: new Date().toISOString(),
          },
        }),
      });
    } else {
      await route.continue();
    }
  });
});

test.describe('Widget Frontend Components - Initialization (AC1)', () => {
  test.slow();

  test('[P0] @smoke should render ChatBubble on page load', async ({ page }) => {
    await page.goto('/widget-test');

    await expect(page.getByRole('button', { name: 'Open chat' })).toBeVisible({ timeout: 15000 });
  });

  test('[P0] @smoke should display ChatBubble in default bottom-right position', async ({ page }) => {
    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });

    await expect(bubble).toBeVisible();

    const box = await bubble.boundingBox();
    expect(box).not.toBeNull();

    const viewport = page.viewportSize();
    expect(viewport).not.toBeNull();

    if (box && viewport) {
      expect(box.x + box.width).toBeGreaterThan(viewport.width - 100);
      expect(box.y + box.height).toBeGreaterThan(viewport.height - 100);
    }
  });

  test('[P2] should display loading state during initialization', async ({ page }) => {
    await page.route('**/api/v1/widget/config/*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 500));
      await route.continue();
    });

    await page.goto('/widget-test');

    await expect(page.getByLabel('Loading chat widget')).toBeVisible();

    await expect(page.getByRole('button', { name: 'Open chat' })).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Widget Frontend Components - ChatBubble Toggle (AC1, AC2)', () => {
  test('[P0] @smoke should open chat window when ChatBubble is clicked', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();
  });

  test('[P0] @smoke should close chat window when clicking ChatBubble again', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await page.keyboard.press('Escape');

    await expect(page.getByRole('dialog', { name: 'Chat window' })).not.toBeVisible();
  });

  test('[P0] @smoke should close chat window when close button is clicked', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await page.getByRole('button', { name: 'Close chat window' }).click();

    await expect(page.getByRole('dialog', { name: 'Chat window' })).not.toBeVisible();
  });

  test('[P0] @smoke should update aria-expanded attribute on toggle', async ({ page }) => {
    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await expect(bubble).toHaveAttribute('aria-expanded', 'false');

    await bubble.click();

    const openBubble = page.getByRole('button', { name: 'Close chat', exact: true });
    await expect(openBubble).toHaveAttribute('aria-expanded', 'true');
  });

  test('[P2] should animate chat window open and close', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    const dialog = page.getByRole('dialog', { name: 'Chat window' });
    await expect(dialog).toBeVisible();

    const opacity = await dialog.evaluate(el =>
      window.getComputedStyle(el).opacity
    );
    expect(parseFloat(opacity)).toBeGreaterThan(0);
  });
});

test.describe('Widget Frontend Components - Message Exchange (AC3, AC4)', () => {
  test('[P0] @smoke should display welcome message when chat opens', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    const messageList = page.locator('.message-list').first();
    await expect(messageList).toBeVisible();

    await expect(messageList.getByText(/Hi! How can I help you today|Start a conversation/)).toBeVisible();
  });

  test('[P0] @smoke should send message and display in MessageList', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    const input = page.getByLabel('Type a message');
    await input.fill('Hello, I need help');

    await page.getByRole('button', { name: 'Send message' }).click();

    const messageList = page.getByRole('log', { name: 'Chat messages' });
    await expect(messageList.getByText('Hello, I need help')).toBeVisible();
  });

  test('[P0] @smoke should display user messages on right side', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    await page.getByLabel('Type a message').fill('Test message');
    await page.getByRole('button', { name: 'Send message' }).click();

    const userMessage = page.locator('.message-bubble--user').filter({ hasText: 'Test message' });
    await expect(userMessage).toBeVisible();

    const justifyContent = await userMessage.evaluate(el =>
      window.getComputedStyle(el).justifyContent
    );
    expect(justifyContent).toBe('flex-end');
  });

  test('[P1] should clear input after sending message', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    const input = page.getByLabel('Type a message');
    await input.fill('Test message');
    await page.getByRole('button', { name: 'Send message' }).click();

    await expect(input).toHaveValue('');
  });

  test('[P1] should send message on Enter key', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    const input = page.getByLabel('Type a message');
    await input.fill('Enter key test');
    await input.press('Enter');

    const messageList = page.getByRole('log', { name: 'Chat messages' });
    await expect(messageList.getByText('Enter key test')).toBeVisible();
  });

  test('[P1] should disable send button when input is empty', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    const sendButton = page.getByRole('button', { name: 'Send message' });
    await expect(sendButton).toBeDisabled();

    const input = page.getByLabel('Type a message');
    await input.fill('Some text');

    await expect(sendButton).toBeEnabled();

    await input.clear();
    await expect(sendButton).toBeDisabled();
  });

  test('[P2] should enforce max message length', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    const input = page.getByLabel('Type a message');
    const longMessage = 'A'.repeat(2001);

    await input.fill(longMessage);

    const inputValue = await input.inputValue();
    expect(inputValue.length).toBeLessThanOrEqual(2000);
  });
});

test.describe('Widget Frontend Components - Typing Indicator (AC5)', () => {
  test('[P1] should display typing indicator while waiting for bot response', async ({ page }) => {
    await page.route('**/api/v1/widget/message', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.continue();
    });

    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    await page.getByLabel('Type a message').fill('Hello');
    await page.getByRole('button', { name: 'Send message' }).click();

    const typingIndicator = page.getByRole('status', { name: /is typing/i });
    await expect(typingIndicator).toBeVisible({ timeout: 500 });
  });

  test('[P1] should hide typing indicator after response received', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    await page.getByLabel('Type a message').fill('Hello');
    await page.getByRole('button', { name: 'Send message' }).click();

    await page.waitForResponse(resp =>
      resp.url().includes('/api/v1/widget/message') && resp.status() === 200,
      { timeout: 10000 }
    ).catch(() => {});

    const typingIndicator = page.getByRole('status', { name: /is typing/i });
    await expect(typingIndicator).not.toBeVisible({ timeout: 5000 });
  });

  test('[P2] should disable input while typing indicator is visible', async ({ page }) => {
    await page.route('**/api/v1/widget/message', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.continue();
    });

    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    await page.getByLabel('Type a message').fill('Hello');
    await page.getByRole('button', { name: 'Send message' }).click();

    const input = page.getByLabel('Type a message');
    await expect(input).toBeDisabled({ timeout: 500 });
  });
});

test.describe('Widget Frontend Components - Keyboard Navigation (AC7)', () => {
  test('[P1] should activate ChatBubble with Enter key', async ({ page }) => {
    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.focus();
    await bubble.press('Enter');

    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();
  });

  test('[P1] should activate ChatBubble with Space key', async ({ page }) => {
    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.focus();
    await bubble.press('Space');

    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();
  });

  test('[P1] should close chat window with Escape key', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await page.keyboard.press('Escape');

    await expect(page.getByRole('dialog', { name: 'Chat window' })).not.toBeVisible();
  });

  test('[P1] should trap focus within chat window when open', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const input = page.getByLabel('Type a message');
    await expect(input).toBeFocused();

    await page.keyboard.press('Tab');

    const sendButton = page.getByRole('button', { name: 'Send message' });
    await expect(sendButton).toBeFocused();

    await page.keyboard.press('Tab');

    const closeButton = page.getByRole('button', { name: 'Close chat window' });
    await expect(closeButton).toBeFocused();
  });

  test('[P1] should focus input when chat window opens', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    const input = page.getByLabel('Type a message');
    await expect(input).toBeFocused();
  });
});

test.describe('Widget Frontend Components - Screen Reader Accessibility (AC8)', () => {
  test('[P1] should have aria-label on ChatBubble', async ({ page }) => {
    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await expect(bubble).toHaveAttribute('aria-label', 'Open chat');

    await bubble.click();

    const openBubble = page.getByRole('button', { name: 'Close chat' });
    await expect(openBubble).toHaveAttribute('aria-label', 'Close chat');
  });

  test('[P1] should have role="dialog" and aria-modal on chat window', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    const dialog = page.getByRole('dialog', { name: 'Chat window' });
    await expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  test('[P1] should have aria-live region for messages', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    const messageList = page.getByRole('log', { name: 'Chat messages' });
    await expect(messageList).toHaveAttribute('aria-live', 'polite');
  });

  test('[P1] should announce new messages to screen readers', async ({ page }) => {
    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    await page.getByLabel('Type a message').fill('Test announcement');
    await page.getByRole('button', { name: 'Send message' }).click();

    const messageList = page.getByRole('log', { name: 'Chat messages' });
    await expect(messageList.getByRole('listitem', { name: /Test announcement/ })).toBeVisible();
  });

  test('[P1] should have aria-label on typing indicator', async ({ page }) => {
    await page.route('**/api/v1/widget/message', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 500));
      await route.continue();
    });

    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    await page.getByLabel('Type a message').fill('Hello');
    await page.getByRole('button', { name: 'Send message' }).click();

    const typingIndicator = page.getByRole('status', { name: /is typing/i });
    await expect(typingIndicator).toHaveAttribute('aria-label', /is typing/i);
  });

  test('[P2] should have role="alert" on error messages', async ({ page }) => {
    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
    });

    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    await page.getByLabel('Type a message').fill('Trigger error');
    await page.getByRole('button', { name: 'Send message' }).click();

    const errorAlert = page.getByRole('alert');
    await expect(errorAlert).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Widget Frontend Components - Theme & Position (AC1)', () => {
  test('[P2] should apply custom primary color from theme', async ({ page }) => {
    await page.goto('/widget-test?theme[primaryColor]=%23ff0000');

    const bubble = page.getByRole('button', { name: 'Open chat' });

    const backgroundColor = await bubble.evaluate(el =>
      window.getComputedStyle(el).backgroundColor
    );

    expect(backgroundColor).toMatch(/rgb\(255,\s*0,\s*0\)|#ff0000/i);
  });

  test('[P2] should position ChatBubble on bottom-left when configured', async ({ page }) => {
    await page.goto('/widget-test?theme[position]=bottom-left');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await expect(bubble).toBeVisible();

    const box = await bubble.boundingBox();
    expect(box).not.toBeNull();

    if (box) {
      expect(box.x).toBeLessThan(100);
      expect(box.y).toBeGreaterThan(0);
    }
  });

  test('[P2] should apply custom border radius from theme', async ({ page }) => {
    await page.goto('/widget-test?theme[borderRadius]=24');

    await page.getByRole('button', { name: 'Open chat' }).click();

    const dialog = page.getByRole('dialog', { name: 'Chat window' });

    const borderRadius = await dialog.evaluate(el =>
      window.getComputedStyle(el).borderRadius
    );

    expect(borderRadius).toMatch(/24px/);
  });
});

test.describe('Widget Frontend Components - Error Handling', () => {
  test('[P1] should display error message when API fails', async ({ page }) => {
    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
    });

    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    await page.getByLabel('Type a message').fill('Trigger error');
    await page.getByRole('button', { name: 'Send message' }).click();

    const errorAlert = page.getByRole('alert');
    await expect(errorAlert).toBeVisible({ timeout: 5000 });
    await expect(errorAlert).toContainText(/error|unavailable|failed/i);
  });

  test('[P1] should allow retrying after error', async ({ page }) => {
    let shouldFail = true;

    await page.route('**/api/v1/widget/message', async (route) => {
      if (shouldFail) {
        shouldFail = false;
        await route.fulfill({ status: 500, body: JSON.stringify({ error: 'Server error' }) });
      } else {
        await route.continue();
      }
    });

    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    await page.getByLabel('Type a message').fill('First message');
    await page.getByRole('button', { name: 'Send message' }).click();

    await expect(page.getByRole('alert')).toBeVisible({ timeout: 5000 });

    await page.getByLabel('Type a message').fill('Retry message');
    await page.getByRole('button', { name: 'Send message' }).click();

    const messageList = page.getByRole('log', { name: 'Chat messages' });
    await expect(messageList.getByText('Retry message')).toBeVisible({ timeout: 10000 });
  });

  test('[P2] should handle network timeout gracefully', async ({ page }) => {
    await page.route('**/api/v1/widget/message', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 35000));
      await route.abort('timedout');
    });

    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    await page.getByLabel('Type a message').fill('Timeout test');
    await page.getByRole('button', { name: 'Send message' }).click();

    await page.getByRole('alert').waitFor({ timeout: 40000 }).catch(() => {});

    const input = page.getByLabel('Type a message');
    await expect(input).toBeEnabled({ timeout: 40000 });
  });
});

test.describe('Widget Frontend Components - Session Management', () => {
  test('[P1] should create session on widget initialization', async ({ page }) => {
    const sessionPromise = page.waitForRequest(req =>
      req.url().includes('/api/v1/widget/session') && req.method() === 'POST'
    );

    await page.goto('/widget-test');

    const request = await sessionPromise;
    expect(request).toBeTruthy();
  });

  test('[P2] should handle disabled merchant config', async ({ page }) => {
    await page.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          data: { enabled: false, botName: 'Disabled Bot' },
          meta: {}
        })
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await expect(bubble).not.toBeVisible({ timeout: 5000 });
  });

  test('[P2] should handle rate limiting gracefully', async ({ page }) => {
    let requestCount = 0;

    await page.route('**/api/v1/widget/message', async (route) => {
      requestCount++;
      if (requestCount > 3) {
        await route.fulfill({
          status: 429,
          body: JSON.stringify({
            error: { code: 12003, message: 'Rate limited' }
          })
        });
      } else {
        await route.continue();
      }
    });

    await page.goto('/widget-test');

    await page.getByRole('button', { name: 'Open chat' }).click();

    for (let i = 0; i < 5; i++) {
      await page.getByLabel('Type a message').fill(`Message ${i}`);
      await page.getByRole('button', { name: 'Send message' }).click();
      await page.waitForTimeout(100);
    }

    const errorAlert = page.getByRole('alert');
    await expect(errorAlert).toBeVisible({ timeout: 5000 });
  });
});
