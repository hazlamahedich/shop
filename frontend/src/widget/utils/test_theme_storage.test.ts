import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  getStoredTheme,
  setStoredTheme,
  THEME_KEY_PREFIX,
} from './storage';

describe('Theme Storage Functions', () => {
  const originalLocalStorage = window.localStorage;
  let localStorageStore: Record<string, string> = {};

  beforeEach(() => {
    localStorageStore = {};
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: vi.fn((key: string) => localStorageStore[key] ?? null),
        setItem: vi.fn((key: string, value: string) => {
          localStorageStore[key] = value;
        }),
        removeItem: vi.fn((key: string) => {
          delete localStorageStore[key];
        }),
        clear: vi.fn(() => {
          localStorageStore = {};
        }),
        length: 0,
        key: vi.fn(),
      },
      writable: true,
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'localStorage', {
      value: originalLocalStorage,
      writable: true,
    });
  });

  describe('getStoredTheme', () => {
    it('returns stored theme value', () => {
      localStorageStore[`${THEME_KEY_PREFIX}test-merchant`] = 'dark';
      
      const result = getStoredTheme('test-merchant');
      
      expect(result).toBe('dark');
    });

    it('returns null when no theme stored', () => {
      const result = getStoredTheme('test-merchant');
      
      expect(result).toBeNull();
    });

    it('returns null for invalid theme value', () => {
      localStorageStore[`${THEME_KEY_PREFIX}test-merchant`] = 'invalid';
      
      const result = getStoredTheme('test-merchant');
      
      expect(result).toBeNull();
    });

    it('returns auto when auto is stored', () => {
      localStorageStore[`${THEME_KEY_PREFIX}test-merchant`] = 'auto';
      
      const result = getStoredTheme('test-merchant');
      
      expect(result).toBe('auto');
    });

    it('returns light when light is stored', () => {
      localStorageStore[`${THEME_KEY_PREFIX}test-merchant`] = 'light';
      
      const result = getStoredTheme('test-merchant');
      
      expect(result).toBe('light');
    });

    it('uses correct key with merchantId', () => {
      const merchantId = 'my-shop-123';
      localStorageStore[`${THEME_KEY_PREFIX}${merchantId}`] = 'dark';
      
      const result = getStoredTheme(merchantId);
      
      expect(result).toBe('dark');
      expect(localStorage.getItem).toHaveBeenCalledWith(
        `${THEME_KEY_PREFIX}${merchantId}`
      );
    });

    it('returns null when localStorage throws (private browsing)', () => {
      Object.defineProperty(window, 'localStorage', {
        value: {
          getItem: vi.fn(() => {
            throw new Error('localStorage not available');
          }),
          setItem: vi.fn(),
          removeItem: vi.fn(),
          clear: vi.fn(),
          length: 0,
          key: vi.fn(),
        },
        writable: true,
      });

      const result = getStoredTheme('test-merchant');
      
      expect(result).toBeNull();
    });
  });

  describe('setStoredTheme', () => {
    it('persists theme correctly', () => {
      const result = setStoredTheme('test-merchant', 'dark');
      
      expect(result).toBe(true);
      expect(localStorageStore[`${THEME_KEY_PREFIX}test-merchant`]).toBe('dark');
    });

    it('uses correct key with merchantId', () => {
      const merchantId = 'my-shop-456';
      
      setStoredTheme(merchantId, 'light');
      
      expect(localStorage.setItem).toHaveBeenCalledWith(
        `${THEME_KEY_PREFIX}${merchantId}`,
        'light'
      );
    });

    it('returns false when localStorage throws (private browsing)', () => {
      Object.defineProperty(window, 'localStorage', {
        value: {
          getItem: vi.fn(),
          setItem: vi.fn(() => {
            throw new Error('localStorage not available');
          }),
          removeItem: vi.fn(),
          clear: vi.fn(),
          length: 0,
          key: vi.fn(),
        },
        writable: true,
      });

      const result = setStoredTheme('test-merchant', 'dark');
      
      expect(result).toBe(false);
    });

    it('returns false when quota exceeded', () => {
      const quotaError = new Error('QuotaExceededError');
      quotaError.name = 'QuotaExceededError';
      
      Object.defineProperty(window, 'localStorage', {
        value: {
          getItem: vi.fn(),
          setItem: vi.fn(() => {
            throw quotaError;
          }),
          removeItem: vi.fn(),
          clear: vi.fn(),
          length: 0,
          key: vi.fn(),
        },
        writable: true,
      });

      const result = setStoredTheme('test-merchant', 'dark');
      
      expect(result).toBe(false);
    });

    it('overwrites existing theme value', () => {
      localStorageStore[`${THEME_KEY_PREFIX}test-merchant`] = 'light';
      
      const result = setStoredTheme('test-merchant', 'dark');
      
      expect(result).toBe(true);
      expect(localStorageStore[`${THEME_KEY_PREFIX}test-merchant`]).toBe('dark');
    });
  });

  describe('Edge Cases', () => {
    it('handles empty string merchantId', () => {
      const result = getStoredTheme('');
      expect(result).toBeNull();
    });

    it('handles special characters in merchantId', () => {
      const merchantId = 'shop-with-special_chars.123';
      localStorageStore[`${THEME_KEY_PREFIX}${merchantId}`] = 'dark';
      
      const result = getStoredTheme(merchantId);
      
      expect(result).toBe('dark');
    });

    it('handles very long merchantId', () => {
      const merchantId = 'a'.repeat(1000);
      
      const result = setStoredTheme(merchantId, 'light');
      
      expect(result).toBe(true);
      expect(localStorageStore[`${THEME_KEY_PREFIX}${merchantId}`]).toBe('light');
    });

    it('handles whitespace in stored value', () => {
      localStorageStore[`${THEME_KEY_PREFIX}test-merchant`] = '  dark  ';
      
      const result = getStoredTheme('test-merchant');
      
      expect(result).toBeNull();
    });

    it('handles case-sensitive theme values', () => {
      localStorageStore[`${THEME_KEY_PREFIX}test-merchant`] = 'DARK';
      
      const result = getStoredTheme('test-merchant');
      
      expect(result).toBeNull();
    });
  });
});
