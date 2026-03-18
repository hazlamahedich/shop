/**
 * ConversationCostDetail Component Tests
 *
 * Tests conversation cost detail display and interactions
 *
 * Story 3-5: Real-Time Cost Tracking
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ConversationCostDetail from './ConversationCostDetail';
import { useCostTrackingStore } from '../../stores/costTrackingStore';
import type { ConversationCost, CostRecord } from '../../types/cost';

// Mock the cost tracking store
vi.mock('../../stores/costTrackingStore', () => ({
  useCostTrackingStore: vi.fn(),
}));

const mockUseCostTrackingStore = vi.mocked(useCostTrackingStore);

// Mock cost records
const mockCostRecords: CostRecord[] = [
  {
    id: 1,
    requestTimestamp: '2026-02-08T10:00:00Z',
    provider: 'openai',
    model: 'gpt-4o-mini',
    promptTokens: 500,
    completionTokens: 300,
    totalTokens: 800,
    inputCostUsd: 0.00015,
    outputCostUsd: 0.00009,
    totalCostUsd: 0.00024,
    processingTimeMs: 1250,
  },
  {
    id: 2,
    requestTimestamp: '2026-02-08T10:05:00Z',
    provider: 'openai',
    model: 'gpt-4o-mini',
    promptTokens: 750,
    completionTokens: 450,
    totalTokens: 1200,
    inputCostUsd: 0.000225,
    outputCostUsd: 0.000135,
    totalCostUsd: 0.00036,
    processingTimeMs: 1800,
  },
  {
    id: 3,
    requestTimestamp: '2026-02-08T10:10:00Z',
    provider: 'ollama',
    model: 'llama3',
    promptTokens: 1000,
    completionTokens: 500,
    totalTokens: 1500,
    inputCostUsd: 0,
    outputCostUsd: 0,
    totalCostUsd: 0,
    processingTimeMs: 3200,
  },
];

// Mock conversation cost data
const mockCostData: ConversationCost = {
  conversationId: 'conv-123',
  totalCostUsd: 0.0456,
  totalTokens: 5000,
  requestCount: 3,
  avgCostPerRequest: 0.0152,
  provider: 'openai',
  model: 'gpt-4o-mini',
  requests: mockCostRecords,
};

// High cost data for testing color coding
const mockHighCostData: ConversationCost = {
  ...mockCostData,
  totalCostUsd: 0.15,
  avgCostPerRequest: 0.05,
};

describe('ConversationCostDetail', () => {
  const mockFetchConversationCost = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchConversationCost.mockResolvedValue(undefined);

    mockUseCostTrackingStore.mockReturnValue({
      conversationCosts: {},
      conversationCostsLoading: {},
      conversationCostsError: {},
      costSummary: null,
      costSummaryLoading: false,
      costSummaryError: null,
      costSummaryParams: {},
      isPolling: false,
      pollingInterval: 30000,
      lastUpdate: null,
      fetchConversationCost: mockFetchConversationCost,
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

  it('shows loading state initially', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCostsLoading: { 'conv-123': true },
      conversationCosts: {},
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    expect(screen.getByText('Loading cost details...')).toBeInTheDocument();
    // Check for the loading spinner icon
    expect(document.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('shows error state when fetch fails', () => {
    const errorMessage = 'Failed to fetch cost data';
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCostsError: { 'conv-123': errorMessage },
      conversationCosts: {},
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    expect(screen.getByText('Failed to load cost details')).toBeInTheDocument();
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });

  it('calls fetchConversationCost when retry button is clicked', async () => {
    const user = userEvent.setup();
    const errorMessage = 'Network error';
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCostsError: { 'conv-123': errorMessage },
      conversationCosts: {},
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    const retryButton = screen.getByRole('button', { name: 'Retry' });
    await user.click(retryButton);

    expect(mockFetchConversationCost).toHaveBeenCalledWith('conv-123');
  });

  it('shows no data state when no cost data exists', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: {},
      conversationCostsLoading: { 'conv-123': false },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    expect(
      screen.getByText('No cost data available for this conversation')
    ).toBeInTheDocument();
  });

  it('displays summary statistics correctly', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': mockCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    // Check summary values
    expect(screen.getByText('$0.0456')).toBeInTheDocument();
    expect(screen.getByText('5.0K')).toBeInTheDocument(); // Total tokens
    expect(screen.getByText('3')).toBeInTheDocument(); // Request count
    expect(screen.getByText('$0.0152')).toBeInTheDocument(); // Avg cost per request
  });

  it('displays provider and model information', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': mockCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    // Provider appears in both the header badge and request rows
    const openaiElements = screen.getAllByText('openai');
    expect(openaiElements.length).toBeGreaterThan(0);

    // Model also appears multiple times
    const modelElements = screen.getAllByText('gpt-4o-mini');
    expect(modelElements.length).toBeGreaterThan(0);
  });

  it('displays request table with correct number of rows', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': mockCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    // Check table header
    expect(screen.getByText('Request Details (3)')).toBeInTheDocument();

    // Check request rows (numbered 1-3)
    expect(screen.getByText('#1')).toBeInTheDocument();
    expect(screen.getByText('#2')).toBeInTheDocument();
    expect(screen.getByText('#3')).toBeInTheDocument();
  });

  it('displays request data correctly in table rows', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': mockCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    // Provider and model appear in request rows
    const openaiElements = screen.getAllByText('openai');
    expect(openaiElements.length).toBeGreaterThan(0);

    // Check that token counts appear in the component
    // Note: 500 is contained in 5000, so we use getAllByText
    const tokenCounts = screen.getAllByText(/500|300|800/);
    expect(tokenCounts.length).toBeGreaterThan(0);
  });

  it('displays costs with correct precision', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': mockCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    // Input/output costs shown with 6 decimals
    expect(screen.getByText('$0.000150')).toBeInTheDocument();
    expect(screen.getByText('$0.000090')).toBeInTheDocument();

    // Total cost shown with 4 decimals
    expect(screen.getByText('$0.0002')).toBeInTheDocument();
  });

  it('displays processing time correctly', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': mockCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    // First request: 1250ms -> should show in seconds
    expect(screen.getByText('1.25s')).toBeInTheDocument();

    // Third request: 3200ms -> should show in seconds
    expect(screen.getByText('3.20s')).toBeInTheDocument();
  });

  it('shows N/A for processing time when not provided', () => {
    const recordWithoutTime: CostRecord = {
      ...mockCostRecords[0],
      processingTimeMs: undefined,
    };

    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: {
        'conv-123': {
          ...mockCostData,
          requests: [recordWithoutTime],
        },
      },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('shows green color for low cost (≤$0.01)', () => {
    const lowCostData: ConversationCost = {
      ...mockCostData,
      totalCostUsd: 0.005,
      avgCostPerRequest: 0.0017,
    };

    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': lowCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    const costElement = screen.getByText('$0.0050');
    expect(costElement).toHaveClass('text-green-600');
  });

  it('shows yellow color for medium cost (>$0.01 and ≤$0.10)', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': mockCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    const costElement = screen.getByText('$0.0456');
    expect(costElement).toHaveClass('text-yellow-700');
  });

  it('shows red color for high cost (>$0.10)', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': mockHighCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    const costElement = screen.getByText('$0.1500');
    expect(costElement).toHaveClass('text-red-700');
  });

  it('shows empty state when requests array is empty', () => {
    const emptyRequestsData: ConversationCost = {
      ...mockCostData,
      requests: [],
      requestCount: 0,
    };

    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': emptyRequestsData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    expect(
      screen.getByText('No individual request records available')
    ).toBeInTheDocument();
  });

  it('displays conversation ID in header', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': mockCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    expect(screen.getByText(/conv-123/)).toBeInTheDocument();
  });

  it('displays table column headers', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': mockCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    // Check for table headers - "Total Cost" appears in summary and table
    const totalCostHeaders = screen.getAllByText('Total Cost');
    expect(totalCostHeaders.length).toBeGreaterThan(0);

    expect(screen.getByText('#')).toBeInTheDocument();
    expect(screen.getByText('Time')).toBeInTheDocument();
    expect(screen.getByText('Provider / Model')).toBeInTheDocument();
    expect(screen.getByText('Prompt')).toBeInTheDocument();
    expect(screen.getByText('Completion')).toBeInTheDocument();
    expect(screen.getByText('Total')).toBeInTheDocument();
    expect(screen.getByText('Input Cost')).toBeInTheDocument();
    expect(screen.getByText('Output Cost')).toBeInTheDocument();
    expect(screen.getByText('Processing Time')).toBeInTheDocument();
  });

  it('displays multiple providers in table', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': mockCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    // Check that both providers appear somewhere in the component
    const allText = screen.getAllByText(/openai|ollama/);
    const hasOpenai = allText.some(el => el.textContent === 'openai');
    const hasOllama = allText.some(el => el.textContent === 'ollama');

    expect(hasOpenai).toBe(true);
    expect(hasOllama).toBe(true);
  });

  it('handles zero cost records (ollama)', () => {
    mockUseCostTrackingStore.mockReturnValue({
      ...mockUseCostTrackingStore(),
      conversationCosts: { 'conv-123': mockCostData },
    });

    render(<ConversationCostDetail conversationId="conv-123" />);

    // Third request has $0 cost (ollama)
    expect(screen.getByText('$0.0000')).toBeInTheDocument();
  });
});
