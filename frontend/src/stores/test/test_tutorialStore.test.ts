/** Tutorial Store Tests.

Tests Zustand store for tutorial progress tracking including:
- State initialization and persistence
- Step navigation actions
- Completion and skip functionality
- Reset functionality
*/

import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useTutorialStore } from '../tutorialStore';

// Mock fetch globally
global.fetch = vi.fn();

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value.toString();
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('TutorialStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Initial State', () => {
    it('should initialize with default values', () => {
      const { result } = renderHook(() => useTutorialStore());

      expect(result.current.currentStep).toBe(1);
      expect(result.current.completedSteps).toEqual([]);
      expect(result.current.isStarted).toBe(false);
      expect(result.current.isCompleted).toBe(false);
      expect(result.current.isSkipped).toBe(false);
      expect(result.current.startedAt).toBeNull();
      expect(result.current.completedAt).toBeNull();
      expect(result.current.stepsTotal).toBe(8);
    });

    it('should persist state to localStorage', async () => {
      const { result } = renderHook(() => useTutorialStore());

      // Modify state
      act(() => {
        result.current.startTutorial();
      });

      await waitFor(() => {
        const stored = localStorage.getItem('shop-tutorial-storage');
        expect(stored).toBeTruthy();
        const parsed = JSON.parse(stored!);
        expect(parsed.isStarted).toBe(true);
      });
    });
  });

  describe('startTutorial', () => {
    it('should mark tutorial as started', async () => {
      const { result } = renderHook(() => useTutorialStore());

      await act(async () => {
        await result.current.startTutorial();
      });

      expect(result.current.isStarted).toBe(true);
      expect(result.current.startedAt).toBeInstanceOf(Date);
      expect(result.current.currentStep).toBe(1);
    });

    it('should call API to start tutorial', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: {} }),
      } as Response);

      const { result } = renderHook(() => useTutorialStore());

      await act(async () => {
        await result.current.startTutorial();
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/tutorial/start'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
    });
  });

  describe('nextStep', () => {
    it('should increment current step', () => {
      const { result } = renderHook(() => useTutorialStore());

      act(() => {
        result.current.nextStep();
      });

      expect(result.current.currentStep).toBe(2);
    });

    it('should not exceed stepsTotal', () => {
      const { result } = renderHook(() => useTutorialStore());

      // Go to last step
      act(() => {
        result.current.jumpToStep(8);
      });

      expect(result.current.currentStep).toBe(8);

      // Try to go beyond
      act(() => {
        result.current.nextStep();
      });

      expect(result.current.currentStep).toBe(8); // Should stay at 8
    });
  });

  describe('previousStep', () => {
    it('should decrement current step', () => {
      const { result } = renderHook(() => useTutorialStore());

      act(() => {
        result.current.jumpToStep(3);
        result.current.previousStep();
      });

      expect(result.current.currentStep).toBe(2);
    });

    it('should not go below step 1', () => {
      const { result } = renderHook(() => useTutorialStore());

      act(() => {
        result.current.previousStep();
      });

      expect(result.current.currentStep).toBe(1); // Should stay at 1
    });
  });

  describe('jumpToStep', () => {
    it('should jump to specific step', () => {
      const { result } = renderHook(() => useTutorialStore());

      act(() => {
        result.current.jumpToStep(5);
      });

      expect(result.current.currentStep).toBe(5);
    });

    it('should allow jumping to any valid step', () => {
      const { result } = renderHook(() => useTutorialStore());

      act(() => {
        result.current.jumpToStep(8);
      });

      expect(result.current.currentStep).toBe(8);
    });
  });

  describe('completeStep', () => {
    it('should add step to completed steps', () => {
      const { result } = renderHook(() => useTutorialStore());

      act(() => {
        result.current.completeStep(3);
      });

      expect(result.current.completedSteps).toContain('step-3');
    });

    it('should not duplicate completed steps', () => {
      const { result } = renderHook(() => useTutorialStore());

      act(() => {
        result.current.completeStep(2);
        result.current.completeStep(2); // Same step again
      });

      expect(result.current.completedSteps.filter((s) => s === 'step-2')).toHaveLength(1);
    });
  });

  describe('skipTutorial', () => {
    it('should mark tutorial as skipped', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: {} }),
      } as Response);

      const { result } = renderHook(() => useTutorialStore());

      await act(async () => {
        await result.current.skipTutorial();
      });

      expect(result.current.isSkipped).toBe(true);
      expect(result.current.isCompleted).toBe(false);
      expect(result.current.completedAt).toBeInstanceOf(Date);
    });

    it('should call skip API', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: { skipped: true } }),
      } as Response);

      const { result } = renderHook(() => useTutorialStore());

      await act(async () => {
        await result.current.skipTutorial();
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/tutorial/skip'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('completeTutorial', () => {
    it('should mark tutorial as completed with all 8 steps', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: {} }),
      } as Response);

      const { result } = renderHook(() => useTutorialStore());

      await act(async () => {
        await result.current.completeTutorial();
      });

      expect(result.current.isCompleted).toBe(true);
      expect(result.current.currentStep).toBe(8);
      expect(result.current.completedSteps).toEqual([
        'step-1',
        'step-2',
        'step-3',
        'step-4',
        'step-5',
        'step-6',
        'step-7',
        'step-8',
      ]);
      expect(result.current.completedAt).toBeInstanceOf(Date);
    });

    it('should call complete API', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: {} }),
      } as Response);

      const { result } = renderHook(() => useTutorialStore());

      await act(async () => {
        await result.current.completeTutorial();
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/tutorial/complete'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('resetTutorial', () => {
    it('should reset all state to initial values', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: {} }),
      } as Response);

      const { result } = renderHook(() => useTutorialStore());

      // Set some state first
      act(() => {
        result.current.jumpToStep(5);
        result.current.completeStep(3);
      });

      expect(result.current.currentStep).toBe(5);
      expect(result.current.completedSteps).toContain('step-3');

      // Reset
      await act(async () => {
        await result.current.resetTutorial();
      });

      expect(result.current.currentStep).toBe(1);
      expect(result.current.completedSteps).toEqual([]);
      expect(result.current.isStarted).toBe(false);
      expect(result.current.isCompleted).toBe(false);
      expect(result.current.isSkipped).toBe(false);
      expect(result.current.startedAt).toBeNull();
      expect(result.current.completedAt).toBeNull();
    });

    it('should call reset API', async () => {
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: {} }),
      } as Response);

      const { result } = renderHook(() => useTutorialStore());

      await act(async () => {
        await result.current.resetTutorial();
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/tutorial/reset'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });

  describe('Persistence Configuration', () => {
    it('should use correct storage key', () => {
      const { result } = renderHook(() => useTutorialStore());

      act(() => {
        result.current.completeStep(1);
      });

      const stored = localStorage.getItem('shop-tutorial-storage');
      expect(stored).toBeTruthy();
    });

    it('should persist only specific fields', async () => {
      const { result } = renderHook(() => useTutorialStore());

      await act(async () => {
        await result.current.completeTutorial();
      });

      const stored = localStorage.getItem('shop-tutorial-storage');
      const parsed = JSON.parse(stored!);

      // Should persist these fields
      expect(parsed).toHaveProperty('isStarted');
      expect(parsed).toHaveProperty('isCompleted');
      expect(parsed).toHaveProperty('isSkipped');
      expect(parsed).toHaveProperty('completedSteps');
      expect(parsed).toHaveProperty('currentStep');
    });
  });
});
