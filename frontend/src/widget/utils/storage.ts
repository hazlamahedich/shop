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

export function getStoredSessionForMerchant(merchantId: string): string | null {
  const storedId = safeStorage.get(SESSION_KEY);
  const storedMerchant = safeStorage.get(MERCHANT_KEY);

  if (!storedId || !isValidSessionId(storedId)) return null;
  if (storedMerchant !== merchantId) return null;

  return storedId;
}

export function clearVisitorId(): void {
  safeLocalStorage.remove(VISITOR_KEY);
}

// Message History Cache Keys
export const MESSAGE_CACHE_PREFIX = 'widget_msg_cache_';
export const MESSAGE_CACHE_META_PREFIX = 'widget_msg_meta_';

// 7 days in milliseconds
const MESSAGE_CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000;

export interface CachedMessage {
  messageId: string;
  content: string;
  sender: 'user' | 'bot' | 'merchant' | 'system';
  createdAt: string;
  products?: import('../types/widget').WidgetProduct[];
  cart?: import('../types/widget').WidgetCart;
  checkoutUrl?: string;
  contactOptions?: import('../types/widget').ContactOption[];
}

export interface MessageCacheMeta {
  sessionId: string;
  createdAt: string;
  expiresAt: string;
}

export function cacheMessages(sessionId: string, messages: CachedMessage[]): boolean {
  try {
    const cacheKey = MESSAGE_CACHE_PREFIX + sessionId;
    const metaKey = MESSAGE_CACHE_META_PREFIX + sessionId;
    const now = Date.now();
    
    const meta: MessageCacheMeta = {
      sessionId,
      createdAt: new Date(now).toISOString(),
      expiresAt: new Date(now + MESSAGE_CACHE_TTL_MS).toISOString(),
    };
    
    safeLocalStorage.set(cacheKey, JSON.stringify(messages));
    safeLocalStorage.set(metaKey, JSON.stringify(meta));
    return true;
  } catch {
    return false;
  }
}

export function getCachedMessages(sessionId: string): CachedMessage[] | null {
  try {
    const cacheKey = MESSAGE_CACHE_PREFIX + sessionId;
    const metaKey = MESSAGE_CACHE_META_PREFIX + sessionId;
    
    const metaJson = safeLocalStorage.get(metaKey);
    if (!metaJson) return null;
    
    const meta: MessageCacheMeta = JSON.parse(metaJson);
    const expiresAt = new Date(meta.expiresAt).getTime();
    
    if (Date.now() > expiresAt) {
      // Cache expired, clear it
      clearMessageCache(sessionId);
      return null;
    }
    
    const messagesJson = safeLocalStorage.get(cacheKey);
    if (!messagesJson) return null;
    
    return JSON.parse(messagesJson) as CachedMessage[];
  } catch {
    return null;
  }
}

export function clearMessageCache(sessionId: string): void {
  const cacheKey = MESSAGE_CACHE_PREFIX + sessionId;
  const metaKey = MESSAGE_CACHE_META_PREFIX + sessionId;
  safeLocalStorage.remove(cacheKey);
  safeLocalStorage.remove(metaKey);
}

export function isMessageCacheExpired(sessionId: string): boolean {
  try {
    const metaKey = MESSAGE_CACHE_META_PREFIX + sessionId;
    const metaJson = safeLocalStorage.get(metaKey);
    if (!metaJson) return true;
    
    const meta: MessageCacheMeta = JSON.parse(metaJson);
    const expiresAt = new Date(meta.expiresAt).getTime();
    
    return Date.now() > expiresAt;
  } catch {
    return true;
  }
}

import type { WidgetPosition } from '../types/widget';

export const POSITION_KEY_PREFIX = 'shopbot-widget-position-';

function isValidPosition(position: unknown): position is WidgetPosition {
  if (!position || typeof position !== 'object') return false;
  const pos = position as Record<string, unknown>;
  return (
    typeof pos.x === 'number' &&
    typeof pos.y === 'number' &&
    !isNaN(pos.x) &&
    !isNaN(pos.y)
  );
}

function isPositionWithinViewport(position: WidgetPosition): boolean {
  if (typeof window === 'undefined') return true;
  const padding = 10;
  // Account for typical widget dimensions if not provided (380x600)
  const width = 380;
  const height = 600;
  
  return (
    position.x >= 0 &&
    position.x <= window.innerWidth - width - padding &&
    position.y >= 0 &&
    position.y <= window.innerHeight - height - padding
  );
}

export function getStoredPosition(merchantId: string): WidgetPosition | null {
  const key = POSITION_KEY_PREFIX + merchantId;
  const saved = safeLocalStorage.get(key);
  if (!saved) return null;
  try {
    const parsed = JSON.parse(saved);
    if (!isValidPosition(parsed)) return null;
    if (!isPositionWithinViewport(parsed)) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function setStoredPosition(merchantId: string, position: WidgetPosition): boolean {
  if (!isValidPosition(position)) return false;
  const key = POSITION_KEY_PREFIX + merchantId;
  return safeLocalStorage.set(key, JSON.stringify(position));
}

export function saveWidgetPosition(position: WidgetPosition): boolean {
  return safeLocalStorage.set('shopbot_widget_position', JSON.stringify(position));
}

export function loadWidgetPosition(): WidgetPosition | null {
  const saved = safeLocalStorage.get('shopbot_widget_position');
  if (!saved) return null;
  try {
    return JSON.parse(saved) as WidgetPosition;
  } catch {
    return null;
  }
}

/**
 * Validate session ID format (UUID v4)
 * Matches the backend validation in backend/app/core/validators.py
 */
const UUID_V4_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function isValidSessionId(sessionId: string | null | undefined): boolean {
  if (!sessionId || typeof sessionId !== 'string') return false;
  return UUID_V4_PATTERN.test(sessionId.trim());
}

export { safeStorage, safeLocalStorage };

import type { ThemeMode } from '../types/widget';

export const THEME_KEY_PREFIX = 'shopbot-widget-theme-';

export function getStoredTheme(merchantId: string): ThemeMode | null {
  const key = THEME_KEY_PREFIX + merchantId;
  const stored = safeLocalStorage.get(key);
  if (stored === 'light' || stored === 'dark' || stored === 'auto') {
    return stored;
  }
  return null;
}

export function setStoredTheme(merchantId: string, mode: ThemeMode): boolean {
  const key = THEME_KEY_PREFIX + merchantId;
  return safeLocalStorage.set(key, mode);
}
