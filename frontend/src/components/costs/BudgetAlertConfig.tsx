/**
 * BudgetAlertConfig Component - Industrial Technical Dashboard
 *
 * Configuration UI for budget alert thresholds
 * Story 3-8: Budget Alert Notifications
 */

import { useState, useEffect } from 'react';
import { useToast } from '../../context/ToastContext';

interface BudgetAlertConfigProps {
  className?: string;
}

export function BudgetAlertConfig({ className = '' }: BudgetAlertConfigProps) {
  const [warningThreshold, setWarningThreshold] = useState(80);
  const [criticalThreshold, setCriticalThreshold] = useState(95);
  const [alertsEnabled, setAlertsEnabled] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const { toast } = useToast();

  const loadConfig = async () => {
    try {
      const response = await fetch('/api/merchant/alert-config', {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const config = data.data || data;
        setWarningThreshold(config.warning_threshold || 80);
        setCriticalThreshold(config.critical_threshold || 95);
        setAlertsEnabled(config.enabled ?? true);
      }
    } catch (error) {
      console.error('Failed to load alert config:', error);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleWarningChange = (value: number) => {
    setWarningThreshold(value);
    setHasChanges(true);
  };

  const handleCriticalChange = (value: number) => {
    setCriticalThreshold(value);
    setHasChanges(true);
  };

  const handleEnabledChange = (enabled: boolean) => {
    setAlertsEnabled(enabled);
    setHasChanges(true);
  };

  const handleSave = async () => {
    if (criticalThreshold <= warningThreshold) {
      toast('Critical threshold must be higher than warning threshold', 'error');
      return;
    }

    setIsSaving(true);

    try {
      const response = await fetch('/api/merchant/alert-config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          warning_threshold: warningThreshold,
          critical_threshold: criticalThreshold,
          enabled: alertsEnabled,
        }),
      });

      if (response.ok) {
        toast('Alert settings saved successfully', 'success');
        setHasChanges(false);
      } else {
        const error = await response.json();
        toast(error.message || 'Failed to save settings', 'error');
      }
    } catch (error) {
      toast('Failed to save settings', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setWarningThreshold(80);
    setCriticalThreshold(95);
    setAlertsEnabled(true);
    setHasChanges(true);
  };

  return (
    <div className={`bg-[#0A0A0A] border border-emerald-500/15 p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-sm font-bold text-white font-['Space_Grotesk'] uppercase tracking-wide">Alert Config</h3>
          <p className="text-[10px] text-white/40 font-mono mt-1 tracking-wide">
            Customize alert thresholds
          </p>
        </div>
        <button
          onClick={() => handleEnabledChange(!alertsEnabled)}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            alertsEnabled ? 'bg-emerald-500' : 'bg-white/20'
          }`}
          aria-label="Toggle alerts"
        >
          <span
            className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform ${
              alertsEnabled ? 'translate-x-5' : 'translate-x-1'
            }`}
          />
        </button>
      </div>

      <div className={`space-y-6 ${!alertsEnabled ? 'opacity-50' : ''}`}>
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-[10px] font-semibold text-white/60 font-mono tracking-[2px] uppercase">
              Warning Threshold
            </label>
            <span className="text-xs font-bold text-orange-400 font-mono">
              {warningThreshold}%
            </span>
          </div>
          <input
            type="range"
            min={50}
            max={95}
            value={warningThreshold}
            onChange={(e) => handleWarningChange(parseInt(e.target.value))}
            className="w-full h-2 bg-orange-500/20 rounded-none appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-orange-500 [&::-webkit-slider-thumb]:cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Warning threshold percentage"
            disabled={!alertsEnabled}
          />
          <div className="flex justify-between text-[10px] text-white/40 font-mono mt-1">
            <span>50%</span>
            <span className="text-orange-400">Yellow banner appears</span>
            <span>95%</span>
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-[10px] font-semibold text-white/60 font-mono tracking-[2px] uppercase">
              Critical Threshold
            </label>
            <span className="text-xs font-bold text-red-400 font-mono">
              {criticalThreshold}%
            </span>
          </div>
          <input
            type="range"
            min={80}
            max={99}
            value={criticalThreshold}
            onChange={(e) => handleCriticalChange(parseInt(e.target.value))}
            className="w-full h-2 bg-red-500/20 rounded-none appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-red-500 [&::-webkit-slider-thumb]:cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Critical threshold percentage"
            disabled={!alertsEnabled}
          />
          <div className="flex justify-between text-[10px] text-white/40 font-mono mt-1">
            <span>80%</span>
            <span className="text-red-400">Red banner (no dismiss)</span>
            <span>99%</span>
          </div>
        </div>

        {criticalThreshold <= warningThreshold && (
          <div className="p-3 bg-orange-500/10 border border-orange-500/30">
            <p className="text-xs text-orange-300 font-mono">
              ⚠️ Critical threshold should be higher than warning threshold
            </p>
          </div>
        )}

        <div className="pt-4 border-t border-white/10">
          <h4 className="text-[10px] font-semibold text-white/60 font-mono tracking-[2px] uppercase mb-3">Preview</h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-orange-500/10 border-l-2 border-orange-500">
              <p className="text-[10px] font-bold text-orange-300 font-mono uppercase tracking-wide">
                Warning at {warningThreshold}%
              </p>
              <p className="text-[10px] text-orange-400/60 font-mono mt-1">Dismissible for 24h</p>
            </div>
            <div className="p-3 bg-red-500/10 border-l-2 border-red-500">
              <p className="text-[10px] font-bold text-red-300 font-mono uppercase tracking-wide">
                Critical at {criticalThreshold}%
              </p>
              <p className="text-[10px] text-red-400/60 font-mono mt-1">Cannot be dismissed</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-white/10">
        <button
          onClick={handleReset}
          disabled={!hasChanges || isSaving}
          className="px-4 py-2 text-[10px] font-bold text-white/60 font-mono uppercase tracking-[2px] bg-white/10 border border-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Reset to defaults"
        >
          Reset Defaults
        </button>
        <button
          onClick={handleSave}
          disabled={!hasChanges || isSaving}
          className="px-4 py-2 text-[10px] font-bold text-white font-mono uppercase tracking-[2px] bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Save alert configuration"
        >
          {isSaving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
}
