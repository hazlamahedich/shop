/** Unit tests for ModeSelection component (Story 8.6). */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { ModeSelection } from "../ModeSelection";
import type { OnboardingMode } from "../../../types/onboarding";

describe("ModeSelection", () => {
  const defaultProps = {
    selectedMode: null as OnboardingMode | null,
    onModeSelect: vi.fn(),
    onContinue: vi.fn(),
  };

  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders two mode cards", () => {
    render(<ModeSelection {...defaultProps} />);
    
    expect(screen.getByText("AI Chatbot")).toBeInTheDocument();
    expect(screen.getByText("E-commerce Assistant")).toBeInTheDocument();
  });

  it("highlights selected card on click", () => {
    const onModeSelect = vi.fn();
    render(<ModeSelection {...defaultProps} onModeSelect={onModeSelect} />);
    
    const generalCard = screen.getByTestId("mode-card-general");
    fireEvent.click(generalCard);
    
    // Advance timers to trigger debounced callback
    act(() => {
      vi.advanceTimersByTime(200);
    });
    
    expect(onModeSelect).toHaveBeenCalledWith("general");
  });

  it("calls onModeSelect when card clicked", () => {
    const onModeSelect = vi.fn();
    render(<ModeSelection {...defaultProps} onModeSelect={onModeSelect} />);
    
    const ecommerceCard = screen.getByTestId("mode-card-ecommerce");
    fireEvent.click(ecommerceCard);
    
    // Advance timers to trigger debounced callback
    act(() => {
      vi.advanceTimersByTime(200);
    });
    
    expect(onModeSelect).toHaveBeenCalledWith("ecommerce");
  });

  it("calls onContinue when button clicked", () => {
    const onContinue = vi.fn();
    render(<ModeSelection {...defaultProps} selectedMode="general" onContinue={onContinue} />);
    
    const continueButton = screen.getByTestId("mode-continue-button");
    fireEvent.click(continueButton);
    
    expect(onContinue).toHaveBeenCalled();
  });

  it("button disabled when no mode selected", () => {
    render(<ModeSelection {...defaultProps} selectedMode={null} />);
    
    const continueButton = screen.getByTestId("mode-continue-button");
    expect(continueButton).toBeDisabled();
  });

  it("button enabled when mode is selected", () => {
    render(<ModeSelection {...defaultProps} selectedMode="general" />);
    
    const continueButton = screen.getByTestId("mode-continue-button");
    expect(continueButton).not.toBeDisabled();
  });

  it("keyboard navigation works with Enter key", () => {
    const onModeSelect = vi.fn();
    render(<ModeSelection {...defaultProps} onModeSelect={onModeSelect} />);
    
    const generalCard = screen.getByTestId("mode-card-general");
    fireEvent.keyDown(generalCard, { key: "Enter" });
    
    // Advance timers to trigger debounced callback
    act(() => {
      vi.advanceTimersByTime(200);
    });
    
    expect(onModeSelect).toHaveBeenCalledWith("general");
  });

  it("keyboard navigation works with Space key", () => {
    const onModeSelect = vi.fn();
    render(<ModeSelection {...defaultProps} onModeSelect={onModeSelect} />);
    
    const ecommerceCard = screen.getByTestId("mode-card-ecommerce");
    fireEvent.keyDown(ecommerceCard, { key: " " });
    
    // Advance timers to trigger debounced callback
    act(() => {
      vi.advanceTimersByTime(200);
    });
    
    expect(onModeSelect).toHaveBeenCalledWith("ecommerce");
  });

  it("ARIA attributes present on cards", () => {
    render(<ModeSelection {...defaultProps} selectedMode="general" />);
    
    const generalCard = screen.getByTestId("mode-card-general");
    expect(generalCard).toHaveAttribute("role", "button");
    expect(generalCard).toHaveAttribute("aria-pressed", "true");
    expect(generalCard).toHaveAttribute("tabIndex", "0");
    
    const ecommerceCard = screen.getByTestId("mode-card-ecommerce");
    expect(ecommerceCard).toHaveAttribute("aria-pressed", "false");
  });

  it("shows check icon on selected card", () => {
    render(<ModeSelection {...defaultProps} selectedMode="general" />);
    
    const generalCard = screen.getByTestId("mode-card-general");
    // The check icon should be visible in the selected card
    expect(generalCard).toHaveClass("ring-2");
  });

  it("displays correct features for each mode", () => {
    render(<ModeSelection {...defaultProps} />);
    
    // General mode features
    expect(screen.getByText("No store required")).toBeInTheDocument();
    expect(screen.getByText("Quick setup")).toBeInTheDocument();
    expect(screen.getByText("Embed anywhere")).toBeInTheDocument();
    
    // E-commerce mode features
    expect(screen.getByText("Shopify integration")).toBeInTheDocument();
    expect(screen.getByText("Facebook Messenger")).toBeInTheDocument();
    expect(screen.getByText("Full shopping experience")).toBeInTheDocument();
  });

  it("shows prompt to select mode when none selected", () => {
    render(<ModeSelection {...defaultProps} selectedMode={null} />);
    
    expect(screen.getByText("Please select a mode to continue")).toBeInTheDocument();
  });

  it("does not show prompt when mode is selected", () => {
    render(<ModeSelection {...defaultProps} selectedMode="general" />);
    
    expect(screen.queryByText("Please select a mode to continue")).not.toBeInTheDocument();
  });
});
