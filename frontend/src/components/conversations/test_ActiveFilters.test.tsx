/**
 * ActiveFilters Component Tests
 *
 * Tests active filter chips display and removal
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ActiveFilters } from './ActiveFilters';

// Mock the conversation store
vi.mock('../../stores/conversationStore', () => ({
  useConversationStore: vi.fn(),
}));

import { useConversationStore } from '../../stores/conversationStore';

describe('ActiveFilters', () => {
  const mockRemoveFilter = vi.fn();
  const mockClearAllFilters = vi.fn();

  const mockFilters = {
    searchQuery: '',
    dateRange: { from: null, to: null },
    statusFilters: [] as string[],
    sentimentFilters: [] as string[],
    hasHandoffFilter: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useConversationStore as any).mockReturnValue({
      filters: mockFilters,
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });
  });

  it('returns null when no active filters', () => {
    const { container } = render(<ActiveFilters />);

    expect(container.firstChild).toBe(null);
  });

  it('renders search query chip', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, searchQuery: 'test search' },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    expect(screen.getByText(/Search: "test search"/)).toBeInTheDocument();
    expect(screen.getByText('🔍')).toBeInTheDocument();
  });

  it('renders date range chip with from date', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, dateRange: { from: '2026-02-01', to: null } },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    expect(screen.getByText(/Date: 2026-02-01 to \.\.\./)).toBeInTheDocument();
    expect(screen.getByText('📅')).toBeInTheDocument();
  });

  it('renders date range chip with to date', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, dateRange: { from: null, to: '2026-02-28' } },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    expect(screen.getByText(/Date: \.\.\. to 2026-02-28/)).toBeInTheDocument();
  });

  it('renders date range chip with both dates', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, dateRange: { from: '2026-02-01', to: '2026-02-28' } },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    expect(screen.getByText('Date: 2026-02-01 to 2026-02-28')).toBeInTheDocument();
  });

  it('renders status filter chips', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, statusFilters: ['active', 'closed'] },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Closed')).toBeInTheDocument();
  });

  it('renders sentiment filter chips with emojis', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, sentimentFilters: ['positive', 'negative'] },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    expect(screen.getByText('😊')).toBeInTheDocument();
    expect(screen.getByText(/Positive/)).toBeInTheDocument();
    expect(screen.getByText('😞')).toBeInTheDocument();
    expect(screen.getByText(/Negative/)).toBeInTheDocument();
  });

  it('renders "Has Handoff" chip', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, hasHandoffFilter: true },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    expect(screen.getByText('Has Handoff')).toBeInTheDocument();
    expect(screen.getByText('👥')).toBeInTheDocument();
  });

  it('renders "No Handoff" chip', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, hasHandoffFilter: false },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    expect(screen.getByText('No Handoff')).toBeInTheDocument();
  });

  it('calls removeFilter when search chip is removed', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, searchQuery: 'test' },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    const searchChip = screen.getByText(/Search:/).closest('button');
    await user.click(searchChip!);

    expect(mockRemoveFilter).toHaveBeenCalledWith('searchQuery', undefined);
  });

  it('calls removeFilter when status chip is removed', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, statusFilters: ['active'] },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    const activeChip = screen.getByText('Active').closest('button');
    await user.click(activeChip!);

    expect(mockRemoveFilter).toHaveBeenCalledWith('statusFilters', 'active');
  });

  it('calls removeFilter when sentiment chip is removed', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, sentimentFilters: ['neutral'] },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    const neutralChip = screen.getByText('Neutral').closest('button');
    await user.click(neutralChip!);

    expect(mockRemoveFilter).toHaveBeenCalledWith('sentimentFilters', 'neutral');
  });

  it('calls removeFilter when handoff chip is removed', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, hasHandoffFilter: true },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    const handoffChip = screen.getByText('Has Handoff').closest('button');
    await user.click(handoffChip!);

    expect(mockRemoveFilter).toHaveBeenCalledWith('hasHandoffFilter', undefined);
  });

  it('calls clearAllFilters when "Clear all" button is clicked', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      filters: {
        ...mockFilters,
        searchQuery: 'test',
        statusFilters: ['active'],
      },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    const clearAllButton = screen.getByRole('button', { name: /Clear all \(2\)/ });
    await user.click(clearAllButton);

    expect(mockClearAllFilters).toHaveBeenCalled();
  });

  it('displays correct filter count', () => {
    (useConversationStore as any).mockReturnValue({
      filters: {
        searchQuery: 'test',
        dateRange: { from: '2026-02-01', to: null },
        statusFilters: ['active', 'closed'],
        sentimentFilters: [],
        hasHandoffFilter: null,
      },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    // Search (1) + Date (1) + Status (2) = 4 total
    expect(screen.getByRole('button', { name: /Clear all \(4\)/ })).toBeInTheDocument();
  });

  it('renders all filter chips together', () => {
    (useConversationStore as any).mockReturnValue({
      filters: {
        searchQuery: 'shoes',
        dateRange: { from: '2026-02-01', to: '2026-02-28' },
        statusFilters: ['active'],
        sentimentFilters: ['positive'],
        hasHandoffFilter: true,
      },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    expect(screen.getByText(/Search: "shoes"/)).toBeInTheDocument();
    expect(screen.getByText(/Date: 2026-02-01 to 2026-02-28/)).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText(/Positive/)).toBeInTheDocument();
    expect(screen.getByText('Has Handoff')).toBeInTheDocument();
  });

  it('applies custom className when provided', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, searchQuery: 'test' },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    const { container } = render(<ActiveFilters className="custom-class" />);

    expect(container.firstChild).toHaveClass('custom-class');
  });

  it('has proper accessibility attributes', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, searchQuery: 'test' },
      removeFilter: mockRemoveFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<ActiveFilters />);

    const chips = screen.getAllByRole('button');
    expect(chips.length).toBeGreaterThan(0);

    chips.forEach(chip => {
      expect(chip).toHaveFocus();
    });
  });
});
