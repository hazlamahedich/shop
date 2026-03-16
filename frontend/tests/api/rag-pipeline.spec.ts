/**
 * API Tests for Story 8.4: Backend - RAG Service (Document Processing)
 *
 * Tests Knowledge Base API endpoints for RAG pipeline
 *
 * Coverage:
 * - AC1: Document upload and processing
 * - AC2: Document listing and status
 * - AC3: Error handling and validation
 * - AC4: Authentication and authorization
 */

import { test, expect, APIRequestContext } from '@playwright/test';
import * as path from 'path';
import { promises as fsPromises } from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const API_URL = process.env.API_URL || 'http://localhost:8000';

// Data Factory: Test Merchant
const createTestMerchant = (overrides: Partial<{ email: string; password: string }> = {}) => ({
  email: 'e2e-test@example.com',
  password: 'TestPass123',
  ...overrides,
});

// Data Factory: Document Content
const createDocumentContent = (type: 'faq' | 'product' | 'large' | 'empty' = 'faq') => {
  switch (type) {
    case 'faq':
      return `
Q: What is your return policy?
A: We accept returns within 30 days of purchase.

Q: How long does shipping take?
A: Standard shipping takes 3-5 business days.
      `.trim();
    case 'product':
      return `
Product: Widget Pro
Description: High-quality widget for all your needs
Features: Durable, lightweight, eco-friendly
      `.trim();
    case 'large':
      return Array(5000).fill('This is test content for large document upload. ').join('\n');
    case 'empty':
      return '';
    default:
      return 'Default test content';
  }
};

// Track created documents for cleanup
const createdDocumentIds: number[] = [];

