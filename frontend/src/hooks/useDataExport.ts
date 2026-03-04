/**
 * Custom hook for merchant data export functionality.
 * Story 6-3: Merchant CSV Export
 * 
 * Handles:
 * - Export trigger with CSRF token
 * - Loading state during export
 * - Error handling (rate limit, auth failure)
 * - Success notification
 */

import { useState, useCallback } from 'react';
import { useToast } from '../context/ToastContext';

interface UseDataExportReturn {
  exportData: () => Promise<void>;
  isExporting: boolean;
  error: string | null;
}

export function useDataExport(merchantId: number): UseDataExportReturn {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const exportData = useCallback(async () => {
    setIsExporting(true);
    setError(null);

    try {
      // Fetch CSRF token first
      const csrfResponse = await fetch('/api/v1/csrf-token', {
        credentials: 'include',
      });

      if (!csrfResponse.ok) {
        throw new Error('Failed to get CSRF token');
      }

      const csrfData = await csrfResponse.json();
      const csrfToken = csrfData.csrf_token;

      if (!csrfToken) {
        throw new Error('CSRF token not found');
      }

      // Trigger export
      const response = await fetch('/api/v1/data/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
          'X-Merchant-ID': merchantId.toString(),
        },
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json();
        
        // Handle specific error cases
        if (response.status === 429) {
          const retryAfter = errorData.details?.retry_after || 3600;
          const minutes = Math.ceil(retryAfter / 60);
          throw new Error(`Export rate limit: Try again in ${minutes} minutes`);
        }
        
        if (response.status === 401) {
          throw new Error('Authentication failed. Please log in again.');
        }

        throw new Error(errorData.message || 'Export failed');
      }

      // Download the CSV file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      
      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      const filenameMatch = contentDisposition?.match(/filename="(.+)"/);
      const filename = filenameMatch ? filenameMatch[1] : `merchant_${merchantId}_export.csv`;
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast('Export completed successfully!', 'success');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Export failed';
      setError(errorMessage);
      toast(errorMessage, 'error');
    } finally {
      setIsExporting(false);
    }
  }, [merchantId, toast]);

  return {
    exportData,
    isExporting,
    error,
  };
}
