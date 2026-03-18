/** Tests for onboardingStore.

Tests localStorage persistence and state management for prerequisite checklist.
*/

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { onboardingStore, PrerequisiteKey } from "./onboardingStore";
import { renderHook, act } from "@testing-library/react";

// Get reference to the mocked localStorage from setup.ts
const localStorageMock = window.localStorage as unknown as {
  getItem: ReturnType<typeof vi.fn>;
  setItem: ReturnType<typeof vi.fn>;
  clear: ReturnType<typeof vi.fn>;
  removeItem: ReturnType<typeof vi.fn>;
};

describe("onboardingStore", () => {
  beforeEach(() => {
    // Reset store state before each test
    onboardingStore.getState().reset();
    vi.clearAllMocks();
    // Mock localStorage functions
    localStorageMock.getItem = vi.fn();
    localStorageMock.setItem = vi.fn();
    localStorageMock.removeItem = vi.fn();
    localStorageMock.clear = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("initial state", () => {
    it("should have initial state with all prerequisites false", () => {
      const state = onboardingStore.getState();
      expect(state.cloudAccount).toBe(false);
      expect(state.facebookAccount).toBe(false);
      expect(state.shopifyAccess).toBe(false);
      expect(state.llmProviderChoice).toBe(false);
      expect(state.updatedAt).toBe(null);
      expect(state.totalCount).toBe(4);
    });
  });

  describe("togglePrerequisite action", () => {
    it("should toggle a prerequisite from false to true", () => {
      const { togglePrerequisite } = onboardingStore.getState();
      
      togglePrerequisite("cloudAccount");
      
      const state = onboardingStore.getState();
      expect(state.cloudAccount).toBe(true);
      expect(state.facebookAccount).toBe(false);
      expect(state.shopifyAccess).toBe(false);
      expect(state.llmProviderChoice).toBe(false);
    });

    it("should toggle a prerequisite from true to false", () => {
      const { togglePrerequisite } = onboardingStore.getState();
      
      // First set to true
      togglePrerequisite("cloudAccount");
      // Then toggle back to false
      togglePrerequisite("cloudAccount");
      
      const state = onboardingStore.getState();
      expect(state.cloudAccount).toBe(false);
    });

    it("should persist toggle state to localStorage", () => {
      const { togglePrerequisite } = onboardingStore.getState();
      
      togglePrerequisite("facebookAccount");
      
      expect(localStorageMock.setItem).toHaveBeenCalled();
      const calledWith = localStorageMock.setItem.mock.calls[0];
      expect(calledWith[0]).toBe("shop_onboarding_prerequisites");
      
      const savedState = JSON.parse(calledWith[1] as string);
      expect(savedState.facebookAccount).toBe(true);
      expect(savedState.updatedAt).toBeDefined();
    });

    it("should handle all prerequisite keys", () => {
      const { togglePrerequisite } = onboardingStore.getState();
      const keys: PrerequisiteKey[] = [
        "cloudAccount", 
        "facebookAccount", 
        "shopifyAccess", 
        "llmProviderChoice"
      ];
      
      keys.forEach(key => {
        togglePrerequisite(key);
        expect(onboardingStore.getState()[key]).toBe(true);
      });
    });
  });

  describe("reset action", () => {
    it("should reset all state to initial values", () => {
      const { togglePrerequisite, reset } = onboardingStore.getState();
      
      // Set some values
      togglePrerequisite("cloudAccount");
      togglePrerequisite("facebookAccount");
      
      // Reset
      reset();
      
      const state = onboardingStore.getState();
      expect(state.cloudAccount).toBe(false);
      expect(state.facebookAccount).toBe(false);
      expect(state.shopifyAccess).toBe(false);
      expect(state.llmProviderChoice).toBe(false);
      expect(state.updatedAt).toBe(null);
    });

    it("should remove stored data from localStorage on reset", () => {
      const { togglePrerequisite, reset } = onboardingStore.getState();
      
      // Toggle something to store it
      togglePrerequisite("cloudAccount");
      
      // Reset
      reset();
      
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("shop_onboarding_prerequisites");
    });

    it("should handle localStorage errors gracefully when removing", () => {
      const { reset } = onboardingStore.getState();
      
      // Simulate an error when removing from localStorage
      localStorageMock.removeItem.mockImplementationOnce(() => {
        throw new Error("localStorage access denied");
      });
      
      // Should not throw error, just log warning
      expect(() => reset()).not.toThrow();
    });
  });

  describe("loadFromStorage action", () => {
    it("should load saved state from localStorage", () => {
      const savedState = {
        cloudAccount: true,
        facebookAccount: false,
        shopifyAccess: true,
        llmProviderChoice: false,
        updatedAt: new Date("2024-01-01T00:00:00.000Z").toISOString(),
      };

      localStorageMock.getItem.mockReturnValue(JSON.stringify(savedState));

      onboardingStore.getState().loadFromStorage();
      const state = onboardingStore.getState();

      expect(state.cloudAccount).toBe(true);
      expect(state.facebookAccount).toBe(false);
      expect(state.shopifyAccess).toBe(true);
      expect(state.llmProviderChoice).toBe(false);
      expect(state.updatedAt).toBe(savedState.updatedAt);
    });

    it("should return initial state when no data is stored", () => {
      localStorageMock.getItem.mockReturnValue(null);

      onboardingStore.getState().loadFromStorage();
      const state = onboardingStore.getState();

      expect(state).toEqual(onboardingStore.getState());
      expect(state.cloudAccount).toBe(false);
      expect(state.updatedAt).toBe(null);
    });

    it("should handle malformed JSON in localStorage", () => {
      localStorageMock.getItem.mockReturnValue("invalid json");

      onboardingStore.getState().loadFromStorage();
      const state = onboardingStore.getState();

      expect(state).toEqual(onboardingStore.getState());
      expect(state.cloudAccount).toBe(false);
    });

    it("should handle localStorage access denied gracefully", () => {
      localStorageMock.getItem.mockImplementationOnce(() => {
        throw new Error("localStorage access denied");
      });

      onboardingStore.getState().loadFromStorage();
      const state = onboardingStore.getState();

      expect(state).toEqual(onboardingStore.getState());
    });

    it("should not load data when localStorage is undefined", () => {
      const originalLocalStorage = global.localStorage;
      (global as any).localStorage = undefined;

      onboardingStore.getState().loadFromStorage();
      const state = onboardingStore.getState();

      expect(state).toEqual(onboardingStore.getState());
      
      // Restore localStorage
      (global as any).localStorage = originalLocalStorage;
    });
  });

  describe("computed values", () => {
    describe("isComplete", () => {
      it("should return true when all prerequisites are completed", () => {
        const { togglePrerequisite } = onboardingStore.getState();

        // Check all items
        togglePrerequisite("cloudAccount");
        togglePrerequisite("facebookAccount");
        togglePrerequisite("shopifyAccess");
        togglePrerequisite("llmProviderChoice");

        expect(onboardingStore.getState().isComplete()).toBe(true);
      });

      it("should return false when any prerequisite is incomplete", () => {
        const { togglePrerequisite } = onboardingStore.getState();

        // Check only 3 items
        togglePrerequisite("cloudAccount");
        togglePrerequisite("facebookAccount");
        togglePrerequisite("shopifyAccess");

        expect(onboardingStore.getState().isComplete()).toBe(false);
      });

      it("should return false when no prerequisites are completed", () => {
        expect(onboardingStore.getState().isComplete()).toBe(false);
      });
    });

    describe("completedCount", () => {
      it("should return 0 when no prerequisites are completed", () => {
        expect(onboardingStore.getState().completedCount()).toBe(0);
      });

      it("should return correct count when some prerequisites are completed", () => {
        const { togglePrerequisite } = onboardingStore.getState();

        togglePrerequisite("cloudAccount");
        expect(onboardingStore.getState().completedCount()).toBe(1);

        togglePrerequisite("facebookAccount");
        expect(onboardingStore.getState().completedCount()).toBe(2);

        togglePrerequisite("shopifyAccess");
        expect(onboardingStore.getState().completedCount()).toBe(3);
      });

      it("should return totalCount when all prerequisites are completed", () => {
        const { togglePrerequisite } = onboardingStore.getState();

        // Check all items
        togglePrerequisite("cloudAccount");
        togglePrerequisite("facebookAccount");
        togglePrerequisite("shopifyAccess");
        togglePrerequisite("llmProviderChoice");

        expect(onboardingStore.getState().completedCount()).toBe(4);
        expect(onboardingStore.getState().completedCount()).toBe(
          onboardingStore.getState().totalCount
        );
      });
    });
  });

  describe("localStorage persistence", () => {
    it("should persist state to localStorage when checkbox is toggled", () => {
      const { togglePrerequisite } = onboardingStore.getState();

      // Toggle cloud account
      togglePrerequisite("cloudAccount");

      // Verify localStorage was called
      expect(localStorageMock.setItem).toHaveBeenCalled();

      const storedData = JSON.parse(localStorageMock.setItem.mock.calls[0][1] as string);
      expect(storedData.cloudAccount).toBe(true);
      expect(storedData.updatedAt).toBeDefined();
    });

    it("should update timestamp on each state change", () => {
      const { togglePrerequisite } = onboardingStore.getState();
      const firstTimestamp = localStorageMock.setItem.mock.calls[0][1];
      
      togglePrerequisite("facebookAccount");
      const secondTimestamp = localStorageMock.setItem.mock.calls[1][1];
      
      expect(firstTimestamp).not.toBe(secondTimestamp);
      
      const firstData = JSON.parse(firstTimestamp as string);
      const secondData = JSON.parse(secondTimestamp as string);
      
      expect(firstData.updatedAt).not.toBe(secondData.updatedAt);
    });

    it("should save complete state with all properties", () => {
      const { togglePrerequisite } = onboardingStore.getState();
      
      togglePrerequisite("cloudAccount");
      togglePrerequisite("facebookAccount");
      
      const storedData = JSON.parse(localStorageMock.setItem.mock.calls[0][1] as string);
      
      expect(storedData).toEqual(expect.objectContaining({
        cloudAccount: true,
        facebookAccount: true,
        shopifyAccess: false,
        llmProviderChoice: false,
        updatedAt: expect.any(String),
      }));
    });
  });

  describe("edge cases", () => {
    it("should handle rapid toggling of the same prerequisite", () => {
      const { togglePrerequisite } = onboardingStore.getState();
      
      // Toggle rapidly
      togglePrerequisite("cloudAccount");
      togglePrerequisite("cloudAccount");
      togglePrerequisite("cloudAccount");
      
      expect(onboardingStore.getState().cloudAccount).toBe(false);
      expect(localStorageMock.setItem).toHaveBeenCalledTimes(3);
    });

    it("should handle toggling multiple prerequisites in sequence", () => {
      const { togglePrerequisite } = onboardingStore.getState();
      const keys: PrerequisiteKey[] = [
        "cloudAccount", 
        "facebookAccount", 
        "shopifyAccess", 
        "llmProviderChoice"
      ];
      
      // Toggle each key
      keys.forEach(key => togglePrerequisite(key));
      
      // Verify all are true
      keys.forEach(key => {
        expect(onboardingStore.getState()[key]).toBe(true);
      });
      
      // Should be complete
      expect(onboardingStore.getState().isComplete()).toBe(true);
      expect(onboardingStore.getState().completedCount()).toBe(4);
    });

    it("should maintain state consistency across multiple actions", () => {
      const { togglePrerequisite, reset, loadFromStorage } = onboardingStore.getState();
      
      // Set some state
      togglePrerequisite("cloudAccount");
      togglePrerequisite("shopifyAccess");
      
      // Verify state
      expect(onboardingStore.getState().completedCount()).toBe(2);
      
      // Reset
      reset();
      expect(onboardingStore.getState().completedCount()).toBe(0);
      
      // Load from storage should not affect reset state
      loadFromStorage();
      expect(onboardingStore.getState().completedCount()).toBe(0);
    });
  });

  describe("React integration", () => {
    it("should work correctly with React hooks", () => {
      const { result } = renderHook(() => {
        const state = onboardingStore.getState();
        return {
          isComplete: state.isComplete(),
          completedCount: state.completedCount(),
          cloudAccount: state.cloudAccount,
        };
      });
      
      // Initial state
      expect(result.current.isComplete).toBe(false);
      expect(result.current.completedCount).toBe(0);
      expect(result.current.cloudAccount).toBe(false);
      
      // Toggle via store action
      act(() => {
        onboardingStore.getState().togglePrerequisite("cloudAccount");
      });
      
      // Update result
      const { result: updatedResult } = renderHook(() => {
        const state = onboardingStore.getState();
        return {
          isComplete: state.isComplete(),
          completedCount: state.completedCount(),
          cloudAccount: state.cloudAccount,
        };
      });
      
      expect(updatedResult.current.isComplete).toBe(false);
      expect(updatedResult.current.completedCount).toBe(1);
      expect(updatedResult.current.cloudAccount).toBe(true);
    });
  });
});
