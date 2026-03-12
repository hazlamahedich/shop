import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Onboarding from "../../pages/Onboarding";
import { onboardingStore } from "../../stores/onboardingStore";
import type { OnboardingMode } from "../../types/onboarding";

// Mock the stores
vi.mock("../../stores/deploymentStore", () => ({
  useDeploymentStore: vi.fn(() => ({
    status: "pending",
    merchantKey: null,
  })),
}));

vi.mock("../../stores/integrationsStore", () => ({
  useIntegrationsStore: vi.fn(() => ({
    facebookConnection: { connected: false },
    shopifyConnection: { connected: false },
  })),
}));

vi.mock("../../stores/llmStore", () => ({
  useLLMStore: vi.fn(() => ({
    configuration: { provider: null },
  })),
}));

// Mock InteractiveTutorial to avoid complex rendering
vi.mock("../../components/onboarding/InteractiveTutorial", () => ({
  InteractiveTutorial: ({ onComplete }: { onComplete: () => void }) => (
    <div data-testid="interactive-tutorial">
      <button onClick={onComplete}>Complete Tutorial</button>
    </div>
  ),
}));

// Mock other onboarding components
vi.mock("../../components/onboarding/DeploymentWizard", () => ({
  DeploymentWizard: () => <div data-testid="deployment-wizard">Deployment Wizard</div>,
}));

vi.mock("../../components/onboarding/FacebookConnection", () => ({
  FacebookConnection: () => <div data-testid="facebook-connection">Facebook Connection</div>,
}));

vi.mock("../../components/onboarding/ShopifyConnection", () => ({
  ShopifyConnection: () => <div data-testid="shopify-connection">Shopify Connection</div>,
}));

vi.mock("../../components/onboarding/LLMConfiguration", () => ({
  LLMConfiguration: () => <div data-testid="llm-configuration">LLM Configuration</div>,
}));

const renderOnboarding = () => {
  return render(
    <BrowserRouter>
      <Onboarding />
    </BrowserRouter>
  );
};

describe("Onboarding with Mode Selection", () => {
  beforeEach(() => {
    // Reset store state to initial (no mode selected)
    onboardingStore.setState({
      cloudAccount: false,
      facebookAccount: false,
      shopifyAccess: false,
      llmProviderChoice: false,
      onboardingMode: null,
      updatedAt: null,
    });
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("mode selection appears first (AC1)", () => {
    renderOnboarding();

    // Mode step should be shown (step 0) when no mode is selected
    expect(screen.getByText("Mode")).toBeInTheDocument();
    expect(screen.getByText("AI Chatbot")).toBeInTheDocument();
    expect(screen.getByText("E-commerce Assistant")).toBeInTheDocument();
  });

  it("mode persisted to store when selected", () => {
    renderOnboarding();

    const generalCard = screen.getByTestId("mode-card-general");
    fireEvent.click(generalCard);

    // Advance timers to trigger debounced callback
    act(() => {
      vi.advanceTimersByTime(200);
    });

    const continueButton = screen.getByTestId("mode-continue-button");
    fireEvent.click(continueButton);

    // Mode should be set in the store
    expect(onboardingStore.getState().onboardingMode).toBe("general");
  });

  it("isComplete() returns true for General mode with only 2 prerequisites", () => {
    onboardingStore.setState({
      cloudAccount: true,
      facebookAccount: false,
      shopifyAccess: false,
      llmProviderChoice: true,
      onboardingMode: "general",
    });

    expect(onboardingStore.getState().isComplete()).toBe(true);
  });

  it("isComplete() returns false for E-commerce mode with missing FB/Shopify", () => {
    onboardingStore.setState({
      cloudAccount: true,
      facebookAccount: false,
      shopifyAccess: false,
      llmProviderChoice: true,
      onboardingMode: "ecommerce",
    });

    expect(onboardingStore.getState().isComplete()).toBe(false);
  });

  it("isComplete() returns true for E-commerce mode with all prerequisites", () => {
    onboardingStore.setState({
      cloudAccount: true,
      facebookAccount: true,
      shopifyAccess: true,
      llmProviderChoice: true,
      onboardingMode: "ecommerce",
    });

    expect(onboardingStore.getState().isComplete()).toBe(true);
  });

  it("completedCount() returns correct count for general mode", () => {
    onboardingStore.setState({
      cloudAccount: true,
      facebookAccount: false,
      shopifyAccess: false,
      llmProviderChoice: true,
      onboardingMode: "general",
    });

    expect(onboardingStore.getState().completedCount()).toBe(2);
  });

  it("completedCount() returns correct count for ecommerce mode", () => {
    onboardingStore.setState({
      cloudAccount: true,
      facebookAccount: true,
      shopifyAccess: false,
      llmProviderChoice: true,
      onboardingMode: "ecommerce",
    });

    expect(onboardingStore.getState().completedCount()).toBe(3);
  });

  it("totalCount returns 2 for general mode", () => {
    onboardingStore.setState({
      onboardingMode: "general",
    });

    expect(onboardingStore.getState().totalCount()).toBe(2);
  });

  it("totalCount returns 4 for ecommerce mode", () => {
    onboardingStore.setState({
      onboardingMode: "ecommerce",
    });

    expect(onboardingStore.getState().totalCount()).toBe(4);
  });
});
