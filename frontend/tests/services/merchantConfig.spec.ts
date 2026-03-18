/**
 * Merchant Configuration Service Tests
 *
 * Unit tests for merchant configuration API
 * Story 1.10: Bot Personality Configuration
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  merchantConfigApi,
  PersonalityConfigError,
  PersonalityErrorCode,
  type PersonalityConfigResponse,
  type PersonalityConfigUpdateRequest,
} from './merchantConfig';
import { apiClient } from './api';

// Mock the apiClient
vi.mock('./api', () => ({
  apiClient: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}));

describe('merchantConfigApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getPersonalityConfig', () => {
    it('should fetch personality configuration', async () => {
      const mockConfig: PersonalityConfigResponse = {
        personality: 'friendly',
        custom_greeting: 'Welcome to our shop!',
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockConfig });

      const result = await merchantConfigApi.getPersonalityConfig();

      expect(result).toEqual(mockConfig);
      expect(apiClient.get).toHaveBeenCalledWith('/api/merchant/personality');
    });

    it('should fetch configuration with null custom greeting', async () => {
      const mockConfig: PersonalityConfigResponse = {
        personality: 'professional',
        custom_greeting: null,
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockConfig });

      const result = await merchantConfigApi.getPersonalityConfig();

      expect(result.custom_greeting).toBeNull();
      expect(result.personality).toBe('professional');
    });

    it('should fetch enthusiastic personality configuration', async () => {
      const mockConfig: PersonalityConfigResponse = {
        personality: 'enthusiastic',
        custom_greeting: 'Super excited to help!',
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockConfig });

      const result = await merchantConfigApi.getPersonalityConfig();

      expect(result.personality).toBe('enthusiastic');
    });

    it('should throw PersonalityConfigError on network failure', async () => {
      const error = new Error('Network error');
      vi.mocked(apiClient.get).mockRejectedValueOnce(error);

      await expect(merchantConfigApi.getPersonalityConfig()).rejects.toThrow(
        PersonalityConfigError
      );
    });

    it('should throw PersonalityConfigError with status code', async () => {
      const error = new Error('Unauthorized');
      (error as any).status = 401;
      vi.mocked(apiClient.get).mockRejectedValueOnce(error);

      try {
        await merchantConfigApi.getPersonalityConfig();
        expect.fail('Should have thrown PersonalityConfigError');
      } catch (err) {
        expect(err).toBeInstanceOf(PersonalityConfigError);
        expect((err as PersonalityConfigError).status).toBe(401);
      }
    });

    it('should handle non-Error errors', async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce('Unknown error');

      await expect(merchantConfigApi.getPersonalityConfig()).rejects.toThrow(
        PersonalityConfigError
      );
    });
  });

  describe('updatePersonalityConfig', () => {
    it('should update personality only', async () => {
      const mockConfig: PersonalityConfigResponse = {
        personality: 'professional',
        custom_greeting: null,
      };

      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockConfig });

      const update: PersonalityConfigUpdateRequest = {
        personality: 'professional',
      };

      const result = await merchantConfigApi.updatePersonalityConfig(update);

      expect(result).toEqual(mockConfig);
      expect(apiClient.patch).toHaveBeenCalledWith(
        '/api/merchant/personality',
        update
      );
    });

    it('should update custom greeting only', async () => {
      const mockConfig: PersonalityConfigResponse = {
        personality: 'friendly',
        custom_greeting: 'Hello and welcome!',
      };

      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockConfig });

      const update: PersonalityConfigUpdateRequest = {
        custom_greeting: 'Hello and welcome!',
      };

      const result = await merchantConfigApi.updatePersonalityConfig(update);

      expect(result.custom_greeting).toBe('Hello and welcome!');
      expect(apiClient.patch).toHaveBeenCalledWith(
        '/api/merchant/personality',
        update
      );
    });

    it('should update both personality and custom greeting', async () => {
      const mockConfig: PersonalityConfigResponse = {
        personality: 'enthusiastic',
        custom_greeting: 'Woohoo! Welcome!',
      };

      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockConfig });

      const update: PersonalityConfigUpdateRequest = {
        personality: 'enthusiastic',
        custom_greeting: 'Woohoo! Welcome!',
      };

      const result = await merchantConfigApi.updatePersonalityConfig(update);

      expect(result.personality).toBe('enthusiastic');
      expect(result.custom_greeting).toBe('Woohoo! Welcome!');
    });

    it('should clear custom greeting by setting to null', async () => {
      const mockConfig: PersonalityConfigResponse = {
        personality: 'professional',
        custom_greeting: null,
      };

      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockConfig });

      const update: PersonalityConfigUpdateRequest = {
        custom_greeting: null,
      };

      const result = await merchantConfigApi.updatePersonalityConfig(update);

      expect(result.custom_greeting).toBeNull();
    });

    it('should handle empty string as null for greeting', async () => {
      const mockConfig: PersonalityConfigResponse = {
        personality: 'friendly',
        custom_greeting: null,
      };

      vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: mockConfig });

      const update: PersonalityConfigUpdateRequest = {
        custom_greeting: '',
      };

      const result = await merchantConfigApi.updatePersonalityConfig(update);

      // Backend handles empty string as null
      expect(apiClient.patch).toHaveBeenCalledWith(
        '/api/merchant/personality',
        update
      );
    });

    it('should throw PersonalityConfigError on failure', async () => {
      const error = new Error('Update failed');
      vi.mocked(apiClient.patch).mockRejectedValueOnce(error);

      await expect(
        merchantConfigApi.updatePersonalityConfig({ personality: 'friendly' })
      ).rejects.toThrow(PersonalityConfigError);
    });

    it('should extract error code from error response', async () => {
      const error = new Error('Invalid personality');
      (error as any).details = {
        error_code: PersonalityErrorCode.INVALID_PERSONALITY,
      };
      vi.mocked(apiClient.patch).mockRejectedValueOnce(error);

      try {
        await merchantConfigApi.updatePersonalityConfig({
          personality: 'invalid' as any,
        });
        expect.fail('Should have thrown PersonalityConfigError');
      } catch (err) {
        expect(err).toBeInstanceOf(PersonalityConfigError);
        expect((err as PersonalityConfigError).code).toBe(
          PersonalityErrorCode.INVALID_PERSONALITY
        );
      }
    });

    it('should handle greeting too long error', async () => {
      const error = new Error('Greeting exceeds maximum length');
      (error as any).details = {
        error_code: PersonalityErrorCode.GREETING_TOO_LONG,
      };
      (error as any).status = 400;
      vi.mocked(apiClient.patch).mockRejectedValueOnce(error);

      try {
        await merchantConfigApi.updatePersonalityConfig({
          custom_greeting: 'a'.repeat(600),
        });
        expect.fail('Should have thrown PersonalityConfigError');
      } catch (err) {
        expect(err).toBeInstanceOf(PersonalityConfigError);
        expect((err as PersonalityConfigError).code).toBe(
          PersonalityErrorCode.GREETING_TOO_LONG
        );
        expect((err as PersonalityConfigError).status).toBe(400);
      }
    });

    it('should handle save failed error', async () => {
      const error = new Error('Failed to save configuration');
      (error as any).details = {
        error_code: PersonalityErrorCode.SAVE_FAILED,
      };
      vi.mocked(apiClient.patch).mockRejectedValueOnce(error);

      try {
        await merchantConfigApi.updatePersonalityConfig({
          personality: 'professional',
        });
        expect.fail('Should have thrown PersonalityConfigError');
      } catch (err) {
        expect(err).toBeInstanceOf(PersonalityConfigError);
        expect((err as PersonalityConfigError).code).toBe(
          PersonalityErrorCode.SAVE_FAILED
        );
      }
    });
  });
});

describe('PersonalityConfigError', () => {
  it('should create error with message', () => {
    const error = new PersonalityConfigError('Test error');

    expect(error.message).toBe('Test error');
    expect(error.name).toBe('PersonalityConfigError');
    expect(error.code).toBeUndefined();
    expect(error.status).toBeUndefined();
  });

  it('should create error with code', () => {
    const error = new PersonalityConfigError(
      'Invalid personality',
      PersonalityErrorCode.INVALID_PERSONALITY
    );

    expect(error.code).toBe(PersonalityErrorCode.INVALID_PERSONALITY);
  });

  it('should create error with status', () => {
    const error = new PersonalityConfigError(
      'Unauthorized',
      undefined,
      401
    );

    expect(error.status).toBe(401);
  });

  it('should create error with all parameters', () => {
    const error = new PersonalityConfigError(
      'Greeting too long',
      PersonalityErrorCode.GREETING_TOO_LONG,
      400
    );

    expect(error.message).toBe('Greeting too long');
    expect(error.code).toBe(PersonalityErrorCode.GREETING_TOO_LONG);
    expect(error.status).toBe(400);
  });
});

describe('PersonalityErrorCode', () => {
  it('should have correct error code values', () => {
    expect(PersonalityErrorCode.INVALID_PERSONALITY).toBe(4000);
    expect(PersonalityErrorCode.GREETING_TOO_LONG).toBe(4001);
    expect(PersonalityErrorCode.SAVE_FAILED).toBe(4002);
  });
});
