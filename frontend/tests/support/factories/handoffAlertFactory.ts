/**
 * Handoff Alert Factory
 *
 * Factory functions for creating test data for Story 4-6 handoff notifications.
 * Uses faker for dynamic, collision-free data generation.
 *
 * @package frontend/tests/support/factories/handoffAlertFactory.ts
 */

import { faker } from '@faker-js/faker';

export type UrgencyLevel = 'high' | 'medium' | 'low';
export type HandoffReason = 'keyword' | 'low_confidence' | 'clarification_loop';

export interface HandoffAlert {
  id: string;
  merchantId: number;
  conversationId: number;
  urgencyLevel: UrgencyLevel;
  customerName: string;
  customerId: string;
  conversationPreview: string;
  waitTimeSeconds: number;
  isRead: boolean;
  createdAt: string;
  handoffReason: HandoffReason;
}

export interface CreateHandoffAlertOptions {
  id?: string;
  merchantId?: number;
  conversationId?: number;
  urgencyLevel?: UrgencyLevel;
  customerName?: string;
  customerId?: string;
  conversationPreview?: string;
  waitTimeSeconds?: number;
  isRead?: boolean;
  createdAt?: string;
  handoffReason?: HandoffReason;
}

export const URGENCY_TO_REASON_MAP: Record<UrgencyLevel, HandoffReason[]> = {
  high: ['low_confidence', 'clarification_loop', 'keyword'],
  medium: ['low_confidence', 'clarification_loop'],
  low: ['keyword'],
};

export const URGENCY_EMOJI: Record<UrgencyLevel, string> = {
  high: '🔴',
  medium: '🟡',
  low: '🟢',
};

export const URGENCY_LABELS: Record<UrgencyLevel, string> = {
  high: 'High Priority',
  medium: 'Medium Priority',
  low: 'Low Priority',
};

export function createHandoffAlert(overrides: CreateHandoffAlertOptions = {}): HandoffAlert {
  const urgencyLevel = overrides.urgencyLevel || randomUrgencyLevel();
  const handoffReason = overrides.handoffReason || randomReasonForUrgency(urgencyLevel);

  return {
    id: overrides.id ?? faker.string.uuid(),
    merchantId: overrides.merchantId ?? faker.number.int({ min: 1, max: 1000 }),
    conversationId: overrides.conversationId ?? faker.number.int({ min: 1, max: 10000 }),
    urgencyLevel,
    customerName: overrides.customerName ?? faker.person.fullName(),
    customerId: overrides.customerId ?? faker.string.alphanumeric(10),
    conversationPreview: overrides.conversationPreview ?? generateConversationPreview(),
    waitTimeSeconds: overrides.waitTimeSeconds ?? faker.number.int({ min: 0, max: 86400 }),
    isRead: overrides.isRead ?? false,
    createdAt: overrides.createdAt ?? faker.date.recent({ days: 7 }).toISOString(),
    handoffReason,
  };
}

export function createHighUrgencyAlert(overrides: CreateHandoffAlertOptions = {}): HandoffAlert {
  return createHandoffAlert({
    ...overrides,
    urgencyLevel: 'high',
    handoffReason: overrides.handoffReason ?? faker.helpers.arrayElement(['low_confidence', 'clarification_loop']),
  });
}

export function createMediumUrgencyAlert(overrides: CreateHandoffAlertOptions = {}): HandoffAlert {
  return createHandoffAlert({
    ...overrides,
    urgencyLevel: 'medium',
    handoffReason: overrides.handoffReason ?? faker.helpers.arrayElement(['low_confidence', 'clarification_loop']),
  });
}

export function createLowUrgencyAlert(overrides: CreateHandoffAlertOptions = {}): HandoffAlert {
  return createHandoffAlert({
    ...overrides,
    urgencyLevel: 'low',
    handoffReason: 'keyword',
  });
}

export function createReadAlert(overrides: CreateHandoffAlertOptions = {}): HandoffAlert {
  return createHandoffAlert({
    ...overrides,
    isRead: true,
  });
}

export function createUnreadAlert(overrides: CreateHandoffAlertOptions = {}): HandoffAlert {
  return createHandoffAlert({
    ...overrides,
    isRead: false,
  });
}

export function createHandoffAlertList(count: number, overrides: CreateHandoffAlertOptions = {}): HandoffAlert[] {
  return Array.from({ length: count }, () => createHandoffAlert(overrides));
}

export function createMixedUrgencyAlerts(countPerLevel: number = 2): HandoffAlert[] {
  return [
    ...createHandoffAlertList(countPerLevel, { urgencyLevel: 'high' }),
    ...createHandoffAlertList(countPerLevel, { urgencyLevel: 'medium' }),
    ...createHandoffAlertList(countPerLevel, { urgencyLevel: 'low' }),
  ];
}

export function createCheckoutBlockingAlert(overrides: CreateHandoffAlertOptions = {}): HandoffAlert {
  const checkoutPreview = generateCheckoutContextPreview();

  return createHandoffAlert({
    ...overrides,
    urgencyLevel: 'high',
    conversationPreview: checkoutPreview,
    handoffReason: overrides.handoffReason ?? 'low_confidence',
  });
}

function randomUrgencyLevel(): UrgencyLevel {
  return faker.helpers.arrayElement(['high', 'medium', 'low'] as const);
}

function randomReasonForUrgency(urgency: UrgencyLevel): HandoffReason {
  const reasons = URGENCY_TO_REASON_MAP[urgency];
  return faker.helpers.arrayElement(reasons);
}

function generateConversationPreview(): string {
  const messages = [
    "I'm having trouble with my order",
    'Can I speak to someone?',
    'This is frustrating',
    'I need help with my account',
    'The checkout is not working',
    'Where is my order?',
    'I want a refund',
    'Can you help me find a product?',
  ];

  return faker.helpers.arrayElement(messages);
}

function generateCheckoutContextPreview(): string {
  const checkoutMessages = [
    "I'm stuck at checkout, it says payment failed",
    'I tried to checkout but something went wrong',
    'My payment is not going through at checkout',
    "I can't complete my purchase, help!",
    'Checkout keeps giving me an error',
  ];

  return faker.helpers.arrayElement(checkoutMessages);
}

export function formatWaitTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    return `${minutes}m`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
  }
}

export function calculateWaitTime(createdAt: string): number {
  const created = new Date(createdAt);
  const now = new Date();
  return Math.floor((now.getTime() - created.getTime()) / 1000);
}
