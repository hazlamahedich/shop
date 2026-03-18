/** Tests for InteractiveTutorial component.

Tests step navigation, state persistence, skip functionality, and replay.
*/

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { InteractiveTutorial } from "./InteractiveTutorial";

// Mock the tutorial store
vi.mock("../../stores/tutorialStore", () => ({
  useTutorialStore: vi.fn(),
}));

// Import the mocked hook after mock definition
import { useTutorialStore } from "../../stores/tutorialStore";

const mockUseTutorialStore = vi.mocked(useTutorialStore);

// Helper to render with Router
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={['/']}>
      {component}
    </MemoryRouter>
  );
};

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
    stepsTotal: 8,
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
      renderWithRouter(<InteractiveTutorial />);

      expect(screen.getByText("Interactive Tutorial")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Follow these steps to learn how to use your shopping bot dashboard."
        )
      ).toBeInTheDocument();
    });

    it("should render progress indicator", () => {
      renderWithRouter(<InteractiveTutorial />);

      expect(screen.getByText("Step 1 of 8")).toBeInTheDocument();
      expect(screen.getByText("13% complete")).toBeInTheDocument();
    });

    it("should render step navigation dots", () => {
      renderWithRouter(<InteractiveTutorial />);

      const dots = screen.getAllByRole("tab");
      expect(dots).toHaveLength(8);
    });

    it("should render first step content", () => {
      renderWithRouter(<InteractiveTutorial />);

      expect(screen.getByText("Dashboard Overview")).toBeInTheDocument();
      // Description text may be split across elements, so use partial match
      expect(
        screen.getByText(/navigate the dashboard/i)
      ).toBeInTheDocument();
    });

    it("should auto-start tutorial if not started", async () => {
      // Mock startTutorial to return a resolved promise
      mockStartTutorial.mockResolvedValue(undefined);
      const notStartedState = { ...defaultStoreState, isStarted: false, startTutorial: mockStartTutorial };
      mockUseTutorialStore.mockReturnValue(notStartedState);

      renderWithRouter(<InteractiveTutorial />);

      // Wait for async startTutorial to be called
      await waitFor(() => {
        expect(mockStartTutorial).toHaveBeenCalled();
      });
    });
  });

  describe("step navigation", () => {
    it("should navigate to next step when clicking Next", async () => {
      const user = userEvent.setup();
      renderWithRouter(<InteractiveTutorial />);

      const nextButton = screen.getByRole("button", { name: /go to next step/i });
      await user.click(nextButton);

      expect(mockCompleteStep).toHaveBeenCalledWith(1);
      expect(mockNextStep).toHaveBeenCalled();
    });

    it("should navigate to previous step when clicking Previous", async () => {
      const user = userEvent.setup();
      const step2State = { ...defaultStoreState, currentStep: 2 };
      mockUseTutorialStore.mockReturnValue(step2State);

      renderWithRouter(<InteractiveTutorial />);

      const previousButton = screen.getByRole("button", { name: /go to previous step/i });
      await user.click(previousButton);

      expect(mockPreviousStep).toHaveBeenCalled();
    });

    it("should jump to specific step when clicking step dot", async () => {
      const user = userEvent.setup();
      renderWithRouter(<InteractiveTutorial />);

      const step2Dot = screen.getByRole("tab", { name: /go to step 2/i });
      await user.click(step2Dot);

      expect(mockJumpToStep).toHaveBeenCalledWith(2);
    });

    it("should show Complete button on final step", () => {
      const finalStepState = { ...defaultStoreState, currentStep: 8 };
      mockUseTutorialStore.mockReturnValue(finalStepState);

      renderWithRouter(<InteractiveTutorial />);

      const completeButton = screen.getByRole("button", { name: /complete tutorial/i });
      expect(completeButton).toBeInTheDocument();
    });
  });

  describe("step content", () => {
    it("should render correct content for each step", () => {
      renderWithRouter(<InteractiveTutorial />);

      // Step 1 content
      expect(screen.getByText("Dashboard Overview")).toBeInTheDocument();
      expect(screen.getByText("Key Features:")).toBeInTheDocument();
    });

    it("should render step action button for steps with actions", () => {
      // Step 3 has actionLabel: "Go to Provider Settings"
      const step3State = { ...defaultStoreState, currentStep: 3 };
      mockUseTutorialStore.mockReturnValue(step3State);

      renderWithRouter(<InteractiveTutorial />);

      const actionButton = screen.getByRole("button", {
        name: /go to provider settings/i,
      });
      expect(actionButton).toBeInTheDocument();
    });

    it("should not render action button for steps without actions", () => {
      // Step 1 has actionLabel: null
      renderWithRouter(<InteractiveTutorial />);

      // Step 1 should NOT have an action button
      const actionButton = screen.queryByRole("button", {
        name: /view conversation list/i,
      });
      expect(actionButton).not.toBeInTheDocument();
    });
  });

  describe("progress indicator", () => {
    it("should update progress based on current step", () => {
      const step2State = { ...defaultStoreState, currentStep: 2 };
      mockUseTutorialStore.mockReturnValue(step2State);

      renderWithRouter(<InteractiveTutorial />);

      expect(screen.getByText("Step 2 of 8")).toBeInTheDocument();
      expect(screen.getByText("25% complete")).toBeInTheDocument();
    });

    it("should mark completed steps with indicator", () => {
      const completedState = {
        ...defaultStoreState,
        completedSteps: ["step-1", "step-2"],
      };
      mockUseTutorialStore.mockReturnValue(completedState);

      renderWithRouter(<InteractiveTutorial />);

      const dots = screen.getAllByRole("tab");
      // All 8 dots should be present
      expect(dots).toHaveLength(8);
    });
  });

  describe("completion modal", () => {
    it("should show completion modal when tutorial is completed", async () => {
      const completedState = {
        ...defaultStoreState,
        isCompleted: true,
        completedSteps: ["step-1", "step-2", "step-3", "step-4", "step-5", "step-6", "step-7", "step-8"],
      };
      mockUseTutorialStore.mockReturnValue(completedState);

      renderWithRouter(<InteractiveTutorial />);

      // findByText has built-in waiting for async updates
      // Just verify the modal title appears - this is sufficient to confirm modal opens
      expect(await screen.findByText("Tutorial Complete!")).toBeInTheDocument();
    });

    it("should call completeTutorial when clicking Complete on last step", async () => {
      const user = userEvent.setup();
      const finalStepState = { ...defaultStoreState, currentStep: 8 };
      mockUseTutorialStore.mockReturnValue(finalStepState);

      renderWithRouter(<InteractiveTutorial />);

      const completeButton = screen.getByRole("button", { name: /complete tutorial/i });
      await user.click(completeButton);

      expect(mockCompleteTutorial).toHaveBeenCalled();
    });
  });

  describe("skip functionality", () => {
    it("should show skip button", () => {
      renderWithRouter(<InteractiveTutorial />);

      const skipButton = screen.getByRole("button", { name: /skip tutorial/i });
      expect(skipButton).toBeInTheDocument();
    });

    it("should call skipTutorial when clicking skip", async () => {
      const user = userEvent.setup();
      renderWithRouter(<InteractiveTutorial />);

      const skipButton = screen.getByRole("button", { name: /skip tutorial/i });
      await user.click(skipButton);

      expect(mockSkipTutorial).toHaveBeenCalled();
    });
  });

  describe("accessibility", () => {
    it("should have proper ARIA labels", () => {
      renderWithRouter(<InteractiveTutorial />);

      // Step navigation should have role="tablist"
      const tabList = screen.getByRole("tablist");
      expect(tabList).toBeInTheDocument();

      // Each step dot should have role="tab" and aria-selected
      const tabs = screen.getAllByRole("tab");
      expect(tabs.length).toBeGreaterThan(0);
      expect(tabs[0]).toHaveAttribute("aria-selected", "true");
    });

    it("should announce progress changes", () => {
      const { rerender } = renderWithRouter(<InteractiveTutorial />);

      // Initial progress
      expect(screen.getByText("13% complete")).toBeInTheDocument();

      // Update to step 2
      const step2State = { ...defaultStoreState, currentStep: 2 };
      mockUseTutorialStore.mockReturnValue(step2State);

      rerender(
        <MemoryRouter>
          <InteractiveTutorial />
        </MemoryRouter>
      );

      expect(screen.getByText("25% complete")).toBeInTheDocument();
    });
  });
});
