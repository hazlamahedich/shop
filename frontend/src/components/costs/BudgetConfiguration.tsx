/**
 * Budget Configuration Component
 *
 * Provides budget cap management interface:
 * - Display current budget cap with edit capability
 * - Show current spend vs budget with percentage
 * - Inline validation for invalid inputs
 * - Immediate save on valid input change
 *
 * Story 3-6: Budget Cap Configuration
 */

import { useState, useEffect } from 'react';
import { DollarSign, Save, AlertCircle } from 'lucide-react';
import { useCostTrackingStore } from '../../stores/costTrackingStore';
import { formatCost } from '../../types/cost';
import { useToast } from '../../context/ToastContext';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/Dialog';

interface BudgetConfigurationProps {
  currentSpend?: number;
}

const DEFAULT_BUDGET_CAP = 50;

export const BudgetConfiguration = ({ currentSpend = 0 }: BudgetConfigurationProps) => {
  const {
    merchantSettings,
    merchantSettingsLoading,
    merchantSettingsError,
    updateMerchantSettings,
    getMerchantSettings,
    clearErrors,
  } = useCostTrackingStore();

  const { toast } = useToast();

  // Local state for budget editing
  const [budgetInput, setBudgetInput] = useState<string>(() => {
    if (merchantSettings?.budgetCap === null) return '';
    return (merchantSettings?.budgetCap ?? DEFAULT_BUDGET_CAP).toString();
  });
  const [validationError, setValidationError] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  // Track errors we've already shown to prevent repetitive toasts
  const [shownErrors, setShownErrors] = useState<Set<string>>(new Set());

  // Sync with store when merchant settings change
  useEffect(() => {
    if (merchantSettings?.budgetCap === null) {
      setBudgetInput('');
    } else if (merchantSettings?.budgetCap !== undefined) {
      setBudgetInput(merchantSettings.budgetCap.toString());
    }
  }, [merchantSettings?.budgetCap]);

  // Load merchant settings on mount
  useEffect(() => {
    getMerchantSettings();
  }, [getMerchantSettings]);

  // Show error toasts from store (only show once per unique error)
  useEffect(() => {
    if (merchantSettingsError && !shownErrors.has(merchantSettingsError)) {
      toast(merchantSettingsError, 'error');
      setShownErrors((prev) => new Set(prev).add(merchantSettingsError));
      // Clear the error from the store after showing it
      clearErrors();
    }
  }, [merchantSettingsError, toast, shownErrors, clearErrors]);

  // Validate budget input
  const validateBudget = (value: string): string => {
    if (value === '') {
      return 'Budget amount is required';
    }

    const numValue = parseFloat(value);

    if (isNaN(numValue)) {
      return 'Budget must be a valid number';
    }

    if (numValue < 0) {
      return 'Budget cannot be negative';
    }

    if (numValue === 0) {
      return 'Budget cannot be zero. Use null for no limit or enter a positive amount.';
    }

    return '';
  };

  // Handle input change with validation
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setBudgetInput(value);

    // Clear error on input
    setValidationError('');

    // Validate
    const error = validateBudget(value);
    if (error) {
      setValidationError(error);
    }
  };

  // Handle save
  const handleSave = async () => {
    const error = validateBudget(budgetInput);
    if (error) {
      setValidationError(error);
      return;
    }

    const newBudget = parseFloat(budgetInput);

    setIsSaving(true);
    try {
      await updateMerchantSettings(newBudget);
      toast('Budget cap saved successfully', 'success');
      // Refresh settings to ensure UI is in sync
      getMerchantSettings();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to save budget cap';
      toast(errorMessage, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  // Calculate budget percentage
  const parsedBudget = parseFloat(budgetInput) || DEFAULT_BUDGET_CAP;
  const budgetPercentage =
    parsedBudget > 0 ? Math.min((currentSpend / parsedBudget) * 100, 100) : 0;

  return (
    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-bold text-gray-900">Budget Overview</h3>
      </div>

      <div className="space-y-4">
        {/* Budget Input Section */}
        <div className="space-y-3">
          <div>
            <label htmlFor="budget-input" className="block text-sm font-medium text-gray-700 mb-1">
              Monthly Budget Cap
            </label>
            <div className="relative">
              <DollarSign
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                size={16}
              />
              <input
                id="budget-input"
                type="number"
                value={budgetInput}
                onChange={handleInputChange}
                step="0.01"
                min="0"
                disabled={merchantSettingsLoading || isSaving}
                className={`w-full pl-9 pr-4 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all ${
                  validationError ? 'border-red-300 bg-red-50' : 'border-gray-200'
                } ${merchantSettingsLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                placeholder="Enter budget amount"
              />
            </div>
            {validationError && (
              <div className="mt-1.5 flex items-start text-xs text-red-600">
                <AlertCircle size={14} className="mr-1 mt-0.5 flex-shrink-0" />
                <span>{validationError}</span>
              </div>
            )}
          </div>

          <button
            onClick={() => setShowConfirmation(true)}
            disabled={!!validationError || isSaving || merchantSettingsLoading}
            className="w-full py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center shadow-sm"
          >
            {isSaving ? (
              <>
                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                Saving...
              </>
            ) : (
              <>
                <Save size={16} className="mr-2" />
                Save Budget
              </>
            )}
          </button>
        </div>

        {/* Budget usage progress (Display only if there's spend) */}
        {currentSpend > 0 && (
          <div className="pt-4 border-t border-gray-100">
            {budgetInput === '' ? (
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 font-medium">Budget Usage</span>
                <span className="font-medium text-gray-500">No Limit Set</span>
              </div>
            ) : (
              <>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 font-medium">Budget Usage</span>
                  <span className="font-bold text-gray-900">{budgetPercentage.toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full transition-all duration-500 ${
                      budgetPercentage > 90
                        ? 'bg-red-500'
                        : budgetPercentage > 70
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                    }`}
                    style={{ width: `${budgetPercentage}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-2">
                  <span>{formatCost(currentSpend, 2)} spent</span>
                  <span>of {formatCost(parsedBudget, 2)} budget</span>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Confirmation Dialog */}
      <Dialog open={showConfirmation} onOpenChange={setShowConfirmation}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Budget Update</DialogTitle>
            <DialogDescription>
              Are you sure you want to update your monthly budget cap to{' '}
              <span className="font-bold text-gray-900">
                {formatCost(parseFloat(budgetInput) || 0, 2)}
              </span>
              ? This will be used to monitor your spending and send alerts if exceeded.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-6 flex space-x-2">
            <button
              onClick={() => {
                setShowConfirmation(false);
                handleSave();
              }}
              disabled={isSaving}
              className="flex-1 py-1.5 px-3 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {isSaving ? 'Updating...' : 'Confirm Update'}
            </button>
            <button
              onClick={() => setShowConfirmation(false)}
              disabled={isSaving}
              className="flex-1 py-1.5 px-3 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BudgetConfiguration;
