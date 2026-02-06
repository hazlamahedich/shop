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
      stepsTotal: 4,

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
        try {
          await fetch(`${API_BASE}/start?merchant_id=1`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
          });
        } catch (error) {
          console.error('Failed to start tutorial on server:', error);
        }
        set({
          isStarted: true,
          startedAt: new Date(),
          currentStep: 1,
        });
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
          await fetch(`${API_BASE}/skip?merchant_id=1`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
          });
        } catch (error) {
          console.error('Failed to skip tutorial on server:', error);
        }
        set({
          isSkipped: true,
          isCompleted: false,
          completedAt: new Date(),
        });
      },

      completeTutorial: async () => {
        try {
          await fetch(`${API_BASE}/complete?merchant_id=1`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
          });
        } catch (error) {
          console.error('Failed to complete tutorial on server:', error);
        }
        set({
          isCompleted: true,
          completedAt: new Date(),
          currentStep: 4,
          completedSteps: ['step-1', 'step-2', 'step-3', 'step-4'],
        });
      },

      resetTutorial: async () => {
        try {
          await fetch(`${API_BASE}/reset?merchant_id=1`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
          });
        } catch (error) {
          console.error('Failed to reset tutorial on server:', error);
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
      }),
    }
  )
);
