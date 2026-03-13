/**
 * Shared Mock Setup for Knowledge Base Tests
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Provides reusable mock setup for all knowledge base test files
 *
 * @tags helper mocks knowledge-base story-8-8
 */

import { Page } from '@playwright/test';

type DocumentStatus = 'pending' | 'processing' | 'ready' | 'error';

interface KnowledgeDocument {
  id: number;
  filename: string;
  fileType: string;
  fileSize: number;
  status: DocumentStatus;
  errorMessage?: string;
  chunkCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface MockOptions {
  onboardingMode?: 'general' | 'ecommerce';
  documents?: KnowledgeDocument[];
  uploadShouldFail?: boolean;
  deleteShouldFail?: boolean;
  delay?: number;
  networkError?: boolean;
  serverError?: boolean;
  uploadError?: number;
  deleteError?: number;
}

/**
 * Setup all mocks for knowledge base page tests
 * Reduces duplication across test files
 */
export async function setupKnowledgeBaseMocks(page: Page, options: MockOptions = {}) {
  const mode = options.onboardingMode || 'general';
  const documents = options.documents || [];

  // Auth state mock
  await page.addInitScript((initMode: string) => {
    const mockAuthState = {
      isAuthenticated: true,
      merchant: {
        id: 1,
        email: 'test@test.com',
        name: 'Test Merchant',
        has_store_connected: true,
        store_provider: 'shopify',
        onboardingMode: initMode,
      },
      sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
      isLoading: false,
      error: null,
    };
    localStorage.setItem('shop_auth_state', JSON.stringify(mockAuthState));
    localStorage.removeItem('onboarding-storage');
  }, mode);

  // CSRF token mock
  await page.route('**/api/v1/csrf-token', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ csrf_token: 'test-csrf-token' }),
    });
  });

  // Auth me mock
  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          merchant: {
            id: 1,
            email: 'test@test.com',
            name: 'Test Merchant',
            has_store_connected: true,
            store_provider: 'shopify',
            onboardingMode: mode,
          },
        },
      }),
    });
  });

  // Knowledge base API mock
  await page.route('**/api/knowledge-base**', async (route) => {
    if (options.networkError) {
      await route.abort('failed');
      return;
    }

    if (options.serverError) {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Internal server error' }),
      });
      return;
    }

    const request = route.request();
    const url = request.url();
    
    if (request.method() === 'GET') {
      // List vs Detail
      const isDetail = /\/\d+$/.test(url);
      
      if (options.delay) {
        await new Promise(resolve => setTimeout(resolve, options.delay));
      }

      if (isDetail) {
        const id = parseInt(url.split('/').pop() || '0');
        const doc = documents.find(d => d.id === id) || documents[0];
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: doc }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { documents },
          }),
        });
      }
    } else if (request.method() === 'DELETE') {
      if (options.deleteError) {
        let detail = 'Delete failed';
        if (options.deleteError === 404) detail = 'Document not found';
        if (options.deleteError === 500) detail = 'Internal server error';

        await route.fulfill({
          status: options.deleteError,
          contentType: 'application/json',
          body: JSON.stringify({ detail }),
        });
      } else if (options.deleteShouldFail) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Failed to delete document' }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { deleted: true, message: 'Document deleted successfully' }
          }),
        });
      }
    } else {
      await route.continue();
    }
  });

  // Upload mock
  await page.route('**/api/knowledge-base/upload', async (route) => {
    if (options.uploadError) {
      let detail = 'Upload failed';
      if (options.uploadError === 413) detail = 'File too large. Maximum size: 10MB';
      if (options.uploadError === 400) detail = 'Invalid file type';

      await route.fulfill({
        status: options.uploadError,
        contentType: 'application/json',
        body: JSON.stringify({ detail }),
      });
      return;
    }

    if (options.uploadShouldFail) {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid file type' }),
      });
    } else {
      if (options.delay) {
        await new Promise(resolve => setTimeout(resolve, options.delay));
      }
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: Date.now(),
            filename: 'test-document.pdf',
            fileType: 'application/pdf',
            fileSize: 1024,
            status: 'pending',
            createdAt: new Date().toISOString(),
          },
        }),
      });
    }
  });

  // Status mock
  await page.route('**/api/knowledge-base/*/status', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          status: 'ready',
          progress: 100,
          chunkCount: 5,
        },
      }),
    });
  });

  // Reprocess mock
  await page.route('**/api/knowledge-base/*/reprocess', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({}),
    });
  });
}

/**
 * Create a mock document for testing
 */
export function createMockDocument(overrides: Partial<KnowledgeDocument> = {}): KnowledgeDocument {
  return {
    id: Math.floor(Math.random() * 1000),
    filename: 'test-document.pdf',
    fileType: 'application/pdf',
    fileSize: 1024,
    status: 'ready',
    chunkCount: 5,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides,
  };
}

export type { KnowledgeDocument, DocumentStatus };
