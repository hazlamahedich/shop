/**
 * Component tests for ExportProgress
 * P0 - Progress display, status messages, error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ExportProgress } from '@/components/export';

// Mock the Zustand store
let mockExportState = {
  status: 'idle' as 'idle' | 'preparing' | 'exporting' | 'completed' | 'error',
  progress: 0,
  error: null as string | null,
  options: {} as any,
  metadata: null as any,
  isOptionsModalOpen: false,
};

const mockFunctions = {
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
    ...mockFunctions,
  })), {
    getState: vi.fn(() => ({
      ...mockExportState,
      ...mockFunctions,
    })),
  }),
}));

function setMockExportState(state: Partial<typeof mockExportState>) {
  Object.assign(mockExportState, state);
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
  Object.values(mockFunctions).forEach(fn => {
    if (typeof fn === 'function' && 'mockClear' in fn) {
      (fn as any).mockClear();
    }
  });
}

describe('ExportProgress Component', () => {
  beforeEach(() => {
    resetMockExportState();
  });

  it('should not render when status is idle', () => {
    const { container } = render(<ExportProgress />);

    // When status is idle, the component returns null
    expect(container.firstChild).toBeNull();
  });

  it('should render preparing state message', () => {
    setMockExportState({ status: 'preparing' });

    render(<ExportProgress />);

    expect(screen.getByText('Preparing export...')).toBeVisible();
  });

  it('should render exporting state message with progress bar', () => {
    setMockExportState({ status: 'exporting', progress: 50 });

    render(<ExportProgress />);

    expect(screen.getByText('Generating CSV file...')).toBeVisible();
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toBeVisible();
    expect(progressbar).toHaveAttribute('aria-valuenow', '50');
  });

  it('should render completed state with metadata', () => {
    const metadata = {
      exportCount: 150,
      exportDate: '2026-02-07T10:30:00Z',
      filename: 'conversations-2026-02-07.csv',
    };

    setMockExportState({ status: 'completed', progress: 100, metadata });

    render(<ExportProgress />);

    expect(screen.getByText(/150 conversations exported/)).toBeVisible();
    expect(screen.getByText(/File: conversations-2026-02-07.csv/)).toBeVisible();
  });

  it('should render completed state without metadata', () => {
    setMockExportState({ status: 'completed', progress: 100, metadata: null });

    render(<ExportProgress />);

    expect(screen.getByText('Export complete!')).toBeVisible();
  });

  it('should render error state', () => {
    setMockExportState({ status: 'error', error: 'Network error occurred' });

    render(<ExportProgress />);

    expect(screen.getByText('Network error occurred')).toBeVisible();
  });

  it('should render default error message when error is null', () => {
    setMockExportState({ status: 'error', error: null });

    render(<ExportProgress />);

    expect(screen.getByText('Export failed. Please try again.')).toBeVisible();
  });

  it('should show dismiss button when there is an error', () => {
    setMockExportState({ status: 'error', error: 'Export failed' });

    render(<ExportProgress />);

    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    expect(dismissButton).toBeVisible();
  });

  it('should not show progress bar when completed', () => {
    setMockExportState({ status: 'completed', progress: 100 });

    render(<ExportProgress />);

    expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
  });

  it('should show progress bar during preparing state', () => {
    setMockExportState({ status: 'preparing', progress: 10 });

    render(<ExportProgress />);

    expect(screen.getByRole('progressbar')).toBeVisible();
  });

  it('should format date correctly in metadata', () => {
    const metadata = {
      exportCount: 100,
      exportDate: '2026-02-07T10:30:00Z',
      filename: 'conversations-2026-02-07.csv',
    };

    setMockExportState({ status: 'completed', progress: 100, metadata });

    render(<ExportProgress />);

    // Check that formatted date is visible
    expect(screen.getByText(/\d{1,2}\/\d{1,2}\/\d{4}/)).toBeVisible();
  });

  it('should apply custom className', () => {
    setMockExportState({ status: 'exporting', progress: 50 });

    render(<ExportProgress className="custom-class" />);

    const progressContainer = document.querySelector('.rounded-lg');
    expect(progressContainer).toHaveClass('custom-class');
  });

  it('should have proper ARIA attributes on progress bar', () => {
    setMockExportState({ status: 'exporting', progress: 75 });

    render(<ExportProgress />);

    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '75');
    expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    expect(progressbar).toHaveAttribute('aria-valuemax', '100');
  });

  it('should dismiss error when close button clicked', () => {
    setMockExportState({ status: 'error', error: 'Export failed' });

    render(<ExportProgress />);

    const dismissButton = screen.getByRole('button', { name: /dismiss/i });
    fireEvent.click(dismissButton);
    expect(mockFunctions.clearError).toHaveBeenCalled();
  });

  it('should not show dismiss button in non-error states', () => {
    setMockExportState({ status: 'exporting', progress: 50 });

    render(<ExportProgress />);

    // Should not have any buttons
    const buttons = screen.queryAllByRole('button');
    expect(buttons.length).toBe(0);
  });
});
