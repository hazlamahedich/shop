import { test, expect } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
} from '../helpers/widget-test-helpers';
import {
  mockMultiTurnConversation,
  sendAndWaitForResponse,
} from '../helpers/multi-turn-test-helpers';

const NATURAL_QUESTION_HANDLERS = {
  ambiguousProductQuery: {
    match: (msg: string) => msg.includes('shoes') || msg.includes('looking for'),
    response: {
      content:
        "I'd love to help you find the right shoes! Could you tell me your budget range and any brand you prefer?",
      multiTurnState: 'CLARIFYING',
      pendingQuestions: ['budget', 'brand', 'size'],
      turnCount: 0,
      originalQuery: 'shoes',
    },
  },
  partialBudgetResponse: {
    match: (msg: string) => msg.includes('100') || msg.includes('budget') || msg.includes('under'),
    response: {
      content:
        "Great, under $100 noted! Now, do you have a preferred brand you'd like me to look for?",
      multiTurnState: 'CLARIFYING',
      accumulatedConstraints: { budget_max: 100 },
      pendingQuestions: ['brand', 'size'],
      turnCount: 1,
      originalQuery: 'shoes',
    },
  },
  brandResponseWithSize: {
    match: (msg: string) => msg.includes('nike') || msg.includes('brand'),
    response: {
      content:
        "Nike, great choice! Since you mentioned Nike under $100, do you have a size in mind as well?",
      multiTurnState: 'CLARIFYING',
      accumulatedConstraints: { budget_max: 100, brand: 'nike' },
      pendingQuestions: ['size'],
      turnCount: 2,
      originalQuery: 'shoes',
    },
  },
  sizeResponse: {
    match: (msg: string) => msg.includes('size') || msg.includes('large') || msg.includes('l'),
    response: {
      content:
        "Here are the best Nike running shoes under $100 in size L! I've got 3 great options for you.",
      multiTurnState: 'REFINE_RESULTS',
      accumulatedConstraints: { budget_max: 100, brand: 'nike', size: 'l' },
      pendingQuestions: [],
      turnCount: 3,
      originalQuery: 'shoes',
    },
  },
  formatterFailure: {
    match: (msg: string) => msg.includes('laptop') || msg.includes('computer'),
    response: {
      content: "What's your budget range?",
      multiTurnState: 'CLARIFYING',
      pendingQuestions: ['budget', 'brand'],
      turnCount: 0,
      originalQuery: 'laptop',
    },
  },
};

const GENERAL_MODE_NATURAL_HANDLERS = {
  accountProblem: {
    match: (msg: string) => msg.includes('account') || msg.includes('problem'),
    response: {
      content:
        "I'm sorry to hear about the account trouble! Could you describe when this started and how it's affecting you?",
      multiTurnState: 'CLARIFYING',
      pendingQuestions: ['severity', 'timeframe'],
      turnCount: 0,
      originalQuery: 'account problem',
    },
  },
  severityResponse: {
    match: (msg: string) => msg.includes('urgent') || msg.includes('critical'),
    response: {
      content:
        "Understood, this sounds urgent. Given this is critical, when exactly did it start happening?",
      multiTurnState: 'CLARIFYING',
      accumulatedConstraints: { severity: 'urgent' },
      pendingQuestions: ['timeframe'],
      turnCount: 1,
      originalQuery: 'account problem',
    },
  },
  timeframeResponse: {
    match: (msg: string) => msg.includes('today') || msg.includes('started'),
    response: {
      content:
        'Thanks for the details about your urgent account issue from today. I recommend resetting your password first.',
      multiTurnState: 'REFINE_RESULTS',
      accumulatedConstraints: { severity: 'urgent', timeframe: 'today' },
      pendingQuestions: [],
      turnCount: 2,
      originalQuery: 'account problem',
    },
  },
};

test.describe('Story 11.11 - Natural Clarification Questions', () => {
  test('[P0] 11.11-E2E-001 AC1/AC2: ambiguous query produces natural combined question', async ({
    page,
  }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-natural-session');
    await mockMultiTurnConversation(page, [
      NATURAL_QUESTION_HANDLERS.ambiguousProductQuery,
    ]);
    await loadWidgetWithSession(page, 'test-natural-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForResponse(page, 'I am looking for shoes');

    await expect(page.getByText(/budget.*brand|could you tell me/i)).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText(/your budget range/i)).toBeVisible();
  });

  test('[P0] 11.11-E2E-002 AC4: partial answer acknowledged with thanks and remaining question', async ({
    page,
  }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-partial-session');
    await mockMultiTurnConversation(page, [
      NATURAL_QUESTION_HANDLERS.ambiguousProductQuery,
      NATURAL_QUESTION_HANDLERS.partialBudgetResponse,
    ]);
    await loadWidgetWithSession(page, 'test-partial-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForResponse(page, 'I am looking for shoes');
    await sendAndWaitForResponse(page, 'under $100');

    await expect(
      page.getByText(/noted|great.*under \$100|thanks.*\$100/i)
    ).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/brand|preferred brand/i)).toBeVisible();
  });

  test('[P0] 11.11-E2E-006 AC6: formatter failure degrades gracefully to robotic template', async ({
    page,
  }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-degradation-session');
    await mockMultiTurnConversation(page, [
      NATURAL_QUESTION_HANDLERS.formatterFailure,
    ]);
    await loadWidgetWithSession(page, 'test-degradation-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForResponse(page, 'I need a laptop');

    await expect(page.getByText(/budget/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/error|crash|undefined|null/i)).not.toBeVisible();
  });

  test('[P1] 11.11-E2E-003 AC3: multi-turn context accumulation references previous answers', async ({
    page,
  }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-context-session');
    await mockMultiTurnConversation(page, [
      NATURAL_QUESTION_HANDLERS.ambiguousProductQuery,
      NATURAL_QUESTION_HANDLERS.partialBudgetResponse,
      NATURAL_QUESTION_HANDLERS.brandResponseWithSize,
    ]);
    await loadWidgetWithSession(page, 'test-context-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForResponse(page, 'I am looking for shoes');
    await sendAndWaitForResponse(page, 'under $100');
    await sendAndWaitForResponse(page, 'Nike');

    await expect(page.getByText(/nike.*under \$100|since you mentioned/i)).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByText(/size/i)).toBeVisible();
  });

  test('[P1] 11.11-E2E-004 AC5: general mode produces mode-appropriate questions', async ({
    page,
  }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-general-session');
    await mockMultiTurnConversation(page, [
      GENERAL_MODE_NATURAL_HANDLERS.accountProblem,
      GENERAL_MODE_NATURAL_HANDLERS.severityResponse,
    ]);
    await loadWidgetWithSession(page, 'test-general-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForResponse(page, 'I have an account problem');

    await expect(
      page.getByText(/describe when|started.*affecting|could you describe/i)
    ).toBeVisible({ timeout: 5000 });

    await sendAndWaitForResponse(page, 'it is urgent');

    await expect(page.getByText(/critical|when exactly did it start/i)).toBeVisible({
      timeout: 5000,
    });
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

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendAndWaitForResponse(page, 'I am looking for shoes');
    const firstResponse = page.locator('[data-testid="message-bubble"].message-bubble--bot');
    const firstText = await firstResponse.last().textContent();

    await sendAndWaitForResponse(page, 'under $100');
    const secondText = await firstResponse.last().textContent();

    expect(firstText).not.toBe(secondText);
    expect(firstText).toBeTruthy();
    expect(secondText).toBeTruthy();
  });
});
