/**
 * Performance & Stress Tests for Story 8.4: Backend - RAG Service
 *
 * P3 Tests: Performance benchmarks and stress testing
 *
 * Performance Targets (from Story 8-4):
 * - Embedding generation (single): <500ms
 * - Embedding generation (batch 100): <5s
 * - Vector similarity search: <100ms
 * - Full retrieval pipeline: <500ms
 * - Document processing (1MB): <30s
 *
 * Prerequisites:
 * - Backend API running on http://localhost:8000
 * - Test merchant account exists
 * - PostgreSQL + pgvector extension available
 */

import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const API_URL = process.env.API_URL || 'http://localhost:8000';

const TEST_MERCHANT = {
  email: 'e2e-test@example.com',
  password: 'TestPass123',
};

/**
 * Helper: Get auth token
 */
async function getAuthToken(request: any): Promise<string> {
  const response = await request.post(`${API_URL}/api/v1/auth/login`, {
    data: TEST_MERCHANT,
  });
  const body = await response.json();
  return body.data?.session?.token || '';
}

/**
 * Helper: Create document of specific size
 */
function createDocumentOfSize(sizeKB: number): string {
  const tempPath = path.join(__dirname, `perf-test-${sizeKB}kb-${Date.now()}.txt`);
  const content = 'Performance test content. '.repeat(Math.ceil((sizeKB * 1024) / 25));
  fs.writeFileSync(tempPath, content);
  return tempPath;
}

/**
 * Helper: Cleanup test file
 */
function cleanup(filePath: string) {
  if (fs.existsSync(filePath)) {
    fs.unlinkSync(filePath);
  }
}

test.describe('Story 8.4: Performance Benchmarks [P3]', () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    authToken = await getAuthToken(request);
  });

  test('[P3] should complete document upload in <5 seconds', async ({ request }) => {
    // Given: 1MB document
    const testFile = createDocumentOfSize(1024); // 1MB
    const fileBuffer = fs.readFileSync(testFile);

    // When: Upload document and measure time
    const startTime = Date.now();
    const response = await request.post(`${API_URL}/api/knowledge-base/upload`, {
      headers: { Authorization: `Bearer ${authToken}` },
      multipart: {
        file: {
          name: 'perf-test-1mb.txt',
          mimeType: 'text/plain',
          buffer: fileBuffer,
        },
      },
    });
    const uploadTime = Date.now() - startTime;

    // Then: Upload should complete in <5s
    expect(response.status()).toBe(200);
    expect(uploadTime).toBeLessThan(5000);

    console.log(`✅ Upload time: ${uploadTime}ms (target: <5000ms)`);

    cleanup(testFile);
  });

  test('[P3] should retrieve document status in <200ms', async ({ request }) => {
    // Given: Existing document
    const testFile = createDocumentOfSize(10); // 10KB
    const fileBuffer = fs.readFileSync(testFile);

    const uploadResponse = await request.post(`${API_URL}/api/knowledge-base/upload`, {
      headers: { Authorization: `Bearer ${authToken}` },
      multipart: {
        file: {
          name: 'perf-test-10kb.txt',
          mimeType: 'text/plain',
          buffer: fileBuffer,
        },
      },
    });

    const uploadBody = await uploadResponse.json();
    const documentId = uploadBody.data.id;

    // When: Retrieve status and measure time
    const startTime = Date.now();
    const response = await request.get(`${API_URL}/api/knowledge-base/${documentId}/status`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const retrievalTime = Date.now() - startTime;

    // Then: Retrieval should complete in <200ms
    expect(response.status()).toBe(200);
    expect(retrievalTime).toBeLessThan(200);

    console.log(`✅ Status retrieval time: ${retrievalTime}ms (target: <200ms)`);

    cleanup(testFile);
  });

  test('[P3] should list documents in <500ms', async ({ request }) => {
    // When: List documents and measure time
    const startTime = Date.now();
    const response = await request.get(`${API_URL}/api/knowledge-base/documents`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const retrievalTime = Date.now() - startTime;

    // Then: List should complete in <500ms
    expect(response.status()).toBe(200);
    expect(retrievalTime).toBeLessThan(500);

    console.log(`✅ List retrieval time: ${retrievalTime}ms (target: <500ms)`);
  });

  test('[P3] should handle 10 concurrent uploads without errors', async ({ request }) => {
    // Given: 10 test documents
    const testFiles = Array(10)
      .fill(null)
      .map((_, i) => {
        const filePath = createDocumentOfSize(50); // 50KB each
        return { path: filePath, buffer: fs.readFileSync(filePath) };
      });

    // When: Upload all concurrently
    const startTime = Date.now();
    const uploadPromises = testFiles.map((file, i) =>
      request.post(`${API_URL}/api/knowledge-base/upload`, {
        headers: { Authorization: `Bearer ${authToken}` },
        multipart: {
          file: {
            name: `concurrent-perf-test-${i}.txt`,
            mimeType: 'text/plain',
            buffer: file.buffer,
          },
        },
      })
    );

    const responses = await Promise.all(uploadPromises);
    const totalTime = Date.now() - startTime;

    // Then: All uploads should succeed
    const successCount = responses.filter((r) => r.status() === 200).length;
    expect(successCount).toBe(10);

    // And: Total time should be reasonable (<15s for 10 concurrent)
    expect(totalTime).toBeLessThan(15000);

    console.log(`✅ 10 concurrent uploads completed in ${totalTime}ms (target: <15000ms)`);

    // Cleanup
    testFiles.forEach((file) => cleanup(file.path));
  });

  test('[P3] should process document within 30 seconds (1MB target)', async ({ request }) => {
    // Given: 1MB document
    const testFile = createDocumentOfSize(1024); // 1MB
    const fileBuffer = fs.readFileSync(testFile);

    // When: Upload document
    const uploadResponse = await request.post(`${API_URL}/api/knowledge-base/upload`, {
      headers: { Authorization: `Bearer ${authToken}` },
      multipart: {
        file: {
          name: 'processing-perf-test.txt',
          mimeType: 'text/plain',
          buffer: fileBuffer,
        },
      },
    });

    const uploadBody = await uploadResponse.json();
    const documentId = uploadBody.data.id;

    // Then: Poll for completion (max 30s)
    const maxWaitTime = 30000;
    const pollInterval = 2000;
    const startTime = Date.now();
    let status = 'pending';

    while (Date.now() - startTime < maxWaitTime) {
      const statusResponse = await request.get(
        `${API_URL}/api/knowledge-base/${documentId}/status`,
        {
          headers: { Authorization: `Bearer ${authToken}` },
        }
      );

      const statusBody = await statusResponse.json();
      status = statusBody.data.status;

      if (status === 'ready' || status === 'error') {
        break;
      }

      await new Promise((resolve) => setTimeout(resolve, pollInterval));
    }

    const processingTime = Date.now() - startTime;

    // Then: Processing should complete within 30s
    expect(status).toBe('ready');
    expect(processingTime).toBeLessThan(30000);

    console.log(`✅ Document processing time: ${processingTime}ms (target: <30000ms)`);

    cleanup(testFile);
  });
});

