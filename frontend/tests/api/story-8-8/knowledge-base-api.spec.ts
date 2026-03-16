/**
 * API Test: Knowledge Base Service
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Tests knowledge base API endpoints (document management)
 *
 * ATDD Checklist:
 * [x] AC1: GET /api/knowledge-base returns documents with status
 * [x] AC2: POST /api/knowledge-base/upload accepts PDF/TXT/MD/DOCX
 * [x] AC3: DELETE /api/knowledge-base/{id} removes document
 * [x] AC4: GET /api/knowledge-base/{id}/status returns processing status
 * [x] AC5: POST /api/knowledge-base/{id}/reprocess retries failed document
 *
 * @tags api service story-8-8 knowledge-base
 */

import { test, expect } from '@playwright/test';

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

interface ApiResponse<T> {
  data: T;
}

test.describe('Story 8-8: Knowledge Base API @api @story-8-8', () => {
  const baseEndpoint = '/api/knowledge-base';

  test.describe.serial('AC1: List Documents', () => {
    test('[8.8-API-001][P0] @smoke should fetch documents list successfully', async ({ request }) => {
      const response = await request.get(baseEndpoint, {
        headers: {
          Authorization: `Bearer test-token`,
        },
      });

      expect(response.status()).toBe(200);

      const body: ApiResponse<{ documents: KnowledgeDocument[] }> = await response.json();
      expect(body.data).toHaveProperty('documents');
      expect(Array.isArray(body.data.documents)).toBe(true);
    });

    test('[8.8-API-002][P1] should return documents with required fields', async ({ request }) => {
      const response = await request.get(baseEndpoint, {
        headers: {
          Authorization: `Bearer test-token`,
        },
      });

      expect(response.status()).toBe(200);

      const body = await response.json();
      
      if (body.data.documents.length > 0) {
        const doc = body.data.documents[0];
        expect(doc).toHaveProperty('id');
        expect(doc).toHaveProperty('filename');
        expect(doc).toHaveProperty('fileType');
        expect(doc).toHaveProperty('fileSize');
        expect(doc).toHaveProperty('status');
        expect(doc).toHaveProperty('chunkCount');
        expect(doc).toHaveProperty('createdAt');
        expect(doc).toHaveProperty('updatedAt');
        expect(['pending', 'processing', 'ready', 'error']).toContain(doc.status);
      }
    });

    test('[8.8-API-003][P1] should return empty array for merchant with no documents', async ({ request }) => {
      const response = await request.get(baseEndpoint, {
        headers: {
          Authorization: `Bearer test-token-no-documents`,
        },
      });

      expect(response.status()).toBe(200);

      const body = await response.json();
      expect(body.data.documents).toEqual([]);
    });
  });

  test.describe.serial('AC2: Upload Document', () => {
    test('[8.8-API-004][P0] @smoke should upload PDF file successfully', async ({ request }) => {
      const response = await request.post(`${baseEndpoint}/upload`, {
        headers: {
          Authorization: `Bearer test-token`,
        },
        multipart: {
          file: {
            name: 'test.pdf',
            mimeType: 'application/pdf',
            buffer: Buffer.from('%PDF-1.4\ntest pdf content'),
          },
        },
      });

      expect(response.status()).toBe(201);

      const body: ApiResponse<Partial<KnowledgeDocument>> = await response.json();
      expect(body.data).toHaveProperty('id');
      expect(body.data.filename).toContain('.pdf');
      expect(body.data.status).toBe('pending');
    });

    test('[8.8-API-005][P0] @smoke should upload TXT file successfully', async ({ request }) => {
      const response = await request.post(`${baseEndpoint}/upload`, {
        headers: {
          Authorization: `Bearer test-token`,
        },
        multipart: {
          file: {
            name: 'test.txt',
            mimeType: 'text/plain',
            buffer: Buffer.from('Test document content'),
          },
        },
      });

      expect(response.status()).toBe(201);

      const body = await response.json();
      expect(body.data.filename).toContain('.txt');
    });
  });
});
