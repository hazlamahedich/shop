/**
 * Cost Tracking Data Factories
 *
 * Generates realistic test data using @faker-js/faker.
 * All factories support overrides for specific test scenarios.
 *
 * Usage:
 * ```ts
 * import { createConversationCost, createCostSummary } from '@/tests/support/factories/costFactory';
 *
 * const cost = createConversationCost({ provider: 'openai' });
 * const summary = createCostSummary({ totalCostUsd: 100 });
 * ```
 */

import { faker } from '@faker-js/faker';
import type { ConversationCost, CostSummary, CostSummaryParams } from '@/types/cost';

// Set a fixed seed for reproducible tests
faker.seed(12345);

/**
 * Available LLM providers
 */
export const PROVIDERS = ['openai', 'ollama', 'anthropic'] as const;
export type Provider = (typeof PROVIDERS)[number];

/**
 * Available models for each provider
 */
export const MODELS = {
  openai: ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
  ollama: ['llama2', 'mistral', 'codellama'],
  anthropic: ['claude-3-haiku', 'claude-3-sonnet', 'claude-3-opus'],
} as const;

/**
 * Generate a random provider
 */
export function randomProvider(): Provider {
  return faker.helpers.arrayElement(PROVIDERS);
}

/**
 * Generate a random model for a given provider
 */
export function randomModel(provider?: Provider): string {
  const p = provider ?? randomProvider();
  return faker.helpers.arrayElement(MODELS[p]);
}

/**
 * Create a conversation cost object with realistic data
 * @param overrides - Optional overrides for default values
 * @returns ConversationCost object
 */
export function createConversationCost(
  overrides: Partial<ConversationCost> = {}
): ConversationCost {
  const provider = overrides.provider ?? randomProvider();
  const model = overrides.model ?? randomModel(provider);
  const promptTokens = faker.number.int({ min: 50, max: 5000 });
  const completionTokens = faker.number.int({ min: 25, max: 2500 });
  const totalTokens = promptTokens + completionTokens;

  // Calculate costs (roughly based on typical pricing)
  let inputCostUsd = 0;
  let outputCostUsd = 0;

  if (provider === 'openai') {
    inputCostUsd = (promptTokens / 1000) * 0.00015; // GPT-4o-mini pricing
    outputCostUsd = (completionTokens / 1000) * 0.0006;
  } else if (provider === 'anthropic') {
    inputCostUsd = (promptTokens / 1000) * 0.00025; // Claude Haiku pricing
    outputCostUsd = (completionTokens / 1000) * 0.00125;
  }
  // Ollama is free

  const totalCostUsd = inputCostUsd + outputCostUsd;

  return {
    conversationId: overrides.conversationId ?? `fb-psid-${faker.string.alphanumeric(10)}`,
    provider,
    model,
    totalCostUsd: faker.number.float({ min: totalCostUsd * 0.9, max: totalCostUsd * 1.1, precision: 0.0001 }),
    totalTokens,
    requestCount: overrides.requestCount ?? faker.number.int({ min: 1, max: 10 }),
    avgCostPerRequest: 0, // Will be calculated by service
    requests: overrides.requests ?? [],
    ...overrides,
  };
}

/**
 * Create a cost request object
 * @param overrides - Optional overrides for default values
 * @returns Cost request object
 */
export function createCostRequest(overrides: { provider?: Provider; model?: string } = {}) {
  const provider = overrides.provider ?? randomProvider();
  const model = overrides.model ?? randomModel(provider);
  const promptTokens = faker.number.int({ min: 50, max: 5000 });
  const completionTokens = faker.number.int({ min: 25, max: 2500 });
  const totalTokens = promptTokens + completionTokens;

  // Calculate costs
  let inputCostUsd = 0;
  let outputCostUsd = 0;

  if (provider === 'openai') {
    inputCostUsd = (promptTokens / 1000) * 0.00015;
    outputCostUsd = (completionTokens / 1000) * 0.0006;
  } else if (provider === 'anthropic') {
    inputCostUsd = (promptTokens / 1000) * 0.00025;
    outputCostUsd = (completionTokens / 1000) * 0.00125;
  }

  return {
    id: faker.number.int({ min: 1, max: 100000 }),
    requestTimestamp: faker.date.recent({ days: 7 }).toISOString(),
    provider,
    model,
    promptTokens,
    completionTokens,
    totalTokens,
    inputCostUsd: faker.number.float({ min: inputCostUsd * 0.9, max: inputCostUsd * 1.1, precision: 0.000001 }),
    outputCostUsd: faker.number.float({ min: outputCostUsd * 0.9, max: outputCostUsd * 1.1, precision: 0.000001 }),
    totalCostUsd: faker.number.float({ min: (inputCostUsd + outputCostUsd) * 0.9, max: (inputCostUsd + outputCostUsd) * 1.1, precision: 0.000001 }),
    processingTimeMs: faker.number.int({ min: 500, max: 5000 }),
  };
}

/**
 * Create a daily breakdown entry
 * @param date - Specific date (defaults to recent date)
 * @returns Daily breakdown object
 */
