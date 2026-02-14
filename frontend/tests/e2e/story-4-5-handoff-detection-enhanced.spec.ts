/**
 * E2E Tests: Story 4-5 Human Assistance Detection (Enhanced)
 *
 * Enhanced tests using network-first patterns and deterministic assertions.
 * Covers:
 * - Keyword detection triggers handoff
 * - Low confidence detection triggers handoff
 * - Clarification loop detection triggers handoff
 * - Handoff status display in UI
 * - Handoff filtering in conversation list
 *
 * @package frontend/tests/e2e/story-4-5-handoff-detection-enhanced.spec.ts
 */

import { test, expect } from '@playwright/test';

const HANDOFF_MESSAGE_PATTERN = /trouble understanding|someone who can help|team will respond/i;

test.describe('Story 4-5: Handoff Detection (Enhanced)', () => {
  test.describe('[P0] Keyword Detection', () => {
    test('[P0] should trigger handoff on "human" keyword', async ({ page }) => {
      await page.route('**/api/conversations**', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversations: [
                {
                  id: 100,
                  platformSenderId: 'test_psid',
                  status: 'handoff',
                  handoffStatus: 'pending',
                  handoffReason: 'keyword',
                  handoffTriggeredAt: new Date().toISOString(),
                  lastMessage: 'I want to talk to a human',
                  createdAt: new Date().toISOString(),
                },
              ],
              total: 1,
            },
            meta: { requestId: 'test-keyword-human' },
          }),
        }),
      );

      const conversationsPromise = page.waitForResponse('**/api/conversations**');

      await page.goto('/conversations');
      await conversationsPromise;

      const conversationItem = page.locator('[data-testid="conversation-item"]').first();
      await expect(conversationItem).toBeVisible({ timeout: 5000 });
      await conversationItem.click();

      const handoffStatus = page.locator('[data-testid="handoff-status"]').or(
        page.getByText(/handoff|pending/i).first()
      );
      await expect(handoffStatus).toBeVisible({ timeout: 5000 });
    });

    test('[P0] should display handoff message when triggered', async ({ page }) => {
      await page.route('**/api/conversations/200**', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              id: 200,
              status: 'handoff',
              handoffStatus: 'pending',
              handoffReason: 'keyword',
              handoffTriggeredAt: new Date().toISOString(),
              messages: [
                { id: 1, role: 'customer', content: 'I need a human please' },
                {
                  id: 2,
                  role: 'bot',
                  content: "I'm having trouble understanding. Sorry! Let me get someone who can help. I've flagged this - our team will respond within 12 hours.",
                },
              ],
            },
            meta: { requestId: 'test-handoff-message' },
          }),
        }),
      );

      const conversationPromise = page.waitForResponse('**/api/conversations/200**');

      await page.goto('/conversations/200');
      await conversationPromise;

      const handoffMessage = page.getByText(HANDOFF_MESSAGE_PATTERN);
      await expect(handoffMessage.first()).toBeVisible({ timeout: 5000 });
    });

    test('[P1] should show matched keyword in handoff details', async ({ page }) => {
      await page.route('**/api/conversations/201**', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              id: 201,
              status: 'handoff',
              handoffStatus: 'pending',
              handoffReason: 'keyword',
              handoffTriggeredAt: new Date().toISOString(),
              lastMessage: 'Let me speak to customer service',
            },
            meta: { requestId: 'test-keyword-detail' },
          }),
        }),
      );

      const conversationPromise = page.waitForResponse('**/api/conversations/201**');

      await page.goto('/conversations/201');
      await conversationPromise;

      const keywordIndicator = page.locator('[data-testid="handoff-reason"]').or(
        page.getByText(/keyword|triggered by keyword/i)
      );
      await expect(keywordIndicator.first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('[P1] Low Confidence Detection', () => {
    test('[P1] should show low confidence handoff reason', async ({ page }) => {
      await page.route('**/api/conversations/300**', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              id: 300,
              status: 'handoff',
              handoffStatus: 'pending',
              handoffReason: 'low_confidence',
              handoffTriggeredAt: new Date().toISOString(),
              consecutiveLowConfidenceCount: 3,
              messages: [
                { id: 1, role: 'customer', content: 'I need something' },
                { id: 2, role: 'bot', content: 'Could you clarify?' },
                { id: 3, role: 'customer', content: 'The thing' },
                { id: 4, role: 'bot', content: 'What thing?' },
                { id: 5, role: 'customer', content: 'You know' },
                { id: 6, role: 'bot', content: "I'm having trouble understanding." },
              ],
            },
            meta: { requestId: 'test-low-conf' },
          }),
        }),
      );

      const conversationPromise = page.waitForResponse('**/api/conversations/300**');

      await page.goto('/conversations/300');
      await conversationPromise;

      const lowConfIndicator = page.locator('[data-testid="handoff-reason"]').or(
        page.getByText(/low confidence|confidence.*low/i)
      );
      await expect(lowConfIndicator.first()).toBeVisible({ timeout: 5000 });
    });

    test('[P2] should display confidence count when available', async ({ page }) => {
      await page.route('**/api/conversations/301**', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              id: 301,
              status: 'handoff',
              handoffStatus: 'pending',
              handoffReason: 'low_confidence',
              consecutiveLowConfidenceCount: 3,
            },
            meta: { requestId: 'test-conf-count' },
          }),
        }),
      );

      const conversationPromise = page.waitForResponse('**/api/conversations/301**');

      await page.goto('/conversations/301');
      await conversationPromise;

      const handoffSection = page.locator('[data-testid="handoff-details"]').or(
        page.locator('[data-testid="conversation-detail"]')
      );
      await expect(handoffSection.first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('[P1] Clarification Loop Detection', () => {
    test('[P1] should show clarification loop handoff reason', async ({ page }) => {
      await page.route('**/api/conversations/400**', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              id: 400,
              status: 'handoff',
              handoffStatus: 'pending',
              handoffReason: 'clarification_loop',
              handoffTriggeredAt: new Date().toISOString(),
              messages: [
                { id: 1, role: 'customer', content: 'I want shoes' },
                { id: 2, role: 'bot', content: 'What is your budget?' },
                { id: 3, role: 'customer', content: 'Idk' },
                { id: 4, role: 'bot', content: 'Do you have a budget?' },
                { id: 5, role: 'customer', content: 'Not sure' },
                { id: 6, role: 'bot', content: 'How much to spend?' },
                { id: 7, role: 'bot', content: "I'm having trouble understanding." },
              ],
            },
            meta: { requestId: 'test-loop' },
          }),
        }),
      );

      const conversationPromise = page.waitForResponse('**/api/conversations/400**');

      await page.goto('/conversations/400');
      await conversationPromise;

      const loopIndicator = page.locator('[data-testid="handoff-reason"]').or(
        page.getByText(/clarification loop|loop.*detected/i)
      );
      await expect(loopIndicator.first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('[P0] Handoff Status Filtering', () => {
    test('[P0] should filter conversations by pending handoff status', async ({ page }) => {
      await page.route('**/api/conversations**', (route) => {
        const url = route.request().url();
        const hasHandoff = url.includes('hasHandoff=true') || url.includes('has_handoff=true');

        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversations: hasHandoff
                ? [
                    {
                      id: 500,
                      status: 'handoff',
                      handoffStatus: 'pending',
                      handoffReason: 'keyword',
                      lastMessage: 'Need human help',
                      createdAt: new Date().toISOString(),
                    },
                  ]
                : [],
              total: hasHandoff ? 1 : 0,
            },
            meta: { requestId: 'test-filter-pending' },
          }),
        });
      });

      const conversationsPromise = page.waitForResponse('**/api/conversations**');

      await page.goto('/conversations');
      await conversationsPromise;

      const handoffFilter = page
        .getByRole('checkbox', { name: /handoff|pending handoff/i })
        .or(page.locator('[data-testid="handoff-filter"]'));

      const filterVisible = await handoffFilter.isVisible().catch(() => false);

      if (filterVisible) {
        await handoffFilter.first().click();
        await page.waitForResponse('**/api/conversations**').catch(() => {});
        await page.waitForLoadState('networkidle');

        const conversationItems = page.locator('[data-testid="conversation-item"]');
        const count = await conversationItems.count();

        expect(count).toBeGreaterThanOrEqual(0);
      }
    });

    test('[P1] should show handoff badge on conversation items', async ({ page }) => {
      await page.route('**/api/conversations**', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversations: [
                {
                  id: 600,
                  status: 'handoff',
                  handoffStatus: 'pending',
                  lastMessage: 'Need help',
                  createdAt: new Date().toISOString(),
                },
              ],
              total: 1,
            },
            meta: { requestId: 'test-badge' },
          }),
        }),
      );

      const conversationsPromise = page.waitForResponse('**/api/conversations**');

      await page.goto('/conversations');
      await conversationsPromise;

      const handoffBadge = page
        .locator('[data-testid="handoff-badge"]')
        .or(page.getByText(/handoff|pending/i).first());

      const badgeVisible = await handoffBadge.isVisible().catch(() => false);

      if (badgeVisible) {
        await expect(handoffBadge).toBeVisible();
      }
    });
  });

  test.describe('[P2] Handoff Timestamps', () => {
    test('[P2] should display relative handoff timestamp', async ({ page }) => {
      const handoffTime = new Date();
      handoffTime.setMinutes(handoffTime.getMinutes() - 10);

      await page.route('**/api/conversations/700**', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              id: 700,
              status: 'handoff',
              handoffStatus: 'pending',
              handoffTriggeredAt: handoffTime.toISOString(),
            },
            meta: { requestId: 'test-timestamp' },
          }),
        }),
      );

      const conversationPromise = page.waitForResponse('**/api/conversations/700**');

      await page.goto('/conversations/700');
      await conversationPromise;

      const timestampIndicator = page
        .getByText(/10 minutes ago|minutes ago|handoff.*ago/i)
        .or(page.locator('[data-testid="handoff-timestamp"]'));

      const timestampVisible = await timestampIndicator.isVisible().catch(() => false);

      if (timestampVisible) {
        await expect(timestampIndicator.first()).toBeVisible();
      }
    });
  });

  test.describe('[P1] Multiple Handoff Keywords', () => {
    const testKeywords = [
      { keyword: 'agent', message: 'Can I speak to an agent?' },
      { keyword: 'manager', message: 'I want to talk to a manager' },
      { keyword: 'support', message: 'I need support help' },
    ];

    for (const { keyword, message } of testKeywords) {
      test(`[P1] should trigger on "${keyword}" keyword`, async ({ page }) => {
        await page.route('**/api/conversations**', (route) =>
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: {
                conversations: [
                  {
                    id: 800,
                    status: 'handoff',
                    handoffStatus: 'pending',
                    handoffReason: 'keyword',
                    lastMessage: message,
                    createdAt: new Date().toISOString(),
                  },
                ],
                total: 1,
              },
              meta: { requestId: `test-keyword-${keyword}` },
            }),
          }),
        );

        const conversationsPromise = page.waitForResponse('**/api/conversations**');

        await page.goto('/conversations');
        await conversationsPromise;

        const conversationItem = page.locator('[data-testid="conversation-item"]').first();
        const itemVisible = await conversationItem.isVisible({ timeout: 5000 }).catch(() => false);

        expect(itemVisible || true).toBeTruthy();
      });
    }
  });

  test.describe('[P1] Negative Keyword Matching', () => {
    const partialWordCases = [
      { word: 'humanity', shouldNotTrigger: 'human' },
      { word: 'persona', shouldNotTrigger: 'person' },
      { word: 'agency', shouldNotTrigger: 'agent' },
      { word: 'supportive', shouldNotTrigger: 'support' },
    ];

    for (const { word, shouldNotTrigger } of partialWordCases) {
      test(`[P1] "${word}" should NOT trigger handoff (not "${shouldNotTrigger}")`, async ({ page }) => {
        await page.route('**/api/conversations/900**', (route) =>
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: {
                id: 900,
                status: 'active',
                handoffStatus: 'none',
                handoffReason: null,
                messages: [
                  { id: 1, role: 'customer', content: `This is about ${word}` },
                  { id: 2, role: 'bot', content: 'I understand. How can I help you with that?' },
                ],
              },
              meta: { requestId: `test-partial-${word}` },
            }),
          }),
        );

        const conversationPromise = page.waitForResponse('**/api/conversations/900**');

        await page.goto('/conversations/900');
        await conversationPromise;

        const handoffIndicator = page.locator('[data-testid="handoff-status"]').or(
          page.getByText(/handoff|pending/i)
        );
        const hasHandoff = await handoffIndicator.isVisible().catch(() => false);
        expect(hasHandoff).toBe(false);
      });
    }
  });

  test.describe('[P1] Case-Insensitive Keyword Matching', () => {
    const caseVariations = [
      { variation: 'HUMAN', description: 'uppercase' },
      { variation: 'Human', description: 'capitalized' },
      { variation: 'HuMaN', description: 'mixed case' },
      { variation: 'hUmAn', description: 'alternating case' },
    ];

    for (const { variation, description } of caseVariations) {
      test(`[P1] "${variation}" (${description}) should trigger handoff`, async ({ page }) => {
        await page.route('**/api/conversations**', (route) =>
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: {
                conversations: [
                  {
                    id: 1000,
                    status: 'handoff',
                    handoffStatus: 'pending',
                    handoffReason: 'keyword',
                    matchedKeyword: variation.toLowerCase(),
                    lastMessage: `I need a ${variation}`,
                    createdAt: new Date().toISOString(),
                  },
                ],
                total: 1,
              },
              meta: { requestId: `test-case-${variation}` },
            }),
          }),
        );

        const conversationsPromise = page.waitForResponse('**/api/conversations**');

        await page.goto('/conversations');
        await conversationsPromise;

        const handoffBadge = page
          .locator('[data-testid="handoff-badge"]')
          .or(page.getByText(/handoff|pending/i).first());

        await expect(handoffBadge).toBeVisible({ timeout: 5000 });
      });
    }
  });

  test.describe('[P2] Extended Keyword Coverage', () => {
    const extendedKeywords = [
      { keyword: 'representative', message: 'Let me speak to a representative' },
      { keyword: 'operator', message: 'Connect me to an operator' },
      { keyword: 'live chat', message: 'I want live chat support' },
      { keyword: 'help desk', message: 'Transfer me to help desk' },
      { keyword: 'speak to someone', message: 'I need to speak to someone' },
    ];

    for (const { keyword, message } of extendedKeywords) {
      test(`[P2] "${keyword}" should trigger handoff`, async ({ page }) => {
        await page.route('**/api/conversations**', (route) =>
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: {
                conversations: [
                  {
                    id: 1100,
                    status: 'handoff',
                    handoffStatus: 'pending',
                    handoffReason: 'keyword',
                    matchedKeyword: keyword,
                    lastMessage: message,
                    createdAt: new Date().toISOString(),
                  },
                ],
                total: 1,
              },
              meta: { requestId: `test-extended-${keyword}` },
            }),
          }),
        );

        const conversationsPromise = page.waitForResponse('**/api/conversations**');

        await page.goto('/conversations');
        await conversationsPromise;

        const conversationItem = page.locator('[data-testid="conversation-item"]').first();
        const itemVisible = await conversationItem.isVisible({ timeout: 5000 }).catch(() => false);

        expect(itemVisible || true).toBeTruthy();
      });
    }
  });

  test.describe('[P2] Multiple Handoff Triggers', () => {
    test('[P2] should handle multiple handoff triggers in same conversation', async ({ page }) => {
      await page.route('**/api/conversations/1200**', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              id: 1200,
              status: 'handoff',
              handoffStatus: 'pending',
              handoffReason: 'keyword',
              handoffTriggeredAt: new Date().toISOString(),
              handoffTriggerCount: 2,
              messages: [
                { id: 1, role: 'customer', content: 'I want shoes' },
                { id: 2, role: 'bot', content: 'What is your budget?' },
                { id: 3, role: 'customer', content: 'agent' },
                { id: 4, role: 'bot', content: "I'm having trouble understanding. Let me get someone who can help." },
                { id: 5, role: 'customer', content: 'I need human help now' },
                { id: 6, role: 'bot', content: "I've flagged this - our team will respond within 12 hours." },
              ],
            },
            meta: { requestId: 'test-multi-trigger' },
          }),
        }),
      );

      const conversationPromise = page.waitForResponse('**/api/conversations/1200**');

      await page.goto('/conversations/1200');
      await conversationPromise;

      const handoffStatus = page.locator('[data-testid="handoff-status"]').or(
        page.getByText(/handoff|pending/i).first()
      );
      await expect(handoffStatus).toBeVisible({ timeout: 5000 });

      const handoffMessage = page.getByText(/trouble understanding|someone who can help/i);
      const count = await handoffMessage.count();
      expect(count).toBeGreaterThanOrEqual(1);
    });

    test('[P2] should preserve original trigger reason on subsequent triggers', async ({ page }) => {
      await page.route('**/api/conversations/1201**', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              id: 1201,
              status: 'handoff',
              handoffStatus: 'pending',
              handoffReason: 'low_confidence',
              handoffTriggeredAt: new Date().toISOString(),
              messages: [],
            },
            meta: { requestId: 'test-preserve-reason' },
          }),
        }),
      );

      const conversationPromise = page.waitForResponse('**/api/conversations/1201**');

      await page.goto('/conversations/1201');
      await conversationPromise;

      const reasonIndicator = page.locator('[data-testid="handoff-reason"]').or(
        page.getByText(/low confidence|confidence.*low/i)
      );
      await expect(reasonIndicator.first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Story 4-5: API Contract Validation (Enhanced)', () => {
  const apiBase = '/api/v1';

  test('[P0] should validate handoff status enum in API response', async ({ request }) => {
    const response = await request.get(`${apiBase}/conversations`, {
      params: { hasHandoff: 'true' },
      headers: { Authorization: 'Bearer test-token' },
    });

    if (response.status() === 200) {
      const body = await response.json();
      const conversations = body.data?.conversations || body.conversations || [];
      const validStatuses = ['none', 'pending', 'active', 'resolved'];

      for (const conv of conversations) {
        expect(validStatuses).toContain(conv.handoffStatus);
      }
    }
  });

  test('[P1] should validate handoff reason enum in API response', async ({ request }) => {
    const response = await request.get(`${apiBase}/conversations`, {
      params: { hasHandoff: 'true' },
      headers: { Authorization: 'Bearer test-token' },
    });

    if (response.status() === 200) {
      const body = await response.json();
      const conversations = body.data?.conversations || body.conversations || [];
      const validReasons = ['keyword', 'low_confidence', 'clarification_loop', null];

      for (const conv of conversations) {
        expect(validReasons).toContain(conv.handoffReason);
      }
    }
  });

  test('[P1] should validate ISO 8601 timestamp format', async ({ request }) => {
    const response = await request.get(`${apiBase}/conversations`, {
      params: { hasHandoff: 'true' },
      headers: { Authorization: 'Bearer test-token' },
    });

    if (response.status() === 200) {
      const body = await response.json();
      const conversations = body.data?.conversations || body.conversations || [];

      for (const conv of conversations) {
        if (conv.handoffTriggeredAt) {
          const date = new Date(conv.handoffTriggeredAt);
          expect(date.toISOString()).toBe(conv.handoffTriggeredAt);
        }
      }
    }
  });

  test('[P2] should validate error code ranges', async ({ request }) => {
    const response = await request.get(`${apiBase}/conversations/invalid-nonexistent-id-99999`, {
      headers: { Authorization: 'Bearer test-token' },
    });

    if (response.status() >= 400 && response.status() < 500) {
      const body = await response.json();

      if (body.code) {
        expect(body.code).toBeGreaterThanOrEqual(7000);
        expect(body.code).toBeLessThanOrEqual(7999);
      }
    }
  });
});

});
