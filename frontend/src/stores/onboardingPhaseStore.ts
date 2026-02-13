/** Onboarding Phase State Management Store.

Tracks overall onboarding progress across all phases:
prerequisites, deployment, integrations, bot configuration, and tutorial.
*/

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type OnboardingPhase =
  | 'landing'
  | 'deploy'
  | 'connect'
  | 'config'
  | 'tutorial'
  | 'complete';

export interface OnboardingPhaseState {
  // Progress tracking
  completedSteps: string[];
  currentPhase: OnboardingPhase;

  // Bot configuration completion (for tutorial trigger)
  personalityConfigured: boolean;
  businessInfoConfigured: boolean;
  botNamed: boolean;
  greetingsConfigured: boolean;
  pinsConfigured: boolean;

  // Overall onboarding status
  isFullyOnboarded: boolean;
  onboardingCompletedAt: Date | null;

  // Actions
  markStepComplete: (step: string) => void;
  updatePhase: (phase: OnboardingPhase) => void;
  markBotConfigComplete: (configType: 'personality' | 'businessInfo' | 'botName' | 'greetings' | 'pins') => void;
  checkOnboardingStatus: () => OnboardingStatus;
  resetOnboarding: () => void;
}

export interface OnboardingStatus {
  isFullyOnboarded: boolean;
  currentPhase: OnboardingPhase;
  nextStep?: string;
  shouldShowTutorial: boolean;
}

const STORAGE_KEY = 'shop_onboarding_phase_progress';

export const useOnboardingPhaseStore = create<OnboardingPhaseState>()(
  persist(
    (set, get) => ({
      // Initial state
      completedSteps: [],
      currentPhase: 'landing',
      personalityConfigured: false,
      businessInfoConfigured: false,
      botNamed: false,
      greetingsConfigured: false,
      pinsConfigured: false,
      isFullyOnboarded: false,
      onboardingCompletedAt: null,

      // Actions
      markStepComplete: (step: string) =>
        set((state) => {
          const newCompletedSteps = [...new Set([...state.completedSteps, step])];
          return {
            completedSteps: newCompletedSteps,
          };
        }),

      updatePhase: (phase: OnboardingPhase) =>
        set({ currentPhase: phase }),

      markBotConfigComplete: (configType) =>
        set((state) => {
          const updates: Partial<OnboardingPhaseState> = {};

          switch (configType) {
            case 'personality':
              updates.personalityConfigured = true;
              break;
            case 'businessInfo':
              updates.businessInfoConfigured = true;
              break;
            case 'botName':
              updates.botNamed = true;
              break;
            case 'greetings':
              updates.greetingsConfigured = true;
              break;
            case 'pins':
              updates.pinsConfigured = true;
              break;
          }

          return { ...state, ...updates };
        }),

      checkOnboardingStatus: (): OnboardingStatus => {
        const state = get();
        const allBotConfigured =
          state.personalityConfigured &&
          state.businessInfoConfigured &&
          state.botNamed;

        const isFullyOnboarded = allBotConfigured;
        const shouldShowTutorial = allBotConfigured;

        // Determine next step if not fully onboarded
        let nextStep: string | undefined;
        if (!isFullyOnboarded) {
          if (!state.personalityConfigured) {
            nextStep = 'Select bot personality';
          } else if (!state.businessInfoConfigured) {
            nextStep = 'Configure business info & FAQ';
          } else if (!state.botNamed) {
            nextStep = 'Set bot name';
          } else if (!state.greetingsConfigured) {
            nextStep = 'Configure greeting templates';
          } else if (!state.pinsConfigured) {
            nextStep = 'Pin featured products';
          }
        }

        return {
          isFullyOnboarded,
          currentPhase: state.currentPhase,
          nextStep,
          shouldShowTutorial,
        };
      },

      resetOnboarding: () =>
        set({
          completedSteps: [],
          currentPhase: 'landing',
          personalityConfigured: false,
          businessInfoConfigured: false,
          botNamed: false,
          greetingsConfigured: false,
          pinsConfigured: false,
          isFullyOnboarded: false,
          onboardingCompletedAt: null,
        }),
    }),
    {
      name: STORAGE_KEY,
      partialize: (state) => ({
        completedSteps: state.completedSteps,
        currentPhase: state.currentPhase,
        personalityConfigured: state.personalityConfigured,
        businessInfoConfigured: state.businessInfoConfigured,
        botNamed: state.botNamed,
        greetingsConfigured: state.greetingsConfigured,
        pinsConfigured: state.pinsConfigured,
        isFullyOnboarded: state.isFullyOnboarded,
      }),
    }
  )
);
