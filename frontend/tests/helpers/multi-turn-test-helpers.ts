import { Page, expect } from '@playwright/test';
import { sendMessage } from './widget-test-helpers';

export interface ClarificationMessageOptions {
  content: string;
  isClarificationQuestion?: boolean;
  accumulatedConstraints?: Record<string, unknown>;
  turnCount?: number;
  pendingQuestions?: string[];
  multiTurnState?: string;
  originalQuery?: string;
}

export function createClarificationResponse(options: ClarificationMessageOptions) {
  return {
    content: options.content,
    isClarificationQuestion: options.isClarificationQuestion ?? false,
    accumulatedConstraints: options.accumulatedConstraints ?? {},
    turnCount: options.turnCount ?? 0,
    pendingQuestions: options.pendingQuestions ?? [],
    multiTurnState: options.multiTurnState ?? 'IDLE',
    originalQuery: options.originalQuery ?? null,
  };
}

export async function mockMultiTurnConversation(
  page: Page,
  handlers: Array<{
    match: (message: string) => boolean;
    response: {
      content: string;
      multiTurnState?: string;
      accumulatedConstraints?: Record<string, unknown>;
      pendingQuestions?: string[];
      turnCount?: number;
      originalQuery?: string;
    };
  }>
) {
  await page.route('**/api/v1/widget/message', async (route) => {
    const body = route.request().postDataJSON();
    const message = body?.message?.toLowerCase() || '';

    for (const handler of handlers) {
      if (handler.match(message)) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              message_id: crypto.randomUUID(),
              sender: 'bot',
              created_at: new Date().toISOString(),
              ...handler.response,
            },
          }),
        });
        return;
      }
    }

    await route.continue();
  });
}

export const CLARIFICATION_QUESTIONS = [
  "What's your budget range?",
  'Do you have a preferred brand?',
  'What size are you looking for?',
  'Any color preference?',
];

export const MULTI_TURN_HANDLERS = {
  ambiguousQuery: {
    match: (msg: string) => msg.includes('shoes') || msg.includes('looking for'),
    response: {
      content: "I'd love to help you find the right shoes! What's your budget range?",
      multiTurnState: 'CLARIFYING',
      pendingQuestions: ['budget', 'brand', 'size'],
      turnCount: 0,
      originalQuery: 'shoes',
    },
  },
  budgetResponse: {
    match: (msg: string) => msg.includes('100') || msg.includes('budget') || msg.includes('under'),
    response: {
      content: 'Got it, under $100. Do you have a preferred brand?',
      multiTurnState: 'CLARIFYING',
      accumulatedConstraints: { budget_max: 100 },
      pendingQuestions: ['brand', 'size'],
      turnCount: 1,
      originalQuery: 'shoes',
    },
  },
  brandResponse: {
    match: (msg: string) => msg.includes('nike') || msg.includes('brand'),
    response: {
      content: 'Nike, great choice! What size are you looking for?',
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
      content: 'Here are the best Nike running shoes under $100 in size L!',
      multiTurnState: 'REFINE_RESULTS',
      accumulatedConstraints: { budget_max: 100, brand: 'nike', size: 'l' },
      pendingQuestions: [],
      turnCount: 3,
      originalQuery: 'shoes',
    },
  },
  topicChange: {
    match: (msg: string) =>
      msg.includes('pizza') || msg.includes('weather') || msg.includes('cancel'),
    response: {
      content: "Sure, let's talk about that instead! How can I help?",
      multiTurnState: 'IDLE',
      pendingQuestions: [],
      turnCount: 0,
    },
  },
  invalidResponse: {
    match: (msg: string) =>
      msg === 'asdf' || msg === 'idk' || msg === '?' || msg.length < 2,
    response: {
      content:
        "I didn't quite catch that. Could you try rephrasing? For example, you could mention a specific price range, size, or brand.",
      multiTurnState: 'CLARIFYING',
      pendingQuestions: ['budget'],
      turnCount: 0,
      originalQuery: 'shoes',
    },
  },
};

export const GENERAL_MODE_HANDLERS = {
  accountProblem: {
    match: (msg: string) => msg.includes('account') || msg.includes('problem'),
    response: {
      content: "I'm sorry to hear about your account issue! How severe is this problem?",
      multiTurnState: 'CLARIFYING',
      pendingQuestions: ['severity', 'timeframe'],
      turnCount: 0,
      originalQuery: 'account problem',
    },
  },
  urgentSeverity: {
    match: (msg: string) => msg.includes('urgent') || msg.includes('critical'),
    response: {
      content: 'Understood, this is urgent. When did this issue start?',
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
        'Here is what I found for your urgent account issue that started today. I recommend resetting your password first.',
      multiTurnState: 'REFINE_RESULTS',
      accumulatedConstraints: { severity: 'urgent', timeframe: 'today' },
      pendingQuestions: [],
      turnCount: 2,
      originalQuery: 'account problem',
    },
  },
  topicChange: {
    match: (msg: string) =>
      msg.includes('pizza') || msg.includes('buy') || msg.includes('shoes'),
    response: {
      content: "Sure, let's talk about that instead! How can I help?",
      multiTurnState: 'IDLE',
      pendingQuestions: [],
      turnCount: 0,
    },
  },
};

export async function sendAndWaitForResponse(page: Page, message: string) {
  const responsePromise = page.waitForResponse('**/api/v1/widget/message');
  await sendMessage(page, message);
  await responsePromise;
}

export async function completeShoeClarification(page: Page) {
  await sendAndWaitForResponse(page, 'I am looking for shoes');
  await expect(page.getByText('budget')).toBeVisible();

  await sendAndWaitForResponse(page, 'under $100');
  await expect(page.getByText('brand')).toBeVisible();

  await sendAndWaitForResponse(page, 'Nike');
  await expect(page.getByText('size')).toBeVisible();

  await sendAndWaitForResponse(page, 'size L');
}
