import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface TutorialState {
  // Tutorial progress
  currentStep: number;
  completedSteps: string[];
  isStarted: boolean;
  isCompleted: boolean;
  isSkipped: boolean;
  startedAt: Date | null;
  completedAt: Date | null;
  stepsTotal: number;

  // Actions
  reset: () => void;
  startTutorial: () => Promise<void>;
  nextStep: () => void;
  previousStep: () => void;
  jumpToStep: (step: number) => void;
  completeStep: (step: number) => void;
  skipTutorial: () => Promise<void>;
  completeTutorial: () => Promise<void>;
  resetTutorial: () => Promise<void>;
}

const API_BASE = '/api/tutorial';

export const useTutorialStore = create<TutorialState>()(
  persist(
    (set, get) => ({
      // Initial state
      currentStep: 1,
      completedSteps: [],
      isStarted: false,
      isCompleted: false,
      isSkipped: false,
      startedAt: null,
      completedAt: null,
      stepsTotal: 8,

      // Actions
      reset: () =>
        set({
          currentStep: 1,
          completedSteps: [],
          isStarted: false,
          isCompleted: false,
          isSkipped: false,
          startedAt: null,
          completedAt: null,
        }),

      startTutorial: async () => {
        console.log('[tutorialStore] Starting tutorial...');
        try {
          const response = await fetch(`${API_BASE}/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include', // Include httpOnly cookies
          });

          console.log('[tutorialStore] Start response:', response.status, response.statusText);

          if (!response.ok) {
            throw new Error(`Failed to start tutorial: ${response.statusText}`);
          }

          const data = await response.json();
          console.log('[tutorialStore] Start response data:', data);

          set({
            isStarted: true,
            startedAt: new Date(),
            currentStep: 1,
          });
          console.log('[tutorialStore] Tutorial started, state updated');
        } catch (error) {
          console.error('[tutorialStore] Failed to start tutorial:', error);
          // Set started state anyway so tutorial can proceed
          set({
            isStarted: true,
            startedAt: new Date(),
            currentStep: 1,
          });
        }
      },

      nextStep: () =>
        set((state) => ({
          currentStep: Math.min(state.currentStep + 1, state.stepsTotal),
        })),

      previousStep: () =>
        set((state) => ({
          currentStep: Math.max(state.currentStep - 1, 1),
        })),

      jumpToStep: (step: number) => set({ currentStep: step }),

      completeStep: (step: number) =>
        set((state) => {
          const stepKey = `step-${step}`;
          if (state.completedSteps.includes(stepKey)) {
            return state;
          }
          return {
            completedSteps: [...state.completedSteps, stepKey],
          };
        }),

      skipTutorial: async () => {
        try {
          const response = await fetch(`${API_BASE}/skip`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include', // Include httpOnly cookies
          });

          if (!response.ok) {
            throw new Error(`Failed to skip tutorial: ${response.statusText}`);
          }

          set({
            isSkipped: true,
            isCompleted: false,
            completedAt: new Date(),
          });
        } catch (error) {
          console.error('Failed to skip tutorial:', error);
          // Set skipped state anyway
          set({
            isSkipped: true,
            isCompleted: false,
            completedAt: new Date(),
          });
        }
      },

      completeTutorial: async () => {
        try {
          const response = await fetch(`${API_BASE}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include', // Include httpOnly cookies
          });

          if (!response.ok) {
            throw new Error(`Failed to complete tutorial: ${response.statusText}`);
          }

          set({
            isCompleted: true,
            completedAt: new Date(),
            currentStep: 8,
            completedSteps: ['step-1', 'step-2', 'step-3', 'step-4', 'step-5', 'step-6', 'step-7', 'step-8'],
          });
        } catch (error) {
          console.error('Failed to complete tutorial:', error);
          // Set completed state anyway
          set({
            isCompleted: true,
            completedAt: new Date(),
            currentStep: 8,
            completedSteps: ['step-1', 'step-2', 'step-3', 'step-4', 'step-5', 'step-6', 'step-7', 'step-8'],
          });
        }
      },

      resetTutorial: async () => {
        try {
          const response = await fetch(`${API_BASE}/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include', // Include httpOnly cookies
          });

          if (!response.ok) {
            throw new Error(`Failed to reset tutorial: ${response.statusText}`);
          }

          set({
            currentStep: 1,
            completedSteps: [],
            isStarted: false,
            isCompleted: false,
            isSkipped: false,
            startedAt: null,
            completedAt: null,
          });
        } catch (error) {
          console.error('Failed to reset tutorial:', error);
          // Reset state anyway
          set({
            currentStep: 1,
            completedSteps: [],
            isStarted: false,
            isCompleted: false,
            isSkipped: false,
            startedAt: null,
            completedAt: null,
          });
        }
      },
    }),
    {
      name: 'shop-tutorial-storage',
      partialize: (state) => ({
        isStarted: state.isStarted,
        isCompleted: state.isCompleted,
        isSkipped: state.isSkipped,
        completedSteps: state.completedSteps,
        currentStep: state.currentStep,
        startedAt: state.startedAt,
        completedAt: state.completedAt,
        stepsTotal: state.stepsTotal,
      }),
    },
  ),
);
