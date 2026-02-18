import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWidgetSession } from './useWidgetSession';

vi.mock('../api/widgetClient', () => ({
  widgetClient: {
    createSession: vi.fn(),
    getSession: vi.fn(),
    endSession: vi.fn(),
  },
}));

describe('useWidgetSession', () => {
  const merchantId = 'test-merchant';

  beforeEach(() => {
    sessionStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  it('should initialize with null session when no stored session', () => {
    const { result } = renderHook(() => useWidgetSession(merchantId));
    expect(result.current.session).toBeNull();
  });

  it('should create a new session', async () => {
    const mockSession = {
      sessionId: 'test-session-id',
      merchantId,
      expiresAt: '2024-01-01T01:00:00Z',
      createdAt: '2024-01-01T00:00:00Z',
      lastActivityAt: '2024-01-01T00:00:00Z',
    };

    const { widgetClient } = await import('../api/widgetClient');
    vi.mocked(widgetClient.createSession).mockResolvedValue(mockSession);

    const { result } = renderHook(() => useWidgetSession(merchantId));

    await act(async () => {
      const session = await result.current.createSession();
      expect(session).toEqual(mockSession);
    });
  });

  it('should end session and clear storage', async () => {
    const { widgetClient } = await import('../api/widgetClient');
    vi.mocked(widgetClient.endSession).mockResolvedValue(undefined);

    const { result } = renderHook(() => useWidgetSession(merchantId));

    await act(async () => {
      await result.current.endSession();
    });

    expect(result.current.session).toBeNull();
  });
});
