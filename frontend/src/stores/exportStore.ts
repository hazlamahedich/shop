/**
 * Export Store - Zustand state management for CSV export
 * Handles export options, progress tracking, and download status
 */

import { create } from 'zustand';
import type { ExportRequest, ExportMetadata } from '../services/export';
import { exportService } from '../services/export';

type ExportStatus = 'idle' | 'preparing' | 'exporting' | 'completed' | 'error';

export interface ExportState {
  // UI state
  status: ExportStatus;
  progress: number;
  error: string | null;

  // Export options
  options: ExportRequest;

  // Export metadata
  metadata: ExportMetadata | null;

  // UI state
  isOptionsModalOpen: boolean;

  // Actions
  openOptionsModal: () => void;
  closeOptionsModal: () => void;
  setExportOptions: (options: ExportRequest) => void;
  startExport: () => Promise<void>;
  cancelExport: () => void;
  clearError: () => void;
  reset: () => void;
}

// Initial state
const initialState = {
  status: 'idle' as ExportStatus,
  progress: 0,
  error: null as string | null,
  options: {} as ExportRequest,
  metadata: null as ExportMetadata | null,
  isOptionsModalOpen: false,
};

/**
 * Export store using Zustand
 */
export const useExportStore = create<ExportState>()((set, get) => ({
  ...initialState,

  /**
   * Open export options modal
   */
  openOptionsModal: () => {
    set({ isOptionsModalOpen: true });
  },

  /**
   * Close export options modal
   */
  closeOptionsModal: () => {
    set({ isOptionsModalOpen: false });
  },

  /**
   * Set export options
   */
  setExportOptions: (options: ExportRequest) => {
    set({ options: { ...options } });
  },

  /**
   * Start export process
   */
  startExport: async () => {
    const { options } = get();

    set({ status: 'preparing', progress: 0, error: null, metadata: null });

    try {
      // Simulate progress for large exports
      set({ status: 'exporting', progress: 10 });

      const { blob, metadata } = await exportService.exportConversations(options);

      set({ progress: 80, metadata });

      // Download the file
      exportService.downloadBlob(blob, metadata.filename);

      set({ status: 'completed', progress: 100, isOptionsModalOpen: false });

      // Reset to idle after a delay
      setTimeout(() => {
        set({ status: 'idle', progress: 0, metadata: null });
      }, 3000);
    } catch (error) {
      set({
        status: 'error',
        error: error instanceof Error ? error.message : 'Export failed',
        progress: 0,
      });
    }
  },

  /**
   * Cancel export (resets to idle state)
   */
  cancelExport: () => {
    set({ status: 'idle', progress: 0, error: null, metadata: null });
  },

  /**
   * Clear error state
   */
  clearError: () => {
    set({ error: null });
  },

  /**
   * Reset store to initial state
   */
  reset: () => {
    set(initialState);
  },
}));
