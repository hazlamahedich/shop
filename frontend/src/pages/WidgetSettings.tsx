/**
 * Widget Settings Page
 *
 * Story 5.6: Merchant Widget Settings UI
 *
 * Provides a UI for merchants to configure their embeddable widget:
 * - Enable/disable widget
 * - Customize primary color and position
 * - View and copy embed code with platform-specific instructions
 *
 * Note: Bot name is configured in Bot Config page.
 * Welcome message is configured in Bot Personality page.
 */

import React, { useEffect, useState } from 'react';
import { Save, Loader2, Palette, Code, ExternalLink } from 'lucide-react';
import { useWidgetSettingsStore } from '../stores/widgetSettingsStore';
import { useAuthStore } from '../stores/authStore';
import { EmbedCodePreview } from '../components/widget/EmbedCodePreview';
import {
  validateWidgetSettings,
  hasValidationErrors,
  type WidgetSettingsErrors,
} from '../utils/widgetSettingsValidation';
import { useToast } from '../context/ToastContext';

export default function WidgetSettings() {
  const { toast } = useToast();
  const merchant = useAuthStore((state) => state.merchant);
  const merchantId = merchant?.id ?? null;

  const {
    config,
    loading,
    saving,
    error,
    hasUnsavedChanges,
    fetchConfig,
    updateConfig,
    setConfig,
    resetDirty,
  } = useWidgetSettingsStore();

  const [validationErrors, setValidationErrors] = useState<WidgetSettingsErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  useEffect(() => {
    if (!config) return;

    const errors = validateWidgetSettings({
      primaryColor: config.theme.primaryColor,
      position: config.theme.position,
    });
    setValidationErrors(errors);
  }, [config]);

  const handleFieldBlur = (field: string) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
  };

  const handleToggleEnabled = () => {
    if (!config) return;
    setConfig({ enabled: !config.enabled });
  };

  const handlePrimaryColorChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!config) return;
    setConfig({
      theme: { ...config.theme, primaryColor: e.target.value },
    });
  };

  const handlePositionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    if (!config) return;
    const position = e.target.value as 'bottom-right' | 'bottom-left';
    setConfig({
      theme: { ...config.theme, position },
    });
  };

  const handleSave = async () => {
    if (!config || hasValidationErrors(validationErrors)) {
      toast('Please fix validation errors before saving', 'error');
      setTouched({
        primaryColor: true,
        position: true,
      });
      return;
    }

    try {
      await updateConfig({
        enabled: config.enabled,
        theme: {
          primaryColor: config.theme.primaryColor,
          position: config.theme.position,
        },
      });
      toast('Widget settings saved successfully', 'success');
    } catch (err) {
      toast('Failed to save widget settings', 'error');
    }
  };

  const handleCancel = () => {
    if (hasUnsavedChanges) {
      if (window.confirm('You have unsaved changes. Are you sure you want to discard them?')) {
        resetDirty();
        fetchConfig();
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (error && !config) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <p>{error}</p>
        <button
          onClick={() => fetchConfig()}
          className="mt-2 text-sm font-medium text-red-600 hover:text-red-800"
        >
          Try again
        </button>
      </div>
    );
  }

  if (!config) {
    return null;
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Widget Settings</h1>
          <p className="text-sm text-gray-500 mt-1">
            Configure your embeddable chat widget
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          <p>{error}</p>
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm divide-y divide-gray-200">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <Palette className="h-5 w-5 text-gray-400" />
            <h2 className="text-lg font-medium text-gray-900">Appearance</h2>
          </div>

          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Widget Enabled
                </label>
                <p className="text-sm text-gray-500 mt-1">
                  Turn your chat widget on or off
                </p>
              </div>
              <button
                type="button"
                onClick={handleToggleEnabled}
                data-testid="widget-enabled-toggle"
                className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 ${
                  config.enabled ? 'bg-indigo-600' : 'bg-gray-200'
                }`}
                role="switch"
                aria-checked={config.enabled}
              >
                <span
                  className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    config.enabled ? 'translate-x-5' : 'translate-x-0'
                  }`}
                />
              </button>
            </div>

            <div>
              <label htmlFor="primaryColor" className="block text-sm font-medium text-gray-700">
                Primary Color
              </label>
              <div className="mt-1 flex items-center gap-3">
                <input
                  type="color"
                  id="primaryColorPicker"
                  data-testid="color-picker-input"
                  value={config.theme.primaryColor}
                  onChange={handlePrimaryColorChange}
                  onBlur={() => handleFieldBlur('primaryColor')}
                  className="h-10 w-14 rounded cursor-pointer border border-gray-300"
                />
                <input
                  type="text"
                  id="primaryColor"
                  data-testid="hex-color-input"
                  value={config.theme.primaryColor}
                  onChange={handlePrimaryColorChange}
                  onBlur={() => handleFieldBlur('primaryColor')}
                  placeholder="#6366f1"
                  className={`block w-32 rounded-md shadow-sm sm:text-sm uppercase ${
                    touched.primaryColor && validationErrors.primaryColor
                      ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                      : 'border-gray-300 focus:border-indigo-500 focus:ring-indigo-500'
                  }`}
                />
              </div>
              {touched.primaryColor && validationErrors.primaryColor && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.primaryColor}</p>
              )}
            </div>

            <div>
              <label htmlFor="position" className="block text-sm font-medium text-gray-700">
                Widget Position
              </label>
              <select
                id="position"
                data-testid="position-select"
                value={config.theme.position}
                onChange={handlePositionChange}
                onBlur={() => handleFieldBlur('position')}
                className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                  touched.position && validationErrors.position ? 'border-red-300' : ''
                }`}
              >
                <option value="bottom-right">Bottom Right</option>
                <option value="bottom-left">Bottom Left</option>
              </select>
              {touched.position && validationErrors.position && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.position}</p>
              )}
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="flex items-center gap-3 mb-4">
            <Code className="h-5 w-5 text-gray-400" />
            <h2 className="text-lg font-medium text-gray-900">Embed Code</h2>
          </div>

          <EmbedCodePreview
            merchantId={merchantId}
            primaryColor={config.theme.primaryColor}
            enabled={config.enabled}
          />
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 mb-2">Bot Configuration</h3>
        <p className="text-sm text-blue-700 mb-3">
          To customize your bot&apos;s name and welcome message, visit these pages:
        </p>
        <div className="flex gap-4">
          <a
            href="/bot-config"
            className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
          >
            <ExternalLink className="h-3 w-3" />
            Bot Name Settings
          </a>
          <a
            href="/personality"
            className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
          >
            <ExternalLink className="h-3 w-3" />
            Bot Personality & Greeting
          </a>
        </div>
      </div>

      <div className="flex items-center justify-end gap-3">
        {hasUnsavedChanges && (
          <button
            type="button"
            data-testid="cancel-button"
            onClick={handleCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Cancel
          </button>
        )}
        <button
          type="button"
          data-testid="save-settings-button"
          onClick={handleSave}
          disabled={saving || hasValidationErrors(validationErrors)}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4" />
              Save Settings
            </>
          )}
        </button>
      </div>
    </div>
  );
}
