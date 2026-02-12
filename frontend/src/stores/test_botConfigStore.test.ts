/**
 * Tests for Bot Config Store
 *
 * Story 1.12: Bot Naming
 *
 * Tests state management, actions, and persistence for bot configuration.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act } from 'react';
import { useBotConfigStore } from './botConfigStore';
import * as botConfigService from '../services/botConfig';

// Mock the bot config service
vi.mock('../services/botConfig', () => ({
  botConfigApi: {
    getBotConfig: vi.fn(),
    updateBotName: vi.fn(),
  },
  BotConfigError: class extends Error {
    constructor(message: string, public code?: number, public status?: number) {
      super(message);
      this.name = 'BotConfigError';
    }
  },
}));

describe('BotConfigStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useBotConfigStore.getState().reset();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useBotConfigStore.getState();

      expect(state.botName).toBeNull();
      expect(state.personality).toBeNull();
      expect(state.customGreeting).toBeNull();
      expect(state.loadingState).toBe('idle');
      expect(state.error).toBeNull();
      expect(state.isDirty).toBe(false);
    });

    it('should have no unsaved changes initially', () => {
      const state = useBotConfigStore.getState();

      expect(state.hasUnsavedChanges()).toBe(false);
    });
  });

  describe('fetchBotConfig', () => {
    it('should fetch bot config successfully', async () => {
      const mockConfig = {
        botName: 'GearBot',
        personality: 'friendly',
        customGreeting: null,
      };

      vi.mocked(botConfigService.botConfigApi.getBotConfig).mockResolvedValue(mockConfig);

      await act(async () => {
        await useBotConfigStore.getState().fetchBotConfig();
      });

      const state = useBotConfigStore.getState();
      expect(state.botName).toBe('GearBot');
      expect(state.personality).toBe('friendly');
      expect(state.customGreeting).toBeNull();
      expect(state.loadingState).toBe('success');
      expect(state.error).toBeNull();
      expect(state.isDirty).toBe(false);
    });

    it('should handle fetch error', async () => {
      vi.mocked(botConfigService.botConfigApi.getBotConfig).mockRejectedValue(
        new Error('Failed to fetch bot configuration')
      );

      await act(async () => {
        await expect(
          useBotConfigStore.getState().fetchBotConfig()
        ).rejects.toThrow();
      });

      const state = useBotConfigStore.getState();
      expect(state.loadingState).toBe('error');
      expect(state.error).toBe('Failed to fetch bot configuration');
    });
  });

  describe('updateBotName', () => {
    it('should update bot name successfully', async () => {
      const mockConfig = {
        botName: 'ShopBot',
        personality: 'professional',
        customGreeting: 'Welcome!',
      };

      vi.mocked(botConfigService.botConfigApi.updateBotName).mockResolvedValue(mockConfig);

      await act(async () => {
        await useBotConfigStore.getState().updateBotName({ bot_name: 'ShopBot' });
      });

      const state = useBotConfigStore.getState();
      expect(state.botName).toBe('ShopBot');
      expect(state.personality).toBe('professional');
      expect(state.customGreeting).toBe('Welcome!');
      expect(state.loadingState).toBe('success');
      expect(state.isDirty).toBe(false);
    });

    it('should handle update error', async () => {
      vi.mocked(botConfigService.botConfigApi.updateBotName).mockRejectedValue(
        new Error('Failed to update bot name')
      );

      await act(async () => {
        await expect(
          useBotConfigStore.getState().updateBotName({ bot_name: 'TestBot' })
        ).rejects.toThrow();
      });

      const state = useBotConfigStore.getState();
      expect(state.loadingState).toBe('error');
      expect(state.error).toBe('Failed to update bot name');
    });

    it('should call API with correct parameters', async () => {
      vi.mocked(botConfigService.botConfigApi.updateBotName).mockResolvedValue({
        botName: 'NewBot',
        personality: null,
        customGreeting: null,
      });

      await act(async () => {
        await useBotConfigStore.getState().updateBotName({ bot_name: 'NewBot' });
      });

      expect(botConfigService.botConfigApi.updateBotName).toHaveBeenCalledWith({ bot_name: 'NewBot' });
    });
  });

  describe('setBotName', () => {
    it('should set bot name locally', () => {
      act(() => {
        useBotConfigStore.getState().setBotName('MyBot');
      });

      const state = useBotConfigStore.getState();
      expect(state.botName).toBe('MyBot');
      expect(state.isDirty).toBe(true);
    });

    it('should trim whitespace from bot name', () => {
      act(() => {
        useBotConfigStore.getState().setBotName('  MyBot  ');
      });

      expect(useBotConfigStore.getState().botName).toBe('MyBot');
    });

    it('should set to null if empty string after trim', () => {
      act(() => {
        useBotConfigStore.getState().setBotName('   ');
      });

      expect(useBotConfigStore.getState().botName).toBeNull();
    });

    it('should set to null if empty string', () => {
      act(() => {
        useBotConfigStore.getState().setBotName('');
      });

      expect(useBotConfigStore.getState().botName).toBeNull();
    });

    it('should mark store as dirty when setting bot name', () => {
      expect(useBotConfigStore.getState().hasUnsavedChanges()).toBe(false);

      act(() => {
        useBotConfigStore.getState().setBotName('TestBot');
      });

      expect(useBotConfigStore.getState().hasUnsavedChanges()).toBe(true);
    });
  });

  describe('State Management', () => {
    it('should clear error when clearError is called', () => {
      useBotConfigStore.setState({ error: 'Test error' });

      act(() => {
        useBotConfigStore.getState().clearError();
      });

      expect(useBotConfigStore.getState().error).toBeNull();
    });

    it('should reset store to initial state when reset is called', () => {
      useBotConfigStore.setState({
        botName: 'TestBot',
        personality: 'friendly',
        customGreeting: 'Hello!',
        loadingState: 'success',
        error: null,
        isDirty: true,
      });

      expect(useBotConfigStore.getState().botName).toBe('TestBot');
      expect(useBotConfigStore.getState().isDirty).toBe(true);

      act(() => {
        useBotConfigStore.getState().reset();
      });

      const state = useBotConfigStore.getState();
      expect(state.botName).toBeNull();
      expect(state.personality).toBeNull();
      expect(state.customGreeting).toBeNull();
      expect(state.loadingState).toBe('idle');
      expect(state.isDirty).toBe(false);
    });

    it('should discard changes when discardChanges is called', () => {
      useBotConfigStore.setState({ isDirty: true });

      expect(useBotConfigStore.getState().hasUnsavedChanges()).toBe(true);

      act(() => {
        useBotConfigStore.getState().discardChanges();
      });

      expect(useBotConfigStore.getState().hasUnsavedChanges()).toBe(false);
    });
  });

  describe('Selectors', () => {
    it('should select bot name correctly', () => {
      useBotConfigStore.setState({ botName: 'SelectorBot' });

      const botName = useBotConfigStore.getState().botName;
      expect(botName).toBe('SelectorBot');
    });

    it('should select personality correctly', () => {
      useBotConfigStore.setState({ personality: 'professional' });

      const personality = useBotConfigStore.getState().personality;
      expect(personality).toBe('professional');
    });

    it('should select custom greeting correctly', () => {
      useBotConfigStore.setState({ customGreeting: 'Welcome!' });

      const customGreeting = useBotConfigStore.getState().customGreeting;
      expect(customGreeting).toBe('Welcome!');
    });

    it('should select loading state correctly', () => {
      useBotConfigStore.setState({ loadingState: 'loading' });

      const isLoading = useBotConfigStore.getState().loadingState === 'loading';
      expect(isLoading).toBe(true);
    });

    it('should select error correctly', () => {
      useBotConfigStore.setState({ error: 'Test error' });

      const error = useBotConfigStore.getState().error;
      expect(error).toBe('Test error');
    });

    it('should select dirty state correctly', () => {
      useBotConfigStore.setState({ isDirty: true });

      const isDirty = useBotConfigStore.getState().isDirty;
      expect(isDirty).toBe(true);
    });
  });

  describe('Helper Functions', () => {
    describe('initializeBotConfig', () => {
      it('should initialize bot config from API', async () => {
        vi.mocked(botConfigService.botConfigApi.getBotConfig).mockResolvedValue({
          botName: 'InitBot',
          personality: 'friendly',
          customGreeting: null,
        });

        const { initializeBotConfig } = await import('./botConfigStore');

        await act(async () => {
          await initializeBotConfig();
        });

        const state = useBotConfigStore.getState();
        expect(state.botName).toBe('InitBot');
      });

      it('should handle initialization error', async () => {
        vi.mocked(botConfigService.botConfigApi.getBotConfig).mockRejectedValue(
          new Error('Network error')
        );

        const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
        const { initializeBotConfig } = await import('./botConfigStore');

        await act(async () => {
          await expect(initializeBotConfig()).rejects.toThrow();
        });

        consoleSpy.mockRestore();
      });
    });
  });
});
