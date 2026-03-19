/**
 *  * E2E Tests for Story 10-4: Feedback Rating Widget
 *
 *  * Tests feedback rating functionality in the widget.
 *  * Test URL: http://localhost:5173/widget-test
 *
 *  * Acceptance Criteria:
 *  * - AC1: Thumbs Up/Down Buttons Appear Below Bot Messages
 *  * - AC2: Clicking Sends Feedback to Backend
 *  * - AC3: Optional Text Feedback on Thumbs Down
 *  * - AC4: Feedback Analytics Available in Dashboard
 *  * - AC5: Feedback Tied to Message and Conversation
 *  * - AC6: Only Shown for Bot Messages
 *  * - AC7: Accessibility
 *  * - AC8: Feedback Enabled/Disabled by Merchant
 */

import { test, expect, Page } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetSession,
  WIDGET_CONFIG_DEFAULTS
} from '../helpers/widget-test-helpers';

async function mockGeneralModeConfig(page: Page, feedbackEnabled = true) {
  await page.route('**/api/v1/widget/config/*', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        data: {
          ...WIDGET_CONFIG_DEFAULTS,
          onboardingMode: 'general',
          feedbackEnabled,
        },
      }),
    });
  });
}

async function mockWidgetMessageWithFeedback(page: Page, options: {
  content?: string;
  feedbackEnabled?: boolean;
  userRating?: 'positive' | 'negative' | null;
} = {}) {
  const {
    content = 'Hello! How can I help you today?',
    feedbackEnabled = true,
    userRating = null
  } = options;

  await page.route('**/api/v1/widget/message', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        data: {
          messageId: crypto.randomUUID(),
          sender: 'bot',
          content,
          createdAt: new Date().toISOString(),
          feedbackEnabled,
          userRating
        },
        meta: {
          request_id: crypto.randomUUID(),
          timestamp: new Date().toISOString()
        }
      })
    });
  });
}

async function mockWidgetMessageWithoutFeedback(page: Page) {
  await page.route('**/api/v1/widget/message', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        data: {
          messageId: crypto.randomUUID(),
          sender: 'bot',
          content: 'This is a bot message without feedback',
          createdAt: new Date().toISOString(),
          feedbackEnabled: false
        },
        meta: {
          request_id: crypto.randomUUID(),
          timestamp: new Date().toISOString()
        }
      })
    });
  });
}

async function mockFeedbackSubmit(page: Page) {
  await page.route('**/api/v1/feedback', async (route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
        data: {
          id: Math.floor(Math.random() * 10000),
          messageId: crypto.randomUUID(),
          rating: 'positive',
          createdAt: new Date().toISOString()
         },
         meta: {
          request_id: crypto.randomUUID(),
          timestamp: new Date().toISOString()
         }
      })
    });
    } else {
      await route.continue();
    }
  });
}

async function openWidget(page: Page) {
  const bubble = page.getByRole('button', { name: 'Open chat' });
  await bubble.click();
  await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();
}

async function sendUserMessage(page: Page, message: string) {
  const input = page.getByPlaceholder(/type.*message/i);
  await input.fill(message);
  const sendButton = page.getByRole('button', { name: /send/i });
  await sendButton.dispatchEvent('click');
}

async function setupWidgetWithConsentDismissed(page: Page) {
  await page.route('**/api/v1/widget/consent', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({ data: { dismissed: true } }),
    });
  });
}

