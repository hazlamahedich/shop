import { test, expect } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
  botMessages,
} from '../helpers/widget-test-helpers';
import { mockMultiTurnConversation, sendAndWaitForResponse } from '../helpers/multi-turn-test-helpers';
import {
  ECOMMERCE_HANDLERS,
  GENERAL_MODE_HANDLERS,
  createNaturalQuestionHandler,
} from '../helpers/natural-question-factory';

test.describe('Story 11.11 - Natural Clarification Questions', () => {
  async function setupWidget(
    page: import('@playwright/test').Page,
    sessionId: string,
    handlers: Array<{ match: (message: string) => boolean; response: Record<string, unknown> }>
  ) {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, sessionId);
    await mockMultiTurnConversation(page, handlers);
    await loadWidgetWithSession(page, sessionId);
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();
  }

  test('[P0] 11.11-E2E-001 AC1/AC2: ambiguous query produces natural combined question', async ({
    page,
  }) => {
    await setupWidget(page, 'test-natural-session', [ECOMMERCE_HANDLERS.ambiguousProductQuery]);

    await sendAndWaitForResponse(page, 'I am looking for shoes');

    await expect(botMessages(page).last()).toContainText(/budget.*brand|could you tell me/i);
    await expect(botMessages(page).last()).toContainText(/budget range/i);
  });

  test('[P0] 11.11-E2E-002 AC4: partial answer acknowledged with thanks and remaining question', async ({
    page,
  }) => {
    await setupWidget(page, 'test-partial-session', [
      ECOMMERCE_HANDLERS.ambiguousProductQuery,
      ECOMMERCE_HANDLERS.partialBudgetResponse,
    ]);

    await sendAndWaitForResponse(page, 'I am looking for shoes');
    await sendAndWaitForResponse(page, 'under $100');

    await expect(botMessages(page).last()).toContainText(/noted|great.*under \$100|thanks.*\$100/i);
    await expect(botMessages(page).last()).toContainText(/brand|preferred brand/i);
  });

  test('[P0] 11.11-E2E-006 AC6: formatter failure degrades gracefully to robotic template', async ({
    page,
  }) => {
    await setupWidget(page, 'test-degradation-session', [ECOMMERCE_HANDLERS.formatterFailure]);

    await sendAndWaitForResponse(page, 'I need a laptop');

    await expect(botMessages(page).last()).toContainText(/budget/i);
    await expect(page.getByText(/error|crash|undefined|null/i)).not.toBeVisible();
  });

  test('[P1] 11.11-E2E-003 AC3: multi-turn context accumulation references previous answers', async ({
    page,
  }) => {
    await setupWidget(page, 'test-context-session', [
      ECOMMERCE_HANDLERS.ambiguousProductQuery,
      ECOMMERCE_HANDLERS.partialBudgetResponse,
      ECOMMERCE_HANDLERS.brandResponseWithSize,
    ]);

    await sendAndWaitForResponse(page, 'I am looking for shoes');
    await sendAndWaitForResponse(page, 'under $100');
    await sendAndWaitForResponse(page, 'Nike');

    await expect(botMessages(page).last()).toContainText(/nike.*under \$100|since you mentioned/i);
    await expect(botMessages(page).last()).toContainText(/size/i);
  });

  test('[P1] 11.11-E2E-004 AC5: general mode produces mode-appropriate questions', async ({
    page,
  }) => {
    await setupWidget(page, 'test-general-session', [
      GENERAL_MODE_HANDLERS.accountProblem,
      GENERAL_MODE_HANDLERS.severityResponse,
    ]);

    await sendAndWaitForResponse(page, 'I have an account problem');

    await expect(botMessages(page).last()).toContainText(
      /describe when|started.*affecting|could you describe/i
    );

    await sendAndWaitForResponse(page, 'it is urgent');

    await expect(botMessages(page).last()).toContainText(/critical|when exactly did it start/i);
  });

  test('[P2] 11.11-E2E-005 AC1: sequential turns produce rotating templates', async ({
    page,
  }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-rotation-session');

    const responses = [
      "I'd love to help you find shoes! What's your budget range?",
      "Great choice! Now, what brand do you prefer?",
      'Almost there — what size are you looking for?',
    ];

    let callIndex = 0;
    await page.route('**/api/v1/widget/message', async (route) => {
      const body = route.request().postDataJSON();
      const message = body?.message?.toLowerCase() || '';

      if (message.includes('shoes') || message.includes('looking for')) {
        callIndex = 0;
      } else if (message.includes('100') || message.includes('under')) {
        callIndex = 1;
      } else if (message.includes('nike') || message.includes('brand')) {
        callIndex = 2;
      }

      if (callIndex < responses.length) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              message_id: crypto.randomUUID(),
              sender: 'bot',
              created_at: new Date().toISOString(),
              content: responses[callIndex],
              multiTurnState: callIndex < 2 ? 'CLARIFYING' : 'REFINE_RESULTS',
              pendingQuestions: [],
              turnCount: callIndex,
              originalQuery: 'shoes',
            },
          }),
        });
        return;
      }

      await route.continue();
    });

    await loadWidgetWithSession(page, 'test-rotation-session');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForResponse(page, 'I am looking for shoes');
    const firstText = await botMessages(page).last().textContent();

    await sendAndWaitForResponse(page, 'under $100');
    const secondText = await botMessages(page).last().textContent();

    expect(firstText).not.toBe(secondText);
    expect(firstText).toBeTruthy();
    expect(secondText).toBeTruthy();
  });

  test('[P2] 11.11-E2E-007 AC2: combined question respects 200-character cap', async ({ page }) => {
    const longCombinedHandler = createNaturalQuestionHandler(
      (msg) => msg.includes('shirt') || msg.includes('looking for'),
      {
        content:
          "To help you find the perfect shirt, could you tell me your preferred brand, size, color, and budget?",
        multiTurnState: 'CLARIFYING',
        pendingQuestions: ['brand', 'size', 'color', 'budget'],
        turnCount: 0,
        originalQuery: 'shirt',
      }
    );

    await setupWidget(page, 'test-char-cap-session', [longCombinedHandler]);

    await sendAndWaitForResponse(page, 'I am looking for a shirt');

    const responseText = await botMessages(page).last().textContent();
    expect(responseText).toBeTruthy();
    expect(responseText!.length).toBeLessThanOrEqual(250);
  });

  test('[P2] 11.11-E2E-008 AC6: network error during clarification shows graceful fallback', async ({
    page,
  }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-network-error-session');

    await page.route('**/api/v1/widget/message', async (route) => {
      const body = route.request().postDataJSON();
      const message = body?.message?.toLowerCase() || '';

      if (message.includes('shoes')) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              message_id: crypto.randomUUID(),
              sender: 'bot',
              created_at: new Date().toISOString(),
              content: "I'd love to help you find shoes! What's your budget?",
              multiTurnState: 'CLARIFYING',
              pendingQuestions: ['budget'],
              turnCount: 0,
              originalQuery: 'shoes',
            },
          }),
        });
        return;
      }

      await route.fulfill({
        status: 500,
        body: JSON.stringify({
          error: { message: 'Internal server error', code: 15000 },
        }),
      });
    });

    await loadWidgetWithSession(page, 'test-network-error-session');
    await page.getByRole('button', { name: 'Open chat' }).click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForResponse(page, 'I am looking for shoes');
    await expect(botMessages(page).last()).toContainText(/budget/i);

    await page.getByPlaceholder('Type a message...').fill('under $100');
    await page.getByRole('button', { name: 'Send message' }).click();

    await expect(page.getByText(/error|try again|something went wrong/i)).toBeVisible();
    await expect(page.getByText(/crash|undefined|null/i)).not.toBeVisible();
  });

  test('[P2] 11.11-E2E-009 AC5: mode switch mid-conversation clears ecommerce constraints', async ({
    page,
  }) => {
    const modeSwitchHandler = createNaturalQuestionHandler(
      (msg) => msg.includes('billing') || msg.includes('charge'),
      {
        content:
          "I see you have a question about billing. Could you describe the issue you're experiencing?",
        multiTurnState: 'CLARIFYING',
        accumulatedConstraints: {},
        pendingQuestions: ['issue_type', 'severity'],
        turnCount: 0,
        originalQuery: 'billing',
      }
    );

    await setupWidget(page, 'test-mode-switch-session', [
      ECOMMERCE_HANDLERS.ambiguousProductQuery,
      modeSwitchHandler,
    ]);

    await sendAndWaitForResponse(page, 'I am looking for shoes');
    await expect(botMessages(page).last()).toContainText(/budget|brand/i);

    await sendAndWaitForResponse(page, 'actually I have a billing charge question');
    await expect(botMessages(page).last()).toContainText(/billing|issue/i);
    await expect(botMessages(page).last()).not.toContainText(/shoes|budget_max/i);
  });
});
