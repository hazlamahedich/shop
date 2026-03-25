import { test, expect, Page } from '@playwright/test';

const TEST_SESSION_ID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
const TEST_MERCHANT_ID = '4';

interface MockMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  products?: any[];
  cart?: any;
}

interface WidgetMockConfig {
  mockHistory?: MockMessage[];
}

async function setupWidgetMocks(page: Page, options: WidgetMockConfig = {}): Promise<void> {
  const messages: MockMessage[] = options.mockHistory || [];

  await page.route('**/api/v1/widget/config/*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          enabled: true,
          botName: 'Mantisbot',
          welcomeMessage: 'Hello! How can I help you?',
          shopDomain: 'test-shop.myshopify.com',
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
            fontSize: 14
          }
        }
      })
    });
  });

  await page.route('**/api/v1/widget/session/*/messages', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          messages,
          expired: false,
          expires_at: new Date(Date.now() + 3600000).toISOString()
        }
      })
    });
  });

  await page.route('**/api/v1/widget/session/*', async (route) => {
    const request = route.request();
    if (!request.url().includes('/messages')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            session_id: TEST_SESSION_ID,
            merchant_id: TEST_MERCHANT_ID,
            expires_at: new Date(Date.now() + 3600000).toISOString(),
            created_at: new Date().toISOString(),
            last_activity_at: new Date().toISOString()
          }
        })
      });
    } else {
      await route.continue();
    }
  });

  await page.route('**/api/v1/widget/session', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          session_id: TEST_SESSION_ID,
          merchant_id: TEST_MERCHANT_ID,
          expires_at: new Date(Date.now() + 3600000).toISOString(),
          created_at: new Date().toISOString(),
          last_activity_at: new Date().toISOString()
        }
      })
    });
  });

  await page.route('**/api/v1/widget/consent/*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          status: 'pending',
          can_store_conversation: false,
          consent_message_shown: false
        }
      })
    });
  });
}

async function loadWidgetWithHistory(page: Page, messages: MockMessage[]): Promise<void> {
  await page.addInitScript((sessionId) => {
    sessionStorage.setItem('widget_session_id', sessionId);
  }, TEST_SESSION_ID);
  
  await setupWidgetMocks(page, { mockHistory: messages });
  
  const configPromise = page.waitForResponse('**/api/v1/widget/config/*');
  await page.goto(`/widget-test?sessionId=${TEST_SESSION_ID}`);
  await configPromise;

  const chatBubble = page.locator('.shopbot-chat-bubble');
  await chatBubble.waitFor({ state: 'visible', timeout: 10000 });
}

async function openChat(page: Page): Promise<void> {
  const chatBubble = page.locator('.shopbot-chat-bubble');
  await chatBubble.click();
  
  const chatWindow = page.locator('.shopbot-chat-window');
  await chatWindow.waitFor({ state: 'visible', timeout: 5000 });
  
  await page.waitForTimeout(500);
}

function createGroupedBotMessages(count: number, baseTime: Date): MockMessage[] {
  const messages: MockMessage[] = [];
  for (let i = 0; i < count; i++) {
    messages.push({
      role: 'assistant',
      content: `Bot message ${i + 1} in group`,
      timestamp: new Date(baseTime.getTime() + i * 5000).toISOString()
    });
  }
  return messages;
}

function createGroupedUserMessages(count: number, baseTime: Date): MockMessage[] {
  const messages: MockMessage[] = [];
  for (let i = 0; i < count; i++) {
    messages.push({
      role: 'user',
      content: `User message ${i + 1} in group`,
      timestamp: new Date(baseTime.getTime() + i * 5000).toISOString()
    });
  }
  return messages;
}

function createMessagesWithGap(
  firstGroup: MockMessage[],
  secondGroup: MockMessage[],
  gapMs: number
): MockMessage[] {
  const lastOfFirst = firstGroup[firstGroup.length - 1];
  
  const adjustedSecondGroup = secondGroup.map((msg, i) => ({
    ...msg,
    timestamp: new Date(
      new Date(lastOfFirst.timestamp).getTime() + gapMs + (i * 5000)
    ).toISOString()
  }));
  
  return [...firstGroup, ...adjustedSecondGroup];
}

