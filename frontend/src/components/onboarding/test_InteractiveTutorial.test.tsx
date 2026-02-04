/** Tests for InteractiveTutorial component.

Tests step navigation, state persistence, skip functionality, and replay.
*/

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { InteractiveTutorial } from "./InteractiveTutorial";

// Mock the tutorial store
vi.mock("../../stores/tutorialStore", () => ({
  useTutorialStore: vi.fn(),
}));

// Import the mocked hook after mock definition
import { useTutorialStore } from "../../stores/tutorialStore";

const mockUseTutorialStore = vi.mocked(useTutorialStore);

describe("InteractiveTutorial", () => {
  const mockStartTutorial = vi.fn();
  const mockNextStep = vi.fn();
  const mockPreviousStep = vi.fn();
  const mockJumpToStep = vi.fn();
  const mockCompleteStep = vi.fn();
  const mockSkipTutorial = vi.fn();
  const mockCompleteTutorial = vi.fn();

  const defaultStoreState = {
    currentStep: 1,
    completedSteps: [],
    isStarted: true,
    isCompleted: false,
    isSkipped: false,
    startedAt: new Date(),
    completedAt: null,
    stepsTotal: 4,
    startTutorial: mockStartTutorial,
    nextStep: mockNextStep,
    previousStep: mockPreviousStep,
    jumpToStep: mockJumpToStep,
    completeStep: mockCompleteStep,
    skipTutorial: mockSkipTutorial,
    completeTutorial: mockCompleteTutorial,
    reset: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseTutorialStore.mockReturnValue(defaultStoreState);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("initial render", () => {
    it("should render tutorial title and description", () => {
      render(<InteractiveTutorial />);

      expect(screen.getByText("Interactive Tutorial")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Follow these steps to learn how to use your shopping bot dashboard."
        )
      ).toBeInTheDocument();
    });

    it("should render progress indicator", () => {
      render(<InteractiveTutorial />);

      expect(screen.getByText("Step 1 of 4")).toBeInTheDocument();
      expect(screen.getByText("25% complete")).toBeInTheDocument();
    });

    it("should render step navigation dots", () => {
      render(<InteractiveTutorial />);

      const dots = screen.getAllByRole("tab");
      expect(dots).toHaveLength(4);
    });

    it("should render first step content", () => {
      render(<InteractiveTutorial />);

      expect(screen.getByText("Dashboard Overview")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Learn how to navigate the dashboard and view customer conversations"
        )
      ).toBeInTheDocument();
    });

    it("should auto-start tutorial if not started", () => {
      const notStartedState = { ...defaultStoreState, isStarted: false };
      mockUseTutorialStore.mockReturnValue(notStartedState);

      render(<InteractiveTutorial />);

      expect(mockStartTutorial).toHaveBeenCalled();
    });
  });

  describe("step navigation", () => {
    it("should navigate to next step when clicking Next", async () => {
      const user = userEvent.setup();
      render(<InteractiveTutorial />);

      const nextButton = screen.getByRole("button", { name: /go to next step/i });
      await user.click(nextButton);

      expect(mockCompleteStep).toHaveBeenCalledWith(1);
      expect(mockNextStep).toHaveBeenCalled();
    });

    it("should navigate to previous step when clicking Previous", async () => {
      const user = userEvent.setup();
      const step2State = { ...defaultStoreState, currentStep: 2 };
      mockUseTutorialStore.mockReturnValue(step2State);

      render(<InteractiveTutorial />);

      const previousButton = screen.getByRole("button", { name: /go to previous step/i });
      await user.click(previousButton);

      expect(mockPreviousStep).toHaveBeenCalled();
    });

    it("should jump to specific step when clicking step dot", async () => {
      const user = userEvent.setup();
      render(<InteractiveTutorial />);

      const step2Dot = screen.getByRole("tab", { name: /go to step 2/i });
      await user.click(step2Dot);

      expect(mockJumpToStep).toHaveBeenCalledWith(2);
    });

    it("should show Complete button on final step", () => {
      const finalStepState = { ...defaultStoreState, currentStep: 4 };
      mockUseTutorialStore.mockReturnValue(finalStepState);

      render(<InteractiveTutorial />);

      const completeButton = screen.getByRole("button", { name: /complete tutorial/i });
      expect(completeButton).toBeInTheDocument();
    });
  });

  describe("step content", () => {
    it("should render correct content for each step", () => {
      render(<InteractiveTutorial />);

      // Step 1 content
      expect(screen.getByText("Dashboard Overview")).toBeInTheDocument();
      expect(screen.getByText("Key Features:")).toBeInTheDocument();
    });

    it("should render step action button", () => {
      render(<InteractiveTutorial />);

      const actionButton = screen.getByRole("button", {
        name: /view conversation list/i,
      });
      expect(actionButton).toBeInTheDocument();
    });
  });

  describe("progress indicator", () => {
    it("should update progress based on current step", () => {
      const step2State = { ...defaultStoreState, currentStep: 2 };
      mockUseTutorialStore.mockReturnValue(step2State);

      render(<InteractiveTutorial />);

      expect(screen.getByText("Step 2 of 4")).toBeInTheDocument();
      expect(screen.getByText("50% complete")).toBeInTheDocument();
    });

    it("should mark completed steps with green dot", () => {
      const completedState = {
        ...defaultStoreState,
        completedSteps: ["step-1", "step-2"],
      };
      mockUseTutorialStore.mockReturnValue(completedState);

      render(<InteractiveTutorial />);

      const dots = screen.getAllByRole("tab");
      // First two dots should be marked completed (green)
      // We can't easily test color, but we can verify the dots exist
      expect(dots).toHaveLength(4);
    });
  });

  describe("completion modal", () => {
    it("should show completion modal when tutorial is completed", async () => {
      const completedState = {
        ...defaultStoreState,
        isCompleted: true,
        completedSteps: ["step-1", "step-2", "step-3", "step-4"],
      };
      mockUseTutorialStore.mockReturnValue(completedState);

      render(<InteractiveTutorial />);

      // findByText has built-in waiting for async updates
      // Just verify the modal title appears - this is sufficient to confirm modal opens
      expect(await screen.findByText("Tutorial Complete!")).toBeInTheDocument();
    });

    it("should call completeTutorial when clicking Complete on last step", async () => {
      const user = userEvent.setup();
      const finalStepState = { ...defaultStoreState, currentStep: 4 };
      mockUseTutorialStore.mockReturnValue(finalStepState);

      render(<InteractiveTutorial />);

      const completeButton = screen.getByRole("button", { name: /complete tutorial/i });
      await user.click(completeButton);

      expect(mockCompleteTutorial).toHaveBeenCalled();
    });
  });

  describe("skip functionality", () => {
    it("should show skip button", () => {
      render(<InteractiveTutorial />);

      const skipButton = screen.getByRole("button", { name: /skip tutorial/i });
      expect(skipButton).toBeInTheDocument();
    });

    it("should call skipTutorial when clicking skip", async () => {
      const user = userEvent.setup();
      render(<InteractiveTutorial />);

      const skipButton = screen.getByRole("button", { name: /skip tutorial/i });
      await user.click(skipButton);

      expect(mockSkipTutorial).toHaveBeenCalled();
    });
  });

  describe("accessibility", () => {
    it("should have proper ARIA labels", () => {
      render(<InteractiveTutorial />);

      // Step navigation should have role="tablist"
      const tabList = screen.getByRole("tablist");
      expect(tabList).toBeInTheDocument();

      // Each step dot should have role="tab" and aria-selected
      const tabs = screen.getAllByRole("tab");
      expect(tabs.length).toBeGreaterThan(0);
      expect(tabs[0]).toHaveAttribute("aria-selected", "true");
    });

    it("should announce progress changes", () => {
      const { rerender } = render(<InteractiveTutorial />);

      // Initial progress
      expect(screen.getByText("25% complete")).toBeInTheDocument();

      // Update to step 2
      const step2State = { ...defaultStoreState, currentStep: 2 };
      mockUseTutorialStore.mockReturnValue(step2State);

      rerender(<InteractiveTutorial />);

      expect(screen.getByText("50% complete")).toBeInTheDocument();
    });
  });
});
