/**
 * ContextSidebar Component Tests - Story 4-8
 *
 * Tests for the context sidebar component including:
 * - Customer info display
 * - Handoff context (urgency, wait time, trigger reason)
 * - Bot internal state (cart, constraints)
 * - Formatting functions edge cases
 *
 * Acceptance Criteria Coverage:
 * - AC3: Bot Internal State
 * - AC4: User Info Display
 * - AC5: Handoff Context
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ContextSidebar from './ContextSidebar';
import type { ConversationContext, HandoffContext, CustomerInfo } from '../../types/conversation';

const createMockCustomer = (overrides: Partial<CustomerInfo> = {}): CustomerInfo => ({
  maskedId: '1234****',
  orderCount: 0,
  ...overrides,
});

const createMockHandoff = (overrides: Partial<HandoffContext> = {}): HandoffContext => ({
  triggerReason: 'keyword',
  triggeredAt: new Date(Date.now() - 300000).toISOString(),
  urgencyLevel: 'medium',
  waitTimeSeconds: 300,
  ...overrides,
});

const createMockContext = (overrides: Partial<ConversationContext> = {}): ConversationContext => ({
  cartState: null,
  extractedConstraints: null,
  ...overrides,
});

describe('ContextSidebar Component', () => {
  describe('Customer Info Section (AC4)', () => {
    it('displays masked customer ID', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer({ maskedId: '5678****' })}
          handoff={createMockHandoff()}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('5678****')).toBeInTheDocument();
    });

    it('displays order count', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer({ orderCount: 5 })}
          handoff={createMockHandoff()}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('displays zero order count for MVP', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer({ orderCount: 0 })}
          handoff={createMockHandoff()}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('has correct test id for customer info section', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext()}
        />
      );

      expect(screen.getByTestId('customer-info-section')).toBeInTheDocument();
    });
  });

  describe('Handoff Context Section (AC5)', () => {
    it('displays urgency badge for high urgency', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ urgencyLevel: 'high' })}
          context={createMockContext()}
        />
      );

      const badge = screen.getByTestId('urgency-badge');
      expect(badge).toHaveTextContent('High');
      expect(badge).toHaveTextContent('\u{1F534}');
    });

    it('displays urgency badge for medium urgency', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ urgencyLevel: 'medium' })}
          context={createMockContext()}
        />
      );

      const badge = screen.getByTestId('urgency-badge');
      expect(badge).toHaveTextContent('Medium');
      expect(badge).toHaveTextContent('\u{1F7E1}');
    });

    it('displays urgency badge for low urgency', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ urgencyLevel: 'low' })}
          context={createMockContext()}
        />
      );

      const badge = screen.getByTestId('urgency-badge');
      expect(badge).toHaveTextContent('Low');
      expect(badge).toHaveTextContent('\u{1F7E2}');
    });

    it('displays formatted wait time in seconds', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ waitTimeSeconds: 45 })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('45s')).toBeInTheDocument();
    });

    it('displays formatted wait time in minutes', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ waitTimeSeconds: 300 })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('5 min')).toBeInTheDocument();
    });

    it('displays formatted wait time in hours', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ waitTimeSeconds: 7200 })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('2h')).toBeInTheDocument();
    });

    it('displays formatted wait time with hours and minutes', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ waitTimeSeconds: 5400 })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('1h 30m')).toBeInTheDocument();
    });

    it('displays trigger reason for keyword', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ triggerReason: 'keyword' })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('Customer requested human help')).toBeInTheDocument();
    });

    it('displays trigger reason for low_confidence', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ triggerReason: 'low_confidence' })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('Bot needed assistance')).toBeInTheDocument();
    });

    it('displays trigger reason for clarification_loop', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ triggerReason: 'clarification_loop' })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('Multiple clarification attempts')).toBeInTheDocument();
    });

    it('displays unknown trigger reason as-is', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ triggerReason: 'unknown_reason' })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('unknown_reason')).toBeInTheDocument();
    });

    it('has correct test id for handoff context section', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext()}
        />
      );

      expect(screen.getByTestId('handoff-context-section')).toBeInTheDocument();
    });
  });

  describe('Bot Internal State Section (AC3)', () => {
    it('displays empty cart message when no items', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext({ cartState: null })}
        />
      );

      expect(screen.getByText('No items in cart')).toBeInTheDocument();
    });

    it('displays empty cart message when items array is empty', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext({ cartState: { items: [] } })}
        />
      );

      expect(screen.getByText('No items in cart')).toBeInTheDocument();
    });

    it('displays cart items with quantities', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext({
            cartState: {
              items: [
                { productId: 'prod-1', name: 'Nike Air Max', quantity: 1 },
                { productId: 'prod-2', name: 'Adidas Runner', quantity: 2 },
              ],
            },
          })}
        />
      );

      expect(screen.getByText('Nike Air Max')).toBeInTheDocument();
      expect(screen.getByText('x1')).toBeInTheDocument();
      expect(screen.getByText('Adidas Runner')).toBeInTheDocument();
      expect(screen.getByText('x2')).toBeInTheDocument();
    });

    it('displays no constraints message when empty', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext({ extractedConstraints: null })}
        />
      );

      expect(screen.getByText('No constraints detected')).toBeInTheDocument();
    });

    it('displays no constraints message when all fields null', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext({
            extractedConstraints: { budget: null, size: null, category: null },
          })}
        />
      );

      expect(screen.getByText('No constraints detected')).toBeInTheDocument();
    });

    it('displays budget constraint', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext({
            extractedConstraints: { budget: '$100-150' },
          })}
        />
      );

      expect(screen.getByText('Budget')).toBeInTheDocument();
      expect(screen.getByText('$100-150')).toBeInTheDocument();
    });

    it('displays size constraint', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext({
            extractedConstraints: { size: '10' },
          })}
        />
      );

      expect(screen.getByText('Size')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
    });

    it('displays category constraint', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext({
            extractedConstraints: { category: 'running shoes' },
          })}
        />
      );

      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('running shoes')).toBeInTheDocument();
    });

    it('displays all constraints together', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext({
            extractedConstraints: { budget: '$100', size: '10', category: 'running' },
          })}
        />
      );

      expect(screen.getByText('$100')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('running')).toBeInTheDocument();
    });

    it('has correct test id for bot state section', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext()}
        />
      );

      expect(screen.getByTestId('bot-state-section')).toBeInTheDocument();
    });
  });

  describe('formatWaitTime Edge Cases', () => {
    it('handles zero seconds', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ waitTimeSeconds: 0 })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('0s')).toBeInTheDocument();
    });

    it('handles exactly 60 seconds (1 minute boundary)', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ waitTimeSeconds: 60 })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('1 min')).toBeInTheDocument();
    });

    it('handles exactly 3600 seconds (1 hour boundary)', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ waitTimeSeconds: 3600 })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('1h')).toBeInTheDocument();
    });

    it('handles large wait times', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ waitTimeSeconds: 86400 })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('24h')).toBeInTheDocument();
    });

    it('handles 59 seconds (just under a minute)', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ waitTimeSeconds: 59 })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('59s')).toBeInTheDocument();
    });

    it('handles 3599 seconds (just under an hour)', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff({ waitTimeSeconds: 3599 })}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('59 min')).toBeInTheDocument();
    });
  });

  describe('Component Structure', () => {
    it('has correct test id for sidebar container', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext()}
        />
      );

      expect(screen.getByTestId('context-sidebar')).toBeInTheDocument();
    });

    it('renders all three sections', () => {
      render(
        <ContextSidebar
          customer={createMockCustomer()}
          handoff={createMockHandoff()}
          context={createMockContext()}
        />
      );

      expect(screen.getByText('Customer Info')).toBeInTheDocument();
      expect(screen.getByText('Handoff Context')).toBeInTheDocument();
      expect(screen.getByText('Bot State')).toBeInTheDocument();
    });
  });
});
