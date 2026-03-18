/** Tests for tutorialStore.

Tests localStorage persistence and state management for interactive tutorial progress.
*/

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

// Get reference to the mocked localStorage from setup.ts
const localStorageMock = window.localStorage as unknown as {
  getItem: ReturnType<typeof vi.fn>;
  setItem: ReturnType<typeof vi.fn>;
  clear: ReturnType<typeof vi.fn>;
  removeItem: ReturnType<typeof vi.fn>;
};

// Mock fetch for API calls
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe("tutorialStore", () => {
  // We'll import the store after creating it
  let tutorialStore: any;

  beforeEach(async () => {
    // Dynamic import to avoid issues with module resolution during tests
    const storeModule = await import("./tutorialStore");
    tutorialStore = storeModule.useTutorialStore;

    // Reset store state before each test
    tutorialStore.getState().reset();
    vi.clearAllMocks();
    // Mock localStorage functions
    localStorageMock.getItem = vi.fn();
    localStorageMock.setItem = vi.fn();
    localStorageMock.removeItem = vi.fn();
    localStorageMock.clear = vi.fn();

    // Mock successful fetch responses by default
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ data: {} }),
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("initial state", () => {
    it("should have initial state with tutorial not started", () => {
      const state = tutorialStore.getState();
      expect(state.currentStep).toBe(1);
      expect(state.completedSteps).toEqual([]);
      expect(state.isStarted).toBe(false);
      expect(state.isCompleted).toBe(false);
      expect(state.isSkipped).toBe(false);
      expect(state.startedAt).toBe(null);
      expect(state.completedAt).toBe(null);
    });

    it("should have stepsTotal set to 8", () => {
      const state = tutorialStore.getState();
      expect(state.stepsTotal).toBe(8);
    });
  });

  describe("startTutorial action", () => {
    it("should mark tutorial as started", async () => {
      const { startTutorial } = tutorialStore.getState();

      await startTutorial();

      const state = tutorialStore.getState();
      expect(state.isStarted).toBe(true);
      expect(state.currentStep).toBe(1);
      expect(state.startedAt).toBeInstanceOf(Date);
    });

    it("should call API endpoint when starting tutorial", async () => {
      const { startTutorial } = tutorialStore.getState();

      await startTutorial();

      expect(mockFetch).toHaveBeenCalledWith("/api/tutorial/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });
    });

    it("should persist startTutorial state to localStorage", async () => {
      const { startTutorial } = tutorialStore.getState();

      await startTutorial();

      expect(localStorageMock.setItem).toHaveBeenCalled();
      const calledWith = localStorageMock.setItem.mock.calls[0];
      expect(calledWith[0]).toBe("shop-tutorial-storage");

      const savedData = JSON.parse(calledWith[1] as string);
      // zustand persist stores data as { state: {...}, version: 0 }
      expect(savedData.state.isStarted).toBe(true);
      expect(savedData.state.currentStep).toBe(1);
    });
  });

  describe("nextStep action", () => {
    it("should increment current step", () => {
      const { nextStep } = tutorialStore.getState();

      nextStep();
      expect(tutorialStore.getState().currentStep).toBe(2);

      nextStep();
      expect(tutorialStore.getState().currentStep).toBe(3);
    });

    it("should not exceed stepsTotal (8)", () => {
      const { nextStep, jumpToStep } = tutorialStore.getState();

      // Jump to step 8
      jumpToStep(8);

      // Try to go beyond
      nextStep();
      expect(tutorialStore.getState().currentStep).toBe(8);

      nextStep();
      expect(tutorialStore.getState().currentStep).toBe(8);
    });

    it("should persist step change to localStorage", () => {
      const { nextStep } = tutorialStore.getState();

      nextStep();

      expect(localStorageMock.setItem).toHaveBeenCalled();
    });
  });

  describe("previousStep action", () => {
    it("should decrement current step", () => {
      const { previousStep, jumpToStep } = tutorialStore.getState();

      jumpToStep(3);
      expect(tutorialStore.getState().currentStep).toBe(3);

      previousStep();
      expect(tutorialStore.getState().currentStep).toBe(2);

      previousStep();
      expect(tutorialStore.getState().currentStep).toBe(1);
    });

    it("should not go below step 1", () => {
      const { previousStep } = tutorialStore.getState();

      previousStep();
      expect(tutorialStore.getState().currentStep).toBe(1);

      previousStep();
      expect(tutorialStore.getState().currentStep).toBe(1);
    });
  });

  describe("jumpToStep action", () => {
    it("should jump to specified step", () => {
      const { jumpToStep } = tutorialStore.getState();

      jumpToStep(3);
      expect(tutorialStore.getState().currentStep).toBe(3);

      jumpToStep(1);
      expect(tutorialStore.getState().currentStep).toBe(1);
    });

    it("should handle jumping to last step", () => {
      const { jumpToStep } = tutorialStore.getState();

      jumpToStep(8);
      expect(tutorialStore.getState().currentStep).toBe(8);
    });
  });

  describe("completeStep action", () => {
    it("should add step to completedSteps", () => {
      const { completeStep } = tutorialStore.getState();

      completeStep(1);
      expect(tutorialStore.getState().completedSteps).toEqual(["step-1"]);

      completeStep(2);
      expect(tutorialStore.getState().completedSteps).toEqual([
        "step-1",
        "step-2",
      ]);
    });

    it("should not duplicate step in completedSteps", () => {
      const { completeStep } = tutorialStore.getState();

      completeStep(1);
      completeStep(1);
      expect(tutorialStore.getState().completedSteps).toEqual(["step-1"]);
    });
  });

  describe("skipTutorial action", () => {
    it("should mark tutorial as skipped", async () => {
      const { skipTutorial } = tutorialStore.getState();

      await skipTutorial();

      const state = tutorialStore.getState();
      expect(state.isSkipped).toBe(true);
      expect(state.isCompleted).toBe(false);
      expect(state.completedAt).toBeInstanceOf(Date);
    });

    it("should call API endpoint when skipping tutorial", async () => {
      const { skipTutorial } = tutorialStore.getState();

      await skipTutorial();

      expect(mockFetch).toHaveBeenCalledWith("/api/tutorial/skip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });
    });

    it("should persist skipTutorial state to localStorage", async () => {
      const { skipTutorial } = tutorialStore.getState();

      await skipTutorial();

      expect(localStorageMock.setItem).toHaveBeenCalled();
      const savedData = JSON.parse(localStorageMock.setItem.mock.calls[0][1] as string);
      // zustand persist stores data as { state: {...}, version: 0 }
      expect(savedData.state.isSkipped).toBe(true);
    });
  });

  describe("completeTutorial action", () => {
    it("should mark tutorial as completed", async () => {
      const { completeTutorial } = tutorialStore.getState();

      await completeTutorial();

      const state = tutorialStore.getState();
      expect(state.isCompleted).toBe(true);
      expect(state.completedAt).toBeInstanceOf(Date);
      expect(state.currentStep).toBe(8);
      expect(state.completedSteps).toEqual([
        "step-1",
        "step-2",
        "step-3",
        "step-4",
        "step-5",
        "step-6",
        "step-7",
        "step-8",
      ]);
    });

    it("should call API endpoint when completing tutorial", async () => {
      const { completeTutorial } = tutorialStore.getState();

      await completeTutorial();

      expect(mockFetch).toHaveBeenCalledWith("/api/tutorial/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });
    });
  });

  describe("resetTutorial action", () => {
    it("should reset all state to initial values", async () => {
      const { startTutorial, completeStep, resetTutorial } = tutorialStore.getState();

      // Set some state
      await startTutorial();
      completeStep(1);
      completeStep(2);

      // Reset
      await resetTutorial();

      const state = tutorialStore.getState();
      expect(state.currentStep).toBe(1);
      expect(state.completedSteps).toEqual([]);
      expect(state.isStarted).toBe(false);
      expect(state.isCompleted).toBe(false);
      expect(state.isSkipped).toBe(false);
      expect(state.startedAt).toBe(null);
      expect(state.completedAt).toBe(null);
    });

    it("should call API endpoint when resetting tutorial", async () => {
      const { resetTutorial } = tutorialStore.getState();

      await resetTutorial();

      expect(mockFetch).toHaveBeenCalledWith("/api/tutorial/reset", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });
    });

    it("should remove stored data from localStorage on reset", async () => {
      const { startTutorial, resetTutorial } = tutorialStore.getState();

      await startTutorial();

      // Reset
      await resetTutorial();

      // After reset, state should be initial
      const state = tutorialStore.getState();
      expect(state.isStarted).toBe(false);
      expect(state.currentStep).toBe(1);
    });
  });

  describe("localStorage persistence", () => {
    it("should persist state to localStorage when actions are called", async () => {
      const { startTutorial } = tutorialStore.getState();

      await startTutorial();

      expect(localStorageMock.setItem).toHaveBeenCalled();
      const storedData = JSON.parse(localStorageMock.setItem.mock.calls[0][1] as string);

      // zustand persist stores data as { state: {...}, version: 0 }
      expect(storedData.state).toEqual(
        expect.objectContaining({
          isStarted: true,
          currentStep: 1,
          completedSteps: [],
        })
      );
    });
  });

  describe("edge cases", () => {
    it("should handle rapid step changes", () => {
      const { nextStep, previousStep } = tutorialStore.getState();

      nextStep();
      nextStep();
      previousStep();

      expect(tutorialStore.getState().currentStep).toBe(2);
    });

    it("should handle completing steps out of order", () => {
      const { completeStep } = tutorialStore.getState();

      completeStep(3);
      completeStep(1);
      completeStep(2);

      expect(tutorialStore.getState().completedSteps).toEqual([
        "step-3",
        "step-1",
        "step-2",
      ]);
    });

    it("should maintain state consistency across multiple actions", async () => {
      const { startTutorial, completeStep, nextStep, resetTutorial } = tutorialStore.getState();

      await startTutorial();
      completeStep(1);
      nextStep();
      completeStep(2);

      expect(tutorialStore.getState().completedSteps).toEqual(["step-1", "step-2"]);

      await resetTutorial();
      expect(tutorialStore.getState().completedSteps).toEqual([]);
    });
  });

  describe("API error handling", () => {
    it("should handle API errors gracefully in skipTutorial", async () => {
      const { skipTutorial } = tutorialStore.getState();
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      // Should not throw error
      await expect(skipTutorial()).resolves.not.toThrow();
    });

    it("should handle API errors gracefully in completeTutorial", async () => {
      const { completeTutorial } = tutorialStore.getState();
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      await expect(completeTutorial()).resolves.not.toThrow();
    });

    it("should handle API errors gracefully in resetTutorial", async () => {
      const { resetTutorial } = tutorialStore.getState();
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      await expect(resetTutorial()).resolves.not.toThrow();
    });
  });
});
