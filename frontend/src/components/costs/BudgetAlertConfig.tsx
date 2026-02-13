/**
 * BudgetAlertConfig Component
 *
 * Configuration UI for budget alert thresholds
 * Story 3-8: Budget Alert Notifications
 */

import { useState, useEffect } from 'react';
import { useCostTrackingStore } from '../../stores/costTrackingStore';
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
    <div className={`bg-white p-6 rounded-xl border border-gray-200 shadow-sm ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="font-bold text-gray-900">Alert Configuration</h3>
          <p className="text-xs text-gray-500 mt-1">
            Customize when you receive budget alerts
          </p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={alertsEnabled}
            onChange={(e) => handleEnabledChange(e.target.checked)}
            className="sr-only peer"
            aria-label="Enable budget alerts"
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          <span className="ml-3 text-sm font-medium text-gray-700">
            {alertsEnabled ? 'Enabled' : 'Disabled'}
          </span>
        </label>
      </div>

      <div className={`space-y-6 ${!alertsEnabled ? 'opacity-50' : ''}`}>
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm font-medium text-gray-700">
              Warning Threshold
            </label>
            <span className="text-sm font-bold text-yellow-600">
              {warningThreshold}%
            </span>
          </div>
          <input
            type="range"
            min={50}
            max={95}
            value={warningThreshold}
            onChange={(e) => handleWarningChange(parseInt(e.target.value))}
            className="w-full h-2 bg-yellow-100 rounded-lg appearance-none cursor-pointer accent-yellow-500 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Warning threshold percentage"
            disabled={!alertsEnabled}
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>50%</span>
            <span className="text-yellow-600">Yellow banner appears</span>
            <span>95%</span>
          </div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="text-sm font-medium text-gray-700">
              Critical Threshold
            </label>
            <span className="text-sm font-bold text-red-600">
              {criticalThreshold}%
            </span>
          </div>
          <input
            type="range"
            min={80}
            max={99}
            value={criticalThreshold}
            onChange={(e) => handleCriticalChange(parseInt(e.target.value))}
            className="w-full h-2 bg-red-100 rounded-lg appearance-none cursor-pointer accent-red-500 disabled:cursor-not-allowed disabled:opacity-50"
            aria-label="Critical threshold percentage"
            disabled={!alertsEnabled}
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>80%</span>
            <span className="text-red-600">Red banner (no dismiss)</span>
            <span>99%</span>
          </div>
        </div>

        {criticalThreshold <= warningThreshold && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-700">
              ⚠️ Critical threshold should be higher than warning threshold
            </p>
          </div>
        )}

        <div className="pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Preview</h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-yellow-100 border-l-4 border-yellow-400 rounded">
              <p className="text-xs font-bold text-yellow-800">
                Warning at {warningThreshold}%
              </p>
              <p className="text-xs text-yellow-700 mt-1">Dismissible for 24h</p>
            </div>
            <div className="p-3 bg-red-100 border-l-4 border-red-400 rounded">
              <p className="text-xs font-bold text-red-800">
                Critical at {criticalThreshold}%
              </p>
              <p className="text-xs text-red-700 mt-1">Cannot be dismissed</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
        <button
          onClick={handleReset}
          disabled={!hasChanges || isSaving}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Reset to defaults"
        >
          Reset Defaults
        </button>
        <button
          onClick={handleSave}
          disabled={!hasChanges || isSaving}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          aria-label="Save alert configuration"
        >
          {isSaving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
}