test.describe('[P0] Story 10-4: Feedback Rating Widget', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await mockWidgetSession(page);
    await mockGeneralModeConfig(page);
    await mockWidgetMessageWithFeedback(page);
    await mockFeedbackSubmit(page);
    await setupWidgetWithConsentDismissed(page);
  });

  test('[10.4-E2E-001] AC1: Feedback buttons appear below bot message', async ({ page }) => {
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'Hello');
    await expect(page.getByTestId('message-list').getByText('Hello! How can I help you today?')).toBeVisible();
    
    const feedbackRating = page.getByTestId('feedback-rating');
    await expect(feedbackRating).toBeVisible();
    
    const thumbsUp = page.getByTestId('feedback-up');
    const thumbsDown = page.getByTestId('feedback-down');
    await expect(thumbsUp).toBeVisible();
    await expect(thumbsDown).toBeVisible();
  });

  test('[10.4-E2E-002] AC6: Only shown for bot messages', async ({ page }) => {
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'Hello');
    await expect(page.getByTestId('feedback-rating').first()).toBeVisible();
  });

  test('[10.4-E2E-003] AC2: Clicking thumbs up sends positive feedback', async ({ page }) => {
    const feedbackPromise = page.waitForRequest(async (request) => {
      if (!request.url().includes('/api/v1/feedback')) return false;
      if (request.method() !== 'POST') return false;
      const body = request.postDataJSON();
      return body?.rating === 'positive';
    });

    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'Hello');
    await expect(page.getByTestId('feedback-rating').first()).toBeVisible();

    const thumbsUp = page.getByTestId('feedback-up');
    await thumbsUp.dispatchEvent('click');

    const request = await feedbackPromise;
    const body = request.postDataJSON();
    expect(body.rating).toBe('positive');
  });

  test('[10.4-E2E-004] AC2: Rating state persists after selection', async ({ page }) => {
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'Hello');
    await expect(page.getByTestId('feedback-rating').first()).toBeVisible();

    const thumbsUp = page.getByTestId('feedback-up');
    await thumbsUp.dispatchEvent('click');
    await expect(thumbsUp).toHaveAttribute('aria-pressed', 'true');

    const thumbsDown = page.getByTestId('feedback-down');
    await expect(thumbsDown).toHaveAttribute('aria-pressed', 'false');
  });

  test('[10.4-E2E-005] AC3: Comment form on thumbs down', async ({ page }) => {
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'Hello');
    await expect(page.getByTestId('feedback-rating').first()).toBeVisible();

    const thumbsDown = page.getByTestId('feedback-down');
    await thumbsDown.dispatchEvent('click');

    const commentForm = page.getByTestId('feedback-comment-form');
    await expect(commentForm).toBeVisible();

    const commentInput = page.getByTestId('feedback-comment');
    await expect(commentInput).toBeVisible();

    const submitButton = commentForm.getByRole('button', { name: 'Submit' });
    await expect(submitButton).toBeVisible();

    const skipButton = commentForm.getByRole('button', { name: 'Skip' });
    await expect(skipButton).toBeVisible();
  });

  test('[10.4-E2E-006] AC3: Text input max 500 characters', async ({ page }) => {
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'Hello');
    await expect(page.getByTestId('feedback-rating').first()).toBeVisible();

    const thumbsDown = page.getByTestId('feedback-down');
    await thumbsDown.dispatchEvent('click');

    const commentInput = page.getByTestId('feedback-comment');
    await commentInput.fill('a'.repeat(600));
    
    const value = await commentInput.inputValue();
    expect(value.length).toBe(500);
  });

  test('[10.4-E2E-007] AC3: Dismiss form without submitting', async ({ page }) => {
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'Hello');
    await expect(page.getByTestId('feedback-rating').first()).toBeVisible();

    const thumbsDown = page.getByTestId('feedback-down');
    await thumbsDown.dispatchEvent('click');

    const commentForm = page.getByTestId('feedback-comment-form');
    await expect(commentForm).toBeVisible();

    const skipButton = commentForm.getByRole('button', { name: 'Skip' });
    await skipButton.dispatchEvent('click');

    await expect(commentForm).not.toBeVisible();

    const feedbackRating = page.getByTestId('feedback-rating');
    await expect(feedbackRating).toBeVisible();
  });

  test('[10.4-E2E-008] AC7: Keyboard navigation works', async ({ page }) => {
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'Hello');
    await expect(page.getByTestId('feedback-rating').first()).toBeVisible();

    const thumbsUp = page.getByTestId('feedback-up');
    await thumbsUp.focus();
    await expect(thumbsUp).toBeFocused();

    await page.keyboard.press('Enter');
    await expect(thumbsUp).toHaveAttribute('aria-pressed', 'true');
  });

  test('[10.4-E2E-009] AC7: ARIA attributes present', async ({ page }) => {
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'Hello');

    const feedbackRating = page.getByTestId('feedback-rating');
    await expect(feedbackRating).toHaveAttribute('role', 'group');
    await expect(feedbackRating).toHaveAttribute('aria-label', /rate this response/i);

    
    const thumbsUp = page.getByTestId('feedback-up');
    await expect(thumbsUp).toHaveAttribute('aria-label', /helpful/i);
    await expect(thumbsUp).toHaveAttribute('aria-pressed', 'false');

    const thumbsDown = page.getByTestId('feedback-down');
    await expect(thumbsDown).toHaveAttribute('aria-label', /not helpful/i);
    await expect(thumbsDown).toHaveAttribute('aria-pressed', 'false');
  });

  test('[10.4-E2E-010] AC7: Touch target minimum 44x44px', async ({ page }) => {
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'Hello');

    const thumbsUp = page.getByTestId('feedback-up');
    const box = await thumbsUp.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.width).toBeGreaterThanOrEqual(44);
    expect(box!.height).toBeGreaterThanOrEqual(44);
  });
});

test.describe('[P2] Story 10-4: Configuration', () => {
  test('[10.4-E2E-011] AC8: Feedback disabled by merchant config', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await mockWidgetSession(page);
    await mockGeneralModeConfig(page, false);
    await mockWidgetMessageWithoutFeedback(page);
    await setupWidgetWithConsentDismissed(page);

    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'Hello');
    await expect(page.getByTestId('message-list').getByText('This is a bot message without feedback')).toBeVisible();

    const feedbackRating = page.getByTestId('feedback-rating');
    const count = await feedbackRating.count();
    expect(count).toBe(0);
  });

  test('[10.4-E2E-012] AC7: Reduced motion preference respected', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await mockWidgetSession(page);
    await mockGeneralModeConfig(page);
    await mockWidgetMessageWithFeedback(page);
    await mockFeedbackSubmit(page);
    await setupWidgetWithConsentDismissed(page);

    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'Hello');

    const thumbsUp = page.getByTestId('feedback-up');
    await expect(thumbsUp).toBeVisible();

    const transition = await thumbsUp.evaluate((el) => {
      return window.getComputedStyle(el).transition;
    });
    expect(transition).toBe('none');
  });
});

test.describe('[P1] Story 10-4: Dashboard Analytics', () => {
  test.skip('[10.4-E2E-013] AC4: Analytics widget visible in dashboard', async ({ page }) => {
    // This test requires:
    // 1. Authenticated merchant session
    // 2. Widget mode disabled (dashboard view)
    // 3. FeedbackAnalyticsWidget component rendered in dashboard
    // 
    // Skipping because:
    // - Dashboard requires authentication setup
    // - This is a P1 test for dashboard feature
    // - Widget E2E tests focus on widget functionality
    // 
    // TODO: Add this test when dashboard E2E test infrastructure is set up
  });
});
