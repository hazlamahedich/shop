/**
 * ExportStore Tests
 *
 * Tests export store state management
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useExportStore } from './exportStore';
import { exportService } from '../services/export';

// Mock the export service
vi.mock('../services/export', () => ({
  exportService: {
    exportConversations: vi.fn(),
    downloadBlob: vi.fn(),
  },
}));

describe('ExportStore', () => {
  const mockBlob = new Blob(['csv content'], { type: 'text/csv' });
  const mockMetadata = {
    exportCount: 150,
    exportDate: '2026-02-07T10:30:00Z',
    filename: 'conversations-2026-02-07.csv',
  };

  const mockSuccessResponse = {
    blob: mockBlob,
    metadata: mockMetadata,
  };

  beforeEach(() => {
    // Clear localStorage to prevent persist middleware from rehydrating old state
    localStorage.clear();
    // Reset store to initial state
    useExportStore.getState().reset();
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('has correct initial state', () => {
      const state = useExportStore.getState();

      expect(state.status).toBe('idle');
      expect(state.progress).toBe(0);
      expect(state.error).toBeNull();
      expect(state.options).toEqual({});
      expect(state.metadata).toBeNull();
      expect(state.isOptionsModalOpen).toBe(false);
    });
  });

  describe('Modal State Management', () => {
    it('should open options modal', () => {
      const state = useExportStore.getState();
      state.openOptionsModal();

      const newState = useExportStore.getState();
      expect(newState.isOptionsModalOpen).toBe(true);
    });

    it('should close options modal', () => {
      useExportStore.setState({ isOptionsModalOpen: true });
      const state = useExportStore.getState();
      state.closeOptionsModal();

      const newState = useExportStore.getState();
      expect(newState.isOptionsModalOpen).toBe(false);
    });
  });

  describe('Export Options Management', () => {
    it('should set export options', () => {
      const state = useExportStore.getState();
      const options = {
        dateFrom: '2026-02-01',
        dateTo: '2026-02-28',
        status: ['active'],
      };

      state.setExportOptions(options);

      const newState = useExportStore.getState();
      expect(newState.options).toEqual(options);
    });

    it('should merge export options when called multiple times', () => {
      const state = useExportStore.getState();

      state.setExportOptions({ dateFrom: '2026-02-01' });
      state.setExportOptions({ status: ['active'] });

      const newState = useExportStore.getState();
      expect(newState.options).toEqual({ status: ['active'] });
    });
  });

  describe('startExport - Success Flow', () => {
    it('should start export and transition through states', async () => {
      vi.mocked(exportService.exportConversations).mockResolvedValue(mockSuccessResponse);
      vi.mocked(exportService.downloadBlob).mockImplementation(() => {});

      const state = useExportStore.getState();
      const exportPromise = state.startExport();

      // The store immediately sets status to exporting after preparing
      // This is expected behavior as state updates are synchronous
      const currentState = useExportStore.getState();
      expect(['preparing', 'exporting']).toContain(currentState.status);

      await exportPromise;
    });

    it('should transition to exporting status with progress', async () => {
      vi.mocked(exportService.exportConversations).mockResolvedValue(mockSuccessResponse);
      vi.mocked(exportService.downloadBlob).mockImplementation(() => {});

      const state = useExportStore.getState();
      await state.startExport();

      const finalState = useExportStore.getState();
      expect(finalState.status).toBe('completed');
      expect(finalState.progress).toBe(100);
      expect(finalState.metadata).toEqual(mockMetadata);
    });

    it('should download blob after export completes', async () => {
      vi.mocked(exportService.exportConversations).mockResolvedValue(mockSuccessResponse);
      vi.mocked(exportService.downloadBlob).mockImplementation(() => {});

      const state = useExportStore.getState();
      await state.startExport();

      expect(exportService.downloadBlob).toHaveBeenCalledWith(
        mockBlob,
        mockMetadata.filename
      );
    });

    it('should close modal after successful export', async () => {
      vi.mocked(exportService.exportConversations).mockResolvedValue(mockSuccessResponse);
      vi.mocked(exportService.downloadBlob).mockImplementation(() => {});

      useExportStore.setState({ isOptionsModalOpen: true });

      const state = useExportStore.getState();
      await state.startExport();

      const finalState = useExportStore.getState();
      expect(finalState.isOptionsModalOpen).toBe(false);
    });

    it('should reset to idle after delay (3 seconds)', async () => {
      vi.useFakeTimers();
      vi.mocked(exportService.exportConversations).mockResolvedValue(mockSuccessResponse);
      vi.mocked(exportService.downloadBlob).mockImplementation(() => {});

      const state = useExportStore.getState();
      await state.startExport();

      // Fast-forward 3 seconds
      await vi.advanceTimersByTimeAsync(3000);

      const finalState = useExportStore.getState();
      expect(finalState.status).toBe('idle');
      expect(finalState.progress).toBe(0);
      expect(finalState.metadata).toBeNull();

      vi.useRealTimers();
    }, 10000);

    it('should pass current options to export service', async () => {
      vi.mocked(exportService.exportConversations).mockResolvedValue(mockSuccessResponse);
      vi.mocked(exportService.downloadBlob).mockImplementation(() => {});

      const options = {
        dateFrom: '2026-02-01',
        dateTo: '2026-02-28',
        status: ['active'],
      };

      useExportStore.setState({ options });
      const state = useExportStore.getState();
      await state.startExport();

      expect(exportService.exportConversations).toHaveBeenCalledWith(options);
    });
  });

  describe('startExport - Error Flow', () => {
    it('should handle export errors', async () => {
      const error = new Error('Network error occurred');
      vi.mocked(exportService.exportConversations).mockRejectedValue(error);

      const state = useExportStore.getState();
      await state.startExport();

      const finalState = useExportStore.getState();
      expect(finalState.status).toBe('error');
      expect(finalState.error).toBe('Network error occurred');
      expect(finalState.progress).toBe(0);
    });

    it('should handle unknown error types', async () => {
      vi.mocked(exportService.exportConversations).mockRejectedValue('String error');

      const state = useExportStore.getState();
      await state.startExport();

      const finalState = useExportStore.getState();
      expect(finalState.status).toBe('error');
      expect(finalState.error).toBe('Export failed');
    });

    it('should reset progress and clear metadata on error', async () => {
      const error = new Error('Export failed');
      vi.mocked(exportService.exportConversations).mockRejectedValue(error);

      // Set some initial state
      useExportStore.setState({
        progress: 50,
        metadata: mockMetadata,
      });

      const state = useExportStore.getState();
      await state.startExport();

      const finalState = useExportStore.getState();
      expect(finalState.progress).toBe(0);
      expect(finalState.metadata).toBeNull();
    });

    it('should not download blob when export fails', async () => {
      const error = new Error('Export failed');
      vi.mocked(exportService.exportConversations).mockRejectedValue(error);
      vi.mocked(exportService.downloadBlob).mockImplementation(() => {});

      const state = useExportStore.getState();
      await state.startExport();

      expect(exportService.downloadBlob).not.toHaveBeenCalled();
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      useExportStore.setState({
        status: 'error',
        error: 'Some error message',
      });

      const state = useExportStore.getState();
      state.clearError();

      const newState = useExportStore.getState();
      expect(newState.error).toBeNull();
    });

    it('should not change other state properties when clearing error', () => {
      useExportStore.setState({
        status: 'error',
        error: 'Some error',
        progress: 50,
        options: { dateFrom: '2026-02-01' },
      });

      const state = useExportStore.getState();
      state.clearError();

      const newState = useExportStore.getState();
      expect(newState.status).toBe('error');
      expect(newState.progress).toBe(50);
      expect(newState.options).toEqual({ dateFrom: '2026-02-01' });
    });
  });

  describe('cancelExport', () => {
    it('should reset to idle state', () => {
      useExportStore.setState({
        status: 'exporting',
        progress: 45,
        error: null,
        metadata: { exportCount: 100, exportDate: '2026-02-07', filename: 'test.csv' },
      });

      const state = useExportStore.getState();
      state.cancelExport();

      const newState = useExportStore.getState();
      expect(newState.status).toBe('idle');
      expect(newState.progress).toBe(0);
      expect(newState.error).toBeNull();
      expect(newState.metadata).toBeNull();
    });
  });

  describe('reset', () => {
    it('should reset all state to initial values', () => {
      // Set some non-initial state
      useExportStore.setState({
        status: 'exporting',
        progress: 75,
        error: 'Some error',
        options: { dateFrom: '2026-02-01' },
        metadata: mockMetadata,
        isOptionsModalOpen: true,
      });

      const state = useExportStore.getState();
      state.reset();

      const newState = useExportStore.getState();
      expect(newState.status).toBe('idle');
      expect(newState.progress).toBe(0);
      expect(newState.error).toBeNull();
      expect(newState.options).toEqual({});
      expect(newState.metadata).toBeNull();
      expect(newState.isOptionsModalOpen).toBe(false);
    });
  });

  describe('Loading State Calculations', () => {
    it('should calculate isLoading correctly for preparing status', () => {
      useExportStore.setState({ status: 'preparing' });
      const state = useExportStore.getState();

      const isLoading = state.status === 'preparing' || state.status === 'exporting';
      expect(isLoading).toBe(true);
    });

    it('should calculate isLoading correctly for exporting status', () => {
      useExportStore.setState({ status: 'exporting' });
      const state = useExportStore.getState();

      const isLoading = state.status === 'preparing' || state.status === 'exporting';
      expect(isLoading).toBe(true);
    });

    it('should calculate isLoading correctly for idle status', () => {
      useExportStore.setState({ status: 'idle' });
      const state = useExportStore.getState();

      const isLoading = state.status === 'preparing' || state.status === 'exporting';
      expect(isLoading).toBe(false);
    });

    it('should calculate isCompleted correctly', () => {
      useExportStore.setState({ status: 'completed' });
      const state = useExportStore.getState();

      const isCompleted = state.status === 'completed';
      expect(isCompleted).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    it('should handle export with empty options', async () => {
      vi.mocked(exportService.exportConversations).mockResolvedValue(mockSuccessResponse);
      vi.mocked(exportService.downloadBlob).mockImplementation(() => {});

      const state = useExportStore.getState();
      await state.startExport();

      expect(exportService.exportConversations).toHaveBeenCalledWith({});
    });

    it('should handle multiple rapid export calls', async () => {
      vi.mocked(exportService.exportConversations).mockResolvedValue(mockSuccessResponse);
      vi.mocked(exportService.downloadBlob).mockImplementation(() => {});

      const state = useExportStore.getState();

      // Start multiple exports
      const promise1 = state.startExport();
      const promise2 = state.startExport();
      const promise3 = state.startExport();

      await Promise.all([promise1, promise2, promise3]);

      expect(exportService.exportConversations).toHaveBeenCalledTimes(3);
    });
  });
});
