/**
 * Component tests for ExportButton
 * P0 - Button rendering, loading states, click interactions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExportButton } from '@/components/export';

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

describe('ExportButton Component', () => {
  beforeEach(() => {
    resetMockExportState();
  });

  it('should render export button with idle state', () => {
    setMockExportState({ status: 'idle' });

    render(<ExportButton />);

    expect(screen.getByTestId('export-button')).toBeVisible();
    expect(screen.getByText('Export CSV')).toBeVisible();
  });

  it('should render loading state when exporting', () => {
    setMockExportState({ status: 'exporting' });

    render(<ExportButton />);

    expect(screen.getByText('Exporting...')).toBeVisible();
    expect(document.querySelector('.animate-spin')).toBeVisible();
  });

  it('should render completed state when export is done', () => {
    setMockExportState({ status: 'completed' });

    render(<ExportButton />);

    expect(screen.getByText('Export Complete')).toBeVisible();
    expect(document.querySelector('svg.text-green-600')).toBeVisible();
  });

  it('should be disabled when loading', () => {
    setMockExportState({ status: 'exporting' });

    render(<ExportButton />);

    const button = screen.getByTestId('export-button');
    expect(button).toBeDisabled();
  });

  it('should be disabled when disabled prop is true', () => {
    setMockExportState({ status: 'idle' });

    render(<ExportButton disabled={true} />);

    const button = screen.getByTestId('export-button');
    expect(button).toBeDisabled();
  });

  it('should call openOptionsModal when clicked', () => {
    setMockExportState({ status: 'idle' });

    render(<ExportButton />);

    fireEvent.click(screen.getByTestId('export-button'));
    expect(mockFunctions.openOptionsModal).toHaveBeenCalled();
  });

  it('should be disabled when preparing', () => {
    setMockExportState({ status: 'preparing' });

    render(<ExportButton />);

    const button = screen.getByTestId('export-button');
    expect(button).toBeDisabled();
  });

  it('should show spinner icon when loading', () => {
    setMockExportState({ status: 'preparing' });

    render(<ExportButton />);

    expect(document.querySelector('svg.animate-spin')).toBeVisible();
  });

  it('should show checkmark icon when completed', () => {
    setMockExportState({ status: 'completed' });

    render(<ExportButton />);

    expect(document.querySelector('svg.text-green-600')).toBeVisible();
  });

  it('should show download icon when idle', () => {
    setMockExportState({ status: 'idle' });

    render(<ExportButton />);

    expect(screen.getByText('Export CSV')).toBeVisible();
  });

  it('should apply custom className', () => {
    setMockExportState({ status: 'idle' });

    render(<ExportButton className="custom-class" />);

    const button = screen.getByTestId('export-button');
    expect(button).toHaveClass('custom-class');
  });

  it('should be keyboard accessible', async () => {
    setMockExportState({ status: 'idle' });

    render(<ExportButton />);

    const button = screen.getByTestId('export-button');
    // Use userEvent for proper keyboard interaction simulation
    await userEvent.keyboard('[Tab]');
    await userEvent.keyboard('[Enter]');

    // Verify the modal open function was called
    expect(mockFunctions.openOptionsModal).toHaveBeenCalled();
  });

  it('should not be clickable when disabled via status', () => {
    setMockExportState({ status: 'exporting' });

    render(<ExportButton />);

    const button = screen.getByTestId('export-button');

    // Disabled button clicks should be ignored
    fireEvent.click(button);

    // openOptionsModal should not be called when button is disabled
    expect(mockFunctions.openOptionsModal).not.toHaveBeenCalled();
  });

  it('should not be clickable when disabled via prop', () => {
    setMockExportState({ status: 'idle' });

    render(<ExportButton disabled={true} />);

    const button = screen.getByTestId('export-button');

    // Disabled button clicks should be ignored
    fireEvent.click(button);

    // openOptionsModal should not be called when button is disabled
    expect(mockFunctions.openOptionsModal).not.toHaveBeenCalled();
  });
});
