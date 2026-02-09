/**
 * BudgetConfiguration Component Tests
 *
 * Tests budget cap management interface:
 * - Display mode with current budget
 * - Edit mode with validation
 * - Save and cancel functionality
 * - Budget usage percentage display
 *
 * Story 3-6: Budget Cap Configuration
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, act, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BudgetConfiguration } from './BudgetConfiguration';
import { useCostTrackingStore } from '../../stores/costTrackingStore';
import { ToastProvider } from '../../context/ToastContext';

// Mock the cost tracking store
vi.mock('../../stores/costTrackingStore', () => ({
  useCostTrackingStore: vi.fn(),
}));

const mockUseCostTrackingStore = vi.mocked(useCostTrackingStore);

// Helper to render with ToastProvider
const renderWithToast = (ui: React.ReactElement) => {
  return render(<ToastProvider>{ui}</ToastProvider>);
};

describe('BudgetConfiguration', () => {
  const mockUpdateMerchantSettings = vi.fn();
  const mockGetMerchantSettings = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    mockUseCostTrackingStore.mockReturnValue({
      conversationCosts: {},
      conversationCostsLoading: {},
      conversationCostsError: {},
      costSummary: null,
      previousPeriodSummary: null,
      costSummaryLoading: false,
      costSummaryError: null,
      costSummaryParams: {},
      merchantSettings: { budgetCap: 100, config: {} },
      merchantSettingsLoading: false,
      merchantSettingsError: null,
      budgetRecommendation: null,
      budgetRecommendationLoading: false,
      budgetRecommendationError: null,
      updateMerchantSettings: mockUpdateMerchantSettings,
      getMerchantSettings: mockGetMerchantSettings,
      getBudgetRecommendation: vi.fn(),
      fetchConversationCost: vi.fn(),
      clearConversationCost: vi.fn(),
      fetchCostSummary: vi.fn(),
      setCostSummaryParams: vi.fn(),
      startPolling: vi.fn(),
      stopPolling: vi.fn(),
      setPollingInterval: vi.fn(),
      clearErrors: vi.fn(),
      reset: vi.fn(),
      isPolling: false,
      pollingInterval: 30000,
      lastUpdate: null,
    });
  });

  describe('Display Mode', () => {
    it('displays monthly budget cap title', () => {
      renderWithToast(<BudgetConfiguration />);

      expect(screen.getByText('Monthly Budget Cap')).toBeInTheDocument();
    });

    it('displays current budget amount', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...mockUseCostTrackingStore(),
        merchantSettings: { budgetCap: 150, config: {} },
      });

      renderWithToast(<BudgetConfiguration />);

      expect(screen.getByText('$150.00')).toBeInTheDocument();
    });

    it('shows default budget when no settings exist', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...mockUseCostTrackingStore(),
        merchantSettings: null,
      });

      renderWithToast(<BudgetConfiguration />);

      expect(screen.getByText('$50.00')).toBeInTheDocument();
    });

    it('displays edit button in display mode', () => {
      renderWithToast(<BudgetConfiguration />);

      const editButton = screen.getByRole('button', { name: /edit budget/i });
      expect(editButton).toBeInTheDocument();
    });

    it('shows loading skeleton when loading settings', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...mockUseCostTrackingStore(),
        merchantSettingsLoading: true,
        merchantSettings: null,
      });

      renderWithToast(<BudgetConfiguration />);

      const skeletons = document.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('enters edit mode when edit button is clicked', async () => {
      renderWithToast(<BudgetConfiguration />);

      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await act(async () => {
        await userEvent.click(editButton);
      });

      expect(screen.getByLabelText(/monthly budget/i)).toBeInTheDocument();
    });

    it('loads merchant settings on mount', () => {
      renderWithToast(<BudgetConfiguration />);

      expect(mockGetMerchantSettings).toHaveBeenCalled();
    });
  });

  describe('Budget Usage Display', () => {
    it('does not show usage when current spend is zero', () => {
      renderWithToast(<BudgetConfiguration currentSpend={0} />);

      expect(screen.queryByText(/budget usage/i)).not.toBeInTheDocument();
    });

    it('displays budget usage when current spend > 0', () => {
      renderWithToast(<BudgetConfiguration currentSpend={50} />);

      expect(screen.getByText(/budget usage/i)).toBeInTheDocument();
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('calculates correct budget percentage', () => {
      renderWithToast(<BudgetConfiguration currentSpend={75} />);

      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('caps percentage at 100%', () => {
      renderWithToast(<BudgetConfiguration currentSpend={200} />);

      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('shows spent and budget amounts', () => {
      renderWithToast(<BudgetConfiguration currentSpend={30} />);

      expect(screen.getByText(/\$30\.00 spent/i)).toBeInTheDocument();
      expect(screen.getByText(/of \$100\.00 budget/i)).toBeInTheDocument();
    });

    it('shows green progress bar for low usage (<70%)', () => {
      renderWithToast(<BudgetConfiguration currentSpend={50} />);

      const progressBar = document.querySelector('.bg-green-500');
      expect(progressBar).toBeInTheDocument();
    });

    it('shows yellow progress bar for medium usage (70-90%)', () => {
      renderWithToast(<BudgetConfiguration currentSpend={80} />);

      const progressBar = document.querySelector('.bg-yellow-500');
      expect(progressBar).toBeInTheDocument();
    });

    it('shows red progress bar for high usage (>90%)', () => {
      renderWithToast(<BudgetConfiguration currentSpend={95} />);

      const progressBar = document.querySelector('.bg-red-500');
      expect(progressBar).toBeInTheDocument();
    });
  });

  describe('Edit Mode', () => {
    it('displays budget input field', async () => {
      renderWithToast(<BudgetConfiguration />);

      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await act(async () => {
        await userEvent.click(editButton);
      });

      expect(screen.getByLabelText(/monthly budget/i)).toBeInTheDocument();
    });

    it('pre-fills input with current budget', async () => {
      renderWithToast(<BudgetConfiguration />);

      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await act(async () => {
        await userEvent.click(editButton);
      });

      const input = screen.getByLabelText(/monthly budget/i) as HTMLInputElement;

      // Wait for useEffect to set the input value
      await waitFor(() => {
        expect(input.value).toBe('100');
      });
    });

    it('shows save and cancel buttons', async () => {
      renderWithToast(<BudgetConfiguration />);

      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await act(async () => {
        await userEvent.click(editButton);
      });

      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('validates empty input', async () => {
      renderWithToast(<BudgetConfiguration />);

      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await act(async () => {
        await userEvent.click(editButton);
      });

      const input = screen.getByLabelText(/monthly budget/i);

      await act(async () => {
        await userEvent.clear(input);
        // Trigger input event to validate
        input.value = '';
        input.dispatchEvent(new Event('input', { bubbles: true }));
      });

      await waitFor(() => {
        expect(screen.getByText(/budget amount is required/i)).toBeInTheDocument();
      });
    });

    it('validates non-numeric input', async () => {
      renderWithToast(<BudgetConfiguration />);

      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await act(async () => {
        await userEvent.click(editButton);
      });

      const input = screen.getByLabelText(/monthly budget/i);

      await act(async () => {
        // For type="number" inputs, non-numeric values result in empty string
        // This is correct browser behavior - type="number" prevents non-numeric input
        (input as HTMLInputElement).value = 'abc';
        input.dispatchEvent(new Event('input', { bubbles: true }));
      });

      // The component receives empty string from type="number" with invalid value
      // So it shows "Budget amount is required" rather than "must be a valid number"
      await waitFor(() => {
        expect(screen.getByText(/budget amount is required/i)).toBeInTheDocument();
      });
    });

    it('validates negative numbers', async () => {
      renderWithToast(<BudgetConfiguration />);

      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await act(async () => {
        await userEvent.click(editButton);
      });

      const input = screen.getByLabelText(/monthly budget/i);

      await act(async () => {
        await userEvent.clear(input);
        await userEvent.type(input, '-50');
      });

      await waitFor(() => {
        expect(screen.getByText(/budget cannot be negative/i)).toBeInTheDocument();
      });
    });

    it('validates zero value', async () => {
      renderWithToast(<BudgetConfiguration />);

      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await act(async () => {
        await userEvent.click(editButton);
      });

      const input = screen.getByLabelText(/monthly budget/i);

      await act(async () => {
        await userEvent.clear(input);
        await userEvent.type(input, '0');
      });

      await waitFor(() => {
        expect(screen.getByText(/budget cannot be zero/i)).toBeInTheDocument();
      });
    });

    it('disables save button when validation fails', async () => {
      renderWithToast(<BudgetConfiguration />);

      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await act(async () => {
        await userEvent.click(editButton);
      });

      const input = screen.getByLabelText(/monthly budget/i);
      const saveButton = screen.getByRole('button', { name: /save/i });

      await act(async () => {
        await userEvent.clear(input);
        await userEvent.type(input, '-10');
      });

      await waitFor(() => {
        expect(saveButton).toBeDisabled();
      });
    });

    it('clears validation error on input change', async () => {
      renderWithToast(<BudgetConfiguration />);

      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await act(async () => {
        await userEvent.click(editButton);
      });

      const input = screen.getByLabelText(/monthly budget/i);

      await act(async () => {
        await userEvent.clear(input);
        await userEvent.type(input, '0');
      });

      await waitFor(() => {
        expect(screen.getByText(/budget cannot be zero/i)).toBeInTheDocument();
      });

      await act(async () => {
        await userEvent.clear(input);
        await userEvent.type(input, '50');
      });

      await waitFor(() => {
        expect(screen.queryByText(/budget cannot be zero/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Save Functionality', () => {
    beforeEach(async () => {
      mockUpdateMerchantSettings.mockResolvedValue(undefined);
      renderWithToast(<BudgetConfiguration />);
      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await userEvent.click(editButton);
    });

    it('saves valid budget value', async () => {
      const input = screen.getByLabelText(/monthly budget/i);
      const saveButton = screen.getByRole('button', { name: /save/i });

      await userEvent.clear(input);
      await userEvent.type(input, '200');
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(mockUpdateMerchantSettings).toHaveBeenCalledWith(200);
      });
    });

    it('shows saving state while saving', async () => {
      const input = screen.getByLabelText(/monthly budget/i);
      const saveButton = screen.getByRole('button', { name: /save/i });

      // Make update take some time
      mockUpdateMerchantSettings.mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(undefined), 100))
      );

      await userEvent.clear(input);
      await userEvent.type(input, '200');
      await userEvent.click(saveButton);

      expect(screen.getByText(/saving\.\.\./i)).toBeInTheDocument();
    });

    it('exits edit mode after successful save', async () => {
      const input = screen.getByLabelText(/monthly budget/i);
      const saveButton = screen.getByRole('button', { name: /save/i });

      await userEvent.clear(input);
      await userEvent.type(input, '200');
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(screen.queryByLabelText(/monthly budget/i)).not.toBeInTheDocument();
      });
    });

    it('refreshes settings after save', async () => {
      const input = screen.getByLabelText(/monthly budget/i);
      const saveButton = screen.getByRole('button', { name: /save/i });

      await userEvent.clear(input);
      await userEvent.type(input, '200');
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(mockGetMerchantSettings).toHaveBeenCalled();
      });
    });

    it('handles save error gracefully', async () => {
      mockUpdateMerchantSettings.mockRejectedValue(new Error('Network error'));

      const input = screen.getByLabelText(/monthly budget/i);
      const saveButton = screen.getByRole('button', { name: /save/i });

      await userEvent.clear(input);
      await userEvent.type(input, '200');
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(mockUpdateMerchantSettings).toHaveBeenCalledWith(200);
      });
    });
  });

  describe('Cancel Functionality', () => {
    beforeEach(async () => {
      renderWithToast(<BudgetConfiguration />);
      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await userEvent.click(editButton);
    });

    it('resets input to original value on cancel', async () => {
      const input = screen.getByLabelText(/monthly budget/i);
      const cancelButton = screen.getByRole('button', { name: /cancel/i });

      await userEvent.clear(input);
      await userEvent.type(input, '999');
      await userEvent.click(cancelButton);

      // After cancel, should show display mode with original value
      expect(screen.getByText('$100.00')).toBeInTheDocument();
    });

    it('clears validation errors on cancel', async () => {
      const input = screen.getByLabelText(/monthly budget/i);
      const cancelButton = screen.getByRole('button', { name: /cancel/i });

      await userEvent.clear(input);
      await userEvent.type(input, '-50');

      expect(screen.getByText(/budget cannot be negative/i)).toBeInTheDocument();

      await userEvent.click(cancelButton);

      // Re-enter edit mode to check error is cleared
      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await userEvent.click(editButton);

      expect(screen.queryByText(/budget cannot be negative/i)).not.toBeInTheDocument();
    });

    it('exits edit mode on cancel', async () => {
      const cancelButton = screen.getByRole('button', { name: /cancel/i });

      await userEvent.click(cancelButton);

      expect(screen.queryByLabelText(/monthly budget/i)).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: /edit budget/i })).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('shows error toast when merchantSettingsError exists', async () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...mockUseCostTrackingStore(),
        merchantSettingsError: 'Failed to load settings',
      });

      renderWithToast(<BudgetConfiguration />);

      await waitFor(() => {
        // Toast should be shown (via ToastContext)
        const toastContainer = document.querySelector('.fixed.bottom-5');
        expect(toastContainer).toBeInTheDocument();
      });
    });

    it('does not show edit button while loading', () => {
      mockUseCostTrackingStore.mockReturnValue({
        ...mockUseCostTrackingStore(),
        merchantSettingsLoading: true,
      });

      renderWithToast(<BudgetConfiguration />);

      expect(screen.queryByRole('button', { name: /edit budget/i })).not.toBeInTheDocument();
    });
  });

  describe('Budget Sync', () => {
    it('syncs budget input when store budget changes', async () => {
      const { rerender } = renderWithToast(<BudgetConfiguration />);

      // Initial budget
      expect(screen.getByText('$100.00')).toBeInTheDocument();

      // Update store
      mockUseCostTrackingStore.mockReturnValue({
        ...mockUseCostTrackingStore(),
        merchantSettings: { budgetCap: 250, config: {} },
      });

      rerender(<ToastProvider><BudgetConfiguration /></ToastProvider>);

      expect(screen.getByText('$250.00')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper aria-label on edit button', () => {
      renderWithToast(<BudgetConfiguration />);

      const editButton = screen.getByRole('button', { name: /edit budget/i });
      expect(editButton).toHaveAttribute('aria-label', 'Edit budget');
    });

    it('associates label with input field', async () => {
      renderWithToast(<BudgetConfiguration />);
      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await userEvent.click(editButton);

      const input = screen.getByLabelText(/monthly budget/i);
      expect(input).toHaveAttribute('id', 'budget-input');
    });

    it('disables save button with reason', async () => {
      renderWithToast(<BudgetConfiguration />);
      const editButton = screen.getByRole('button', { name: /edit budget/i });
      await userEvent.click(editButton);

      const input = screen.getByLabelText(/monthly budget/i);
      const saveButton = screen.getByRole('button', { name: /save/i });

      await userEvent.clear(input);
      await userEvent.type(input, '0');

      expect(saveButton).toBeDisabled();
      expect(saveButton).toHaveClass('disabled:cursor-not-allowed');
    });
  });
});
