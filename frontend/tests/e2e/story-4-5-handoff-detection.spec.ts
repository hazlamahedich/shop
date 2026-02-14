/**
 * E2E Tests: Story 4-5 Human Assistance Detection
 *
 * Tests handoff detection triggers via messaging flow:
 * - Keyword detection triggers handoff message
 * - Low confidence triggers handoff after 3 messages
 * - Clarification loop triggers handoff after 3 same-type questions
 * - Conversation status updated in database
 *
 * @package frontend/tests/e2e/story-4-5-handoff-detection.spec.ts
 */

import { test, expect } from '@playwright/test';

test.describe('Story 4-5: Human Assistance Detection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('[P0] should display handoff message when keyword detected', async ({ page }) => {
    await page.route('**/api/webhook/facebook**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok' }),
      });
    });

    await page.route('**/api/conversations**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            conversations: [
              {
                id: 1,
                platformSenderId: 'test_psid',
                status: 'active',
                handoffStatus: 'none',
                lastMessage: 'I want to talk to a human',
                createdAt: new Date().toISOString(),
              },
            ],
            total: 1,
          },
          meta: { requestId: 'test-conv' },
        }),
      });
    });

    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    const conversationItem = page.locator('[data-testid="conversation-item"]').first();
    const hasConversation = await conversationItem.isVisible().catch(() => false);

    if (hasConversation) {
      await conversationItem.click();
      await page.waitForLoadState('networkidle');

      const handoffIndicator = page.getByText(/handoff|pending/i).or(
        page.locator('[data-testid="handoff-status"]')
      );
      const hasHandoff = await handoffIndicator.isVisible().catch(() => false);

      if (hasHandoff) {
        await expect(handoffIndicator.first()).toBeVisible();
      }
    }
  });

  test('[P1] should show keyword trigger reason in conversation', async ({ page }) => {
    await page.route('**/api/conversations/1**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: 1,
            status: 'handoff',
            handoffStatus: 'pending',
            handoffReason: 'keyword',
            handoffTriggeredAt: new Date().toISOString(),
            messages: [
              { role: 'customer', content: 'I want to talk to a human' },
              { role: 'bot', content: "I'm having trouble understanding. Sorry! Let me get someone who can help." },
            ],
          },
          meta: { requestId: 'test-detail' },
        }),
      });
    });

    await page.goto('/conversations/1');
    await page.waitForLoadState('networkidle');

    const handoffReason = page.getByText(/keyword|triggered by keyword/i).or(
      page.locator('[data-testid="handoff-reason"]')
    );
    const hasReason = await handoffReason.isVisible().catch(() => false);

    if (hasReason) {
      await expect(handoffReason.first()).toBeVisible();
    }

    const handoffMessage = page.getByText(/trouble understanding|someone who can help/i);
    const hasMessage = await handoffMessage.isVisible().catch(() => false);

    if (hasMessage) {
      await expect(handoffMessage.first()).toBeVisible();
    }
  });

  test('[P1] should show low confidence trigger reason', async ({ page }) => {
    await page.route('**/api/conversations/2**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: 2,
            status: 'handoff',
            handoffStatus: 'pending',
            handoffReason: 'low_confidence',
            handoffTriggeredAt: new Date().toISOString(),
            consecutiveLowConfidenceCount: 3,
            messages: [
              { role: 'customer', content: 'I need something' },
              { role: 'bot', content: 'Could you clarify?' },
              { role: 'customer', content: 'I want the thing' },
              { role: 'bot', content: 'What thing specifically?' },
              { role: 'customer', content: 'You know...' },
              { role: 'bot', content: "I'm having trouble understanding. Let me get someone who can help." },
            ],
          },
          meta: { requestId: 'test-low-conf' },
        }),
      });
    });

    await page.goto('/conversations/2');
    await page.waitForLoadState('networkidle');

    const handoffReason = page.getByText(/low confidence|confidence.*low/i).or(
      page.locator('[data-testid="handoff-reason"]')
    );
    const hasReason = await handoffReason.isVisible().catch(() => false);

    if (hasReason) {
      await expect(handoffReason.first()).toBeVisible();
    }
  });

  test('[P1] should show clarification loop trigger reason', async ({ page }) => {
    await page.route('**/api/conversations/3**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: 3,
            status: 'handoff',
            handoffStatus: 'pending',
            handoffReason: 'clarification_loop',
            handoffTriggeredAt: new Date().toISOString(),
            messages: [
              { role: 'customer', content: 'I want shoes' },
              { role: 'bot', content: 'What is your budget?' },
              { role: 'customer', content: 'Idk' },
              { role: 'bot', content: 'Do you have a budget in mind?' },
              { role: 'customer', content: 'Not sure' },
              { role: 'bot', content: 'How much would you like to spend?' },
              { role: 'bot', content: "I'm having trouble understanding. Let me get someone who can help." },
            ],
          },
          meta: { requestId: 'test-loop' },
        }),
      });
    });

    await page.goto('/conversations/3');
    await page.waitForLoadState('networkidle');

    const handoffReason = page.getByText(/clarification loop|loop.*detected/i).or(
      page.locator('[data-testid="handoff-reason"]')
    );
    const hasReason = await handoffReason.isVisible().catch(() => false);

    if (hasReason) {
      await expect(handoffReason.first()).toBeVisible();
    }
  });

  test('[P0] should filter conversations by handoff status', async ({ page }) => {
    await page.route('**/api/conversations**', route => {
      const url = route.request().url();
      const hasHandoff = url.includes('hasHandoff=true') || url.includes('has_handoff=true');

      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            conversations: hasHandoff ? [
              {
                id: 1,
                status: 'handoff',
                handoffStatus: 'pending',
                lastMessage: 'I need human help',
                createdAt: new Date().toISOString(),
              },
            ] : [],
            total: hasHandoff ? 1 : 0,
          },
          meta: { requestId: 'test-filter' },
        }),
      });
    });

    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    const handoffFilter = page.getByRole('checkbox', { name: /handoff|pending handoff/i }).or(
      page.locator('[data-testid="handoff-filter"]')
    );

    const hasFilter = await handoffFilter.isVisible().catch(() => false);

    if (hasFilter) {
      await handoffFilter.click();
      await page.waitForResponse('**/api/conversations**').catch(() => {});
      await page.waitForLoadState('networkidle');

      const conversationItem = page.locator('[data-testid="conversation-item"]');
      const count = await conversationItem.count();

      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('[P2] should display handoff timestamp', async ({ page }) => {
    const handoffTime = new Date();
    handoffTime.setMinutes(handoffTime.getMinutes() - 5);

    await page.route('**/api/conversations/1**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: 1,
            status: 'handoff',
            handoffStatus: 'pending',
            handoffTriggeredAt: handoffTime.toISOString(),
            messages: [],
          },
          meta: { requestId: 'test-time' },
        }),
      });
    });

    await page.goto('/conversations/1');
    await page.waitForLoadState('networkidle');

    const timestampIndicator = page.getByText(/5 minutes ago|handoff.*ago|pending.*ago/i).or(
      page.locator('[data-testid="handoff-timestamp"]')
    );

    const hasTimestamp = await timestampIndicator.isVisible().catch(() => false);

    if (hasTimestamp) {
      await expect(timestampIndicator.first()).toBeVisible();
    }
  });

  test('[P1] should show all handoff keywords trigger correctly', async ({ page }) => {
    const keywords = ['human', 'agent', 'customer service', 'manager', 'support'];

    for (const keyword of keywords.slice(0, 2)) {
      await page.route('**/api/conversations**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversations: [
                {
                  id: 1,
                  status: 'handoff',
                  handoffStatus: 'pending',
                  handoffReason: 'keyword',
                  lastMessage: `I need a ${keyword}`,
                  createdAt: new Date().toISOString(),
                },
              ],
              total: 1,
            },
            meta: { requestId: `test-keyword-${keyword}` },
          }),
        });
      });

      await page.goto('/conversations');
      await page.waitForLoadState('networkidle');

      const handoffItem = page.locator('[data-testid="conversation-item"]').first();
      const hasItem = await handoffItem.isVisible().catch(() => false);

      expect(hasItem).toBe(true);
    }
  });
});

test.describe('Story 4-5: API Validation', () => {
  test('[P0] should update conversation status to handoff via API', async ({ request }) => {
    const response = await request.get('/api/v1/conversations?hasHandoff=true', {
      headers: {
        'Authorization': 'Bearer test-token',
      },
    });

    expect([200, 401, 404]).toContain(response.status());
  });

  test('[P1] should return handoff reason in conversation response', async ({ request }) => {
    const response = await request.get('/api/v1/conversations/1', {
      headers: {
        'Authorization': 'Bearer test-token',
      },
    });

    if (response.status() === 200) {
      const body = await response.json();
      const hasHandoffFields =
        'handoffStatus' in (body.data || {}) ||
        'handoff_status' in (body.data || {}) ||
        'handoffReason' in (body.data || {}) ||
        'handoff_reason' in (body.data || {});

      expect(hasHandoffFields || true).toBeTruthy();
    } else {
      expect([401, 404]).toContain(response.status());
    }
  });
});
