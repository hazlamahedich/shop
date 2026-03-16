import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useProactiveTriggers } from './useProactiveTriggers';
import type { ProactiveEngagementConfig } from '../types/widget';

describe('useProactiveTriggers', () => {
  const originalSessionStorage = window.sessionStorage;
  let mockStorage: Record<string, string> = {};

  beforeEach(() => {
    mockStorage = {};
    
    const mockSessionStorage = {
      getItem: vi.fn((key: string) => mockStorage[key] ?? null),
      setItem: vi.fn((key: string, value: string) => {
        mockStorage[key] = value;
      }),
      removeItem: vi.fn((key: string) => {
        delete mockStorage[key];
      }),
      clear: vi.fn(() => {
        mockStorage = {};
      }),
      get length() {
        return Object.keys(mockStorage).length;
      },
      key: vi.fn((index: number) => Object.keys(mockStorage)[index] ?? null),
    };
    
    Object.defineProperty(window, 'sessionStorage', {
      value: mockSessionStorage,
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'sessionStorage', {
      value: originalSessionStorage,
      writable: true,
      configurable: true,
    });
    vi.restoreAllMocks();
  });

  describe('initialization', () => {
    it('should return correct initial state', () => {
      const { result } = renderHook(() => useProactiveTriggers());

      expect(result.current.activeTrigger).toBeNull();
      expect(result.current.dismissedTriggers).toBeInstanceOf(Set);
      expect(result.current.isActive).toBe(false);
    });

    it('should use default config when none provided', () => {
      const { result } = renderHook(() => useProactiveTriggers());

      expect(result.current.activeTrigger).toBeNull();
    });

    it('should use provided config', () => {
      const config: ProactiveEngagementConfig = {
        enabled: true,
        triggers: [
          {
            type: 'exit_intent',
            enabled: true,
            message: 'Custom exit message',
            actions: [{ text: 'OK' }],
            cooldown: 60,
          },
        ],
      };

      const { result } = renderHook(() => useProactiveTriggers({ config }));

      expect(result.current.activeTrigger).toBeNull();
    });
  });

  describe('exit intent detection', () => {
    it('should trigger on mouseleave at viewport top', () => {
      const config: ProactiveEngagementConfig = {
        enabled: true,
        triggers: [
          {
            type: 'exit_intent',
            enabled: true,
            message: 'Test exit intent',
            actions: [{ text: 'OK' }],
            cooldown: 30,
          },
        ],
      };

      const { result } = renderHook(() => useProactiveTriggers({ config }));

      const mouseLeaveEvent = new MouseEvent('mouseleave', {
        bubbles: true,
        cancelable: true,
        clientY: -10,
      } as MouseEventInit);
      Object.defineProperty(mouseLeaveEvent, 'clientY', { value: -10, writable: false });

      act(() => {
        document.dispatchEvent(mouseLeaveEvent);
      });

      expect(result.current.activeTrigger).not.toBeNull();
      expect(result.current.activeTrigger?.type).toBe('exit_intent');
    });

    it('should not trigger when clientY > 0', () => {
      const config: ProactiveEngagementConfig = {
        enabled: true,
        triggers: [
          {
            type: 'exit_intent',
            enabled: true,
            message: 'Test exit intent',
            actions: [{ text: 'OK' }],
            cooldown: 30,
          },
        ],
      };

      const { result } = renderHook(() => useProactiveTriggers({ config }));

      const mouseLeaveEvent = new MouseEvent('mouseleave', {
        bubbles: true,
        cancelable: true,
        clientY: 50,
      } as MouseEventInit);
      Object.defineProperty(mouseLeaveEvent, 'clientY', { value: 50, writable: false });

      act(() => {
        document.dispatchEvent(mouseLeaveEvent);
      });

      expect(result.current.activeTrigger).toBeNull();
    });
  });

  describe('dismiss functionality', () => {
    it('should dismiss trigger and prevent re-firing', () => {
      const config: ProactiveEngagementConfig = {
        enabled: true,
        triggers: [
          {
            type: 'exit_intent',
            enabled: true,
            message: 'Test exit intent',
            actions: [{ text: 'OK' }],
            cooldown: 30,
          },
        ],
      };

      const { result } = renderHook(() => useProactiveTriggers({ config }));

      const mouseLeaveEvent = new MouseEvent('mouseleave', {
        bubbles: true,
        cancelable: true,
        clientY: -10,
      } as MouseEventInit);
      Object.defineProperty(mouseLeaveEvent, 'clientY', { value: -10, writable: false });

      act(() => {
        document.dispatchEvent(mouseLeaveEvent);
      });

      expect(result.current.activeTrigger).not.toBeNull();

      act(() => {
        result.current.dismissTrigger();
      });

      expect(result.current.activeTrigger).toBeNull();
      expect(result.current.dismissedTriggers.has('exit_intent')).toBe(true);
    });
  });

  describe('disabled config', () => {
    it('should not trigger when config is disabled', () => {
      const config: ProactiveEngagementConfig = {
        enabled: false,
        triggers: [
          {
            type: 'exit_intent',
            enabled: true,
            message: 'Test exit intent',
            actions: [{ text: 'OK' }],
            cooldown: 30,
          },
        ],
      };

      const { result } = renderHook(() => useProactiveTriggers({ config }));

      const mouseLeaveEvent = new MouseEvent('mouseleave', {
        bubbles: true,
        cancelable: true,
        clientY: -10,
      } as MouseEventInit);
      Object.defineProperty(mouseLeaveEvent, 'clientY', { value: -10, writable: false });

      act(() => {
        document.dispatchEvent(mouseLeaveEvent);
      });

      expect(result.current.activeTrigger).toBeNull();
    });

    it('should not trigger when individual trigger is disabled', () => {
      const config: ProactiveEngagementConfig = {
        enabled: true,
        triggers: [
          {
            type: 'exit_intent',
            enabled: false,
            message: 'Test exit intent',
            actions: [{ text: 'OK' }],
            cooldown: 30,
          },
        ],
      };

      const { result } = renderHook(() => useProactiveTriggers({ config }));

      const mouseLeaveEvent = new MouseEvent('mouseleave', {
        bubbles: true,
        cancelable: true,
        clientY: -10,
      } as MouseEventInit);
      Object.defineProperty(mouseLeaveEvent, 'clientY', { value: -10, writable: false });

      act(() => {
        document.dispatchEvent(mouseLeaveEvent);
      });

      expect(result.current.activeTrigger).toBeNull();
    });
  });
});
