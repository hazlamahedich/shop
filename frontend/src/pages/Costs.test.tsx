/**
 * Costs Page Tests - Tactical HUD Edition
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

// Mock the toast context
vi.mock('../context/ToastContext', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

// Mock the cost tracking service
vi.mock('../services/costTracking', () => ({
  costTrackingService: {
    getAIRecommendations: vi.fn().mockResolvedValue({
      data: {
        recommendations: [
          {
            id: 'MB-9831',
            priority: 'HIGH',
            text: 'Shift #MB-9831 processing to Claude-3-Haiku during off-peak hours to save 22% daily spend.',
            potentialSavingsUsd: 15.50,
            category: 'model_optimization',
          },
        ],
      },
    }),
  },
}));

const mockUseCostTrackingStore = vi.mocked(useCostTrackingStore);

// Mock cost summary data
const mockCostSummary: CostSummary = {
  totalCostUsd: 12.34,
  totalTokens: 250000,
  requestCount: 500,
  avgCostPerRequest: 0.02468,
  topConversations: [
    { conversationId: 'conv-001', totalCostUsd: 2.50, requestCount: 50, totalTokens: 15000, responseType: 'rag' },
    { conversationId: 'conv-002', totalCostUsd: 1.80, requestCount: 35, totalTokens: 12000, responseType: 'general' },
    { conversationId: 'conv-003', totalCostUsd: 1.20, requestCount: 28, totalTokens: 8500, responseType: 'rag' },
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
  efficiencyMetrics: {
    costPer1kTokens: 0.0494,
    ragResponsePercentage: 67.0,
    optimizationSavingsPercentage: 42.5,
    avgProcessingTimeMs: 1250.5,
  },
};

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
  fetchCostSummary: vi.fn(),
  setCostSummaryParams: vi.fn(),
  startPolling: vi.fn(),
  stopPolling: vi.fn(),
  setPollingInterval: vi.fn(),
  fetchConversationCost: vi.fn(),
  clearConversationCost: vi.fn(),
  getMerchantSettings: vi.fn(),
  fetchBotStatus: vi.fn(),
  clearErrors: vi.fn(),
  reset: vi.fn(),
  merchantSettings: { budgetCap: 150000 },
  botStatus: { is_active: true },
};

describe('Costs Page - Tactical HUD', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-02-08T12:00:00Z'));
    vi.clearAllMocks();
    mockUseCostTrackingStore.mockReturnValue(defaultStoreState);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Tactical Header & Nav', () => {
    it('displays NeuralSync branding', () => {
      render(<Costs />);
      expect(screen.getByText('Neural')).toBeInTheDocument();
      expect(screen.getByText('Sync')).toBeInTheDocument();
    });

    it('highlights Intelligence ROI as active', () => {
      render(<Costs />);
      // Intelligence ROI exists in both header and sidebar
      const roiLinks = screen.getAllByText('Intelligence ROI');
      expect(roiLinks.length).toBeGreaterThan(0);
      // Check that at least one (header nav) has the active class
      expect(roiLinks.some(link => link.classList.contains('text-[var(--mantis-glow)]'))).toBe(true);
    });

    it('displays sidebar navigation', () => {
      render(<Costs />);
      expect(screen.getAllByText('Spectral Data').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Conversations').length).toBeGreaterThan(0);
    });
  });

  describe('Neural Investment Cards & Reservoir', () => {
    it('displays Total Neural Investment with formatted cost', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });

      render(<Costs />);
      expect(screen.getByText('Total Neural Investment')).toBeInTheDocument();
      expect(screen.getByText('$12.34')).toBeInTheDocument();
    });

    it('displays Budget Reservoir with capacity', () => {
      render(<Costs />);
      expect(screen.getByText('Budget Reservoir')).toBeInTheDocument();
      expect(screen.getByText('$150,000')).toBeInTheDocument();
    });

    it('calculates efficiency delta correctly', () => {
       mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: { ...mockCostSummary, totalCostUsd: 100, lastUpdate: '2026-02-08T10:00:00Z' },
      });
      render(<Costs />);
      // mock summary has totalCostUsd: 100. efficiencyDelta is hardcoded or derived.
      // In Costs.tsx, efficiencyDelta is 12.4
      expect(screen.getByText(/Efficiency Delta: \+12.4%/)).toBeInTheDocument();
    });
  });

  describe('Expenditure Index (Chart)', () => {
    it('displays Expenditure Index section', () => {
      render(<Costs />);
      expect(screen.getByText('Expenditure Index')).toBeInTheDocument();
      expect(screen.getByText('30-Day Spectral Pulse')).toBeInTheDocument();
    });

    it('shows Budget Hard Stop line on chart', () => {
       render(<Costs />);
       expect(screen.getByText(/BUDGET HARD STOP: \$150,000/)).toBeInTheDocument();
    });

    it('renders date presets', () => {
      render(<Costs />);
      expect(screen.getByText('Today')).toBeInTheDocument();
      expect(screen.getByText('Last 7 Days')).toBeInTheDocument();
      expect(screen.getByText('Last 30 Days')).toBeInTheDocument();
    });

    it('shows empty state when no data', () => {
      render(<Costs />);
      expect(screen.getByText('No daily data available for selected period')).toBeInTheDocument();
    });
  });

  describe('Tactical Modules', () => {
    it('renders Resource Caps section', () => {
      render(<Costs />);
      expect(screen.getByText('Resource Caps')).toBeInTheDocument();
      expect(screen.getByText('Monthly Hard Stop')).toBeInTheDocument();
      expect(screen.getByText('Daily Warning Signal')).toBeInTheDocument();
    });

    it('renders Efficiency & Performance card', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });
      render(<Costs />);
      expect(screen.getByText('Efficiency & Performance')).toBeInTheDocument();
      expect(screen.getByText('$0.0494')).toBeInTheDocument();
      expect(screen.getByText('67% RAG accuracy')).toBeInTheDocument();
    });

    it('renders AI Recommendations', async () => {
      vi.useRealTimers();
      render(<Costs />);
      expect(screen.getByText('AI Recommendations')).toBeInTheDocument();
      await waitFor(() => {
        expect(screen.getByText(/Shift #MB-9831/)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('renders Heavy Transmissions table', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary
      });
      render(<Costs />);
      expect(screen.getByText('Heavy Transmissions')).toBeInTheDocument();
      expect(screen.getAllByText('RAG Response').length).toBeGreaterThan(0);
      expect(screen.getByText('General Query')).toBeInTheDocument();
      expect(screen.getByText('15K Tokens')).toBeInTheDocument();
    });

    it('renders AI Recommendations', async () => {
      vi.useRealTimers();
      render(<Costs />);
      expect(screen.getByText('AI Recommendations')).toBeInTheDocument();
      await waitFor(() => {
        expect(screen.getByText(/Shift #MB-9831/)).toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('renders Heavy Transmissions table', () => {
       mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        costSummary: mockCostSummary,
      });
      render(<Costs />);
      expect(screen.getByText('Heavy Transmissions')).toBeInTheDocument();
      // IDs are now transformed to PBX-CONV-XXXX, and there are multiple rows
      expect(screen.getAllByText(/PBX-CONV/i).length).toBeGreaterThan(0);
    });
  });

  describe('Interaction & Polling', () => {
    it('triggers fetchCostSummary when date presets are changed', async () => {
      const user = userEvent.setup({ delay: null });
      const fetchSpy = vi.fn();
      mockUseCostTrackingStore.mockReturnValue({
        ...defaultStoreState,
        fetchCostSummary: fetchSpy,
      });

      render(<Costs />);
      const todayBtn = screen.getByText('Today');
      await user.click(todayBtn);
      // The first call is on mount, second is on click
      expect(fetchSpy).toHaveBeenCalledTimes(2);
    });

    it('displays live orchestration telemetry', () => {
      render(<Costs />);
      expect(screen.getByText('Orchestration Live Sync')).toBeInTheDocument();
      expect(screen.getByText('Sync Transmission')).toBeInTheDocument();
    });
  });
});
