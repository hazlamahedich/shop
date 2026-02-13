/**
 * Tests for BudgetWarningBanner Component
 *
 * Story 3-8: Budget Alert Notifications
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { BudgetWarningBanner } from './BudgetWarningBanner';

vi.mock('../../stores/costTrackingStore', () => ({
  useCostTrackingStore: vi.fn((selector) => {
    const state = {
      costSummary: { totalCostUsd: 85, dailyBreakdown: [] },
      merchantSettings: { budgetCap: 100, config: {} },
    };
    return selector(state);
  }),
}));

describe('BudgetWarningBanner', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    cleanup();
  });

  it('does not render when budget percentage is below 80%', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        costSummary: { totalCostUsd: 50, dailyBreakdown: [] },
        merchantSettings: { budgetCap: 100, config: {} },
      };
      return selector(state);
    });

    const { container } = render(<BudgetWarningBanner />);
    expect(container.firstChild).toBeNull();
  });

  it('renders with yellow styling at 80-94%', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        costSummary: { totalCostUsd: 85, dailyBreakdown: [] },
        merchantSettings: { budgetCap: 100, config: {} },
      };
      return selector(state);
    });

    render(<BudgetWarningBanner />);
    const banner = screen.getByTestId('budget-warning-banner');
    expect(banner).toHaveClass('bg-yellow-100');
    expect(screen.getByText(/Budget Alert: 85%/)).toBeInTheDocument();
  });

  it('renders with red styling at 95%+', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        costSummary: { totalCostUsd: 97, dailyBreakdown: [] },
        merchantSettings: { budgetCap: 100, config: {} },
      };
      return selector(state);
    });

    render(<BudgetWarningBanner />);
    const banner = screen.getByTestId('budget-warning-banner');
    expect(banner).toHaveClass('bg-red-100');
    expect(screen.getByText(/Budget Alert: 97%/)).toBeInTheDocument();
  });

  it('calls onIncreaseBudget when button clicked', () => {
    const onIncreaseBudget = vi.fn();

    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        costSummary: { totalCostUsd: 85, dailyBreakdown: [] },
        merchantSettings: { budgetCap: 100, config: {} },
      };
      return selector(state);
    });

    render(<BudgetWarningBanner onIncreaseBudget={onIncreaseBudget} />);
    fireEvent.click(screen.getByText('Increase Budget'));
    expect(onIncreaseBudget).toHaveBeenCalled();
  });

  it('calls onViewDetails when View Details clicked', () => {
    const onViewDetails = vi.fn();

    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        costSummary: { totalCostUsd: 85, dailyBreakdown: [] },
        merchantSettings: { budgetCap: 100, config: {} },
      };
      return selector(state);
    });

    render(<BudgetWarningBanner onViewDetails={onViewDetails} />);
    fireEvent.click(screen.getByText('View Details'));
    expect(onViewDetails).toHaveBeenCalled();
  });

  it('dismiss hides banner for 24 hours at yellow level', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        costSummary: { totalCostUsd: 85, dailyBreakdown: [] },
        merchantSettings: { budgetCap: 100, config: {} },
      };
      return selector(state);
    });

    const { container, rerender } = render(<BudgetWarningBanner />);
    fireEvent.click(screen.getByLabelText(/Dismiss/i));

    rerender(<BudgetWarningBanner />);
    expect(container.firstChild).toBeNull();
  });

  it('no dismiss button at critical (95%+) level', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        costSummary: { totalCostUsd: 97, dailyBreakdown: [] },
        merchantSettings: { budgetCap: 100, config: {} },
      };
      return selector(state);
    });

    render(<BudgetWarningBanner />);
    expect(screen.queryByLabelText(/Dismiss/i)).not.toBeInTheDocument();
  });

  it('shows projection when dailyBreakdown available', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        costSummary: {
          totalCostUsd: 85,
          dailyBreakdown: [{ date: '2026-02-13', totalCostUsd: 5 }],
        },
        merchantSettings: { budgetCap: 100, config: {} },
      };
      return selector(state);
    });

    render(<BudgetWarningBanner />);
    expect(screen.getByText(/At current rate/)).toBeInTheDocument();
  });

  it('does not render when budgetCap is null (no limit)', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        costSummary: { totalCostUsd: 500, dailyBreakdown: [] },
        merchantSettings: { budgetCap: null, config: {} },
      };
      return selector(state);
    });

    const { container } = render(<BudgetWarningBanner />);
    expect(container.firstChild).toBeNull();
  });
});

import { useCostTrackingStore } from '../../stores/costTrackingStore';
