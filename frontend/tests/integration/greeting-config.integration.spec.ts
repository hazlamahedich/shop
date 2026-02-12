/**
 * Greeting Configuration Integration Tests
 *
 * Story 1.14: Smart Greeting Templates
 *
 * Integration tests covering greeting config store operations.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useBotConfigStore } from '../../src/stores/botConfigStore';

// Types for mocked API
interface GreetingConfigResponse {
  greetingTemplate: string | null;
  useCustomGreeting: boolean;
  personality: string;
  defaultTemplate: string | null;
  availableVariables: string[];
}

describe('Greeting Configuration Integration (Story 1.14)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // Mock fetch at global level
  global.fetch = vi.fn();

  describe('Greeting config API integration', () => {
    it('should fetch and store greeting configuration', async () => {
      const mockResponse: GreetingConfigResponse = {
        greetingTemplate: 'Welcome to {business_name}!',
        useCustomGreeting: true,
        personality: 'friendly',
        defaultTemplate: "Hey there! 👋 I'm {bot_name} from {business_name}. How can I help you today?",
        availableVariables: ['bot_name', 'business_name', 'business_hours'],
      };

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      // First, set bot config (including personality)
      useBotConfigStore.setState({
        botName: 'GearBot',
        personality: 'friendly',
        customGreeting: null,
        greetingTemplate: null,
        useCustomGreeting: false,
        defaultTemplate: null,
        availableVariables: [],
        loadingState: 'idle',
        error: null,
        isDirty: false,
      });

      // Fetch greeting config - uses mocked fetch
      await act(async () => {
        await useBotConfigStore.getState().fetchGreetingConfig();
      });

      // Verify greeting-related state is updated
      const state = useBotConfigStore.getState();
      expect(state.greetingTemplate).toBe('Welcome to {business_name}!');
      expect(state.useCustomGreeting).toBe(true);
      expect(state.defaultTemplate).toBe("Hey there! 👋 I'm {bot_name} from {business_name}. How can I help you today?");
      expect(state.availableVariables).toEqual(['bot_name', 'business_name', 'business_hours']);
      expect(state.loadingState).toBe('success');
      expect(state.isDirty).toBe(false);
    });

    it('should update greeting configuration via API', async () => {
      useBotConfigStore.setState({
        botName: 'GearBot',
        personality: 'friendly',
        customGreeting: null,
        greetingTemplate: null,
        useCustomGreeting: false,
        defaultTemplate: "Default template",
        availableVariables: [],
        loadingState: 'idle',
        error: null,
        isDirty: false,
      });

      const mockResponse: GreetingConfigResponse = {
        greetingTemplate: 'Custom welcome message!!!',
        useCustomGreeting: true,
        personality: 'friendly',
        defaultTemplate: 'Default template',
        availableVariables: ['bot_name', 'business_name', 'business_hours'],
      };

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      // Update greeting config
      await act(async () => {
        await useBotConfigStore.getState().updateGreetingConfig({
          greeting_template: 'Custom welcome message!!!',
          use_custom_greeting: true,
        });
      });

      // Verify state is updated
      const state = useBotConfigStore.getState();
      expect(state.greetingTemplate).toBe('Custom welcome message!!!');
      expect(state.useCustomGreeting).toBe(true);
      expect(state.loadingState).toBe('success');
      expect(state.isDirty).toBe(false);
    });

    it('should reset greeting to default', async () => {
      useBotConfigStore.setState({
        botName: 'GearBot',
        personality: 'friendly',
        customGreeting: null,
        greetingTemplate: 'Old greeting',
        useCustomGreeting: true,
        defaultTemplate: "Hey there! 👋",
        availableVariables: ['bot_name'],
        loadingState: 'idle',
        error: null,
        isDirty: false,
      });

      const mockResponse: GreetingConfigResponse = {
        data: {
          greetingTemplate: null,
          useCustomGreeting: false,
          personality: 'friendly',
          defaultTemplate: "Hey there! 👋 I'm {bot_name} from {business_name}. How can I help you today?",
          availableVariables: ['bot_name', 'business_name', 'business_hours'],
        },
        meta: {},
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => Promise.resolve(mockResponse),
      } as Response);

      // Reset to default
      await act(async () => {
        await useBotConfigStore.getState().resetGreetingToDefault();
      });

      const state = useBotConfigStore.getState();
      expect(state.greetingTemplate).toBeNull();
      expect(state.useCustomGreeting).toBe(false);
    });

    it('should handle API errors gracefully', async () => {
      useBotConfigStore.setState({
        botName: 'GearBot',
        personality: 'friendly',
        customGreeting: null,
        greetingTemplate: null,
        useCustomGreeting: false,
        defaultTemplate: null,
        availableVariables: [],
        loadingState: 'idle',
        error: null,
        isDirty: false,
      });

      const apiError = new Error('Internal server error');
      Object.defineProperty(apiError, 'status', { value: 500, writable: true, configurable: true });
      Object.defineProperty(apiError, 'code', { value: 1000, writable: true, configurable: true });
      Object.defineProperty(apiError, 'details', { value: {
        error_code: 1000,
        message: 'Internal server error',
      }, writable: true, configurable: true });

      (global.fetch as any).mockRejectedValueOnce(apiError);

      // Attempt to fetch
      await act(async () => {
        await expect(useBotConfigStore.getState().fetchGreetingConfig()).rejects.toThrow();
      });

      const state = useBotConfigStore.getState();
      expect(state.loadingState).toBe('error');
      expect(state.error).toBeTruthy();
    });

    describe('Greeting variable substitution', () => {
      it('should include all three required variables in default template', async () => {
        const mockResponse: GreetingConfigResponse = {
          data: {
            greetingTemplate: null,
            useCustomGreeting: false,
            personality: 'friendly',
            defaultTemplate: "Hi! I'm {bot_name} from {business_name}. Hours: {business_hours}",
            availableVariables: ['bot_name', 'business_name', 'business_hours'],
          },
          meta: {},
        };

        (global.fetch as any).mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => Promise.resolve(mockResponse),
        } as Response);

        useBotConfigStore.setState({
          botName: 'GearBot',
          personality: 'friendly',
          customGreeting: null,
          greetingTemplate: null,
          useCustomGreeting: false,
          defaultTemplate: null,
          availableVariables: [],
          loadingState: 'idle',
          error: null,
          isDirty: false,
        });

        await act(async () => {
          await useBotConfigStore.getState().fetchGreetingConfig();
        });

        const state = useBotConfigStore.getState();
        expect(state.availableVariables).toEqual(['bot_name', 'business_name', 'business_hours']);
        expect(state.defaultTemplate).toContain('Hours:');
      });
    });

    describe('Character limit validation', () => {
      it('should enforce 500 character limit on greeting template', async () => {
        const longGreeting = 'a'.repeat(501);

        useBotConfigStore.setState({
          botName: 'GearBot',
          personality: 'friendly',
          customGreeting: null,
          greetingTemplate: null,
          useCustomGreeting: false,
          defaultTemplate: null,
          availableVariables: [],
          loadingState: 'idle',
          error: null,
          isDirty: false,
        });

        const validationError = new Error('Validation error');
        Object.defineProperty(validationError, 'status', { value: 422, writable: true, configurable: true });
        Object.defineProperty(validationError, 'code', { value: 3000, writable: true, configurable: true });
        Object.defineProperty(validationError, 'details', { value: {
          error_code: 3000,
          message: 'greeting_template: String must have at most 500 characters',
        }, writable: true, configurable: true });

        (global.fetch as any).mockRejectedValueOnce(validationError);

        // Try to update with long greeting
        await act(async () => {
          await expect(
            useBotConfigStore.getState().updateGreetingConfig({
              greeting_template: longGreeting,
              use_custom_greeting: true,
            })
          ).rejects.toThrow();
        });

        const state = useBotConfigStore.getState();
        expect(state.loadingState).toBe('error');
      });

      it('should accept greeting at exactly 500 characters', async () => {
        const validGreeting = 'a'.repeat(500);

        useBotConfigStore.setState({
          botName: 'GearBot',
          personality: 'friendly',
          customGreeting: null,
          greetingTemplate: null,
          useCustomGreeting: false,
          defaultTemplate: null,
          availableVariables: [],
          loadingState: 'idle',
          error: null,
          isDirty: false,
        });

        const mockResponse = {
          data: {
            greetingTemplate: validGreeting,
            useCustomGreeting: true,
            personality: 'friendly',
            defaultTemplate: 'Default',
            availableVariables: ['bot_name', 'business_name'],
          },
          meta: {},
        };

        (global.fetch as any).mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => Promise.resolve(mockResponse),
        } as Response);

        await act(async () => {
          await useBotConfigStore.getState().updateGreetingConfig({
            greeting_template: validGreeting,
            use_custom_greeting: true,
          });
        });

        const state = useBotConfigStore.getState();
        expect(state.greetingTemplate).toBe(validGreeting);
        expect(state.loadingState).toBe('success');
      });
    });

    describe('Custom greeting toggle behavior', () => {
      it('should enable custom greeting when template is provided', async () => {
        useBotConfigStore.setState({
          botName: 'GearBot',
          personality: 'friendly',
          customGreeting: null,
          greetingTemplate: null,
          useCustomGreeting: false,
          defaultTemplate: 'Default',
          availableVariables: [],
          loadingState: 'idle',
          error: null,
          isDirty: false,
        });

        const mockResponse: {
          data: {
            greetingTemplate: 'Custom message',
            useCustomGreeting: true,
            personality: 'friendly',
            defaultTemplate: 'Default template',
            availableVariables: ['bot_name', 'business_name'],
          },
          meta: {},
        };

        (global.fetch as any).mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => Promise.resolve(mockResponse),
        } as Response);

        await act(async () => {
          await useBotConfigStore.getState().updateGreetingConfig({
            greeting_template: 'Custom message',
            use_custom_greeting: true,
          });
        });

        const state = useBotConfigStore.getState();
        expect(state.useCustomGreeting).toBe(true);
        expect(state.greetingTemplate).toBe('Custom message');
      });

      it('should disable custom greeting when template is empty', async () => {
        useBotConfigStore.setState({
          botName: 'GearBot',
          personality: 'friendly',
          customGreeting: null,
          greetingTemplate: 'Old greeting',
          useCustomGreeting: true,
          defaultTemplate: 'Default',
          availableVariables: ['bot_name'],
          loadingState: 'idle',
          error: null,
          isDirty: false,
        });

        const mockResponse = {
          data: {
            greetingTemplate: null,
            useCustomGreeting: false,
            personality: 'friendly',
            defaultTemplate: 'Default template',
            availableVariables: ['bot_name'],
          },
          meta: {},
        };

        (global.fetch as any).mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => Promise.resolve(mockResponse),
        } as Response);

        await act(async () => {
          await useBotConfigStore.getState().updateGreetingConfig({
            greeting_template: '',
            use_custom_greeting: false,
          });
        });

        const state = useBotConfigStore.getState();
        expect(state.useCustomGreeting).toBe(false);
        expect(state.greetingTemplate).toBeNull();
      });
    });

    describe('Empty state handling', () => {
      it('should use fallback when no greeting configured', async () => {
        useBotConfigStore.setState({
          botName: 'GearBot',
          personality: null,
          customGreeting: null,
          greetingTemplate: null,
          useCustomGreeting: false,
          defaultTemplate: null,
          availableVariables: [],
          loadingState: 'idle',
          error: null,
          isDirty: false,
        });

        const mockResponse: GreetingConfigResponse = {
          data: {
            greetingTemplate: null,
            useCustomGreeting: false,
            personality: null,
            defaultTemplate: "Hey there! 👋 I'm {bot_name} from {business_name}.",
            availableVariables: ['bot_name', 'business_name', 'business_hours'],
          },
          meta: {},
        };

        (global.fetch as any).mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => Promise.resolve(mockResponse),
        } as Response);

        await act(async () => {
          await useBotConfigStore.getState().fetchGreetingConfig();
        });

        const state = useBotConfigStore.getState();
        expect(state.greetingTemplate).toBeNull();
        expect(state.useCustomGreeting).toBe(false);
        expect(state.defaultTemplate).toContain("Hey there");
      });
    });

    describe('Error state handling', () => {
      it('should clear error on successful operation', async () => {
        useBotConfigStore.setState({
          botName: 'GearBot',
          personality: 'friendly',
          customGreeting: null,
          greetingTemplate: null,
          useCustomGreeting: false,
          defaultTemplate: null,
          availableVariables: [],
          loadingState: 'error',
          error: 'Previous error',
          isDirty: false,
        });

        const mockResponse = {
          data: {
            greetingTemplate: 'New greeting',
            useCustomGreeting: true,
            personality: 'friendly',
            defaultTemplate: 'Default',
            availableVariables: ['bot_name'],
          },
          meta: {},
        };

        (global.fetch as any).mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => Promise.resolve(mockResponse),
        } as Response);

        await act(async () => {
          await useBotConfigStore.getState().updateGreetingConfig({
            greeting_template: 'New greeting',
            use_custom_greeting: true,
          });
        });

        const state = useBotConfigStore.getState();
        expect(state.error).toBeNull();
        expect(state.loadingState).toBe('success');
      });

      it('should handle network errors', async () => {
        useBotConfigStore.setState({
          botName: 'GearBot',
          personality: 'friendly',
          customGreeting: null,
          greetingTemplate: null,
          useCustomGreeting: false,
          defaultTemplate: null,
          availableVariables: [],
          loadingState: 'idle',
          error: null,
          isDirty: false,
        });

        const networkError = new Error('Failed to fetch');
        Object.defineProperty(networkError, 'status', { value: 0, writable: true, configurable: true });
        Object.defineProperty(networkError, 'code', { value: undefined, writable: true, configurable: true });

        (global.fetch as any).mockRejectedValueOnce(networkError);

        // Attempt to fetch
        await act(async () => {
          await expect(useBotConfigStore.getState().fetchGreetingConfig()).rejects.toThrow();
        });

        const state = useBotConfigStore.getState();
        expect(state.loadingState).toBe('error');
        expect(state.error).toBeTruthy();
      });
    });
  });
})();