export function createDailyBreakdown(date?: Date) {
  const requestCount = faker.number.int({ min: 1, max: 50 });
  const costPerRequest = faker.number.float({ min: 0.0001, max: 0.01, precision: 0.00001 });

  return {
    date: (date ?? faker.date.recent({ days: 30 })).toISOString().split('T')[0],
    totalCostUsd: faker.number.float({ min: 0.001, max: 1.0, precision: 0.0001 }),
    requestCount,
    avgCostPerRequest: costPerRequest,
  };
}

/**
 * Create a top conversation entry
 * @returns Top conversation object
 */
export function createTopConversation() {
  const requestCount = faker.number.int({ min: 5, max: 100 });
  const avgCost = faker.number.float({ min: 0.001, max: 0.05, precision: 0.00001 });

  return {
    conversationId: `fb-psid-${faker.string.alphanumeric(10)}`,
    totalCostUsd: faker.number.float({ min: 0.01, max: 5.0, precision: 0.001 }),
    requestCount,
    avgCostPerRequest: avgCost,
  };
}

/**
 * Create a cost summary with realistic data
 * @param overrides - Optional overrides for default values
 * @returns CostSummary object
 */
export function createCostSummary(overrides: Partial<CostSummary> = {}): CostSummary {
  const conversationCount = faker.number.int({ min: 0, max: 20 });

  // Generate provider breakdown
  const costsByProvider: Record<string, { costUsd: number; requests: number }> = {};

  if (conversationCount > 0) {
    PROVIDERS.forEach((provider) => {
      if (Math.random() > 0.3) {
        // 70% chance of having data for each provider
        const requests = faker.number.int({ min: 1, max: 100 });
        const avgCost = provider === 'ollama' ? 0 : faker.number.float({ min: 0.001, max: 0.02, precision: 0.00001 });

        costsByProvider[provider] = {
          costUsd: faker.number.float({ min: 0, max: requests * avgCost * 2, precision: 0.0001 }),
          requests,
        };
      }
    });
  }

  // Generate daily breakdown (last 7-30 days)
  const days = faker.number.int({ min: 7, max: 30 });
  const dailyBreakdown = Array.from({ length: days }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - i);
    return createDailyBreakdown(date);
  }).reverse();

  // Generate top conversations
  const topConversations = Array.from({ length: Math.min(conversationCount, 5) }, () =>
    createTopConversation()
  );

  // Calculate totals
  const totalRequests = Object.values(costsByProvider).reduce((sum, p) => sum + p.requests, 0);
  const totalCostUsd = Object.values(costsByProvider).reduce((sum, p) => sum + p.costUsd, 0);
  const totalTokens = totalRequests * faker.number.int({ min: 100, max: 2000 });
  const avgCostPerRequest = totalRequests > 0 ? totalCostUsd / totalRequests : 0;

  return {
    totalCostUsd: faker.number.float({ min: totalCostUsd * 0.9, max: totalCostUsd * 1.1, precision: 0.01 }),
    totalTokens: faker.number.int({ min: totalTokens * 0.9, max: totalTokens * 1.1 }),
    requestCount: totalRequests,
    avgCostPerRequest: faker.number.float({ min: avgCostPerRequest * 0.9, max: avgCostPerRequest * 1.1, precision: 0.00001 }),
    topConversations: overrides.topConversations ?? topConversations,
    costsByProvider,
    dailyBreakdown,
    ...overrides,
  };
}

/**
 * Create cost summary parameters
 * @param overrides - Optional overrides for default values
 * @returns CostSummaryParams object
 */
export function createCostSummaryParams(
  overrides: Partial<CostSummaryParams> = {}
): CostSummaryParams {
  const dateFrom = faker.date.recent({ days: 30 });
  const dateTo = new Date(dateFrom);
  dateTo.setDate(dateTo.getDate() + faker.number.int({ min: 1, max: 30 }));

  return {
    dateFrom: dateFrom.toISOString().split('T')[0],
    dateTo: dateTo.toISOString().split('T')[0],
    ...overrides,
  };
}

/**
 * Create an empty cost summary (for testing empty states)
 * @returns Empty CostSummary object
 */
export function createEmptyCostSummary(): CostSummary {
  return {
    totalCostUsd: 0,
    totalTokens: 0,
    requestCount: 0,
    avgCostPerRequest: 0,
    topConversations: [],
    costsByProvider: {},
    dailyBreakdown: [],
  };
}

/**
 * Helper to create multiple conversation costs
 * @param count - Number of conversation costs to create
 * @param overrides - Optional overrides applied to all
 * @returns Array of conversation costs
 */
export function createManyConversationCosts(
  count: number,
  overrides: Partial<ConversationCost> = {}
): ConversationCost[] {
  return Array.from({ length: count }, () => createConversationCost(overrides));
}

/**
 * Helper to create multiple daily breakdowns
 * @param count - Number of days
 * @param startDate - Starting date (defaults to today)
 * @returns Array of daily breakdowns
 */
export function createManyDailyBreakdowns(count: number, startDate?: Date) {
  const date = startDate ?? new Date();
  return Array.from({ length: count }, (_, i) => {
    const d = new Date(date);
    d.setDate(d.getDate() - i);
    return createDailyBreakdown(d);
  }).reverse();
}
