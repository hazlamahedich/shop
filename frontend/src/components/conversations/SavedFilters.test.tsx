/**
 * SavedFilters Component Tests
 *
 * Tests save, load, delete, and manage saved filter sets
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SavedFilters } from './SavedFilters';

// Mock the conversation store
vi.mock('../../stores/conversationStore', () => ({
  useConversationStore: vi.fn(),
}));

import { useConversationStore } from '../../stores/conversationStore';

describe('SavedFilters', () => {
  const mockSaveCurrentFilters = vi.fn();
  const mockDeleteSavedFilter = vi.fn();
  const mockApplySavedFilter = vi.fn();

  const mockFilters = {
    searchQuery: '',
    dateRange: { from: null, to: null },
    statusFilters: [] as string[],
    sentimentFilters: [] as string[],
    hasHandoffFilter: null,
  };

  const mockSavedFilters = [
    {
      id: 'filter-1',
      name: 'Active Issues',
      filters: { ...mockFilters, statusFilters: ['active'] },
      createdAt: '2026-02-07T10:00:00Z',
    },
    {
      id: 'filter-2',
      name: 'Positive Sentiment',
      filters: { ...mockFilters, sentimentFilters: ['positive'] },
      createdAt: '2026-02-07T11:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (useConversationStore as any).mockReturnValue({
      savedFilters: mockSavedFilters,
      filters: mockFilters,
      saveCurrentFilters: mockSaveCurrentFilters,
      deleteSavedFilter: mockDeleteSavedFilter,
      applySavedFilter: mockApplySavedFilter,
    });
  });

  it('renders saved filters button with count', () => {
    render(<SavedFilters />);

    expect(screen.getByRole('button', { name: /Saved Filters/ })).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('opens dropdown when button is clicked', async () => {
    const user = userEvent.setup();
    render(<SavedFilters />);

    const button = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(button);

    expect(screen.getByText('Saved Filters')).toBeInTheDocument();
    expect(screen.getByText('Active Issues')).toBeInTheDocument();
    expect(screen.getByText('Positive Sentiment')).toBeInTheDocument();
  });

  it('closes dropdown when clicking outside', async () => {
    const user = userEvent.setup();
    render(<SavedFilters />);

    const button = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(button);

    expect(screen.getByText('Saved Filters')).toBeInTheDocument();

    // Click outside (on document)
    await user.click(document.body);

    await waitFor(() => {
      expect(screen.queryByText('Saved Filters', { selector: 'h3' })).not.toBeInTheDocument();
    });
  });

  it('shows empty state when no saved filters', () => {
    (useConversationStore as any).mockReturnValue({
      savedFilters: [],
      filters: mockFilters,
      saveCurrentFilters: mockSaveCurrentFilters,
      deleteSavedFilter: mockDeleteSavedFilter,
      applySavedFilter: mockApplySavedFilter,
    });

    render(<SavedFilters />);

    const button = screen.getByRole('button', { name: /Saved Filters/ });
    // No count badge when empty
    expect(button).not.toContainHTML('2');
  });

  it('displays saved filters with descriptions when open', async () => {
    const user = userEvent.setup();
    render(<SavedFilters />);

    const button = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(button);

    expect(screen.getByText('Active Issues')).toBeInTheDocument();
    expect(screen.getByText(/1 status\(es\)/)).toBeInTheDocument();
  });

  it('shows save dialog when "Save Current Filters" is clicked', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      savedFilters: mockSavedFilters,
      filters: { ...mockFilters, searchQuery: 'test' },
      saveCurrentFilters: mockSaveCurrentFilters,
      deleteSavedFilter: mockDeleteSavedFilter,
      applySavedFilter: mockApplySavedFilter,
    });

    render(<SavedFilters />);

    const button = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(button);

    const saveButton = screen.getByRole('button', { name: 'Save Current Filters' });
    await user.click(saveButton);

    expect(screen.getByPlaceholderText('Filter name...')).toBeInTheDocument();
  });

  it('disables "Save Current Filters" when no active filters', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      savedFilters: mockSavedFilters,
      filters: mockFilters, // No active filters
      saveCurrentFilters: mockSaveCurrentFilters,
      deleteSavedFilter: mockDeleteSavedFilter,
      applySavedFilter: mockApplySavedFilter,
    });

    render(<SavedFilters />);

    const button = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(button);

    const saveButton = screen.getByRole('button', { name: 'Save Current Filters' });
    expect(saveButton).toBeDisabled();
  });

  it('saves filter with name when Save button is clicked', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      savedFilters: mockSavedFilters,
      filters: { ...mockFilters, searchQuery: 'test' },
      saveCurrentFilters: mockSaveCurrentFilters,
      deleteSavedFilter: mockDeleteSavedFilter,
      applySavedFilter: mockApplySavedFilter,
    });

    render(<SavedFilters />);

    const triggerButton = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(triggerButton);

    const saveButton = screen.getByRole('button', { name: 'Save Current Filters' });
    await user.click(saveButton);

    const input = screen.getByPlaceholderText('Filter name...');
    await user.type(input, 'My Filter');

    const confirmButton = screen.getByRole('button', { name: 'Save' });
    await user.click(confirmButton);

    expect(mockSaveCurrentFilters).toHaveBeenCalledWith('My Filter');
  });

  it('closes save dialog when Cancel is clicked', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      savedFilters: mockSavedFilters,
      filters: { ...mockFilters, searchQuery: 'test' },
      saveCurrentFilters: mockSaveCurrentFilters,
      deleteSavedFilter: mockDeleteSavedFilter,
      applySavedFilter: mockApplySavedFilter,
    });

    render(<SavedFilters />);

    const triggerButton = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(triggerButton);

    const saveButton = screen.getByRole('button', { name: 'Save Current Filters' });
    await user.click(saveButton);

    const cancelButton = screen.getByRole('button', { name: 'Cancel' });
    await user.click(cancelButton);

    expect(screen.queryByPlaceholderText('Filter name...')).not.toBeInTheDocument();
  });

  it('applies saved filter when filter is clicked', async () => {
    const user = userEvent.setup();
    render(<SavedFilters />);

    const triggerButton = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(triggerButton);

    const filterButton = screen.getByRole('button', { name: 'Active Issues' });
    await user.click(filterButton);

    expect(mockApplySavedFilter).toHaveBeenCalledWith('filter-1');
  });

  it('deletes saved filter when delete button is clicked', async () => {
    const user = userEvent.setup();
    render(<SavedFilters />);

    const triggerButton = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(triggerButton);

    // Find the delete button for the first filter
    const deleteButtons = screen.getAllByLabelText('Delete filter');
    await user.click(deleteButtons[0]);

    expect(mockDeleteSavedFilter).toHaveBeenCalledWith('filter-1');
  });

  it('shows correct filter description for each filter', async () => {
    const user = userEvent.setup();
    render(<SavedFilters />);

    const triggerButton = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(triggerButton);

    expect(screen.getByText(/1 status\(es\)/)).toBeInTheDocument();
    expect(screen.getByText(/1 sentiment\(s\)/)).toBeInTheDocument();
  });

  it('saves filter on Enter key press', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      savedFilters: mockSavedFilters,
      filters: { ...mockFilters, searchQuery: 'test' },
      saveCurrentFilters: mockSaveCurrentFilters,
      deleteSavedFilter: mockDeleteSavedFilter,
      applySavedFilter: mockApplySavedFilter,
    });

    render(<SavedFilters />);

    const triggerButton = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(triggerButton);

    const saveButton = screen.getByRole('button', { name: 'Save Current Filters' });
    await user.click(saveButton);

    const input = screen.getByPlaceholderText('Filter name...');
    await user.type(input, 'My Filter{Enter}');

    expect(mockSaveCurrentFilters).toHaveBeenCalledWith('My Filter');
  });

  it('closes save dialog on Escape key press', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      savedFilters: mockSavedFilters,
      filters: { ...mockFilters, searchQuery: 'test' },
      saveCurrentFilters: mockSaveCurrentFilters,
      deleteSavedFilter: mockDeleteSavedFilter,
      applySavedFilter: mockApplySavedFilter,
    });

    render(<SavedFilters />);

    const triggerButton = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(triggerButton);

    const saveButton = screen.getByRole('button', { name: 'Save Current Filters' });
    await user.click(saveButton);

    const input = screen.getByPlaceholderText('Filter name...');
    await user.type(input, '{Escape}');

    expect(screen.queryByPlaceholderText('Filter name...')).not.toBeInTheDocument();
  });

  it('disables Save button when filter name is empty', async () => {
    const user = userEvent.setup();
    (useConversationStore as any).mockReturnValue({
      savedFilters: mockSavedFilters,
      filters: { ...mockFilters, searchQuery: 'test' },
      saveCurrentFilters: mockSaveCurrentFilters,
      deleteSavedFilter: mockDeleteSavedFilter,
      applySavedFilter: mockApplySavedFilter,
    });

    render(<SavedFilters />);

    const triggerButton = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(triggerButton);

    const saveButton = screen.getByRole('button', { name: 'Save Current Filters' });
    await user.click(saveButton);

    const confirmButton = screen.getByRole('button', { name: 'Save' });
    expect(confirmButton).toBeDisabled();
  });

  it('shows date in description for date range filters', async () => {
    const user = userEvent.setup();
    const filtersWithDate = {
      ...mockSavedFilters,
      0: {
        ...mockSavedFilters[0],
        filters: { ...mockFilters, dateRange: { from: '2026-02-01', to: null } },
      },
    };

    (useConversationStore as any).mockReturnValue({
      savedFilters: Object.values(filtersWithDate),
      filters: mockFilters,
      saveCurrentFilters: mockSaveCurrentFilters,
      deleteSavedFilter: mockDeleteSavedFilter,
      applySavedFilter: mockApplySavedFilter,
    });

    render(<SavedFilters />);

    const triggerButton = screen.getByRole('button', { name: /Saved Filters/ });
    await user.click(triggerButton);

    expect(screen.getByText('Date range')).toBeInTheDocument();
  });

  it('applies custom className when provided', () => {
    const { container } = render(<SavedFilters className="custom-class" />);

    expect(container.firstChild).toHaveClass('custom-class');
  });
});