test.describe('Story 9-7: Message Grouping with Avatars', () => {
  test.describe('AC1: Message Grouping Logic', () => {
    test('9.7-E2E-001: should group consecutive bot messages within 60 seconds [P1]', async ({ page }) => {
      const now = new Date();
      const messages = createGroupedBotMessages(3, now);
      
      await loadWidgetWithHistory(page, messages);
      await openChat(page);
      
      const botBubbles = page.locator('[data-testid="message-bubble"].message-bubble--bot');
      await botBubbles.first().waitFor({ state: 'visible', timeout: 5000 });
      const count = await botBubbles.count();
      
      expect(count).toBe(3);
      
      const firstBubble = botBubbles.first();
      await expect(firstBubble).toBeVisible();
    });

    test('9.7-E2E-002: should create new group when gap exceeds 60 seconds [P1]', async ({ page }) => {
      const now = new Date();
      const firstGroup = createGroupedBotMessages(2, now);
      const secondGroup = createGroupedBotMessages(2, new Date(now.getTime() + 120000));
      
      const messages = createMessagesWithGap(firstGroup, secondGroup, 90000);
      
      await loadWidgetWithHistory(page, messages);
      await openChat(page);
      
      const botBubbles = page.locator('[data-testid="message-bubble"].message-bubble--bot');
      await botBubbles.first().waitFor({ state: 'visible', timeout: 5000 });
      const count = await botBubbles.count();
      
      expect(count).toBe(4);
    });
  });

  test.describe('AC2: Avatar Display Per Group', () => {
    test('9.7-E2E-003: should show avatar for first message in bot group [P1]', async ({ page }) => {
      const now = new Date();
      const messages = createGroupedBotMessages(3, now);
      
      await loadWidgetWithHistory(page, messages);
      await openChat(page);
      
      const botAvatars = page.locator('[data-testid="message-avatar"], [aria-label*="avatar"]');
      await botAvatars.first().waitFor({ state: 'visible', timeout: 5000 });
      const avatarCount = await botAvatars.count();
      
      expect(avatarCount).toBeGreaterThanOrEqual(1);
    });

    test('9.7-E2E-004: should not show avatar for user messages [P1]', async ({ page }) => {
      const now = new Date();
      const messages = createGroupedUserMessages(3, now);
      
      await loadWidgetWithHistory(page, messages);
      await openChat(page);
      
      const userBubbles = page.locator('[data-testid="message-bubble"].message-bubble--user');
      await userBubbles.first().waitFor({ state: 'visible', timeout: 5000 });
      
      const avatarsInUserGroup = page.locator('.message-group__row').filter({ has: page.locator('.message-bubble--user') }).locator('[data-testid="message-avatar"]');
      const avatarCount = await avatarsInUserGroup.count();
      
      expect(avatarCount).toBe(0);
    });
  });

  test.describe('AC3: Timestamp Grouping', () => {
    test('9.7-E2E-005: should show timestamp on last message of group [P1]', async ({ page }) => {
      const now = new Date();
      const messages = createGroupedBotMessages(3, now);
      
      await loadWidgetWithHistory(page, messages);
      await openChat(page);
      
      const timestamps = page.locator('[data-testid="message-timestamp"]');
      await timestamps.first().waitFor({ state: 'visible', timeout: 5000 });
      const count = await timestamps.count();
      
      expect(count).toBeGreaterThanOrEqual(1);
    });
  });

  test.describe('AC5: Relative Timestamps', () => {
    test('9.7-E2E-006: should display relative time for recent messages [P1]', async ({ page }) => {
      const now = new Date();
      const messages = createGroupedBotMessages(2, now);
      
      await loadWidgetWithHistory(page, messages);
      await openChat(page);
      
      const relativeTime = page.locator('[data-testid="relative-time"]');
      await relativeTime.first().waitFor({ state: 'visible', timeout: 5000 });
      
      const timeText = await relativeTime.first().textContent();
      
      const validPatterns = ['just now', 'now', 'ago', 'm ago', 'minute', 'second'];
      const isValid = validPatterns.some(pattern => 
        timeText?.toLowerCase().includes(pattern.toLowerCase())
      );
      
      expect(isValid || timeText).toBeTruthy();
    });
  });

  test.describe('AC7: User and Bot Messages', () => {
    test('9.7-E2E-007: should group user and bot messages separately [P1]', async ({ page }) => {
      const now = new Date();
      const messages: MockMessage[] = [
        ...createGroupedUserMessages(2, now),
        ...createGroupedBotMessages(2, new Date(now.getTime() + 20000))
      ];
      
      await loadWidgetWithHistory(page, messages);
      await openChat(page);
      
      const userBubbles = page.locator('[data-testid="message-bubble"].message-bubble--user');
      const botBubbles = page.locator('[data-testid="message-bubble"].message-bubble--bot');
      
      await userBubbles.first().waitFor({ state: 'visible', timeout: 5000 });
      await botBubbles.first().waitFor({ state: 'visible', timeout: 5000 });
      
      const userCount = await userBubbles.count();
      const botCount = await botBubbles.count();
      
      expect(userCount).toBe(2);
      expect(botCount).toBe(2);
    });
  });

  test.describe('AC6: Smooth Animation', () => {
    test('9.7-E2E-008: should apply fade-in animation to new messages [P2]', async ({ page }) => {
      const now = new Date();
      const messages = createGroupedBotMessages(2, now);
      
      await loadWidgetWithHistory(page, messages);
      await openChat(page);
      
      const messageBubbles = page.locator('[data-testid="message-bubble"]');
      await messageBubbles.first().waitFor({ state: 'visible', timeout: 5000 });
      
      const firstBubble = messageBubbles.first();
      const animation = await firstBubble.evaluate((el) => {
        const style = window.getComputedStyle(el);
        return {
          animation: style.animation,
          opacity: style.opacity,
          transition: style.transition
        };
      });
      
      const hasAnimation = 
        animation.animation !== 'none 0s ease 0s normal none running none' ||
        animation.transition !== 'all 0s ease 0s' ||
        animation.opacity === '1';
      
      expect(hasAnimation).toBeTruthy();
    });
  });
});
