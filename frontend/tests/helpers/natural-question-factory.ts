import { ClarificationMessageOptions, createClarificationResponse } from './multi-turn-test-helpers';

export interface NaturalQuestionHandler {
  match: (message: string) => boolean;
  response: ReturnType<typeof createClarificationResponse>;
}

export function createNaturalQuestionHandler(
  matchFn: (message: string) => boolean,
  options: Partial<ClarificationMessageOptions>
): NaturalQuestionHandler {
  const defaults: ClarificationMessageOptions = {
    content: '',
    isClarificationQuestion: true,
    accumulatedConstraints: {},
    turnCount: 0,
    pendingQuestions: [],
    multiTurnState: 'CLARIFYING',
    originalQuery: null,
  };

  return {
    match: matchFn,
    response: createClarificationResponse({ ...defaults, ...options }),
  };
}

export const ECOMMERCE_HANDLERS = {
  ambiguousProductQuery: createNaturalQuestionHandler(
    (msg) => msg.includes('shoes') || msg.includes('looking for'),
    {
      content:
        "I'd love to help you find the right shoes! Could you tell me your budget range and any brand you prefer?",
      multiTurnState: 'CLARIFYING',
      pendingQuestions: ['budget', 'brand', 'size'],
      turnCount: 0,
      originalQuery: 'shoes',
    }
  ),

  partialBudgetResponse: createNaturalQuestionHandler(
    (msg) => msg.includes('100') || msg.includes('budget') || msg.includes('under'),
    {
      content:
        "Great, under $100 noted! Now, do you have a preferred brand you'd like me to look for?",
      multiTurnState: 'CLARIFYING',
      accumulatedConstraints: { budget_max: 100 },
      pendingQuestions: ['brand', 'size'],
      turnCount: 1,
      originalQuery: 'shoes',
    }
  ),

  brandResponseWithSize: createNaturalQuestionHandler(
    (msg) => msg.includes('nike') || msg.includes('brand'),
    {
      content:
        "Nike, great choice! Since you mentioned Nike under $100, do you have a size in mind as well?",
      multiTurnState: 'CLARIFYING',
      accumulatedConstraints: { budget_max: 100, brand: 'nike' },
      pendingQuestions: ['size'],
      turnCount: 2,
      originalQuery: 'shoes',
    }
  ),

  sizeResponse: createNaturalQuestionHandler(
    (msg) => msg.includes('size') || msg.includes('large') || msg.includes('l'),
    {
      content:
        "Here are the best Nike running shoes under $100 in size L! I've got 3 great options for you.",
      multiTurnState: 'REFINE_RESULTS',
      accumulatedConstraints: { budget_max: 100, brand: 'nike', size: 'l' },
      pendingQuestions: [],
      turnCount: 3,
      originalQuery: 'shoes',
    }
  ),

  formatterFailure: createNaturalQuestionHandler(
    (msg) => msg.includes('laptop') || msg.includes('computer'),
    {
      content: "What's your budget range?",
      multiTurnState: 'CLARIFYING',
      pendingQuestions: ['budget', 'brand'],
      turnCount: 0,
      originalQuery: 'laptop',
    }
  ),
};

export const GENERAL_MODE_HANDLERS = {
  accountProblem: createNaturalQuestionHandler(
    (msg) => msg.includes('account') || msg.includes('problem'),
    {
      content:
        "I'm sorry to hear about the account trouble! Could you describe when this started and how it's affecting you?",
      multiTurnState: 'CLARIFYING',
      pendingQuestions: ['severity', 'timeframe'],
      turnCount: 0,
      originalQuery: 'account problem',
    }
  ),

  severityResponse: createNaturalQuestionHandler(
    (msg) => msg.includes('urgent') || msg.includes('critical'),
    {
      content:
        "Understood, this sounds urgent. Given this is critical, when exactly did it start happening?",
      multiTurnState: 'CLARIFYING',
      accumulatedConstraints: { severity: 'urgent' },
      pendingQuestions: ['timeframe'],
      turnCount: 1,
      originalQuery: 'account problem',
    }
  ),

  timeframeResponse: createNaturalQuestionHandler(
    (msg) => msg.includes('today') || msg.includes('started'),
    {
      content:
        'Thanks for the details about your urgent account issue from today. I recommend resetting your password first.',
      multiTurnState: 'REFINE_RESULTS',
      accumulatedConstraints: { severity: 'urgent', timeframe: 'today' },
      pendingQuestions: [],
      turnCount: 2,
      originalQuery: 'account problem',
    }
  ),
};
