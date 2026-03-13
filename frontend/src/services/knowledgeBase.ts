/**
 * Knowledge Base API Service
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Handles API calls for document upload and management
 */

import { apiClient } from './api';
import { getCsrfToken } from '../stores/csrfStore';
import type { KnowledgeDocument, DocumentListResponse, DocumentUploadResponse, DocumentStatusResponse } from '../types/knowledgeBase';

const BASE_PATH = '/api/knowledge-base';

/**
 * Retry configuration for API calls
 */
const RETRY_CONFIG = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 10000,
};

/**
 * Calculate exponential backoff delay with jitter
 */
function calculateDelay(attempt: number): number {
  const exponentialDelay = RETRY_CONFIG.baseDelayMs * Math.pow(2, attempt);
  const jitter = Math.random() * 100;
  return Math.min(exponentialDelay + jitter, RETRY_CONFIG.maxDelayMs);
}

/**
 * Sleep utility for retry delays
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export const knowledgeBaseApi = {
  async getDocuments(): Promise<KnowledgeDocument[]> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= RETRY_CONFIG.maxRetries; attempt++) {
      try {
        const response = await apiClient.get<DocumentListResponse>(BASE_PATH);
        return response.data.documents;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error');

        if (attempt < RETRY_CONFIG.maxRetries) {
          const delay = calculateDelay(attempt);
          await sleep(delay);
        }
      }
    }

    throw lastError || new Error('Failed to fetch documents');
  },

  uploadDocument(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();

    return new Promise((resolve, reject) => {
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = Math.round((event.loaded / event.total) * 100);
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response.data);
          } catch {
            reject(new Error('Failed to parse upload response'));
          }
        } else {
          try {
            const error = JSON.parse(xhr.responseText);
            reject(new Error(error.detail || 'Upload failed'));
          } catch {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Network error during upload'));
      });

      xhr.open('POST', BASE_PATH + '/upload');
      xhr.withCredentials = true;
      xhr.send(formData);
    });
  },

  async deleteDocument(documentId: number): Promise<void> {
    const csrfToken = await getCsrfToken();
    await apiClient.delete(`${BASE_PATH}/${documentId}`, {
      headers: {
        'X-CSRF-Token': csrfToken,
      },
    });
  },

  async reprocessDocument(documentId: number): Promise<void> {
    const csrfToken = await getCsrfToken();
    await apiClient.post(`${BASE_PATH}/${documentId}/reprocess`, {}, {
      headers: {
        'X-CSRF-Token': csrfToken,
      },
    });
  },

  async getDocumentStatus(documentId: number): Promise<DocumentStatusResponse> {
    const response = await apiClient.get<DocumentStatusResponse>(`${BASE_PATH}/${documentId}/status`);
    return response.data;
  },
};
