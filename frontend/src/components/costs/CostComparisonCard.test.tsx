/**
 * Tests for CostComparisonCard component
 *
 * Story 3.9: Cost Comparison Display
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CostComparisonCard } from './CostComparisonCard';

const mockUseCostTrackingStore = vi.fn();
vi.mock('../../stores/costTrackingStore', () => ({
  useCostTrackingStore: () => mockUseCostTrackingStore(),
}));

describe('CostComparisonCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing when costComparison is not available', () => {
    mockUseCostTrackingStore.mockReturnValue({
      costSummary: null,
    });

    const { container } = render(<CostComparisonCard />);
    expect(container.firstChild).toBeNull();
  });

  it('displays merchant spend and ManyChat estimate', () => {
    mockUseCostTrackingStore.mockReturnValue({
      costSummary: {
        costComparison: {
          manyChatEstimate: 25.5,
          savingsAmount: 20.5,
          savingsPercentage: 80.4,
          merchantSpend: 5.0,
          methodology: 'Test methodology',
        },
      },
    });

    render(<CostComparisonCard />);

    expect(screen.getByText(/You spent/)).toBeInTheDocument();
    expect(screen.getByText(/~\$26-38/)).toBeInTheDocument();
  });

  it('shows savings message when savings are positive', () => {
    mockUseCostTrackingStore.mockReturnValue({
      costSummary: {
        costComparison: {
          manyChatEstimate: 25.0,
          savingsAmount: 20.0,
          savingsPercentage: 80,
          merchantSpend: 5.0,
          methodology: 'Test methodology',
        },
      },
    });

    render(<CostComparisonCard />);

    expect(screen.getByText(/You saved \$20.00 \(80%\)/)).toBeInTheDocument();
  });

  it('shows optimization suggestion when savings are negative', () => {
    mockUseCostTrackingStore.mockReturnValue({
      costSummary: {
        costComparison: {
          manyChatEstimate: 15.0,
          savingsAmount: -5.0,
          savingsPercentage: -33,
          merchantSpend: 20.0,
          methodology: 'Test methodology',
        },
      },
    });

    render(<CostComparisonCard />);

    expect(
      screen.getByText(/Consider reviewing your LLM provider configuration/)
    ).toBeInTheDocument();
  });

  it('shows methodology tooltip when info button is clicked', () => {
    mockUseCostTrackingStore.mockReturnValue({
      costSummary: {
        costComparison: {
          manyChatEstimate: 25.0,
          savingsAmount: 20.0,
          savingsPercentage: 80,
          merchantSpend: 5.0,
          methodology:
            'ManyChat pricing: $15-99/month. Shop pricing: Pay per token.',
        },
      },
    });

    render(<CostComparisonCard />);

    const infoButton = screen.getByLabelText(/View comparison methodology/);
    fireEvent.click(infoButton);

    expect(
      screen.getByText(/ManyChat pricing: \$15-99\/month/)
    ).toBeInTheDocument();
  });

  it('toggles tooltip visibility on click', () => {
    mockUseCostTrackingStore.mockReturnValue({
      costSummary: {
        costComparison: {
          manyChatEstimate: 25.0,
          savingsAmount: 20.0,
          savingsPercentage: 80,
          merchantSpend: 5.0,
          methodology: 'Test methodology text',
        },
      },
    });

    render(<CostComparisonCard />);

    const infoButton = screen.getByLabelText(/View comparison methodology/);
    
    // Click to show tooltip
    fireEvent.click(infoButton);
    expect(screen.getByText('Test methodology text')).toBeInTheDocument();
    
    // Click again to hide tooltip
    fireEvent.click(infoButton);
    expect(screen.queryByText('Test methodology text')).not.toBeInTheDocument();
  });

  it('displays progress bars for cost comparison', () => {
    mockUseCostTrackingStore.mockReturnValue({
      costSummary: {
        costComparison: {
          manyChatEstimate: 25.0,
          savingsAmount: 20.0,
          savingsPercentage: 80,
          merchantSpend: 5.0,
          methodology: 'Test',
        },
      },
    });

    render(<CostComparisonCard />);

    expect(screen.getByText('Shop (You)')).toBeInTheDocument();
    expect(screen.getByText('ManyChat (Est.)')).toBeInTheDocument();
  });

  it('handles zero spend correctly', () => {
    mockUseCostTrackingStore.mockReturnValue({
      costSummary: {
        costComparison: {
          manyChatEstimate: 15.0,
          savingsAmount: 15.0,
          savingsPercentage: 100,
          merchantSpend: 0,
          methodology: 'Test methodology',
        },
      },
    });

    render(<CostComparisonCard />);

    expect(screen.getByText(/You spent/)).toBeInTheDocument();
    expect(screen.getByText(/You saved \$15.00 \(100%\)/)).toBeInTheDocument();
  });
});
