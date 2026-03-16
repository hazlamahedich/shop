import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useProactiveTriggers } from './useProactiveTriggers';
import type { ProactiveEngagementConfig } from '../types/widget';

describe('debug test', () => {
  const storage: Record<string, string> = {};

  beforeEach(() => {
    Object.keys(storage).forEach(key => delete storage[key]);
    vi.spyOn(window.sessionStorage, 'getItem').mockImplementation((key: string) => {
      console.log('getItem called:', key, '=>', storage[key] ?? null);
      return storage[key] ?? null;
    });
    vi.spyOn(window.sessionStorage, 'setItem').mockImplementation((key: string, value: string) => {
      console.log('setItem called:', key, '=>', value);
      storage[key] = value;
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('test 1', () => {
    const config: ProactiveEngagementConfig = {
      enabled: true,
      triggers: [{ type: 'exit_intent', enabled: true, message: 'Test', actions: [{ text: 'OK' }], cooldown: 30 }],
    };

    const { result } = renderHook(() => useProactiveTriggers({ config }));

    const event = new MouseEvent('mouseleave', { bubbles: true, cancelable: true });
    Object.defineProperty(event, 'clientY', { value: -10 });

    act(() => {
      document.dispatchEvent(event);
    });

    console.log('activeTrigger after test 1:', result.current.activeTrigger?.type);
  });

  it('test 2', () => {
    console.log('storage at start of test 2:', JSON.stringify(storage));
    
    const config: ProactiveEngagementConfig = {
      enabled: true,
      triggers: [{ type: 'exit_intent', enabled: true, message: 'Test', actions: [{ text: 'OK' }], cooldown: 30 }],
    };

    const { result } = renderHook(() => useProactiveTriggers({ config }));

    const event = new MouseEvent('mouseleave', { bubbles: true, cancelable: true });
    Object.defineProperty(event, 'clientY', { value: -10 });

    act(() => {
      document.dispatchEvent(event);
    });

    console.log('activeTrigger after test 2:', result.current.activeTrigger?.type);
    expect(result.current.activeTrigger).not.toBeNull();
  });
});
