/** Tests for DeploymentWizard component.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { DeploymentWizard } from "./DeploymentWizard";

// Mock the deployment store
vi.mock("../../stores/deploymentStore", () => ({
  useDeploymentStore: vi.fn(() => ({
    platform: null,
    status: "pending",
    progress: 0,
    logs: [],
    currentStep: null,
    errorMessage: null,
    troubleshootingUrl: null,
    merchantKey: null,
    startDeployment: vi.fn(),
    cancelDeployment: vi.fn(),
    reset: vi.fn(),
    setPlatform: vi.fn(),
  })),
  Platform: {
    FLYIO: "flyio",
    RAILWAY: "railway",
    RENDER: "render",
  },
}));

// Mock the onboarding store
vi.mock("../../stores/onboardingStore", () => ({
  onboardingStore: vi.fn(() => ({
    isComplete: () => true,
  })),
}));

import { useDeploymentStore } from "../../stores/deploymentStore";
import { onboardingStore } from "../../stores/onboardingStore";

describe("DeploymentWizard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset onboardingStore to default (prerequisites complete) before each test
    vi.mocked(onboardingStore).mockReturnValue({
      isComplete: () => true,
    });
  });

  it("renders platform selector when no deployment is active", () => {
    render(<DeploymentWizard />);

    expect(screen.getByText("Deploy Your Bot")).toBeInTheDocument();
    expect(screen.getByText(/Choose your cloud platform/)).toBeInTheDocument();
    expect(screen.getByText(/15m 0s/)).toBeInTheDocument();
  });

  it("shows all platform options with proper accessibility", () => {
    render(<DeploymentWizard />);

    // Check that the Select component is rendered
    const selectElement = screen.getByRole("combobox", { name: /Select deployment platform/i });
    expect(selectElement).toBeInTheDocument();

    // Check that options are available in the select
    expect(selectElement).toHaveTextContent(/Fly\.io \(Recommended\)/);
    expect(selectElement).toHaveTextContent(/Railway/);
    expect(selectElement).toHaveTextContent(/Render/);

    // Verify aria-label is present for accessibility
    expect(selectElement).toHaveAttribute("aria-label", "Select deployment platform");
  });

  it("disables deploy button when no platform is selected", () => {
    render(<DeploymentWizard />);

    const deployButton = screen.getByRole("button", { name: /Select a platform to deploy/i });
    expect(deployButton).toBeDisabled();
  });

  it("enables deploy button when platform is selected and prerequisites complete", async () => {
    const mockSetPlatform = vi.fn();
    vi.mocked(useDeploymentStore).mockReturnValue({
      platform: "flyio" as any,
      status: "pending",
      progress: 0,
      logs: [],
      currentStep: null,
      errorMessage: null,
      troubleshootingUrl: null,
      merchantKey: null,
      startDeployment: vi.fn(),
      cancelDeployment: vi.fn(),
      reset: vi.fn(),
      setPlatform: mockSetPlatform,
    });

    render(<DeploymentWizard />);

    const deployButton = screen.getByRole("button", { name: /Deploy to Fly\.io/i });
    expect(deployButton).not.toBeDisabled();
  });

  it("disables deploy button when prerequisites are incomplete", () => {
    vi.mocked(onboardingStore).mockReturnValue({
      isComplete: () => false,
    });

    render(<DeploymentWizard />);

    const deployButton = screen.getByRole("button", { name: /Complete all prerequisites first/i });
    expect(deployButton).toBeDisabled();
  });

  it("shows progress bar during deployment", () => {
    vi.mocked(useDeploymentStore).mockReturnValue({
      platform: "flyio" as any,
      status: "in-progress",
      progress: 45,
      logs: [],
      currentStep: "deploy",
      errorMessage: null,
      troubleshootingUrl: null,
      merchantKey: null,
      startDeployment: vi.fn(),
      cancelDeployment: vi.fn(),
      reset: vi.fn(),
      setPlatform: vi.fn(),
    });

    render(<DeploymentWizard />);

    expect(screen.getByText(/45%/)).toBeInTheDocument();
    expect(screen.getByText(/Deployment Progress/)).toBeInTheDocument();
  });

  it("shows deployment logs with proper accessibility attributes", () => {
    const mockLogs = [
      {
        timestamp: "2026-02-03T12:00:00Z",
        level: "info" as const,
        message: "Starting deployment process",
      },
      {
        timestamp: "2026-02-03T12:01:00Z",
        level: "warning" as const,
        message: "Container build taking longer than expected",
      },
    ];

    vi.mocked(useDeploymentStore).mockReturnValue({
      platform: "flyio" as any,
      status: "in-progress",
      progress: 30,
      logs: mockLogs,
      currentStep: "build",
      errorMessage: null,
      troubleshootingUrl: null,
      merchantKey: null,
      startDeployment: vi.fn(),
      cancelDeployment: vi.fn(),
      reset: vi.fn(),
      setPlatform: vi.fn(),
    });

    render(<DeploymentWizard />);

    expect(screen.getByText(/Starting deployment process/)).toBeInTheDocument();
    expect(screen.getByText(/Container build taking longer than expected/)).toBeInTheDocument();

    // Verify accessibility attributes for logs
    const logsContainer = screen.getByRole("log");
    expect(logsContainer).toHaveAttribute("aria-live", "polite");
    expect(logsContainer).toHaveAttribute("aria-atomic", "true");
    expect(logsContainer).toHaveAttribute("aria-labelledby", "deployment-logs-title");
  });

  it("shows success message when deployment completes", () => {
    vi.mocked(useDeploymentStore).mockReturnValue({
      platform: "railway" as any,
      status: "success",
      progress: 100,
      logs: [],
      currentStep: null,
      errorMessage: null,
      troubleshootingUrl: null,
      merchantKey: "shop-abc123",
      startDeployment: vi.fn(),
      cancelDeployment: vi.fn(),
      reset: vi.fn(),
      setPlatform: vi.fn(),
    });

    render(<DeploymentWizard />);

    expect(screen.getByText(/Deployment Successful/)).toBeInTheDocument();
    expect(screen.getByText(/shop-abc123/)).toBeInTheDocument();
    expect(screen.getByText(/Connect your Facebook Page/)).toBeInTheDocument();
  });

  it("shows error message when deployment fails", () => {
    vi.mocked(useDeploymentStore).mockReturnValue({
      platform: "render" as any,
      status: "failed",
      progress: 70,
      logs: [],
      currentStep: null,
      errorMessage: "Container build timeout",
      troubleshootingUrl: "https://docs.example.com/troubleshoot",
      merchantKey: null,
      startDeployment: vi.fn(),
      cancelDeployment: vi.fn(),
      reset: vi.fn(),
      setPlatform: vi.fn(),
    });

    render(<DeploymentWizard />);

    // "Deployment Failed" appears in both Badge and Alert title
    expect(screen.getAllByText(/Deployment Failed/)).toHaveLength(2);
    expect(screen.getByText(/Container build timeout/)).toBeInTheDocument();
    const troubleshootLink = screen.getByRole("link", { name: /troubleshooting/i });
    expect(troubleshootLink).toBeInTheDocument();
  });

  it("calls startDeployment when deploy button is clicked", async () => {
    const mockStartDeployment = vi.fn();

    vi.mocked(useDeploymentStore).mockReturnValue({
      platform: "flyio" as any,
      status: "pending",
      progress: 0,
      logs: [],
      currentStep: null,
      errorMessage: null,
      troubleshootingUrl: null,
      merchantKey: null,
      startDeployment: mockStartDeployment,
      cancelDeployment: vi.fn(),
      reset: vi.fn(),
      setPlatform: vi.fn(),
    });

    render(<DeploymentWizard />);

    const deployButton = screen.getByRole("button", { name: /Deploy to Fly\.io/i });
    fireEvent.click(deployButton);

    await waitFor(() => {
      expect(mockStartDeployment).toHaveBeenCalledWith("flyio");
    });
  });

  it("calls cancelDeployment when cancel button is clicked", async () => {
    const mockCancelDeployment = vi.fn();

    vi.mocked(useDeploymentStore).mockReturnValue({
      platform: "railway" as any,
      status: "in-progress",
      progress: 50,
      logs: [],
      currentStep: "deploy",
      errorMessage: null,
      troubleshootingUrl: null,
      merchantKey: null,
      startDeployment: vi.fn(),
      cancelDeployment: mockCancelDeployment,
      reset: vi.fn(),
      setPlatform: vi.fn(),
    });

    render(<DeploymentWizard />);

    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(mockCancelDeployment).toHaveBeenCalled();
    });
  });
});
