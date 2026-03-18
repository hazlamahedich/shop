/**
 * FilterPanel Component Tests
 *
 * Tests filter panel with date range, status, sentiment, and handoff filters
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FilterPanel } from './FilterPanel';

// Mock the conversation store
vi.mock('../../stores/conversationStore', () => ({
  useConversationStore: vi.fn(),
}));

import { useConversationStore } from '../../stores/conversationStore';

describe('FilterPanel', () => {
  const mockSetDateRange = vi.fn();
  const mockSetStatusFilters = vi.fn();
  const mockSetSentimentFilters = vi.fn();
  const mockSetHasHandoffFilter = vi.fn();
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
      setDateRange: mockSetDateRange,
      setStatusFilters: mockSetStatusFilters,
      setSentimentFilters: mockSetSentimentFilters,
      setHasHandoffFilter: mockSetHasHandoffFilter,
      clearAllFilters: mockClearAllFilters,
    });
  });

  it('renders filter panel with toggle button', () => {
    render(<FilterPanel />);

    const toggleButton = screen.getByRole('button', { name: /filters/i });
    expect(toggleButton).toBeInTheDocument();
    expect(screen.getByText('Filters')).toBeInTheDocument();
  });

  it('shows "Active" badge when filters are active', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, searchQuery: 'test' },
      setDateRange: mockSetDateRange,
      setStatusFilters: mockSetStatusFilters,
      setSentimentFilters: mockSetSentimentFilters,
      setHasHandoffFilter: mockSetHasHandoffFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<FilterPanel />);

    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('toggles panel content when clicked', async () => {
    const user = userEvent.setup();
    render(<FilterPanel isOpen={false} onToggle={vi.fn()} />);

    const toggleButton = screen.getByRole('button', { name: /filters/i });
    const dateInput = screen.queryByLabelText('From');

    // Initially closed
    expect(dateInput).not.toBeInTheDocument();

    // Click to open - need to re-render with isOpen=true
    const { rerender } = render(<FilterPanel isOpen={false} onToggle={vi.fn()} />);
    rerender(<FilterPanel isOpen={true} onToggle={vi.fn()} />);

    expect(screen.getByLabelText('From')).toBeInTheDocument();
  });

  it('renders date range inputs when open', () => {
    render(<FilterPanel isOpen={true} />);

    expect(screen.getByLabelText('From')).toBeInTheDocument();
    expect(screen.getByLabelText('To')).toBeInTheDocument();
  });

  it('calls setDateRange when date from changes', async () => {
    const user = userEvent.setup();
    render(<FilterPanel isOpen={true} />);

    const dateFromInput = screen.getByLabelText('From');
    await user.type(dateFromInput, '2026-02-01');

    expect(mockSetDateRange).toHaveBeenCalledWith('2026-02-01', null);
  });

  it('calls setDateRange when date to changes', async () => {
    const user = userEvent.setup();
    render(<FilterPanel isOpen={true} />);

    const dateToInput = screen.getByLabelText('To');
    await user.type(dateToInput, '2026-02-28');

    expect(mockSetDateRange).toHaveBeenCalledWith(null, '2026-02-28');
  });

  it('renders status filter buttons', () => {
    render(<FilterPanel isOpen={true} />);

    expect(screen.getByRole('button', { name: 'Active' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Handoff' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Closed' })).toBeInTheDocument();
  });

  it('toggles status filter when clicked', async () => {
    const user = userEvent.setup();
    render(<FilterPanel isOpen={true} />);

    const activeButton = screen.getByRole('button', { name: 'Active' });
    await user.click(activeButton);

    expect(mockSetStatusFilters).toHaveBeenCalledWith(['active']);
  });

  it('removes status filter when clicked again', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, statusFilters: ['active'] },
      setDateRange: mockSetDateRange,
      setStatusFilters: mockSetStatusFilters,
      setSentimentFilters: mockSetSentimentFilters,
      setHasHandoffFilter: mockSetHasHandoffFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<FilterPanel isOpen={true} />);

    const activeButton = screen.getByRole('button', { name: 'Active' });
    await user.click(activeButton);

    expect(mockSetStatusFilters).toHaveBeenCalledWith([]);
  });

  it('renders sentiment filter buttons with emojis', () => {
    render(<FilterPanel isOpen={true} />);

    expect(screen.getByText(/😊.*Positive/)).toBeInTheDocument();
    expect(screen.getByText(/😐.*Neutral/)).toBeInTheDocument();
    expect(screen.getByText(/😞.*Negative/)).toBeInTheDocument();
  });

  it('toggles sentiment filter when clicked', async () => {
    const user = userEvent.setup();
    render(<FilterPanel isOpen={true} />);

    const positiveButton = screen.getByRole('button', { name: /Positive/ });
    await user.click(positiveButton);

    expect(mockSetSentimentFilters).toHaveBeenCalledWith(['positive']);
  });

  it('renders handoff status radio buttons', () => {
    render(<FilterPanel isOpen={true} />);

    expect(screen.getByLabelText('Has handoff')).toBeInTheDocument();
    expect(screen.getByLabelText('No handoff')).toBeInTheDocument();
    expect(screen.getByLabelText('Any')).toBeInTheDocument();
  });

  it('selects "Any" radio by default', () => {
    render(<FilterPanel isOpen={true} />);

    const anyRadio = screen.getByLabelText('Any') as HTMLInputElement;
    expect(anyRadio.checked).toBe(true);
  });

  it('calls setHasHandoffFilter when "Has handoff" is selected', async () => {
    const user = userEvent.setup();
    render(<FilterPanel isOpen={true} />);

    const hasHandoffRadio = screen.getByLabelText('Has handoff');
    await user.click(hasHandoffRadio);

    expect(mockSetHasHandoffFilter).toHaveBeenCalledWith(true);
  });

  it('calls setHasHandoffFilter when "No handoff" is selected', async () => {
    const user = userEvent.setup();
    render(<FilterPanel isOpen={true} />);

    const noHandoffRadio = screen.getByLabelText('No handoff');
    await user.click(noHandoffRadio);

    expect(mockSetHasHandoffFilter).toHaveBeenCalledWith(false);
  });

  it('shows "Clear All Filters" button when filters are active', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, searchQuery: 'test' },
      setDateRange: mockSetDateRange,
      setStatusFilters: mockSetStatusFilters,
      setSentimentFilters: mockSetSentimentFilters,
      setHasHandoffFilter: mockSetHasHandoffFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<FilterPanel isOpen={true} />);

    expect(screen.getByRole('button', { name: 'Clear All Filters' })).toBeInTheDocument();
  });

  it('calls clearAllFilters and resets local state when "Clear All" is clicked', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, searchQuery: 'test' },
      setDateRange: mockSetDateRange,
      setStatusFilters: mockSetStatusFilters,
      setSentimentFilters: mockSetSentimentFilters,
      setHasHandoffFilter: mockSetHasHandoffFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<FilterPanel isOpen={true} />);

    const clearButton = screen.getByRole('button', { name: 'Clear All Filters' });
    await user.click(clearButton);

    expect(mockClearAllFilters).toHaveBeenCalled();
  });

  it('highlights selected status filters', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, statusFilters: ['active', 'closed'] },
      setDateRange: mockSetDateRange,
      setStatusFilters: mockSetStatusFilters,
      setSentimentFilters: mockSetSentimentFilters,
      setHasHandoffFilter: mockSetHasHandoffFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<FilterPanel isOpen={true} />);

    const activeButton = screen.getByRole('button', { name: 'Active' });
    const closedButton = screen.getByRole('button', { name: 'Closed' });
    const handoffButton = screen.getByRole('button', { name: 'Handoff' });

    expect(activeButton.className).toContain('bg-blue-100');
    expect(closedButton.className).toContain('bg-blue-100');
    expect(handoffButton.className).toContain('bg-gray-100');
  });

  it('highlights selected sentiment filters', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { ...mockFilters, sentimentFilters: ['positive'] },
      setDateRange: mockSetDateRange,
      setStatusFilters: mockSetStatusFilters,
      setSentimentFilters: mockSetSentimentFilters,
      setHasHandoffFilter: mockSetHasHandoffFilter,
      clearAllFilters: mockClearAllFilters,
    });

    render(<FilterPanel isOpen={true} />);

    const positiveButton = screen.getByRole('button', { name: /Positive/ });
    expect(positiveButton.className).toContain('bg-purple-100');
  });

  it('has proper ARIA attributes for accessibility', () => {
    render(<FilterPanel isOpen={true} />);

    const toggleButton = screen.getByRole('button', { name: /filters/i });
    expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
  });

  it('displays chevron rotation based on open state', () => {
    const { rerender } = render(<FilterPanel isOpen={false} />);
    const chevron = document.querySelector('svg[class*="transition-transform"]');
    expect(chevron).not.toHaveClass('rotate-180');

    rerender(<FilterPanel isOpen={true} />);
    const rotatedChevron = document.querySelector('svg.rotate-180');
    expect(rotatedChevron).toBeInTheDocument();
  });
});
