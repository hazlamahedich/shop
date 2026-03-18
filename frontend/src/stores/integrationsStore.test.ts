/**
 * Tests for integrations store
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useIntegrationsStore } from './integrationsStore';

// Mock fetch
global.fetch = vi.fn();

describe('Integrations Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store to initial state
    useIntegrationsStore.getState().reset();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useIntegrationsStore());

      expect(result.current.facebookStatus).toBe('idle');
      expect(result.current.facebookConnection.connected).toBe(false);
      expect(result.current.facebookConnection.webhookVerified).toBe(false);
      expect(result.current.facebookError).toBeUndefined();
    });
  });

  describe('checkFacebookStatus', () => {
    it('should update state when Facebook is connected', async () => {
      (global.fetch as unknown as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          data: {
            connected: true,
            pageId: '123456789',
            pageName: 'Test Store',
            pagePictureUrl: 'https://example.com/pic.jpg',
            connectedAt: '2026-02-03T00:00:00Z',
            webhookVerified: true,
          },
        }),
      });

      const { result } = renderHook(() => useIntegrationsStore());

      await act(async () => {
        await result.current.checkFacebookStatus();
      });

      expect(result.current.facebookStatus).toBe('connected');
      expect(result.current.facebookConnection).toEqual({
        connected: true,
        pageId: '123456789',
        pageName: 'Test Store',
        pagePictureUrl: 'https://example.com/pic.jpg',
        connectedAt: '2026-02-03T00:00:00Z',
        webhookVerified: true,
      });
      expect(result.current.facebookError).toBeUndefined();
    });

    it('should update state when Facebook is not connected', async () => {
      (global.fetch as unknown as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          data: {
            connected: false,
          },
        }),
      });

      const { result } = renderHook(() => useIntegrationsStore());

      await act(async () => {
        await result.current.checkFacebookStatus();
      });

      expect(result.current.facebookStatus).toBe('idle');
      expect(result.current.facebookConnection.connected).toBe(false);
    });

    it('should handle errors when checking status', async () => {
      (global.fetch as unknown as jest.Mock).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useIntegrationsStore());

      await act(async () => {
        await result.current.checkFacebookStatus();
      });

      expect(result.current.facebookStatus).toBe('error');
      expect(result.current.facebookError).toBe('Failed to check connection status');
    });
  });

  describe('initiateFacebookOAuth', () => {
    it('should open popup window with OAuth URL', async () => {
      const mockOpen = vi.fn();
      global.open = mockOpen;

      (global.fetch as unknown as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          data: {
            authUrl: 'https://facebook.com/oauth?test',
            state: 'test-state',
          },
        }),
      });

      const { result } = renderHook(() => useIntegrationsStore());

      await act(async () => {
        await result.current.initiateFacebookOAuth();
      });

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/integrations/facebook/authorize?merchant_id=1'
      );
      expect(mockOpen).toHaveBeenCalledWith(
        'https://facebook.com/oauth?test',
        'facebook-oauth',
        expect.stringContaining('width=600')
      );
      expect(result.current.facebookStatus).toBe('connecting');
    });

    it('should handle OAuth initiation errors', async () => {
      (global.fetch as unknown as jest.Mock).mockResolvedValue({
        ok: false,
      });

      const { result } = renderHook(() => useIntegrationsStore());

      await act(async () => {
        await result.current.initiateFacebookOAuth();
      });

      expect(result.current.facebookStatus).toBe('error');
      expect(result.current.facebookError).toBe('Failed to initiate OAuth');
    });

    it('should handle popup blocked error', async () => {
      global.open = vi.fn(() => null);

      (global.fetch as unknown as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          data: {
            authUrl: 'https://facebook.com/oauth',
            state: 'test',
          },
        }),
      });

      const { result } = renderHook(() => useIntegrationsStore());

      await act(async () => {
        await result.current.initiateFacebookOAuth();
      });

      expect(result.current.facebookStatus).toBe('error');
      expect(result.current.facebookError).toContain('Popup blocked');
    });

    it('should set up message listener for popup', async () => {
      const mockAddEventListener = vi.fn();
      const originalWindow = { ...window };
      global.open = vi.fn(() => ({
        close: vi.fn(),
      }));

      Object.defineProperty(window, 'addEventListener', {
        value: mockAddEventListener,
        writable: true,
      });

      (global.fetch as unknown as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          data: {
            authUrl: 'https://facebook.com/oauth',
            state: 'test',
          },
        }),
      });

      const { result } = renderHook(() => useIntegrationsStore());

      await act(async () => {
        await result.current.initiateFacebookOAuth();
      });

      expect(mockAddEventListener).toHaveBeenCalledWith('message', expect.any(Function));

      // Restore original window
      Object.defineProperty(window, 'addEventListener', {
        value: originalWindow.addEventListener,
        writable: true,
      });
    });
  });

  describe('disconnectFacebook', () => {
    it('should disconnect Facebook successfully', async () => {
      (global.fetch as unknown as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          data: { disconnected: true },
        }),
      });

      const { result } = renderHook(() => useIntegrationsStore());

      // Start with connected state
      act(() => {
        useIntegrationsStore.setState({
          facebookConnection: { connected: true, webhookVerified: true },
        });
      });

      await act(async () => {
        await result.current.disconnectFacebook();
      });

      expect(global.fetch).toHaveBeenCalledWith('/api/integrations/facebook/disconnect', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ merchant_id: 1 }),
      });

      expect(result.current.facebookStatus).toBe('idle');
      expect(result.current.facebookConnection.connected).toBe(false);
    });

    it('should handle disconnect errors', async () => {
      (global.fetch as unknown as jest.Mock).mockResolvedValue({
        ok: false,
      });

      const { result } = renderHook(() => useIntegrationsStore());

      await act(async () => {
        await result.current.disconnectFacebook();
      });

      expect(result.current.facebookStatus).toBe('error');
      expect(result.current.facebookError).toBe('Failed to disconnect');
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      const { result } = renderHook(() => useIntegrationsStore());

      act(() => {
        useIntegrationsStore.setState({
          facebookError: 'Test error',
        });
      });

      expect(result.current.facebookError).toBe('Test error');

      act(() => {
        result.current.clearError();
      });

      expect(result.current.facebookError).toBeUndefined();
    });
  });

  describe('reset', () => {
    it('should reset store to initial state', () => {
      const { result } = renderHook(() => useIntegrationsStore());

      act(() => {
        useIntegrationsStore.setState({
          facebookStatus: 'connected',
          facebookConnection: { connected: true, webhookVerified: true },
          facebookError: 'Some error',
        });
      });

      expect(result.current.facebookStatus).toBe('connected');
      expect(result.current.facebookConnection.connected).toBe(true);
      expect(result.current.facebookError).toBe('Some error');

      act(() => {
        result.current.reset();
      });

      expect(result.current.facebookStatus).toBe('idle');
      expect(result.current.facebookConnection.connected).toBe(false);
      expect(result.current.facebookError).toBeUndefined();
    });
  });
});