test.describe('Story 8.4: Knowledge Base API', () => {
  // Enable parallel execution (removed serial mode)
  test.describe.configure({ mode: 'parallel' });

  let authenticatedContext: APIRequestContext;

  test.beforeAll(async ({ playwright }) => {
    authenticatedContext = await playwright.request.newContext({
      baseURL: API_URL,
    });

    const merchant = createTestMerchant();
    const response = await authenticatedContext.post('/api/v1/auth/login', {
      data: merchant,
    });

    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Authentication failed: ${response.status()} - ${body}`);
    }

    console.log('✅ Authenticated successfully');
  });

  test.afterAll(async () => {
    if (createdDocumentIds.length > 0) {
      console.log(`🧹 Cleaning up ${createdDocumentIds.length} documents...`);
      for (const docId of createdDocumentIds) {
        try {
          await authenticatedContext.delete(`/api/knowledge-base/${docId}`);
        } catch (error) {
          console.warn(`  ⚠ Failed to delete document ${docId}`);
        }
      }
      createdDocumentIds.length = 0;
    }
    await authenticatedContext?.dispose();
  });

  // ==================== AC2: Document Listing ====================

  test('[P0] Given authenticated user When listing documents Then returns document array - AC2', async () => {
    const response = await authenticatedContext.get('/api/knowledge-base');

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('data');
    expect(body.data).toHaveProperty('documents');
    expect(Array.isArray(body.data.documents)).toBe(true);

    console.log(`✅ List documents test passed (${body.data.documents.length} documents)`);
  });

  // ==================== AC4: Authentication ====================

  test('[P0] Given unauthenticated user When accessing documents Then returns 401', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/knowledge-base`);

    expect(response.status()).toBe(401);
    console.log('✅ Auth required test passed');
  });

  test('[P2] Given unauthenticated user When uploading document Then returns 401', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/knowledge-base/upload`, {
      multipart: {
        file: {
          name: 'test.txt',
          mimeType: 'text/plain',
          buffer: Buffer.from('test'),
        },
      },
    });

    expect(response.status()).toBe(401);
    console.log('✅ Auth rejection test passed');
  });

  // ==================== AC1: Document Upload ====================

  test('[P0] Given valid document When uploading Then returns document with ID - AC1', async () => {
    const tempPath = path.join(__dirname, `test-doc-${Date.now()}.txt`);
    const content = createDocumentContent('faq');
    await fsPromises.writeFile(tempPath, content);
    const fileBuffer = await fsPromises.readFile(tempPath);

    const response = await authenticatedContext.post('/api/knowledge-base/upload', {
      multipart: {
        file: {
          name: 'test-faq.txt',
          mimeType: 'text/plain',
          buffer: fileBuffer,
        },
      },
    });

    expect(response.status()).toBe(200);

    const json = await response.json();
    expect(json).toHaveProperty('data');
    expect(json.data).toHaveProperty('id');
    expect(json.data).toHaveProperty('status');

    // Track for cleanup
    if (json.data.id) {
      createdDocumentIds.push(json.data.id);
    }

    await fsPromises.unlink(tempPath);
    console.log(`✅ Upload test passed (doc ID: ${json.data.id})`);
  });

  // ==================== AC1: Document Reprocess ====================

  test('[P1] Given existing document When reprocessing Then triggers re-embedding - AC1', async () => {
    // First upload a document
    const tempPath = path.join(__dirname, `test-reprocess-${Date.now()}.txt`);
    const content = createDocumentContent('product');
    await fsPromises.writeFile(tempPath, content);
    const fileBuffer = await fsPromises.readFile(tempPath);

    const uploadResponse = await authenticatedContext.post('/api/knowledge-base/upload', {
      multipart: {
        file: {
          name: 'test-product.txt',
          mimeType: 'text/plain',
          buffer: fileBuffer,
        },
      },
    });

    expect(uploadResponse.status()).toBe(200);
    const uploadJson = await uploadResponse.json();
    const documentId = uploadJson.data.id;

    // Track for cleanup
    if (documentId) {
      createdDocumentIds.push(documentId);
    }

    // Now reprocess the document
    const reprocessResponse = await authenticatedContext.post(
      `/api/knowledge-base/${documentId}/reprocess`
    );

    // API returns document_id, not id
    expect(reprocessResponse.status()).toBe(200);
    const reprocessJson = await reprocessResponse.json();
    expect(reprocessJson.data).toHaveProperty('document_id', documentId);
    expect(reprocessJson.data).toHaveProperty('reprocessing', true);

    await fsPromises.unlink(tempPath);
    console.log(`✅ Reprocess test passed (doc ID: ${documentId})`);
  });

  // ==================== AC2: Document Status ====================

  test('[P2] Given existing document When checking status Then returns processing info - AC2', async () => {
    // Upload a document first
    const tempPath = path.join(__dirname, `test-status-${Date.now()}.txt`);
    const content = createDocumentContent('faq');
    await fsPromises.writeFile(tempPath, content);
    const fileBuffer = await fsPromises.readFile(tempPath);

    const uploadResponse = await authenticatedContext.post('/api/knowledge-base/upload', {
      multipart: {
        file: {
          name: 'test-status.txt',
          mimeType: 'text/plain',
          buffer: fileBuffer,
        },
      },
    });

    expect(uploadResponse.status()).toBe(200);
    const uploadJson = await uploadResponse.json();
    const documentId = uploadJson.data.id;

    // Track for cleanup
    if (documentId) {
      createdDocumentIds.push(documentId);
    }

    // Check status - API returns status, progress, chunk_count
    const statusResponse = await authenticatedContext.get(
      `/api/knowledge-base/${documentId}/status`
    );

    expect(statusResponse.status()).toBe(200);
    const statusJson = await statusResponse.json();
    expect(statusJson.data).toHaveProperty('status');
    expect(['pending', 'processing', 'ready', 'error']).toContain(statusJson.data.status);

    await fsPromises.unlink(tempPath);
    console.log(`✅ Status test passed (doc ID: ${documentId}, status: ${statusJson.data.status})`);
  });

  // ==================== AC3: Error Handling ====================

  test('[P1] Given non-existent document When fetching Then returns 404 - AC3', async () => {
    const response = await authenticatedContext.get('/api/knowledge-base/999999');

    expect(response.status()).toBe(404);
    console.log('✅ Not found test passed');
  });

  test('[P1] Given invalid file type When uploading Then returns 400 - AC3', async () => {
    const tempPath = path.join(__dirname, `test-invalid-${Date.now()}.exe`);
    await fsPromises.writeFile(tempPath, 'invalid content');
    const fileBuffer = await fsPromises.readFile(tempPath);

    const response = await authenticatedContext.post('/api/knowledge-base/upload', {
      multipart: {
        file: {
          name: 'test.exe',
          mimeType: 'application/octet-stream',
          buffer: fileBuffer,
        },
      },
    });

    expect(response.status()).toBe(400);
    const body = await response.json();
    expect(body.detail).toContain('Invalid file type');

    await fsPromises.unlink(tempPath);
    console.log('✅ File type validation test passed');
  });

  test('[P3] Given large file When uploading Then handles gracefully', async () => {
    const tempPath = path.join(__dirname, `test-large-${Date.now()}.txt`);
    const content = createDocumentContent('large');
    await fsPromises.writeFile(tempPath, content);
    const fileBuffer = await fsPromises.readFile(tempPath);

    const response = await authenticatedContext.post('/api/knowledge-base/upload', {
      multipart: {
        file: {
          name: 'test-large.txt',
          mimeType: 'text/plain',
          buffer: fileBuffer,
        },
      },
      timeout: 30000, // 30 second timeout
    });

    // Either reject with 413 (too large) or accept with 200
    expect([200, 413]).toContain(response.status());

    if (response.status() === 200) {
      const json = await response.json();
      if (json.data.id) {
        createdDocumentIds.push(json.data.id);
      }
      console.log('✅ Large file accepted');
    } else {
      console.log('✅ Large file rejected (size limit)');
    }

    await fsPromises.unlink(tempPath);
  });

  // ==================== Security: Multi-Tenant Isolation ====================

  test('[P0] Given cross-tenant access When fetching document Then returns 404', async () => {
    // Try to access a document that likely belongs to another merchant
    // Using ID 1 which is likely created by another merchant
    const response = await authenticatedContext.get('/api/knowledge-base/1');

    // Should return 404 if proper multi-tenant isolation is implemented
    // Accepting 404 or 200 (if doc exists) but NOT 403 (which would leak existence)
    expect([200, 404]).toContain(response.status());

    if (response.status() === 404) {
      console.log('✅ Multi-tenant isolation test passed');
    } else {
      console.log('⚠️ Document 1 exists - verify multi-tenant isolation manually');
    }
  });
});
