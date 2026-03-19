/**
 * Budget Configuration Component - Industrial Technical Dashboard
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
import { DollarSign, Save, AlertCircle, Infinity } from 'lucide-react';
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

  const [budgetInput, setBudgetInput] = useState<string>(() => {
    if (merchantSettings?.budgetCap === null) return '';
    return (merchantSettings?.budgetCap ?? DEFAULT_BUDGET_CAP).toString();
  });
  const [validationError, setValidationError] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [showNoLimitConfirmation, setShowNoLimitConfirmation] = useState(false);
  const [shownErrors, setShownErrors] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (merchantSettings?.budgetCap === null) {
      setBudgetInput('');
    } else if (merchantSettings?.budgetCap !== undefined) {
      setBudgetInput(merchantSettings.budgetCap.toString());
    }
  }, [merchantSettings?.budgetCap]);

  useEffect(() => {
    getMerchantSettings();
  }, [getMerchantSettings]);

  useEffect(() => {
    if (merchantSettingsError && !shownErrors.has(merchantSettingsError)) {
      toast(merchantSettingsError, 'error');
      setShownErrors((prev) => new Set(prev).add(merchantSettingsError));
      clearErrors();
    }
  }, [merchantSettingsError, toast, shownErrors, clearErrors]);

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

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setBudgetInput(value);
    setValidationError('');
    const error = validateBudget(value);
    if (error) {
      setValidationError(error);
    }
  };

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
      getMerchantSettings();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to save budget cap';
      toast(errorMessage, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemoveBudgetCap = async () => {
    setIsSaving(true);
    try {
      await updateMerchantSettings(null as any);
      toast('Budget cap removed. No limit set.', 'success');
      getMerchantSettings();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to remove budget cap';
      toast(errorMessage, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const newBudgetValue = parseFloat(budgetInput) || 0;
  const isBelowCurrentSpend = currentSpend > 0 && newBudgetValue > 0 && newBudgetValue < currentSpend;
  const budgetPercentage = newBudgetValue > 0 ? Math.min((currentSpend / newBudgetValue) * 100, 100) : 0;

  return (
    <div className="bg-[#0A0A0A] border border-emerald-500/15 p-6">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-sm font-bold text-white font-['Space_Grotesk'] uppercase tracking-wide">Budget Overview</h3>
      </div>

      <div className="space-y-4">
        <div className="space-y-3">
          <div>
            <label htmlFor="budget-input" className="block text-[10px] font-semibold text-white/60 font-mono tracking-[2px] uppercase mb-2">
              Monthly Budget Cap
            </label>
            <div className="relative">
              <DollarSign
                className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40"
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
                className={`w-full pl-9 pr-4 py-2.5 text-sm font-mono bg-white/5 border transition-all focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 ${
                  validationError ? 'border-red-500/50 bg-red-500/5' : 'border-white/10'
                } ${merchantSettingsLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                placeholder="Enter budget amount"
              />
            </div>
            {validationError && (
              <div className="mt-1.5 flex items-start text-xs text-red-400 font-mono">
                <AlertCircle size={14} className="mr-1 mt-0.5 flex-shrink-0" />
                <span>{validationError}</span>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setShowConfirmation(true)}
              disabled={!!validationError || isSaving || merchantSettingsLoading}
              className="flex-1 py-2.5 bg-blue-500 text-white text-[10px] font-bold font-mono uppercase tracking-[2px] hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full mr-2" />
                  Saving...
                </>
              ) : (
                <>
                  <Save size={14} className="mr-2" />
                  Save Budget
                </>
              )}
            </button>

            <button
              onClick={() => setShowNoLimitConfirmation(true)}
              disabled={isSaving || merchantSettingsLoading}
              className="py-2.5 px-3 bg-white/10 border border-white/10 text-white/60 text-sm font-medium hover:bg-white/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              title="Remove budget cap (no limit)"
            >
              <Infinity size={16} />
            </button>
          </div>
        </div>

        {currentSpend > 0 && (
          <div className="pt-4 border-t border-white/10">
            {budgetInput === '' ? (
              <div className="flex justify-between text-xs mb-1">
                <span className="text-white/60 font-mono font-medium">Budget Usage</span>
                <span className="font-medium text-white/60 font-mono">No Limit Set</span>
              </div>
            ) : (
              <>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white/60 font-mono font-semibold tracking-[2px] uppercase">Budget Usage</span>
                  <span className="font-bold text-white font-mono">{budgetPercentage.toFixed(0)}%</span>
                </div>
                <div className="w-full bg-white/10 h-2 overflow-hidden">
                  <div
                    className={`h-2 transition-all duration-500 ${
                      budgetPercentage > 90
                        ? 'bg-red-500'
                        : budgetPercentage > 70
                          ? 'bg-orange-500'
                          : 'bg-emerald-500'
                    }`}
                    style={{ width: `${budgetPercentage}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-white/40 font-mono mt-2">
                  <span>{formatCost(currentSpend, 2)} spent</span>
                  <span>of {formatCost(newBudgetValue, 2)} budget</span>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <Dialog open={showConfirmation} onOpenChange={setShowConfirmation}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Budget Update</DialogTitle>
            <DialogDescription>
              Are you sure you want to update your monthly budget cap to{' '}
              <span className="font-bold text-white font-mono">
                {formatCost(parseFloat(budgetInput) || 0, 2)}
              </span>
              ? This will be used to monitor your spending and send alerts if exceeded.
            </DialogDescription>
          </DialogHeader>
          {isBelowCurrentSpend && (
            <div className="bg-red-500/10 border border-red-500/30 p-4 mt-4">
              <div className="flex items-start gap-3">
                <AlertCircle size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-bold text-red-300 font-['Space_Grotesk'] uppercase tracking-wide">Warning: Budget below current spend</p>
                  <p className="text-sm text-red-400/80 font-mono mt-1">
                    Your current monthly spend is <strong>{formatCost(currentSpend, 2)}</strong>, which 
                    exceeds your new budget cap. Your bot will be <strong>paused immediately</strong> after 
                    saving.
                  </p>
                </div>
              </div>
            </div>
          )}
          <DialogFooter className="mt-6 flex space-x-2">
            <button
              onClick={() => {
                setShowConfirmation(false);
                handleSave();
              }}
              disabled={isSaving}
              className="flex-1 py-2 px-4 bg-blue-500 text-white text-sm font-bold font-mono uppercase tracking-wide hover:bg-blue-600 transition-colors disabled:opacity-50"
            >
              {isSaving ? 'Updating...' : 'Confirm Update'}
            </button>
            <button
              onClick={() => setShowConfirmation(false)}
              disabled={isSaving}
              className="flex-1 py-2 px-4 text-sm font-medium text-white/60 bg-white/10 border border-white/10 hover:bg-white/20 transition-colors font-mono"
            >
              Cancel
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showNoLimitConfirmation} onOpenChange={setShowNoLimitConfirmation}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove Budget Cap</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove your budget cap? This means there will be no limit on
              your monthly spending and you won't receive budget alerts.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-6 flex space-x-2">
            <button
              onClick={() => {
                setShowNoLimitConfirmation(false);
                handleRemoveBudgetCap();
              }}
              disabled={isSaving}
              className="flex-1 py-2 px-4 bg-white/20 text-white text-sm font-bold font-mono uppercase tracking-wide hover:bg-white/30 transition-colors disabled:opacity-50"
            >
              {isSaving ? 'Removing...' : 'Remove Cap'}
            </button>
            <button
              onClick={() => setShowNoLimitConfirmation(false)}
              disabled={isSaving}
              className="flex-1 py-2 px-4 text-sm font-medium text-white/60 bg-white/10 border border-white/10 hover:bg-white/20 transition-colors font-mono"
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
