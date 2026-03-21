/**
 * Budget Configuration Component - Hyper-Luminous Observer Aesthetic
 *
 * Provides budget cap management interface:
 * - Display current budget cap with edit capability
 * - Show current spend vs budget with percentage
 * - High-speed tactical inputs
 *
 * Story 3-6: Budget Cap Configuration
 */

import { useState, useEffect } from 'react';
import { DollarSign, Save, AlertCircle, Infinity, ShieldCheck } from 'lucide-react';
import { useCostTrackingStore } from '../../stores/costTrackingStore';
import { formatCost } from '../../types/cost';
import { useToast } from '../../context/ToastContext';
import { GlassCard } from '../ui/GlassCard';
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
      await updateMerchantSettings(null as unknown as number);
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
    <GlassCard accent="mantis" className="p-8 space-y-8 border-white/[0.03] bg-white/[0.01]">
      <div className="flex justify-between items-center">
        <div className="space-y-1">
          <h3 className="text-xl font-black text-white uppercase tracking-tight flex items-center gap-3">
             <ShieldCheck size={20} className="text-emerald-500" />
             Protocol Controls
          </h3>
          <p className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">Resource allocation management</p>
        </div>
      </div>

      <div className="space-y-6">
        <div className="space-y-4">
          <div>
            <label htmlFor="budget-input" className="block text-[10px] font-black text-white/40 uppercase tracking-[0.2em] mb-3">
              Monthly Resource Cap (USD)
            </label>
            <div className="relative group">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-emerald-500 transition-colors">
                 <DollarSign size={18} />
              </div>
              <input
                id="budget-input"
                type="number"
                value={budgetInput}
                onChange={handleInputChange}
                step="0.01"
                min="0"
                disabled={merchantSettingsLoading || isSaving}
                className={`w-full pl-12 pr-4 h-14 text-lg font-black bg-white/5 border transition-all focus:outline-none rounded-2xl ${
                  validationError 
                    ? 'border-rose-500/50 text-rose-500 placeholder:text-rose-500/20' 
                    : 'border-white/10 text-white placeholder:text-white/10 focus:border-emerald-500/50'
                } ${merchantSettingsLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                placeholder="0.00"
              />
            </div>
            {validationError && (
              <div className="mt-2 flex items-start text-[10px] text-rose-400 font-black uppercase tracking-widest">
                <AlertCircle size={14} className="mr-2 flex-shrink-0" />
                <span>{validationError}</span>
              </div>
            )}
          </div>

          <div className="flex gap-4">
            <button
              onClick={() => setShowConfirmation(true)}
              disabled={!!validationError || isSaving || merchantSettingsLoading}
              className="flex-1 h-14 bg-emerald-500 text-black text-[10px] font-black uppercase tracking-[0.3em] rounded-2xl hover:bg-emerald-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.2)]"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-black border-t-transparent rounded-full mr-2" />
                  Updating...
                </>
              ) : (
                <>
                  <Save size={14} className="mr-2" />
                  Save Protocol
                </>
              )}
            </button>

            <button
              onClick={() => setShowNoLimitConfirmation(true)}
              disabled={isSaving || merchantSettingsLoading}
              className="w-14 h-14 bg-white/5 border border-white/10 text-white/40 hover:text-white hover:bg-white/10 transition-all rounded-2xl disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              title="Remove budget cap (no limit)"
            >
              <Infinity size={20} />
            </button>
          </div>
        </div>

        {currentSpend > 0 && (
          <div className="pt-8 border-t border-white/[0.03] space-y-4">
            {budgetInput === '' ? (
              <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest text-emerald-500/60">
                <span>Neural Consumption</span>
                <span>Unlimited Range</span>
              </div>
            ) : (
              <>
                <div className="flex justify-between items-end">
                  <span className="text-[10px] font-black text-white/40 uppercase tracking-[0.2em]">Neural Consumption</span>
                  <span className={`text-xl font-black ${budgetPercentage > 90 ? 'text-rose-500' : 'text-emerald-500'} tracking-tight`}>
                    {budgetPercentage.toFixed(1)}%
                  </span>
                </div>
                <div className="relative w-full h-3 bg-white/5 rounded-full overflow-hidden border border-white/5">
                  <div
                    className={`h-full transition-all duration-1000 shadow-[0_0_15px_rgba(16,185,129,0.2)] ${
                      budgetPercentage > 90
                        ? 'bg-rose-500 shadow-rose-500/30'
                        : budgetPercentage > 70
                          ? 'bg-amber-500 shadow-amber-500/30'
                          : 'bg-emerald-500'
                    }`}
                    style={{ width: `${budgetPercentage}%` }}
                  />
                </div>
                <div className="flex justify-between text-[9px] font-black text-white/20 uppercase tracking-[0.2em]">
                  <span>{formatCost(currentSpend, 2)} Consumed</span>
                  <span>Target: {formatCost(newBudgetValue, 2)}</span>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      <Dialog open={showConfirmation} onOpenChange={setShowConfirmation}>
        <DialogContent className="bg-[#0a0a0f] border-emerald-500/20 text-white">
          <DialogHeader>
            <DialogTitle className="text-xl font-black uppercase tracking-tight">Confirm Protocol Update</DialogTitle>
            <DialogDescription className="text-white/60 text-sm font-medium">
              Are you sure you want to update your monthly resource cap to{' '}
              <span className="font-black text-emerald-400">
                {formatCost(parseFloat(budgetInput) || 0, 2)}
              </span>
              ? This will be used to monitor neural activity and send override alerts.
            </DialogDescription>
          </DialogHeader>
          {isBelowCurrentSpend && (
            <div className="bg-rose-500/5 border border-rose-500/20 p-6 rounded-2xl mt-4 space-y-2">
              <div className="flex items-center gap-3">
                <AlertCircle size={20} className="text-rose-500 flex-shrink-0" />
                <p className="font-black text-rose-500 text-[10px] uppercase tracking-widest">Critical Alert: Range Error</p>
              </div>
              <p className="text-sm text-rose-500/60 font-medium">
                Current consumption <strong>{formatCost(currentSpend, 2)}</strong> exceeds new limit. 
                Bot activity will be <strong>inhibited immediately</strong>.
              </p>
            </div>
          )}
          <DialogFooter className="mt-8 flex gap-3">
            <button
               onClick={() => setShowConfirmation(false)}
               disabled={isSaving}
               className="flex-1 h-12 text-[10px] font-black uppercase tracking-widest text-white/40 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 transition-all font-mono"
             >
               Abort
             </button>
            <button
              onClick={() => {
                setShowConfirmation(false);
                handleSave();
              }}
              disabled={isSaving}
              className="flex-1 h-12 bg-emerald-500 text-black text-[10px] font-black uppercase tracking-[0.2em] rounded-xl hover:bg-emerald-400 transition-all shadow-[0_0_15px_rgba(16,185,129,0.2)]"
            >
              {isSaving ? 'Synching...' : 'Authorize Policy'}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showNoLimitConfirmation} onOpenChange={setShowNoLimitConfirmation}>
        <DialogContent className="bg-[#0a0a0f] border-white/10 text-white">
          <DialogHeader>
            <DialogTitle className="text-xl font-black uppercase tracking-tight">Disable Resource Cap</DialogTitle>
            <DialogDescription className="text-white/60 text-sm font-medium">
              Are you sure you want to remove the resource cap? This will allow unlimited neural load 
              and disable all budget surveillance alerts.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-8 flex gap-3">
            <button
               onClick={() => setShowNoLimitConfirmation(false)}
               disabled={isSaving}
               className="flex-1 h-12 text-[10px] font-black uppercase tracking-widest text-white/40 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 transition-all font-mono"
             >
               Abort
             </button>
            <button
              onClick={() => {
                setShowNoLimitConfirmation(false);
                handleRemoveBudgetCap();
              }}
              disabled={isSaving}
              className="flex-1 h-12 bg-white/10 text-white text-[10px] font-black uppercase tracking-widest hover:bg-white/20 rounded-xl border border-white/10 transition-all"
            >
              {isSaving ? 'Synching...' : 'Execute Policy'}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </GlassCard>
  );
};

export default BudgetConfiguration;
