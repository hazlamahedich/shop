/**
 * SearchBar Component Tests
 *
 * Tests search input with debounce, clear button, and accessibility
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SearchBar } from './SearchBar';

// Mock the conversation store
vi.mock('../../stores/conversationStore', () => ({
  useConversationStore: vi.fn(),
}));

import { useConversationStore } from '../../stores/conversationStore';

describe('SearchBar', () => {
  const mockSetSearchQuery = vi.fn();
  const mockFilters = { searchQuery: '' };

  beforeEach(() => {
    vi.clearAllMocks();
    (useConversationStore as any).mockReturnValue({
      filters: mockFilters,
      setSearchQuery: mockSetSearchQuery,
    });
  });

  it('renders search input with placeholder', () => {
    render(<SearchBar />);

    const input = screen.getByLabelText('Search conversations');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('placeholder', 'Search by customer ID or message content...');
  });

  it('renders custom placeholder when provided', () => {
    render(<SearchBar placeholder="Custom placeholder" />);

    const input = screen.getByLabelText('Search conversations');
    expect(input).toHaveAttribute('placeholder', 'Custom placeholder');
  });

  it('updates local value on input change', async () => {
    const user = userEvent.setup();
    render(<SearchBar />);

    const input = screen.getByLabelText('Search conversations');
    await user.type(input, 'test search');

    expect(input).toHaveValue('test search');
  });

  it('debounces search query updates', async () => {
    const user = userEvent.setup();
    render(<SearchBar debounceMs={300} />);

    const input = screen.getByLabelText('Search conversations');
    await user.type(input, 'test');

    // Should not call setSearchQuery immediately
    expect(mockSetSearchQuery).not.toHaveBeenCalled();

    // Wait for debounce to complete
    await waitFor(
      () => {
        expect(mockSetSearchQuery).toHaveBeenCalledWith('test');
      },
      { timeout: 500 }
    );
  });

  it('shows clear button when input has value', () => {
    (useConversationStore as any).mockReturnValue({
      filters: { searchQuery: 'existing value' },
      setSearchQuery: mockSetSearchQuery,
    });

    render(<SearchBar />);

    const clearButton = screen.getByLabelText('Clear search');
    expect(clearButton).toBeVisible();
  });

  it('hides clear button when input is empty', () => {
    render(<SearchBar />);

    const clearButton = screen.queryByLabelText('Clear search');
    expect(clearButton).not.toBeInTheDocument();
  });

  it('clears input when clear button is clicked', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      filters: { searchQuery: 'test value' },
      setSearchQuery: mockSetSearchQuery,
    });

    render(<SearchBar />);

    const input = screen.getByLabelText('Search conversations') as HTMLInputElement;
    const clearButton = screen.getByLabelText('Clear search');

    await user.click(clearButton);

    expect(input.value).toBe('');
  });

  it('syncs local value with store when store value changes', async () => {
    (useConversationStore as any).mockReturnValue({
      filters: { searchQuery: 'external value' },
      setSearchQuery: mockSetSearchQuery,
    });

    render(<SearchBar />);

    const input = screen.getByLabelText('Search conversations');
    expect(input).toHaveValue('external value');
  });

  it('has proper ARIA labels for accessibility', () => {
    render(<SearchBar />);

    const input = screen.getByLabelText('Search conversations');
    expect(input).toHaveAttribute('aria-label', 'Search conversations');

    // Search icon should have aria-hidden
    const searchIcon = document.querySelector('[aria-hidden="true"]');
    expect(searchIcon).toBeInTheDocument();
  });

  it('respects custom debounce duration', async () => {
    const user = userEvent.setup();
    render(<SearchBar debounceMs={100} />);

    const input = screen.getByLabelText('Search conversations');
    await user.type(input, 'quick');

    // Should be faster than default 300ms
    await waitFor(
      () => {
        expect(mockSetSearchQuery).toHaveBeenCalledWith('quick');
      },
      { timeout: 200 }
    );
  });

  it('does not call setSearchQuery if value has not changed', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      filters: { searchQuery: 'test' },
      setSearchQuery: mockSetSearchQuery,
    });

    render(<SearchBar debounceMs={50} />);

    const input = screen.getByLabelText('Search conversations');
    // Type the same value that's already in the store
    input.value = 'test';
    await user.type(input, '{Enter}');

    // Wait for debounce timeout + margin
    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockSetSearchQuery).not.toHaveBeenCalled();
  });

  it('handles rapid input changes correctly', async () => {
    const user = userEvent.setup();
    render(<SearchBar debounceMs={300} />);

    const input = screen.getByLabelText('Search conversations');

    // Type multiple characters quickly
    await user.type(input, 'abc');

    // Should only call setSearchQuery once with the final value
    await waitFor(
      () => {
        expect(mockSetSearchQuery).toHaveBeenCalledTimes(1);
        expect(mockSetSearchQuery).toHaveBeenLastCalledWith('abc');
      },
      { timeout: 500 }
    );
  });
});
