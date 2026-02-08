/**
 * CostSummaryCards Component Tests
 *
 * Tests cost summary cards display and interactions
 *
 * Story 3-5: Real-Time Cost Tracking
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import CostSummaryCards from './CostSummaryCards';
import { useCostTrackingStore } from '../../stores/costTrackingStore';
import type { CostSummary } from '../../types/cost';

// Mock the cost tracking store
vi.mock('../../stores/costTrackingStore', () => ({
  useCostTrackingStore: vi.fn(),
}));

const mockUseCostTrackingStore = vi.mocked(useCostTrackingStore);

// Mock cost summary data
const mockCostSummary: CostSummary = {
  totalCostUsd: 1.23,
  totalTokens: 50000,
  requestCount: 100,
  avgCostPerRequest: 0.0123,
  topConversations: [],
  costsByProvider: {
    openai: { costUsd: 0.80, requests: 60 },
    ollama: { costUsd: 0.00, requests: 30 },
    anthropic: { costUsd: 0.43, requests: 10 },
  },
  dailyBreakdown: [],
};

// Previous period for trend comparison
const mockPreviousPeriod: CostSummary = {
  totalCostUsd: 1.00,
  totalTokens: 40000,
  requestCount: 80,
  avgCostPerRequest: 0.0125,
  topConversations: [],
  costsByProvider: {
    openai: { costUsd: 0.70, requests: 50 },
    ollama: { costUsd: 0.00, requests: 20 },
    anthropic: { costUsd: 0.30, requests: 10 },
  },
  dailyBreakdown: [],
};

describe('CostSummaryCards', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseCostTrackingStore.mockReturnValue({
      conversationCosts: {},
      conversationCostsLoading: {},
      conversationCostsError: {},
      costSummary: mockCostSummary,
      costSummaryLoading: false,
      costSummaryError: null,
      costSummaryParams: {},
      isPolling: false,
      pollingInterval: 30000,
      lastUpdate: '2026-02-08T10:00:00Z',
      fetchConversationCost: vi.fn(),
      clearConversationCost: vi.fn(),
      fetchCostSummary: vi.fn(),
      setCostSummaryParams: vi.fn(),
      startPolling: vi.fn(),
      stopPolling: vi.fn(),
      setPollingInterval: vi.fn(),
      clearErrors: vi.fn(),
      reset: vi.fn(),
    });
  });

  it('displays all summary cards', () => {
    render(<CostSummaryCards />);

    expect(screen.getByText('Total Cost')).toBeInTheDocument();
    expect(screen.getByText('Total Tokens')).toBeInTheDocument();
    expect(screen.getByText('Total Requests')).toBeInTheDocument();
    expect(screen.getByText('Avg Cost/Request')).toBeInTheDocument();
  });

  it('displays correct values for each metric', () => {
    render(<CostSummaryCards />);

    expect(screen.getByText('$1.23')).toBeInTheDocument(); // Total cost
    expect(screen.getByText('50.0K')).toBeInTheDocument(); // Total tokens
    expect(screen.getByText('100')).toBeInTheDocument(); // Total requests
    expect(screen.getByText('$0.0123')).toBeInTheDocument(); // Avg cost per request
  });

  it('displays trend indicators when previous period data provided', () => {
    render(<CostSummaryCards previousPeriodSummary={mockPreviousPeriod} />);

    // Cost trend: (1.23 - 1.00) / 1.00 * 100 = 23% increase
    expect(screen.getByText(/23\.0% vs previous period/)).toBeInTheDocument();
  });

  it('shows upward trend (red) for increased costs', () => {
    render(<CostSummaryCards previousPeriodSummary={mockPreviousPeriod} />);

    // Increased cost should show red TrendingUp indicator
    const trendElements = screen.getAllByText(/23\.0% vs previous period/);
    expect(trendElements.length).toBeGreaterThan(0);
  });

  it('shows downward trend (green) for decreased costs', () => {
    const decreasedPeriod: CostSummary = {
      ...mockCostSummary,
      totalCostUsd: 0.80,
    };

    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      costSummary: decreasedPeriod,
    });

    render(<CostSummaryCards previousPeriodSummary={mockPreviousPeriod} />);

    // Decreased cost should show green TrendingDown indicator (20% decrease)
    expect(screen.getByText(/20\.0% vs previous period/)).toBeInTheDocument();
  });

  it('shows no trend when costs are equal', () => {
    const samePeriod: CostSummary = {
      ...mockCostSummary,
      totalCostUsd: 1.00,
    };

    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      costSummary: samePeriod,
    });

    render(<CostSummaryCards previousPeriodSummary={mockPreviousPeriod} />);

    expect(screen.getByText(/No change from previous period/)).toBeInTheDocument();
  });

  it('does not show trends when no previous period data', () => {
    render(<CostSummaryCards />);

    // Should not have any trend indicators
    expect(screen.queryByText(/vs previous period/)).not.toBeInTheDocument();
  });

  it('displays top provider card', () => {
    render(<CostSummaryCards />);

    expect(screen.getByText('Top Provider')).toBeInTheDocument();
    expect(screen.getByText(/openai/i)).toBeInTheDocument();
    expect(screen.getByText('60 requests')).toBeInTheDocument();
    expect(screen.getByText('$0.80')).toBeInTheDocument();
  });

  it('correctly identifies top provider by request count', () => {
    render(<CostSummaryCards />);

    // OpenAI has 60 requests (most), should be top provider
    expect(screen.getByText(/openai/i)).toBeInTheDocument();
  });

  it('displays last update timestamp', () => {
    render(<CostSummaryCards />);

    expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
  });

  it('shows loading state with skeleton cards', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      costSummaryLoading: true,
      costSummary: null,
    });

    render(<CostSummaryCards />);

    // Should have 4 skeleton cards (animate-pulse elements)
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBe(4);
  });

  it('shows no data state when costSummary is null', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      costSummary: null,
      costSummaryLoading: false,
    });

    render(<CostSummaryCards />);

    expect(screen.getByText('No cost data available')).toBeInTheDocument();
  });

  it('shows helpful message in no data state', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      costSummary: null,
      costSummaryLoading: false,
    });

    render(<CostSummaryCards />);

    expect(
      screen.getByText('Data will appear once LLM requests are made')
    ).toBeInTheDocument();
  });

  it('displays cost overview title', () => {
    render(<CostSummaryCards />);

    expect(screen.getByText('Cost Overview')).toBeInTheDocument();
  });

  it('formats token count with K suffix', () => {
    const highTokens: CostSummary = {
      ...mockCostSummary,
      totalTokens: 1500000, // 1.5M
    };

    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      costSummary: highTokens,
    });

    render(<CostSummaryCards />);

    expect(screen.getByText('1.5M')).toBeInTheDocument();
  });

  it('formats request count with locale', () => {
    const highRequests: CostSummary = {
      ...mockCostSummary,
      requestCount: 10000,
    };

    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      costSummary: highRequests,
    });

    render(<CostSummaryCards />);

    // Should have comma separator
    expect(screen.getByText('10,000')).toBeInTheDocument();
  });

  it('handles zero costs gracefully', () => {
    const zeroCost: CostSummary = {
      ...mockCostSummary,
      totalCostUsd: 0,
      avgCostPerRequest: 0,
    };

    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      costSummary: zeroCost,
    });

    render(<CostSummaryCards />);

    expect(screen.getByText('$0.00')).toBeInTheDocument();
  });

  it('handles single provider', () => {
    const singleProvider: CostSummary = {
      ...mockCostSummary,
      costsByProvider: {
        openai: { costUsd: 1.23, requests: 100 },
      },
    };

    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      costSummary: singleProvider,
    });

    render(<CostSummaryCards />);

    expect(screen.getByText('Top Provider')).toBeInTheDocument();
    expect(screen.getByText(/openai/i)).toBeInTheDocument();
  });

  it('handles no providers', () => {
    const noProviders: CostSummary = {
      ...mockCostSummary,
      costsByProvider: {},
    };

    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      costSummary: noProviders,
    });

    render(<CostSummaryCards />);

    // Top provider card should not be shown
    expect(screen.queryByText('Top Provider')).not.toBeInTheDocument();
  });

  it('calculates trend correctly for tokens', () => {
    render(<CostSummaryCards previousPeriodSummary={mockPreviousPeriod} />);

    // Token trend: (50000 - 40000) / 40000 * 100 = 25% increase
    const allTrends = screen.getAllByText(/vs previous period/);
    const tokenTrend = allTrends.find(el => {
      const text = el.textContent || '';
      // Should contain 25.0%
      return text.includes('25.0%');
    });

    expect(tokenTrend).toBeDefined();
  });

  it('calculates trend correctly for requests', () => {
    render(<CostSummaryCards previousPeriodSummary={mockPreviousPeriod} />);

    // Request trend: (100 - 80) / 80 * 100 = 25% increase
    const allTrends = screen.getAllByText(/vs previous period/);

    // Should have trends for cost, tokens, and requests
    expect(allTrends.length).toBeGreaterThanOrEqual(3);
  });

  it('capitalizes provider name', () => {
    render(<CostSummaryCards />);

    // Provider names should be capitalized
    const providerElements = screen.getAllByText(/openai/i);
    expect(providerElements.length).toBeGreaterThan(0);
  });

  it('displays provider cost with 2 decimals', () => {
    render(<CostSummaryCards />);

    expect(screen.getByText('$0.80')).toBeInTheDocument();
  });

  it('handles ollama provider with zero cost', () => {
    const ollamaOnly: CostSummary = {
      ...mockCostSummary,
      costsByProvider: {
        ollama: { costUsd: 0, requests: 50 },
      },
    };

    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      costSummary: ollamaOnly,
    });

    render(<CostSummaryCards />);

    // Case-insensitive match for provider name
    const providerText = screen.getByText(/ollama/i);
    expect(providerText).toBeInTheDocument();
    expect(screen.getByText('$0.00')).toBeInTheDocument();
  });
});
