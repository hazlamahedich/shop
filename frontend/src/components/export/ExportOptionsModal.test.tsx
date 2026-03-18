/**
 * Component tests for ExportOptionsModal
 * P0 - Modal rendering, filter display, export actions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { ExportOptionsModal } from '@/components/export';

// Mock the export Zustand store
let mockExportState = {
  status: 'idle' as 'idle' | 'preparing' | 'exporting' | 'completed' | 'error',
  progress: 0,
  error: null as string | null,
  options: {} as any,
  metadata: null as any,
  isOptionsModalOpen: false,
};

const mockExportFunctions = {
  openOptionsModal: vi.fn(() => {
    mockExportState.isOptionsModalOpen = true;
  }),
  closeOptionsModal: vi.fn(() => {
    mockExportState.isOptionsModalOpen = false;
  }),
  setExportOptions: vi.fn((options: any) => {
    mockExportState.options = options;
  }),
  startExport: vi.fn(() => Promise.resolve()),
  cancelExport: vi.fn(() => {
    mockExportState.status = 'idle';
    mockExportState.progress = 0;
    mockExportState.error = null;
    mockExportState.metadata = null;
  }),
  clearError: vi.fn(() => {
    mockExportState.error = null;
  }),
  reset: vi.fn(() => {
    mockExportState = {
      status: 'idle',
      progress: 0,
      error: null,
      options: {},
      metadata: null,
      isOptionsModalOpen: false,
    };
  }),
};

vi.mock('@/stores/exportStore', () => ({
  useExportStore: Object.assign(vi.fn(() => ({
    ...mockExportState,
    ...mockExportFunctions,
  })), {
    getState: vi.fn(() => ({
      ...mockExportState,
      ...mockExportFunctions,
    })),
  }),
}));

// Mock the conversation Zustand store
let mockFilters = {
  searchQuery: '',
  dateRange: { from: null as string | null, to: null as string | null },
  statusFilters: [] as string[],
  sentimentFilters: [] as string[],
  hasHandoffFilter: null as boolean | null,
};

vi.mock('@/stores/conversationStore', () => ({
  useConversationStore: vi.fn(() => ({
    filters: mockFilters,
  })),
}));

function setMockExportState(state: Partial<typeof mockExportState>) {
  Object.assign(mockExportState, state);
}

function getMockExportFunctions() {
  return mockExportFunctions;
}

function resetMockExportState() {
  mockExportState = {
    status: 'idle',
    progress: 0,
    error: null,
    options: {},
    metadata: null,
    isOptionsModalOpen: false,
  };
  Object.values(mockExportFunctions).forEach(fn => {
    if (typeof fn === 'function' && 'mockClear' in fn) {
      (fn as any).mockClear();
    }
  });
}

function setMockConversationFilters(filters: Partial<typeof mockFilters>) {
  Object.assign(mockFilters, filters);
}

function resetMockConversationState() {
  mockFilters = {
    searchQuery: '',
    dateRange: { from: null, to: null },
    statusFilters: [],
    sentimentFilters: [],
    hasHandoffFilter: null,
  };
}

describe('ExportOptionsModal Component', () => {
  beforeEach(() => {
    resetMockExportState();
    resetMockConversationState();
  });

  it('should not render when modal is closed', () => {
    setMockExportState({ isOptionsModalOpen: false });

    const { container } = render(<ExportOptionsModal />);

    expect(container.querySelector('[role="dialog"]')).not.toBeInTheDocument();
  });

  it('should render dialog when open', () => {
    setMockExportState({ isOptionsModalOpen: true });

    render(<ExportOptionsModal />);

    expect(screen.getByRole('dialog')).toBeVisible();
    expect(screen.getByText('Export Conversations')).toBeVisible();
    // Use regex to match partial text
    expect(screen.getByText(/Configure filters to export/)).toBeVisible();
  });

  it('should show no filters message when no filters applied', () => {
    setMockExportState({ isOptionsModalOpen: true });

    render(<ExportOptionsModal />);

    expect(screen.getByText('No filters - export all conversations')).toBeVisible();
  });

  it('should show filter count when filters are applied', () => {
    // Set filters first, then open modal to trigger useEffect
    setMockConversationFilters({ statusFilters: ['active'] });
    setMockExportState({ isOptionsModalOpen: true });

    const { rerender } = render(<ExportOptionsModal />);

    // Rerender to ensure useEffect has processed the filters
    rerender(<ExportOptionsModal />);

    expect(screen.getByText('1 filter(s) applied')).toBeVisible();
    // Use regex to match the text that may be split across nodes
    expect(screen.getByText(/Status: active/)).toBeVisible();
  });

  it('should display export limit warning', () => {
    setMockExportState({ isOptionsModalOpen: true });

    render(<ExportOptionsModal />);

    expect(screen.getByText(/Export is limited to 10,000 conversations/)).toBeVisible();
  });

  it('should display CSV format information', () => {
    setMockExportState({ isOptionsModalOpen: true });

    render(<ExportOptionsModal />);

    expect(screen.getByText(/The CSV file will include:/)).toBeVisible();
    expect(screen.getByText('Conversation ID and masked Customer ID')).toBeVisible();
    expect(screen.getByText('Dates, Status, and Sentiment')).toBeVisible();
    expect(screen.getByText('Message count and order status')).toBeVisible();
    expect(screen.getByText('LLM provider, tokens, and estimated cost')).toBeVisible();
    expect(screen.getByText('Last message preview')).toBeVisible();
  });

  it('should display search filter', () => {
    setMockExportState({ isOptionsModalOpen: true });
    setMockConversationFilters({ searchQuery: 'test search' });

    render(<ExportOptionsModal />);

    expect(screen.getByText(/Search: "test search"/)).toBeVisible();
  });

  it('should display date range filter (both dates)', () => {
    setMockExportState({ isOptionsModalOpen: true });
    setMockConversationFilters({ dateRange: { from: '2026-01-01', to: '2026-12-31' } });

    render(<ExportOptionsModal />);

    expect(screen.getByText(/Date: 2026-01-01 to 2026-12-31/)).toBeVisible();
  });

  it('should display date range filter (from date only)', () => {
    setMockExportState({ isOptionsModalOpen: true });
    setMockConversationFilters({ dateRange: { from: '2026-01-01', to: null } });

    render(<ExportOptionsModal />);

    expect(screen.getByText(/From: 2026-01-01/)).toBeVisible();
  });

  it('should display date range filter (to date only)', () => {
    setMockExportState({ isOptionsModalOpen: true });
    setMockConversationFilters({ dateRange: { from: null, to: '2026-12-31' } });

    render(<ExportOptionsModal />);

    expect(screen.getByText(/To: 2026-12-31/)).toBeVisible();
  });

  it('should display multiple status filters', () => {
    setMockExportState({ isOptionsModalOpen: true });
    setMockConversationFilters({ statusFilters: ['active', 'closed'] });

    render(<ExportOptionsModal />);

    expect(screen.getByText(/Status: active, closed/)).toBeVisible();
  });

  it('should display sentiment filter', () => {
    setMockExportState({ isOptionsModalOpen: true });
    setMockConversationFilters({ sentimentFilters: ['positive', 'neutral'] });

    render(<ExportOptionsModal />);

    expect(screen.getByText(/Sentiment: positive, neutral/)).toBeVisible();
  });

  it('should display handoff filter (true)', () => {
    setMockExportState({ isOptionsModalOpen: true });
    setMockConversationFilters({ hasHandoffFilter: true });

    render(<ExportOptionsModal />);

    expect(screen.getByText(/Handoff: Yes/)).toBeVisible();
  });

  it('should display handoff filter (false)', () => {
    setMockExportState({ isOptionsModalOpen: true });
    setMockConversationFilters({ hasHandoffFilter: false });

    render(<ExportOptionsModal />);

    expect(screen.getByText(/Handoff: No/)).toBeVisible();
  });

  it('should call setExportOptions and startExport when Export clicked', () => {
    setMockExportState({ isOptionsModalOpen: true });
    setMockConversationFilters({ searchQuery: 'test', statusFilters: ['active'] });

    render(<ExportOptionsModal />);

    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }));

    expect(mockExportFunctions.setExportOptions).toHaveBeenCalled();
    expect(mockExportFunctions.closeOptionsModal).toHaveBeenCalled();
    expect(mockExportFunctions.startExport).toHaveBeenCalled();
  });

  it('should close modal when Cancel clicked', () => {
    setMockExportState({ isOptionsModalOpen: true });

    render(<ExportOptionsModal />);

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(mockExportFunctions.closeOptionsModal).toHaveBeenCalled();
  });

  it('should show clear all button when filters are active', () => {
    setMockExportState({ isOptionsModalOpen: true });
    setMockConversationFilters({ statusFilters: ['active'] });

    render(<ExportOptionsModal />);

    expect(screen.getByRole('button', { name: 'Clear all' })).toBeVisible();
  });

  it('should initialize form with current filters', () => {
    setMockExportState({ isOptionsModalOpen: true });
    setMockConversationFilters({
      searchQuery: 'shoes',
      dateRange: { from: '2026-02-01', to: '2026-02-28' },
      statusFilters: ['active'],
      sentimentFilters: ['positive'],
      hasHandoffFilter: true,
    });

    render(<ExportOptionsModal />);

    // All filters should be displayed
    expect(screen.getByText(/Search: "shoes"/)).toBeVisible();
    expect(screen.getByText(/Date: 2026-02-01 to 2026-02-28/)).toBeVisible();
    expect(screen.getByText(/Status: active/)).toBeVisible();
    expect(screen.getByText(/Sentiment: positive/)).toBeVisible();
    expect(screen.getByText(/Handoff: Yes/)).toBeVisible();
  });

  it('should count filters correctly', () => {
    setMockExportState({ isOptionsModalOpen: true });
    setMockConversationFilters({
      searchQuery: 'test',
      dateRange: { from: '2026-01-01', to: null },
      statusFilters: ['active', 'closed'],
      sentimentFilters: ['positive'],
      hasHandoffFilter: null,
    });

    render(<ExportOptionsModal />);

    expect(screen.getByText('4 filter(s) applied')).toBeVisible();
  });

  it('should have proper ARIA attributes', () => {
    setMockExportState({ isOptionsModalOpen: true });

    render(<ExportOptionsModal />);

    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeVisible();
    expect(dialog).toHaveAttribute('aria-modal', 'true');
  });

  it('should be keyboard accessible', () => {
    setMockExportState({ isOptionsModalOpen: true });

    render(<ExportOptionsModal />);

    const exportButton = screen.getByRole('button', { name: 'Export CSV' });
    expect(exportButton).toBeVisible();
  });

  it('should not show clear all button when no filters', () => {
    setMockExportState({ isOptionsModalOpen: true });

    render(<ExportOptionsModal />);

    const clearButton = screen.queryByRole('button', { name: 'Clear all' });
    expect(clearButton).not.toBeInTheDocument();
  });
});
