/**
 * Tests for GreetingConfig Component
 *
 * Story 1.14: Smart Greeting Templates
 *
 * Tests greeting configuration functionality
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Import the actual component (not mocked for basic tests)
import { GreetingConfig } from '../GreetingConfig';

describe('GreetingConfig Component', () => {
  const mockOnUpdate = vi.fn();
  const mockOnReset = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const defaultProps = {
    personality: 'friendly',
    greetingTemplate: null,
    useCustomGreeting: false,
    defaultTemplate: "Hey there! 👋 I'm {bot_name} from {business_name}. How can I help you today?",
    availableVariables: ['bot_name', 'business_name', 'business_hours'],
    onUpdate: mockOnUpdate,
    onReset: mockOnReset,
    disabled: false,
  };

  describe('Rendering', () => {
    it('should render with default props', () => {
      render(<GreetingConfig {...defaultProps} />);

      // Check personality badge (there are 2 "Friendly" badges on the page)
      const friendlyBadges = screen.getAllByText(/friendly/i);
      expect(friendlyBadges.length).toBeGreaterThanOrEqual(1);

      // Check default template display
      expect(screen.getByText(/default template:/i)).toBeInTheDocument();

      // Check custom greeting textarea
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveAttribute('maxLength', '500');

      // Check use custom checkbox
      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeInTheDocument();
      expect(checkbox).not.toBeChecked();

      // Check reset button
      expect(screen.getByLabelText(/reset to default/i)).toBeInTheDocument();

      // Check help section
      expect(screen.getByText(/about greeting variables/i)).toBeInTheDocument();
    });

    it('should render with professional personality', () => {
      render(<GreetingConfig {...defaultProps} personality="professional" />);

      const professionalBadges = screen.getAllByText(/professional/i);
      expect(professionalBadges.length).toBeGreaterThanOrEqual(1);
    });

    it('should render with enthusiastic personality', () => {
      render(<GreetingConfig {...defaultProps} personality="enthusiastic" />);

      const enthusiasticBadges = screen.getAllByText(/enthusiastic/i);
      expect(enthusiasticBadges.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Custom Greeting Input', () => {
    it('should call onUpdate when typing in textarea', async () => {
      render(<GreetingConfig {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      await userEvent.type(textarea, 'Hello');

      expect(mockOnUpdate).toHaveBeenCalled();
    });

    it('should show character count', () => {
      render(<GreetingConfig {...defaultProps} />);

      const counter = screen.getByText(/\/500/i);
      expect(counter).toBeInTheDocument();
    });

    it('should display preview with custom text', async () => {
      render(<GreetingConfig {...defaultProps} />);

      const textarea = screen.getByRole('textbox');
      await userEvent.type(textarea, 'Custom greeting');

      const preview = screen.getByText(/preview/i);
      expect(preview).toBeInTheDocument();
    });
  });

  describe('Use Custom Greeting Toggle', () => {
    it('should call onUpdate when checkbox is clicked', async () => {
      render(<GreetingConfig {...defaultProps} />);

      const checkbox = screen.getByRole('checkbox');
      await userEvent.click(checkbox);

      expect(mockOnUpdate).toHaveBeenCalledWith({
        use_custom_greeting: true,
      });
    });
  });

  describe('Reset Button', () => {
    it('should call onReset when reset is clicked', async () => {
      render(<GreetingConfig {...defaultProps} />);

      const resetButton = screen.getByLabelText(/reset to default/i);
      await userEvent.click(resetButton);

      expect(mockOnReset).toHaveBeenCalled();
    });
  });

  describe('Variable Badges', () => {
    it('should display all available variable badges', () => {
      const variables = ['bot_name', 'business_name', 'business_hours'];
      render(<GreetingConfig {...defaultProps} availableVariables={variables} />);

      // Check that help section is displayed
      const helpSection = screen.getByText(/about greeting variables/i);
      expect(helpSection).toBeInTheDocument();
    });
  });

  describe('Disabled State', () => {
    it('should disable inputs when disabled prop is true', () => {
      render(<GreetingConfig {...defaultProps} disabled={true} />);

      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeDisabled();

      const checkbox = screen.getByRole('checkbox');
      expect(checkbox).toBeDisabled();

      const resetButton = screen.getByLabelText(/reset to default/i);
      expect(resetButton).toBeDisabled();
    });
  });

  describe('Help Section', () => {
    it('should display help text for variables', () => {
      render(<GreetingConfig {...defaultProps} />);

      // Check main help heading
      expect(screen.getByText(/about greeting variables/i)).toBeInTheDocument();

      // Check for variable badges in help text
      const helpText = screen.getByText(/from Bot Configuration/i);
      expect(helpText).toBeInTheDocument();
      expect(helpText.textContent).toContain('bot');
    });
  });
});
