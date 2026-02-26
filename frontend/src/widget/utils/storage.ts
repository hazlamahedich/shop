/**
 * Safe storage utilities for widget data.
 *
 * Story 6-1 Enhancement: Privacy-friendly storage strategy
 * - sessionStorage: session_id, merchant_id (clears on browser close)
 * - localStorage: visitor_id (persists for consent tracking)
 */

const safeStorage = {
  get: (key: string): string | null => {
    try {
      return sessionStorage.getItem(key);
    } catch {
      return null;
    }
  },
  set: (key: string, value: string): boolean => {
    try {
      sessionStorage.setItem(key, value);
      return true;
    } catch {
      return false;
    }
  },
  remove: (key: string): boolean => {
    try {
      sessionStorage.removeItem(key);
      return true;
    } catch {
      return false;
    }
  },
};

const safeLocalStorage = {
  get: (key: string): string | null => {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  },
  set: (key: string, value: string): boolean => {
    try {
      localStorage.setItem(key, value);
      return true;
    } catch {
      return false;
    }
  },
  remove: (key: string): boolean => {
    try {
      localStorage.removeItem(key);
      return true;
    } catch {
      return false;
    }
  },
};

export const SESSION_KEY = 'widget_session_id';
export const MERCHANT_KEY = 'widget_merchant_id';
export const VISITOR_KEY = 'widget_visitor_id';

export const VISITOR_MAX_AGE_MS = 13 * 30 * 24 * 60 * 60 * 1000;

export function getOrCreateVisitorId(): string {
  const stored = safeLocalStorage.get(VISITOR_KEY);
  if (stored) {
    try {
      const parsed = JSON.parse(stored);
      const createdAt = new Date(parsed.createdAt).getTime();
      const now = Date.now();
      if (now - createdAt < VISITOR_MAX_AGE_MS) {
        return parsed.visitorId;
      }
    } catch {
      // Invalid JSON, create new
    }
  }

  const visitorId = crypto.randomUUID();
  safeLocalStorage.set(VISITOR_KEY, JSON.stringify({
    visitorId,
    createdAt: new Date().toISOString(),
  }));
  return visitorId;
}

export function getVisitorId(): string | null {
  const stored = safeLocalStorage.get(VISITOR_KEY);
  if (!stored) return null;

  try {
    const parsed = JSON.parse(stored);
    const createdAt = new Date(parsed.createdAt).getTime();
    const now = Date.now();
    if (now - createdAt < VISITOR_MAX_AGE_MS) {
      return parsed.visitorId;
    }
    return null;
  } catch {
    return null;
  }
}

export function clearVisitorId(): void {
  safeLocalStorage.remove(VISITOR_KEY);
}

export { safeStorage, safeLocalStorage };
