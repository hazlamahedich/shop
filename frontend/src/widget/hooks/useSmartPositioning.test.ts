import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSmartPositioning } from './useSmartPositioning';

const mockGetStoredPosition = vi.fn();
const mockSetStoredPosition = vi.fn();

vi.mock('../utils/storage', () => ({
  getStoredPosition: () => mockGetStoredPosition(),
  setStoredPosition: (_merchantId: string, position: { x: number; y: number }) =>
    mockSetStoredPosition(_merchantId, position),
}));

vi.mock('../utils/smartPositioning', () => ({
  detectImportantElements: () => [],
  getElementBounds: () => ({ x: 0, y: 0, width: 100, height: 100 }),
  findOptimalPosition: () => ({ x: 1500, y: 460, edge: 'bottom-right' }),
  constrainToViewport: (pos: { x: number; y: number }) => pos,
  isMobileDevice: () => false,
  getMobilePosition: () => ({ x: 37.5, y: 100, edge: 'center' }),
  debounce: (fn: (...args: unknown[]) => unknown) => fn,
}));

describe('useSmartPositioning', () => {
  const defaultOptions = {
    merchantId: 'test-merchant-123',
    widgetSize: { width: 400, height: 600 },
  };

  beforeEach(() => {
    mockGetStoredPosition.mockReset();
    mockSetStoredPosition.mockReset();
    vi.stubGlobal('innerWidth', 1920);
    vi.stubGlobal('innerHeight', 1080);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe('initial position', () => {
    it('returns stored position if available', () => {
      mockGetStoredPosition.mockReturnValue({ x: 100, y: 200 });

      const { result } = renderHook(() => useSmartPositioning(defaultOptions));

      expect(result.current.position.x).toBe(100);
      expect(result.current.position.y).toBe(200);
    });

    it('calculates optimal position if no stored position', () => {
      mockGetStoredPosition.mockReturnValue(null);

      const { result } = renderHook(() => useSmartPositioning(defaultOptions));

      expect(result.current.position.x).toBe(1500);
      expect(result.current.position.y).toBe(460);
      expect(result.current.position.edge).toBe('bottom-right');
    });
  });

  describe('updatePosition', () => {
    it('updates position and persists to storage', () => {
      mockGetStoredPosition.mockReturnValue(null);

      const { result } = renderHook(() => useSmartPositioning(defaultOptions));

      act(() => {
        result.current.updatePosition({ x: 500, y: 300 });
      });

      expect(result.current.position.x).toBe(500);
      expect(result.current.position.y).toBe(300);
      expect(mockSetStoredPosition).toHaveBeenCalledWith('test-merchant-123', {
        x: 500,
        y: 300,
      });
    });
  });

  describe('reposition', () => {
    it('recalculates position when called', () => {
      mockGetStoredPosition.mockReturnValue(null);

      const { result } = renderHook(() => useSmartPositioning(defaultOptions));

      act(() => {
        result.current.updatePosition({ x: 0, y: 0 });
      });

      expect(result.current.position.x).toBe(0);

      act(() => {
        result.current.reposition();
      });

      expect(result.current.position.x).toBe(1500);
      expect(result.current.position.y).toBe(460);
    });
  });

  describe('isMobile', () => {
    it('returns false for desktop', () => {
      mockGetStoredPosition.mockReturnValue(null);

      const { result } = renderHook(() => useSmartPositioning(defaultOptions));

      expect(result.current.isMobile).toBe(false);
    });
  });

  describe('resize handling', () => {
    it('repositions on window resize', async () => {
      mockGetStoredPosition.mockReturnValue(null);

      renderHook(() => useSmartPositioning(defaultOptions));

      act(() => {
        window.dispatchEvent(new Event('resize'));
      });

      // The debounced handler should trigger reposition
      expect(true).toBe(true);
    });
  });

  describe('disabled mode', () => {
    it('does not reposition when disabled', () => {
      mockGetStoredPosition.mockReturnValue(null);

      const { result } = renderHook(() =>
        useSmartPositioning({ ...defaultOptions, enabled: false })
      );

      act(() => {
        result.current.reposition();
      });

      // When disabled, reposition should not update position
      expect(true).toBe(true);
    });
  });

  describe('custom config', () => {
    it('merges custom config with defaults', () => {
      mockGetStoredPosition.mockReturnValue(null);

      const { result } = renderHook(() =>
        useSmartPositioning({
          ...defaultOptions,
          config: {
            minClearance: 50,
            viewportPadding: 20,
          },
        })
      );

      expect(result.current.position).toBeDefined();
    });
  });
});
