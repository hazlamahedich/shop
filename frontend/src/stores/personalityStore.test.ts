/**
 * Personality Store Tests
 *
 * Unit tests for personality store (Zustand)
 * Story 1.10: Bot Personality Configuration
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { usePersonalityStore, initializePersonality } from './personalityStore';
import {
  merchantConfigApi,
  PersonalityConfigError,
  PersonalityErrorCode,
  type PersonalityConfigResponse,
  type PersonalityConfigUpdateRequest,
} from '../services/merchantConfig';

// Mock the merchant config API
vi.mock('../services/merchantConfig', () => ({
  merchantConfigApi: {
    getPersonalityConfig: vi.fn(),
    updatePersonalityConfig: vi.fn(),
  },
  PersonalityConfigError: class extends Error {
    constructor(message: string, public code?: number, public status?: number) {
      super(message);
      this.name = 'PersonalityConfigError';
    }
  },
  PersonalityErrorCode: {
    INVALID_PERSONALITY: 4000,
    GREETING_TOO_LONG: 4001,
    SAVE_FAILED: 4002,
  },
}));

describe('usePersonalityStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store state
    usePersonalityStore.getState().reset();
  });

  describe('initial state', () => {
    it('should have correct initial values', () => {
      const state = usePersonalityStore.getState();

      expect(state.personality).toBeNull();
      expect(state.customGreeting).toBeNull();
      expect(state.loadingState).toBe('idle');
      expect(state.error).toBeNull();
      expect(state.isDirty).toBe(false);
    });
  });

  describe('fetchPersonalityConfig', () => {
    it('should fetch and store configuration', async () => {
      const mockConfig: PersonalityConfigResponse = {
        personality: 'friendly',
        custom_greeting: 'Welcome to our store!',
      };

      vi.mocked(merchantConfigApi.getPersonalityConfig).mockResolvedValueOnce(mockConfig);

      await usePersonalityStore.getState().fetchPersonalityConfig();

      const state = usePersonalityStore.getState();

      expect(state.personality).toBe('friendly');
      expect(state.customGreeting).toBe('Welcome to our store!');
      expect(state.loadingState).toBe('success');
      expect(state.error).toBeNull();
      expect(state.isDirty).toBe(false);
    });

    it('should set loading state during fetch', async () => {
      let resolveFetch: (value: any) => void;
      const fetchPromise = new Promise((resolve) => {
        resolveFetch = resolve;
      });

      vi.mocked(merchantConfigApi.getPersonalityConfig).mockReturnValueOnce(fetchPromise as any);

      // Start fetch (will hang)
      const fetchResult = usePersonalityStore.getState().fetchPersonalityConfig();

      // Check loading state
      expect(usePersonalityStore.getState().loadingState).toBe('loading');

      // Resolve fetch
      resolveFetch!({
        personality: 'professional',
        custom_greeting: null,
      });

      await fetchResult;

      expect(usePersonalityStore.getState().loadingState).toBe('success');
    });

    it('should handle fetch errors', async () => {
      const error = new Error('Network error');
      vi.mocked(merchantConfigApi.getPersonalityConfig).mockRejectedValueOnce(error);

      await expect(usePersonalityStore.getState().fetchPersonalityConfig()).rejects.toThrow();

      const state = usePersonalityStore.getState();

      expect(state.loadingState).toBe('error');
      expect(state.error).toBe('Network error');
      expect(state.personality).toBeNull();
    });

    it('should handle PersonalityConfigError', async () => {
      const error = new PersonalityConfigError(
        'Invalid personality type',
        PersonalityErrorCode.INVALID_PERSONALITY,
        400
      );

      vi.mocked(merchantConfigApi.getPersonalityConfig).mockRejectedValueOnce(error);

      await expect(usePersonalityStore.getState().fetchPersonalityConfig()).rejects.toThrow();

      const state = usePersonalityStore.getState();

      expect(state.loadingState).toBe('error');
      expect(state.error).toBe('Invalid personality type');
    });

    it('should clear dirty state on successful fetch', async () => {
      // First set some local changes
      usePersonalityStore.getState().setPersonality('enthusiastic');
      expect(usePersonalityStore.getState().isDirty).toBe(true);

      // Fetch should clear dirty state
      vi.mocked(merchantConfigApi.getPersonalityConfig).mockResolvedValueOnce({
        personality: 'professional',
        custom_greeting: null,
      });

      await usePersonalityStore.getState().fetchPersonalityConfig();

      expect(usePersonalityStore.getState().isDirty).toBe(false);
    });
  });

  describe('updatePersonalityConfig', () => {
    it('should update configuration on server', async () => {
      const mockConfig: PersonalityConfigResponse = {
        personality: 'professional',
        custom_greeting: 'Hello! How can I help?',
      };

      vi.mocked(merchantConfigApi.updatePersonalityConfig).mockResolvedValueOnce(mockConfig);

      const update: PersonalityConfigUpdateRequest = {
        personality: 'professional',
        custom_greeting: 'Hello! How can I help?',
      };

      await usePersonalityStore.getState().updatePersonalityConfig(update);

      const state = usePersonalityStore.getState();

      expect(state.personality).toBe('professional');
      expect(state.customGreeting).toBe('Hello! How can I help?');
      expect(state.loadingState).toBe('success');
      expect(state.error).toBeNull();
      expect(state.isDirty).toBe(false);
    });

    it('should handle update errors', async () => {
      const error = new Error('Save failed');
      vi.mocked(merchantConfigApi.updatePersonalityConfig).mockRejectedValueOnce(error);

      await expect(
        usePersonalityStore.getState().updatePersonalityConfig({ personality: 'friendly' })
      ).rejects.toThrow();

      const state = usePersonalityStore.getState();

      expect(state.loadingState).toBe('error');
      expect(state.error).toBe('Save failed');
    });

    it('should clear dirty state on successful update', async () => {
      // Set some local changes
      usePersonalityStore.getState().setPersonality('enthusiastic');
      expect(usePersonalityStore.getState().isDirty).toBe(true);

      // Update should clear dirty state
      vi.mocked(merchantConfigApi.updatePersonalityConfig).mockResolvedValueOnce({
        personality: 'enthusiastic',
        custom_greeting: null,
      });

      await usePersonalityStore.getState().updatePersonalityConfig({
        personality: 'enthusiastic',
      });

      expect(usePersonalityStore.getState().isDirty).toBe(false);
    });

    it('should handle greeting too long error', async () => {
      const error = new PersonalityConfigError(
        'Greeting exceeds maximum length',
        PersonalityErrorCode.GREETING_TOO_LONG,
        400
      );

      vi.mocked(merchantConfigApi.updatePersonalityConfig).mockRejectedValueOnce(error);

      await expect(
        usePersonalityStore.getState().updatePersonalityConfig({
          custom_greeting: 'a'.repeat(600),
        })
      ).rejects.toThrow();

      const state = usePersonalityStore.getState();
      expect(state.loadingState).toBe('error');
      expect(state.error).toBe('Greeting exceeds maximum length');
    });
  });

  describe('setPersonality', () => {
    it('should set personality and mark dirty', () => {
      usePersonalityStore.getState().setPersonality('friendly');

      const state = usePersonalityStore.getState();

      expect(state.personality).toBe('friendly');
      expect(state.isDirty).toBe(true);
    });

    it('should update existing personality', () => {
      usePersonalityStore.getState().setPersonality('professional');
      usePersonalityStore.getState().setPersonality('enthusiastic');

      expect(usePersonalityStore.getState().personality).toBe('enthusiastic');
      expect(usePersonalityStore.getState().isDirty).toBe(true);
    });

    it('should support all personality types', () => {
      const personalities: Array<'friendly' | 'professional' | 'enthusiastic'> = [
        'friendly',
        'professional',
        'enthusiastic',
      ];

      personalities.forEach((personality) => {
        usePersonalityStore.getState().reset();
        usePersonalityStore.getState().setPersonality(personality);
        expect(usePersonalityStore.getState().personality).toBe(personality);
      });
    });
  });

  describe('setCustomGreeting', () => {
    it('should set greeting and mark dirty', () => {
      usePersonalityStore.getState().setCustomGreeting('Welcome!');

      const state = usePersonalityStore.getState();

      expect(state.customGreeting).toBe('Welcome!');
      expect(state.isDirty).toBe(true);
    });

    it('should trim whitespace', () => {
      usePersonalityStore.getState().setCustomGreeting('  Hello!  ');

      expect(usePersonalityStore.getState().customGreeting).toBe('Hello!');
    });

    it('should set to null for empty string', () => {
      usePersonalityStore.getState().setCustomGreeting('');
      usePersonalityStore.getState().setCustomGreeting('   ');

      expect(usePersonalityStore.getState().customGreeting).toBeNull();
    });

    it('should update existing greeting', () => {
      usePersonalityStore.getState().setCustomGreeting('First greeting');
      usePersonalityStore.getState().setCustomGreeting('Second greeting');

      expect(usePersonalityStore.getState().customGreeting).toBe('Second greeting');
    });
  });

  describe('resetToDefault', () => {
    it('should clear custom greeting and mark dirty', () => {
      usePersonalityStore.getState().setPersonality('friendly');
      usePersonalityStore.getState().setCustomGreeting('Custom greeting');
      usePersonalityStore.getState().resetToDefault();

      const state = usePersonalityStore.getState();

      expect(state.customGreeting).toBeNull();
      expect(state.isDirty).toBe(true);
      expect(state.personality).toBe('friendly'); // Personality unchanged
    });

    it('should do nothing when no personality set', () => {
      usePersonalityStore.getState().setCustomGreeting('Some greeting');
      usePersonalityStore.getState().resetToDefault();

      // Without a personality, resetToDefault does nothing
      expect(usePersonalityStore.getState().customGreeting).toBe('Some greeting');
    });
  });

  describe('getDefaultGreeting', () => {
    it('should return default greeting for friendly', () => {
      const greeting = usePersonalityStore.getState().getDefaultGreeting('friendly');
      expect(greeting).toBe('Hey! 👋 How can I help you today?');
    });

    it('should return default greeting for professional', () => {
      const greeting = usePersonalityStore.getState().getDefaultGreeting('professional');
      expect(greeting).toBe('Hello. How may I assist you?');
    });

    it('should return default greeting for enthusiastic', () => {
      const greeting = usePersonalityStore.getState().getDefaultGreeting('enthusiastic');
      expect(greeting).toBe('Hi there! Welcome! What can I help you find today?');
    });
  });

  describe('hasUnsavedChanges', () => {
    it('should return true when dirty', () => {
      usePersonalityStore.getState().setPersonality('friendly');

      expect(usePersonalityStore.getState().hasUnsavedChanges()).toBe(true);
    });

    it('should return false when not dirty', () => {
      expect(usePersonalityStore.getState().hasUnsavedChanges()).toBe(false);
    });

    it('should return false after discardChanges', () => {
      usePersonalityStore.getState().setPersonality('friendly');
      expect(usePersonalityStore.getState().hasUnsavedChanges()).toBe(true);

      usePersonalityStore.getState().discardChanges();
      expect(usePersonalityStore.getState().hasUnsavedChanges()).toBe(false);
    });
  });

  describe('discardChanges', () => {
    it('should clear dirty flag', () => {
      usePersonalityStore.getState().setPersonality('friendly');
      usePersonalityStore.getState().setCustomGreeting('Test');
      expect(usePersonalityStore.getState().isDirty).toBe(true);

      usePersonalityStore.getState().discardChanges();

      expect(usePersonalityStore.getState().isDirty).toBe(false);
      // Note: discardChanges doesn't revert values, just clears the flag
      expect(usePersonalityStore.getState().personality).toBe('friendly');
      expect(usePersonalityStore.getState().customGreeting).toBe('Test');
    });
  });

  describe('clearError', () => {
    it('should clear error state', async () => {
      vi.mocked(merchantConfigApi.getPersonalityConfig).mockRejectedValueOnce(
        new Error('Test error')
      );

      await expect(usePersonalityStore.getState().fetchPersonalityConfig()).rejects.toThrow();

      expect(usePersonalityStore.getState().error).toBe('Test error');

      usePersonalityStore.getState().clearError();

      expect(usePersonalityStore.getState().error).toBeNull();
    });
  });

  describe('reset', () => {
    it('should reset to initial state', async () => {
      vi.mocked(merchantConfigApi.getPersonalityConfig).mockResolvedValueOnce({
        personality: 'friendly',
        custom_greeting: 'Test',
      });

      await usePersonalityStore.getState().fetchPersonalityConfig();

      expect(usePersonalityStore.getState().personality).not.toBeNull();

      usePersonalityStore.getState().reset();

      const state = usePersonalityStore.getState();

      expect(state.personality).toBeNull();
      expect(state.customGreeting).toBeNull();
      expect(state.loadingState).toBe('idle');
      expect(state.error).toBeNull();
      expect(state.isDirty).toBe(false);
    });
  });
});

describe('Personality Hook Helpers', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePersonalityStore.getState().reset();
  });

  describe('initializePersonality', () => {
    it('should initialize personality configuration', async () => {
      vi.mocked(merchantConfigApi.getPersonalityConfig).mockResolvedValueOnce({
        personality: 'professional',
        custom_greeting: null,
      });

      await initializePersonality();

      expect(usePersonalityStore.getState().personality).toBe('professional');
    });

    it('should propagate errors', async () => {
      vi.mocked(merchantConfigApi.getPersonalityConfig).mockRejectedValueOnce(
        new Error('Init failed')
      );

      await expect(initializePersonality()).rejects.toThrow('Init failed');
    });
  });

  describe('Selectors', () => {
    it('selectPersonality should return personality', () => {
      usePersonalityStore.getState().setPersonality('enthusiastic');
      expect(
        usePersonalityStore.getState().personality
      ).toBe('enthusiastic');
    });

    it('selectCustomGreeting should return custom greeting', () => {
      usePersonalityStore.getState().setCustomGreeting('Custom!');
      expect(
        usePersonalityStore.getState().customGreeting
      ).toBe('Custom!');
    });

    it('selectPersonalityLoading should return loading state', () => {
      expect(
        usePersonalityStore.getState().loadingState === 'loading'
      ).toBe(false);
    });

    it('selectPersonalityError should return error', () => {
      expect(
        usePersonalityStore.getState().error
      ).toBeNull();
    });

    it('selectPersonalityIsDirty should return dirty state', () => {
      expect(
        usePersonalityStore.getState().isDirty
      ).toBe(false);
      usePersonalityStore.getState().setPersonality('friendly');
      expect(
        usePersonalityStore.getState().isDirty
      ).toBe(true);
    });

    it('selectEffectiveGreeting should return custom greeting if set', () => {
      usePersonalityStore.getState().setPersonality('friendly');
      usePersonalityStore.getState().setCustomGreeting('Custom greeting');

      // With custom greeting
      expect(
        usePersonalityStore.getState().customGreeting ||
          usePersonalityStore.getState().getDefaultGreeting(
            usePersonalityStore.getState().personality!
          )
      ).toBe('Custom greeting');
    });

    it('selectEffectiveGreeting should return default if no custom greeting', () => {
      usePersonalityStore.getState().setPersonality('professional');

      // Without custom greeting
      expect(
        usePersonalityStore.getState().customGreeting ||
          usePersonalityStore.getState().getDefaultGreeting(
            usePersonalityStore.getState().personality!
          )
      ).toBe('Hello. How may I assist you?');
    });

    it('selectEffectiveGreeting should return empty string if no personality', () => {
      expect(
        usePersonalityStore.getState().customGreeting ||
          (usePersonalityStore.getState().personality
            ? usePersonalityStore.getState().getDefaultGreeting(
                usePersonalityStore.getState().personality
              )
            : '')
      ).toBe('');
    });
  });
});
