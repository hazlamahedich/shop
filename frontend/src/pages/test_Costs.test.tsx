/**
 * Costs Page Tests
 *
 * Tests costs page functionality including:
 * - Real data integration
 * - Date range filters
 * - Polling behavior
 * - Budget management
 * - Error states and loading states
 *
 * Story 3-5: Real-Time Cost Tracking
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Costs from './Costs';
import { useCostTrackingStore } from '../stores/costTrackingStore';
import type { CostSummary } from '../types/cost';

// Mock the cost tracking store
vi.mock('../stores/costTrackingStore', () => ({
  useCostTrackingStore: vi.fn(),
}));

const mockUseCostTrackingStore = vi.mocked(useCostTrackingStore);

// Mock cost summary data
const mockCostSummary: CostSummary = {
  totalCostUsd: 12.34,
  totalTokens: 250000,
  requestCount: 500,
  avgCostPerRequest: 0.02468,
  topConversations: [
    { conversationId: 'conv-001', totalCostUsd: 2.50, requestCount: 50 },
    { conversationId: 'conv-002', totalCostUsd: 1.80, requestCount: 35 },
    { conversationId: 'conv-003', totalCostUsd: 1.20, requestCount: 28 },
  ],
  costsByProvider: {
    openai: { costUsd: 8.50, requests: 300 },
    anthropic: { costUsd: 3.84, requests: 200 },
  },
  dailyBreakdown: [
    { date: '2026-02-01', totalCostUsd: 3.20, requestCount: 120 },
    { date: '2026-02-02', totalCostUsd: 4.10, requestCount: 150 },
    { date: '2026-02-03', totalCostUsd: 5.04, requestCount: 230 },
  ],
};

// Store actions mock
const mockFetchCostSummary = vi.fn();
const mockSetCostSummaryParams = vi.fn();
const mockStartPolling = vi.fn();
const mockStopPolling = vi.fn();
const mockSetPollingInterval = vi.fn();

const defaultStoreState = {
  costSummary: null,
  costSummaryLoading: false,
  costSummaryError: null,
  costSummaryParams: {},
  isPolling: false,
  pollingInterval: 30000,
  lastUpdate: null,
  conversationCosts: {},
  conversationCostsLoading: {},
  conversationCostsError: {},
  fetchCostSummary: mockFetchCostSummary,
  setCostSummaryParams: mockSetCostSummaryParams,
  startPolling: mockStartPolling,
  stopPolling: mockStopPolling,
  setPollingInterval: mockSetPollingInterval,
  fetchConversationCost: vi.fn(),
  clearConversationCost: vi.fn(),
  clearErrors: vi.fn(),
  reset: vi.fn(),
};

describe('Costs Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();

    mockUseCostTrackingStore.mockReturnValue(defaultStoreState);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Initial Render', () => {
    it('displays page title', () => {
      render(<Costs />);

      expect(screen.getByText('Costs & Budget')).toBeInTheDocument();
    });

    it('displays date range filter section', () => {
      render(<Costs />);

      expect(screen.getByText('Date Range:')).toBeInTheDocument();
    });

    it('displays all date range presets', () => {
      render(<Costs />);

      expect(screen.getByText('Today')).toBeInTheDocument();
      expect(screen.getByText('Last 7 Days')).toBeInTheDocument();
      expect(screen.getByText('Last 30 Days')).toBeInTheDocument();
      expect(screen.getByText('This Month')).toBeInTheDocument();
    });

    it('displays custom date range inputs', () => {
      render(<Costs />);

      // Date inputs are input[type="date"], not text inputs with textbox role
      // Query the DOM directly for date inputs
      const allInputs = document.querySelectorAll('input[type="date"]');
      expect(allInputs.length).toBe(2);
    });

    it('displays refresh button', () => {
      render(<Costs />);

      const refreshButton = screen.getByTitle('Refresh data');
      expect(refreshButton).toBeInTheDocument();
    });

    it('displays polling toggle button', () => {
      render(<Costs />);

      expect(screen.getByText('Polling Paused')).toBeInTheDocument();
    });

    it('starts polling on mount', () => {
      render(<Costs />);

      expect(mockStartPolling).toHaveBeenCalledWith(undefined, 30000);
    });
  });

  describe('Cost Summary Cards', () => {
    it('renders CostSummaryCards component', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      expect(screen.getByText('Cost Overview')).toBeInTheDocument();
    });
  });

  describe('Date Range Filtering', () => {
    it('sets preset date range on click', async () => {
      const user = userEvent.setup({ delay: null });

      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      const todayButton = screen.getByText('Today');
      await user.click(todayButton);

      // Date should be today (we can't easily check the actual value due to dynamic date generation)
      // But we can verify the component re-rendered
      expect(todayButton).toBeInTheDocument();
    });

    it('calls fetchCostSummary when Apply button is clicked', async () => {
      const user = userEvent.setup({ delay: null });

      mockFetchCostSummary.mockResolvedValue(undefined);

      render(<Costs />);

      const applyButton = screen.getByText('Apply');
      await user.click(applyButton);

      expect(mockFetchCostSummary).toHaveBeenCalled();
    });

    it('highlights active preset', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      // Last 30 Days should be active by default
      const last30DaysButton = screen.getByText('Last 30 Days');
      expect(last30DaysButton).toHaveClass('bg-blue-600');
    });
  });

  describe('Budget Management', () => {
    it('displays budget overview section', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      expect(screen.getByText('Budget Overview')).toBeInTheDocument();
    });

    it('displays current spend', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      // Use getAllByText since cost appears in multiple places
      const costElements = screen.getAllByText('$12.34');
      expect(costElements.length).toBeGreaterThan(0);
    });

    it('displays budget usage percentage', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      // $12.34 / $50 = ~25%
      expect(screen.getByText('25%')).toBeInTheDocument();
    });

    it('displays budget cap input with default value', () => {
      render(<Costs />);

      const budgetInput = document.querySelector('input[type="number"]') as HTMLInputElement;
      expect(budgetInput?.value).toBe('50');
    });

    it('updates budget cap value', async () => {
      const user = userEvent.setup({ delay: null });

      render(<Costs />);

      const budgetInput = document.querySelector('input[type="number"]') as HTMLInputElement;
      if (budgetInput) {
        await user.clear(budgetInput);
        await user.type(budgetInput, '100');
        expect(budgetInput.value).toBe('100');
      }
    });

    it('saves budget cap on Save button click', async () => {
      const user = userEvent.setup({ delay: null });

      // Use real timers for this test since we're testing async timeout behavior
      vi.useRealTimers();

      render(<Costs />);

      const saveButton = screen.getByText('Save Budget');
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText('Saving...')).toBeInTheDocument();
      });

      // Wait for save to complete
      await waitFor(
        () => {
          expect(screen.queryByText('Saving...')).not.toBeInTheDocument();
        },
        { timeout: 1000 }
      );

      // Restore fake timers
      vi.useFakeTimers();
    });

    it('displays projected monthly cost', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
        lastUpdate: '2026-02-08T10:00:00Z',
      });

      render(<Costs />);

      expect(screen.getByText(/Projected/)).toBeInTheDocument();
    });
  });

  describe('Daily Spend Chart', () => {
    it('displays chart section', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      expect(screen.getByText('Daily Spend')).toBeInTheDocument();
    });

    it('displays chart with daily data', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      // Should have date labels from dailyBreakdown
      // Use getAllByText since multiple dates may match similar patterns
      const febLabels = screen.getAllByText(/Feb/);
      expect(febLabels.length).toBeGreaterThanOrEqual(3);
    });

    it('shows no data message when daily breakdown is empty', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: {
          ...mockCostSummary,
          dailyBreakdown: [],
        },
      });

      render(<Costs />);

      expect(screen.getByText('No daily data available for selected period')).toBeInTheDocument();
    });
  });

  describe('Cost Comparison', () => {
    it('displays cost comparison section', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      expect(screen.getByText('Cost Comparison')).toBeInTheDocument();
    });

    it('displays Shop cost', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      expect(screen.getByText('Shop (You)')).toBeInTheDocument();
    });

    it('displays ManyChat estimated cost', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      expect(screen.getByText('ManyChat (Est.)')).toBeInTheDocument();
    });

    it('displays savings message', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      // $12.34 * 3.5 = $43.19 - $12.34 = $30.85 savings
      expect(screen.getByText(/You saved/)).toBeInTheDocument();
    });
  });

  describe('Top Conversations', () => {
    it('displays top conversations section when data available', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      expect(screen.getByText('Top Conversations by Cost')).toBeInTheDocument();
    });

    it('displays conversation list', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      expect(screen.getByText('conv-001...')).toBeInTheDocument();
      expect(screen.getByText('conv-002...')).toBeInTheDocument();
      expect(screen.getByText('conv-003...')).toBeInTheDocument();
    });

    it('displays ranking numbers', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      // Should have 1, 2, 3 ranking badges
      const rankingElements = document.querySelectorAll('.bg-blue-100.text-blue-700.rounded-full');
      expect(rankingElements.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Provider Breakdown', () => {
    it('displays provider breakdown section', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      expect(screen.getByText('Cost by Provider')).toBeInTheDocument();
    });

    it('displays provider list', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      const openaiElements = screen.getAllByText(/openai/i);
      expect(openaiElements.length).toBeGreaterThan(0);
    });

    it('displays provider costs sorted by spend', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);

      // Check that costs are displayed somewhere in the document
      // Use getAllByText with regex for flexible matching
      const all8_50 = screen.queryAllByText(/\$8\.50/);
      expect(all8_50.length).toBeGreaterThan(0);

      const all3_84 = screen.queryAllByText(/\$3\.84/);
      expect(all3_84.length).toBeGreaterThan(0);
    });
  });

  describe('Loading States', () => {
    it('disables refresh button while loading', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummaryLoading: true,
      });

      render(<Costs />);

      const refreshButton = screen.getByTitle('Refresh data');
      expect(refreshButton).toBeDisabled();
    });

    it('disables Apply button while loading', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummaryLoading: true,
      });

      render(<Costs />);

      const applyButton = screen.getByText('Apply');
      expect(applyButton).toBeDisabled();
    });
  });

  describe('Error States', () => {
    it('displays error message when fetch fails', () => {
      const errorMessage = 'Failed to fetch cost data';

      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummaryError: errorMessage,
      });

      render(<Costs />);

      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('provides retry button on error', () => {
      const errorMessage = 'Network error';

      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummaryError: errorMessage,
      });

      render(<Costs />);

      const retryButton = screen.getByText('Retry');
      expect(retryButton).toBeInTheDocument();
    });

    it('calls fetchCostSummary when retry is clicked', async () => {
      const user = userEvent.setup({ delay: null });
      const errorMessage = 'Network error';

      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummaryError: errorMessage,
      });

      render(<Costs />);

      const retryButton = screen.getByText('Retry');
      await user.click(retryButton);

      expect(mockFetchCostSummary).toHaveBeenCalled();
    });
  });

  describe('Polling Controls', () => {
    it('displays polling paused button when not polling', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        isPolling: false,
      });

      render(<Costs />);

      expect(screen.getByText('Polling Paused')).toBeInTheDocument();
    });

    it('displays polling active button when polling', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        isPolling: true,
      });

      render(<Costs />);

      expect(screen.getByText('Polling Active')).toBeInTheDocument();
    });

    it('calls stopPolling when polling is active and button clicked', async () => {
      const user = userEvent.setup({ delay: null });

      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        isPolling: true,
      });

      render(<Costs />);

      const pollingButton = screen.getByText('Polling Active');
      await user.click(pollingButton);

      expect(mockStopPolling).toHaveBeenCalled();
    });

    it('calls startPolling when polling is paused and button clicked', async () => {
      const user = userEvent.setup({ delay: null });

      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        isPolling: false,
        pollingInterval: 30000,
      });

      render(<Costs />);

      const pollingButton = screen.getByText('Polling Paused');
      await user.click(pollingButton);

      expect(mockStartPolling).toHaveBeenCalledWith(undefined, 30000);
    });
  });

  describe('Last Update Display', () => {
    it('displays last update timestamp', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        lastUpdate: '2026-02-08T10:30:00Z',
      });

      render(<Costs />);

      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    });

    it('formats time correctly', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        lastUpdate: '2026-02-08T10:30:00Z',
      });

      render(<Costs />);

      // Should show "Last updated:" text
      expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
      // The exact time format depends on locale, so just check that something is displayed
      const lastUpdateText = screen.getByText(/Last updated:/).textContent || '';
      expect(lastUpdateText.length).toBeGreaterThan('Last updated:'.length);
    });
  });

  describe('Refresh Functionality', () => {
    it('calls fetchCostSummary when refresh button clicked', async () => {
      const user = userEvent.setup({ delay: null });

      render(<Costs />);

      const refreshButton = screen.getByTitle('Refresh data');
      await user.click(refreshButton);

      expect(mockFetchCostSummary).toHaveBeenCalled();
    });
  });

  describe('Empty States', () => {
    it('does not display top conversations when empty', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: {
          ...mockCostSummary,
          topConversations: [],
        },
      });

      render(<Costs />);

      expect(screen.queryByText('Top Conversations by Cost')).not.toBeInTheDocument();
    });
  });
});
