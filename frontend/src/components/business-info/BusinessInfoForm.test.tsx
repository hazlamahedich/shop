/**
 * Tests for BusinessInfoForm Component
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Tests business info form functionality including:
 * - Input field rendering
 * - Character count display
 * - Field value updates
 * - Validation
 * - Accessibility
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BusinessInfoForm } from './BusinessInfoForm';
import { useBusinessInfoStore } from '../../stores/businessInfoStore';

// Mock the business info store
vi.mock('../../stores/businessInfoStore');

const mockUseBusinessInfoStore = vi.mocked(useBusinessInfoStore);

// Default mock return value
const createMockStore = () => ({
  businessName: null,
  businessDescription: null,
  businessHours: null,
  setBusinessName: vi.fn(),
  setBusinessDescription: vi.fn(),
  setBusinessHours: vi.fn(),
  error: null,
});

describe('BusinessInfoForm', () => {
  let mockStore: ReturnType<typeof createMockStore>;

  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks();
    mockStore = createMockStore();
    mockUseBusinessInfoStore.mockReturnValue(mockStore);
  });

  describe('Rendering', () => {
    it('should render all input fields', () => {
      render(<BusinessInfoForm />);

      expect(screen.getByLabelText(/Business Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Business Description/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Business Hours/i)).toBeInTheDocument();
    });

    it('should display placeholders', () => {
      render(<BusinessInfoForm />);

      const nameInput = screen.getByPlaceholderText(/Alex's Athletic Gear/i);
      const hoursInput = screen.getByPlaceholderText(/9 AM - 6 PM PST/);

      expect(nameInput).toBeInTheDocument();
      expect(hoursInput).toBeInTheDocument();
    });

    it('should display help text for each field', () => {
      render(<BusinessInfoForm />);

      expect(screen.getByText(/The name of your business/i)).toBeInTheDocument();
      expect(screen.getByText(/A brief description that helps the bot/i)).toBeInTheDocument();
      expect(screen.getByText(/Your business operating hours/i)).toBeInTheDocument();
    });

    it('should display character count for description', () => {
      render(<BusinessInfoForm />);

      expect(screen.getByText(/0 \/ 500/i)).toBeInTheDocument();
    });

    it('should display character count for business name', () => {
      render(<BusinessInfoForm />);

      expect(screen.getByText(/0 \/ 100/i)).toBeInTheDocument();
    });
  });

  describe('Input Handling', () => {
    it('should call setBusinessName when name input changes', async () => {
      render(<BusinessInfoForm />);

      const input = screen.getByLabelText(/Business Name/i);
      input.focus();
      await userEvent.paste('Test Business');

      expect(mockStore.setBusinessName).toHaveBeenCalledWith('Test Business');
    });

    it('should call setBusinessDescription when description input changes', async () => {
      render(<BusinessInfoForm />);

      const textarea = screen.getByLabelText(/Business Description/i);
      textarea.focus();
      await userEvent.paste('Test description');

      expect(mockStore.setBusinessDescription).toHaveBeenCalledWith('Test description');
    });

    it('should call setBusinessHours when hours input changes', async () => {
      render(<BusinessInfoForm />);

      const input = screen.getByLabelText(/Business Hours/i);
      input.focus();
      await userEvent.paste('9 AM - 5 PM');

      expect(mockStore.setBusinessHours).toHaveBeenCalledWith('9 AM - 5 PM');
    });

    it('should enforce max length on business name (100 chars)', async () => {
      render(<BusinessInfoForm />);

      const input = screen.getByLabelText(/Business Name/i);
      const longText = 'a'.repeat(150);

      // Use click + paste to test truncation in one call
      input.focus();
      await userEvent.paste(longText);

      // Should be called with truncated value
      expect(mockStore.setBusinessName).toHaveBeenCalledWith('a'.repeat(100));
    });

    it('should enforce max length on description (500 chars)', async () => {
      render(<BusinessInfoForm />);

      const textarea = screen.getByLabelText(/Business Description/i);
      const longText = 'a'.repeat(600);

      // Use click + paste to test truncation in one call
      textarea.focus();
      await userEvent.paste(longText);

      // Should be called with truncated value
      expect(mockStore.setBusinessDescription).toHaveBeenCalledWith('a'.repeat(500));
    });
  });

  describe('Disabled State', () => {
    it('should disable all inputs when disabled prop is true', () => {
      render(<BusinessInfoForm disabled={true} />);

      const nameInput = screen.getByLabelText(/Business Name/i);
      const descInput = screen.getByLabelText(/Business Description/i);
      const hoursInput = screen.getByLabelText(/Business Hours/i);

      expect(nameInput).toBeDisabled();
      expect(descInput).toBeDisabled();
      expect(hoursInput).toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<BusinessInfoForm />);

      const form = screen.getByRole('form', { name: /business information form/i });
      expect(form).toBeInTheDocument();
    });

    it('should have proper descriptions for inputs', () => {
      render(<BusinessInfoForm />);

      const nameInput = screen.getByLabelText(/Business Name/i);
      expect(nameInput).toHaveAttribute('aria-describedby');
    });

    it('should be keyboard navigable', async () => {
      render(<BusinessInfoForm />);

      const nameInput = screen.getByLabelText(/Business Name/i);
      nameInput.focus();
      expect(nameInput).toHaveFocus();

      await userEvent.tab();
      const descInput = screen.getByLabelText(/Business Description/i);
      expect(descInput).toHaveFocus();
    });
  });

  describe('Character Count Colors', () => {
    it('should show red when description is near max', () => {
      mockStore.businessDescription = 'a'.repeat(490);
      mockUseBusinessInfoStore.mockReturnValue(mockStore);

      render(<BusinessInfoForm />);

      const countElement = screen.getByText(/490 \/ 500/i);
      expect(countElement).toHaveClass('text-red-600');
    });
  });

  describe('Error Display', () => {
    it('should display error message when error exists', () => {
      mockStore.error = 'Failed to save business info';
      mockUseBusinessInfoStore.mockReturnValue(mockStore);

      render(<BusinessInfoForm />);

      expect(screen.getByText(/Failed to save business info/i)).toBeInTheDocument();
    });

    it('should display error with alert role', () => {
      mockStore.error = 'Test error';
      mockUseBusinessInfoStore.mockReturnValue(mockStore);

      render(<BusinessInfoForm />);

      const errorElement = screen.getByRole('alert');
      expect(errorElement).toBeInTheDocument();
      expect(errorElement).toHaveTextContent(/Test error/i);
    });
  });
});
