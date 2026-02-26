import { useCallback, useState } from 'react';
import type { WidgetSession } from '../types/widget';
import { widgetClient } from '../api/widgetClient';
import { safeStorage, SESSION_KEY, MERCHANT_KEY, getVisitorId } from '../utils/storage';

export function useWidgetSession(merchantId: string) {
  const [session, setSession] = useState<WidgetSession | null>(() => {
    const storedId = safeStorage.get(SESSION_KEY);
    const storedMerchant = safeStorage.get(MERCHANT_KEY);
    if (storedId && storedMerchant === merchantId) {
      return {
        sessionId: storedId,
        merchantId,
        expiresAt: '',
        createdAt: '',
        lastActivityAt: '',
      };
    }
    return null;
  });

  const createSession = useCallback(async (): Promise<WidgetSession> => {
    const visitorId = getVisitorId() || undefined;
    const newSession = await widgetClient.createSession(merchantId, visitorId);
    setSession(newSession);
    safeStorage.set(SESSION_KEY, newSession.sessionId);
    safeStorage.set(MERCHANT_KEY, merchantId);
    return newSession;
  }, [merchantId]);

  const getSession = useCallback(async (): Promise<WidgetSession | null> => {
    const sessionId = safeStorage.get(SESSION_KEY);
    if (!sessionId) return null;

    const existingSession = await widgetClient.getSession(sessionId);
    if (existingSession) {
      setSession(existingSession);
      return existingSession;
    }

    safeStorage.remove(SESSION_KEY);
    setSession(null);
    return null;
  }, []);

  const endSession = useCallback(async (): Promise<void> => {
    const sessionId = safeStorage.get(SESSION_KEY);
    if (sessionId) {
      try {
        await widgetClient.endSession(sessionId);
      } catch {
        // Ignore errors on cleanup
      }
    }
    safeStorage.remove(SESSION_KEY);
    safeStorage.remove(MERCHANT_KEY);
    setSession(null);
  }, []);

  return {
    session,
    createSession,
    getSession,
    endSession,
  };
}
