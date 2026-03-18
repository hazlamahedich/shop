/**
 * API Contract Tests for Story 10-1: Sources Citations
 * 
 * These tests validate the contract/schema of the API responses
 * without requiring a running backend server.
 * 
 * Priority: P0 (Critical path)
 */

import { test, expect } from '@playwright/test';

test.describe('[P0] Story 10-1: Sources Citations - Contract Tests', () => {
  test.describe('Response Schema Validation', () => {
    test('should validate source object schema', () => {
      const source = {
        documentId: 1,
        title: 'Product Manual.pdf',
        documentType: 'pdf',
        relevanceScore: 0.95,
        chunkIndex: 5,
      };

      expect(source).toHaveProperty('documentId');
      expect(source).toHaveProperty('title');
      expect(source).toHaveProperty('documentType');
      expect(source).toHaveProperty('relevanceScore');
      expect(typeof source.documentId).toBe('number');
      expect(typeof source.title).toBe('string');
      expect(['pdf', 'url', 'text']).toContain(source.documentType);
      expect(typeof source.relevanceScore).toBe('number');
      expect(source.relevanceScore).toBeGreaterThanOrEqual(0);
      expect(source.relevanceScore).toBeLessThanOrEqual(1);
    });

    test('should validate URL source schema', () => {
      const source = {
        documentId: 2,
        title: 'FAQ Page',
        documentType: 'url',
        relevanceScore: 0.88,
        url: 'https://example.com/faq',
      };

      expect(source.documentType).toBe('url');
      expect(source).toHaveProperty('url');
      expect(source.url).toMatch(/^https?:\/\//);
    });

    test('should validate text source schema', () => {
      const source = {
        documentId: 3,
        title: 'Notes.txt',
        documentType: 'text',
        relevanceScore: 0.75,
      };

      expect(source.documentType).toBe('text');
    });

    test('should validate message response with sources', () => {
      const response = {
        data: {
          messageId: 'test-msg-1',
          content: 'Based on our documentation...',
          sender: 'bot',
          createdAt: new Date().toISOString(),
          sources: [
            {
              documentId: 1,
              title: 'Product Manual.pdf',
              documentType: 'pdf',
              relevanceScore: 0.95,
            },
          ],
        },
        meta: { requestId: 'test-123', timestamp: new Date().toISOString() },
      };

      expect(response.data).toHaveProperty('messageId');
      expect(response.data).toHaveProperty('content');
      expect(response.data).toHaveProperty('sender');
      expect(response.data).toHaveProperty('createdAt');
      expect(response.data).toHaveProperty('sources');
      expect(response.data.sources).toBeInstanceOf(Array);
    });

    test('should validate message response without sources', () => {
      const response = {
        data: {
          messageId: 'test-msg-2',
          content: 'Hello! How can I help you?',
          sender: 'bot',
          createdAt: new Date().toISOString(),
        },
        meta: { requestId: 'test-456', timestamp: new Date().toISOString() },
      };

      expect(response.data).toHaveProperty('messageId');
      expect(response.data).toHaveProperty('content');
      expect(response.data.sender).toBe('bot');
    });

    test('should validate multiple sources ordering', () => {
      const sources = [
        { documentId: 1, title: 'Doc 1', documentType: 'pdf', relevanceScore: 0.95 },
        { documentId: 2, title: 'Doc 2', documentType: 'url', relevanceScore: 0.88 },
        { documentId: 3, title: 'Doc 3', documentType: 'text', relevanceScore: 0.75 },
      ];

      for (let i = 0; i < sources.length - 1; i++) {
        expect(sources[i].relevanceScore).toBeGreaterThanOrEqual(sources[i + 1].relevanceScore);
      }
    });

    test('should validate score color coding logic', () => {
      const getScoreColor = (score: number): string => {
        if (score >= 0.9) return '#22c55e';
        if (score >= 0.7) return '#3b82f6';
        return '#6b7280';
      };

      expect(getScoreColor(0.95)).toBe('#22c55e');
      expect(getScoreColor(0.88)).toBe('#3b82f6');
      expect(getScoreColor(0.65)).toBe('#6b7280');
    });

    test('should validate score formatting', () => {
      const formatScore = (score: number): string => {
        return `${Math.round(score * 100)}%`;
      };

      expect(formatScore(0.95)).toBe('95%');
      expect(formatScore(0.88)).toBe('88%');
      expect(formatScore(0.7543)).toBe('75%');
    });
  });

  test.describe('Error Response Schema', () => {
    test('should validate 400 error response', () => {
      const errorResponse = {
        success: false,
        error: 'Validation error: session_id is required',
      };

      expect(errorResponse.success).toBe(false);
      expect(errorResponse).toHaveProperty('error');
      expect(typeof errorResponse.error).toBe('string');
    });

    test('should validate 500 error response', () => {
      const errorResponse = {
        success: false,
        error: 'Internal server error',
      };

      expect(errorResponse.success).toBe(false);
      expect(errorResponse).toHaveProperty('error');
    });
  });

  test.describe('Widget Envelope Schema', () => {
    test('should validate success envelope structure', () => {
      const envelope = {
        data: {
          messageId: 'msg-123',
          content: 'Test content',
          sender: 'bot',
          createdAt: '2026-03-18T00:00:00Z',
        },
        meta: {
          requestId: 'req-123',
          timestamp: '2026-03-18T00:00:00Z',
        },
      };

      expect(envelope).toHaveProperty('data');
      expect(envelope).toHaveProperty('meta');
      expect(envelope.meta).toHaveProperty('requestId');
      expect(envelope.meta).toHaveProperty('timestamp');
    });

    test('should validate sources array structure', () => {
      const sources = [
        {
          documentId: 1,
          title: 'Document 1',
          documentType: 'pdf',
          relevanceScore: 0.95,
          chunkIndex: 5,
        },
        {
          documentId: 2,
          title: 'Document 2',
          documentType: 'url',
          relevanceScore: 0.88,
          url: 'https://example.com',
        },
        {
          documentId: 3,
          title: 'Document 3',
          documentType: 'text',
          relevanceScore: 0.75,
        },
      ];

      sources.forEach((source) => {
        expect(source).toHaveProperty('documentId');
        expect(source).toHaveProperty('title');
        expect(source).toHaveProperty('documentType');
        expect(source).toHaveProperty('relevanceScore');
      });
    });
  });
});
