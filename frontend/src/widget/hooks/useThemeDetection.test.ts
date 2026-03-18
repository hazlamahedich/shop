import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useThemeDetection } from './useThemeDetection';

describe('useThemeDetection', () => {
  const originalMatchMedia = window.matchMedia;
  let matchMediaListeners: Array<(e: MediaQueryListEvent) => void> = [];

  beforeEach(() => {
    matchMediaListeners = [];
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query === '(prefers-color-scheme: dark)' ? false : false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn((_event: string, listener: (e: MediaQueryListEvent) => void) => {
        matchMediaListeners.push(listener);
      }),
      removeEventListener: vi.fn((_event: string, listener: (e: MediaQueryListEvent) => void) => {
        matchMediaListeners = matchMediaListeners.filter(l => l !== listener);
      }),
      dispatchEvent: vi.fn(),
    }));
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
    matchMediaListeners = [];
  });

  it('returns light when system prefers light', () => {
    window.matchMedia = vi.fn().mockImplementation(() => ({
      matches: false,
      media: '(prefers-color-scheme: dark)',
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    const { result } = renderHook(() => useThemeDetection());
    
    expect(result.current.systemTheme).toBe('light');
    expect(result.current.isDark).toBe(false);
  });

  it('returns dark when system prefers dark', () => {
    window.matchMedia = vi.fn().mockImplementation(() => ({
      matches: true,
      media: '(prefers-color-scheme: dark)',
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    const { result } = renderHook(() => useThemeDetection());
    
    expect(result.current.systemTheme).toBe('dark');
    expect(result.current.isDark).toBe(true);
  });

  it('updates state on system theme change', () => {
    let currentMatches = false;
    
    window.matchMedia = vi.fn().mockImplementation(() => ({
      get matches() { return currentMatches; },
      media: '(prefers-color-scheme: dark)',
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn((_event: string, listener: (e: MediaQueryListEvent) => void) => {
        matchMediaListeners.push(listener);
      }),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    const { result } = renderHook(() => useThemeDetection());
    
    expect(result.current.systemTheme).toBe('light');

    act(() => {
      currentMatches = true;
      matchMediaListeners.forEach(listener => {
        listener({ matches: true } as MediaQueryListEvent);
      });
    });

    expect(result.current.systemTheme).toBe('dark');
    expect(result.current.isDark).toBe(true);
  });

  it('cleanup removes event listener', () => {
    const removeEventListener = vi.fn();
    
    window.matchMedia = vi.fn().mockImplementation(() => ({
      matches: false,
      media: '(prefers-color-scheme: dark)',
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener,
      dispatchEvent: vi.fn(),
    }));

    const { unmount } = renderHook(() => useThemeDetection());
    
    unmount();
    
    expect(removeEventListener).toHaveBeenCalled();
  });
});
