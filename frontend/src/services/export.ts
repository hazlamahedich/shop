/**
 * Export API Service
 *
 * Handles CSV export of conversations with filters
 */

const API_EXPORT = '/api/conversations/export';

/**
 * Export request filters
 */
export interface ExportRequest {
  dateFrom?: string;
  dateTo?: string;
  search?: string;
  status?: string[];
  sentiment?: string[];
  hasHandoff?: boolean;
}

/**
 * Export response metadata
 */
export interface ExportMetadata {
  exportCount: number;
  exportDate: string;
  filename: string;
}

/**
 * Export service
 */
export const exportService = {
  /**
   * Export conversations to CSV
   *
   * @param filters - Export filter parameters
   * @param merchantId - Merchant ID from authentication
   * @returns Promise with blob and metadata
   */
  async exportConversations(
    filters: ExportRequest = {},
    merchantId?: string | number
  ): Promise<{ blob: Blob; metadata: ExportMetadata }> {
    // Get merchant ID from environment or storage if not provided
    const effectiveMerchantId = merchantId || this.getCurrentMerchantId();
    if (!effectiveMerchantId) {
      throw new Error('Merchant ID is required for export');
    }

    // Build request body (camelCase as expected by API)
    const body: Record<string, any> = {};
    if (filters.dateFrom) body.dateFrom = filters.dateFrom;
    if (filters.dateTo) body.dateTo = filters.dateTo;
    if (filters.search) body.search = filters.search;
    if (filters.status && filters.status.length > 0) body.status = filters.status;
    if (filters.sentiment && filters.sentiment.length > 0) body.sentiment = filters.sentiment;
    if (filters.hasHandoff !== undefined) body.hasHandoff = filters.hasHandoff;

    const response = await fetch(API_EXPORT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Merchant-ID': String(effectiveMerchantId),
      },
      body: Object.keys(body).length > 0 ? JSON.stringify(body) : '{}',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || error.detail?.[0]?.msg || 'Failed to export conversations');
    }

    // Extract metadata from headers
    const exportCount = response.headers.get('X-Export-Count');
    const exportDate = response.headers.get('X-Export-Date');
    const contentDisposition = response.headers.get('Content-Disposition') || '';

    // Parse filename from Content-Disposition header
    const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);
    const filename = filenameMatch ? filenameMatch[1] : `conversations-${new Date().toISOString().split('T')[0]}.csv`;

    const metadata: ExportMetadata = {
      exportCount: exportCount ? parseInt(exportCount, 10) : 0,
      exportDate: exportDate || new Date().toISOString(),
      filename,
    };

    // Get blob from response
    const blob = await response.blob();

    return { blob, metadata };
  },

  /**
   * Download blob as file
   *
   * @param blob - Blob to download
   * @param filename - Filename for download
   */
  downloadBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  /**
   * Get current merchant ID from environment or localStorage
   *
   * @returns Merchant ID or undefined
   */
  getCurrentMerchantId(): string | undefined {
    // Try environment variable first (for development)
    // @ts-ignore - VITE_ env variables are injected by Vite
    if (import.meta.env?.VITE_MERCHANT_ID) {
      // @ts-ignore
      return import.meta.env.VITE_MERCHANT_ID;
    }

    // Try localStorage
    try {
      const stored = localStorage.getItem('merchant_id');
      if (stored) return stored;
    } catch {
      // Ignore localStorage errors
    }

    return undefined;
  },
};