test.describe('Story 8.4: Stress Tests [P3]', () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    authToken = await getAuthToken(request);
  });

  test('[P3] should handle large document upload (10MB)', async ({ request }) => {
    // Given: 10MB document
    const testFile = createDocumentOfSize(10240); // 10MB
    const fileBuffer = fs.readFileSync(testFile);

    // When: Upload large document
    const startTime = Date.now();
    const response = await request.post(`${API_URL}/api/knowledge-base/upload`, {
      headers: { Authorization: `Bearer ${authToken}` },
      multipart: {
        file: {
          name: 'stress-test-10mb.txt',
          mimeType: 'text/plain',
          buffer: fileBuffer,
        },
      },
    });
    const uploadTime = Date.now() - startTime;

    // Then: Upload should succeed (or fail gracefully with size limit)
    if (response.status() === 200) {
      expect(uploadTime).toBeLessThan(30000); // <30s for 10MB
      console.log(`✅ 10MB upload completed in ${uploadTime}ms`);
    } else if (response.status() === 400) {
      // File size limit enforced - acceptable
      const body = await response.json();
      expect(body.detail.message.toLowerCase()).toContain('file too large');
      console.log(`✅ File size limit enforced for 10MB file`);
    } else {
      throw new Error(`Unexpected status: ${response.status()}`);
    }

    cleanup(testFile);
  });

  test('[P3] should handle 50 concurrent status checks', async ({ request }) => {
    // Given: Upload a document first
    const testFile = createDocumentOfSize(10);
    const fileBuffer = fs.readFileSync(testFile);

    const uploadResponse = await request.post(`${API_URL}/api/knowledge-base/upload`, {
      headers: { Authorization: `Bearer ${authToken}` },
      multipart: {
        file: {
          name: 'stress-status-test.txt',
          mimeType: 'text/plain',
          buffer: fileBuffer,
        },
      },
    });

    const uploadBody = await uploadResponse.json();
    const documentId = uploadBody.data.id;

    // When: Make 50 concurrent status checks
    const startTime = Date.now();
    const statusPromises = Array(50)
      .fill(null)
      .map(() =>
        request.get(`${API_URL}/api/knowledge-base/${documentId}/status`, {
          headers: { Authorization: `Bearer ${authToken}` },
        })
      );

    const responses = await Promise.all(statusPromises);
    const totalTime = Date.now() - startTime;

    // Then: All requests should succeed
    const successCount = responses.filter((r) => r.status() === 200).length;
    expect(successCount).toBe(50);

    // And: Complete in reasonable time (<10s for 50 requests)
    expect(totalTime).toBeLessThan(10000);

    console.log(`✅ 50 concurrent status checks completed in ${totalTime}ms`);

    cleanup(testFile);
  });

  test('[P3] should handle pagination with large dataset', async ({ request }) => {
    // When: Request page 1 with limit 100
    const startTime = Date.now();
    const response = await request.get(
      `${API_URL}/api/knowledge-base/documents?page=1&limit=100`,
      {
        headers: { Authorization: `Bearer ${authToken}` },
      }
    );
    const retrievalTime = Date.now() - startTime;

    // Then: Should complete in <1s
    expect(response.status()).toBe(200);
    expect(retrievalTime).toBeLessThan(1000);

    const body = await response.json();
    expect(Array.isArray(body.data)).toBe(true);
    expect(body.data.length).toBeLessThanOrEqual(100);

    console.log(`✅ Large pagination query completed in ${retrievalTime}ms`);
  });

  test('[P3] should maintain performance under sustained load', async ({ request }) => {
    // Given: Sustained load for 30 seconds
    const testDuration = 30000;
    const requestInterval = 500; // Request every 500ms
    const startTime = Date.now();
    const responseTimes: number[] = [];

    // When: Make requests for 30 seconds
    while (Date.now() - startTime < testDuration) {
      const reqStart = Date.now();
      const response = await request.get(`${API_URL}/api/knowledge-base/documents`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      const reqTime = Date.now() - reqStart;

      expect(response.status()).toBe(200);
      responseTimes.push(reqTime);

      await new Promise((resolve) => setTimeout(resolve, requestInterval));
    }

    // Then: Average response time should be acceptable (<500ms)
    const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length;
    const maxResponseTime = Math.max(...responseTimes);
    const minResponseTime = Math.min(...responseTimes);

    expect(avgResponseTime).toBeLessThan(500);

    console.log(`✅ Sustained load test results:`);
    console.log(`   - Total requests: ${responseTimes.length}`);
    console.log(`   - Average response time: ${avgResponseTime.toFixed(2)}ms`);
    console.log(`   - Min response time: ${minResponseTime}ms`);
    console.log(`   - Max response time: ${maxResponseTime}ms`);
  });

  test('[P3] should handle rapid upload-delete cycles', async ({ request }) => {
    // Given: 5 rapid upload-delete cycles
    const cycles = 5;
    const times: number[] = [];

    for (let i = 0; i < cycles; i++) {
      // Upload
      const testFile = createDocumentOfSize(50);
      const fileBuffer = fs.readFileSync(testFile);

      const uploadStart = Date.now();
      const uploadResponse = await request.post(`${API_URL}/api/knowledge-base/upload`, {
        headers: { Authorization: `Bearer ${authToken}` },
        multipart: {
          file: {
            name: `rapid-cycle-${i}.txt`,
            mimeType: 'text/plain',
            buffer: fileBuffer,
          },
        },
      });

      const uploadBody = await uploadResponse.json();
      const documentId = uploadBody.data.id;

      // Delete (if endpoint exists)
      const deleteResponse = await request.delete(
        `${API_URL}/api/knowledge-base/${documentId}`,
        {
          headers: { Authorization: `Bearer ${authToken}` },
        }
      );

      const cycleTime = Date.now() - uploadStart;
      times.push(cycleTime);

      cleanup(testFile);

      // Accept either 200 (deleted) or 404 (endpoint not implemented)
      expect([200, 404]).toContain(deleteResponse.status());
    }

    const avgCycleTime = times.reduce((a, b) => a + b, 0) / times.length;
    console.log(`✅ Rapid upload-delete cycles:`);
    console.log(`   - Cycles completed: ${cycles}`);
    console.log(`   - Average cycle time: ${avgCycleTime.toFixed(2)}ms`);
  });

  test('[P3] should handle mixed workload (reads + writes)', async ({ request }) => {
    // Given: Mixed read/write operations
    const operations = 20;
    const promises: Promise<any>[] = [];

    // When: Execute mixed workload
    for (let i = 0; i < operations; i++) {
      if (i % 3 === 0) {
        // Write operation (upload)
        const testFile = createDocumentOfSize(20);
        const fileBuffer = fs.readFileSync(testFile);

        promises.push(
          request
            .post(`${API_URL}/api/knowledge-base/upload`, {
              headers: { Authorization: `Bearer ${authToken}` },
              multipart: {
                file: {
                  name: `mixed-workload-${i}.txt`,
                  mimeType: 'text/plain',
                  buffer: fileBuffer,
                },
              },
            })
            .then((r) => {
              cleanup(testFile);
              return r;
            })
        );
      } else {
        // Read operation (list)
        promises.push(
          request.get(`${API_URL}/api/knowledge-base/documents`, {
            headers: { Authorization: `Bearer ${authToken}` },
          })
        );
      }
    }

    const startTime = Date.now();
    const responses = await Promise.all(promises);
    const totalTime = Date.now() - startTime;

    // Then: All operations should succeed
    const successCount = responses.filter((r) => r.status() === 200).length;
    expect(successCount).toBe(operations);

    // And: Complete in reasonable time (<15s)
    expect(totalTime).toBeLessThan(15000);

    console.log(`✅ Mixed workload test:`);
    console.log(`   - Total operations: ${operations}`);
    console.log(`   - Success rate: ${successCount}/${operations}`);
    console.log(`   - Total time: ${totalTime}ms`);
  });
});
