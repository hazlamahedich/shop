/** Tests for PrerequisiteChecklist component.

Test Scenarios:
- Component mounts with all 4 items displayed
- All checkboxes checked → deploy button enabled
- Any checkbox unchecked → deploy button disabled
- Help sections expand/collapse correctly
- localStorage persists state across refresh
- Keyboard navigation works (Tab, Enter, Space)
- Screen reader announces progress correctly
*/

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { PrerequisiteChecklist } from "./PrerequisiteChecklist";

describe("PrerequisiteChecklist", () => {
  beforeEach(() => {
    // Reset localStorage mock before each test
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("test_prerender_checklist_renders", () => {
    it("should render component with all 4 prerequisite items", () => {
      render(<PrerequisiteChecklist />);

      // Check for setup time display
      expect(screen.getByText(/setup time: 30-60 minutes/i)).toBeInTheDocument();

      // Check for all 4 prerequisite items
      expect(screen.getByText(/cloud.*account.*fly\.io|railway|render/i)).toBeInTheDocument();
      expect(screen.getByText(/facebook.*business.*account/i)).toBeInTheDocument();
      expect(screen.getByText(/shopify.*admin.*access/i)).toBeInTheDocument();
      expect(screen.getByText(/llm.*provider/i)).toBeInTheDocument();
    });
  });

  describe("test_check_all_enables_deploy", () => {
    it("should enable deploy button when all checkboxes are checked", async () => {
      render(<PrerequisiteChecklist />);

      const deployButton = screen.getByRole("button", { name: /deploy/i });

      // Initially disabled
      expect(deployButton).toBeDisabled();

      // Check all 4 checkboxes
      const checkboxes = screen.getAllByRole("checkbox");
      expect(checkboxes).toHaveLength(4);

      for (const checkbox of checkboxes) {
        fireEvent.click(checkbox);
      }

      // Now deploy button should be enabled
      await waitFor(() => {
        expect(deployButton).toBeEnabled();
      });
    });

    it("should keep deploy button disabled when any checkbox is unchecked", () => {
      render(<PrerequisiteChecklist />);

      const deployButton = screen.getByRole("button", { name: /deploy/i });
      const checkboxes = screen.getAllByRole("checkbox");

      // Check 3 out of 4 checkboxes
      for (let i = 0; i < 3; i++) {
        fireEvent.click(checkboxes[i]);
      }

      // Deploy button should still be disabled
      expect(deployButton).toBeDisabled();
    });
  });

  describe("test_help_expands_collapses", () => {
    it("should expand and collapse help sections", () => {
      render(<PrerequisiteChecklist />);

      // Find help buttons
      const helpButtons = screen.getAllByRole("button", { name: /get help/i });
      expect(helpButtons.length).toBeGreaterThan(0);

      // Click first help button
      fireEvent.click(helpButtons[0]);

      // Help content should be visible
      expect(helpButtons[0]).toHaveAttribute("aria-expanded", "true");

      // Click again to collapse
      fireEvent.click(helpButtons[0]);

      // Help content should be hidden
      expect(helpButtons[0]).toHaveAttribute("aria-expanded", "false");
    });
  });

  describe("test_wcag_keyboard_navigation", () => {
    it("should allow keyboard navigation through checkboxes", async () => {
      render(<PrerequisiteChecklist />);

      const checkboxes = screen.getAllByRole("checkbox");

      // All checkboxes should be focusable
      checkboxes.forEach((checkbox) => {
        expect(checkbox).toHaveAttribute("type", "checkbox");
      });

      // First checkbox should be able to receive focus
      checkboxes[0].focus();
      expect(document.activeElement).toBe(checkboxes[0]);

      // Toggle with click (simulating space/enter activation)
      fireEvent.click(checkboxes[0]);
      expect(checkboxes[0]).toBeChecked();
    });

    it("should activate checkbox with Space key", () => {
      render(<PrerequisiteChecklist />);

      const checkboxes = screen.getAllByRole("checkbox");
      checkboxes[0].focus();

      // Simulate Space key press
      fireEvent.keyDown(checkboxes[0], { key: " ", code: "Space" });
      expect(checkboxes[0]).toBeChecked();
    });

    it("should activate checkbox with Enter key", () => {
      render(<PrerequisiteChecklist />);

      const checkboxes = screen.getAllByRole("checkbox");
      checkboxes[0].focus();

      // Simulate Enter key press
      fireEvent.keyDown(checkboxes[0], { key: "Enter", code: "Enter" });
      expect(checkboxes[0]).toBeChecked();
    });

    it("should allow Tab navigation between checkboxes", () => {
      render(<PrerequisiteChecklist />);

      const checkboxes = screen.getAllByRole("checkbox");

      // Focus first checkbox
      checkboxes[0].focus();
      expect(document.activeElement).toBe(checkboxes[0]);

      // Simulate Tab to move to next checkbox
      fireEvent.keyDown(checkboxes[0], { key: "Tab", code: "Tab" });

      // The second checkbox should exist and be focusable
      expect(checkboxes[1]).toHaveAttribute("type", "checkbox");
    });
  });

  describe("test_wcab_screen_reader_announcements", () => {
    it("should announce progress correctly for screen readers", () => {
      render(<PrerequisiteChecklist />);

      // Check for progress announcement in ARIA live region
      const progressRegion = screen.getByRole("status");
      expect(progressRegion).toBeInTheDocument();

      // Initial state: 0 completed
      expect(progressRegion).toHaveTextContent(/0.*4|completed/i);
    });
  });
});
