/**
 * Widget Settings Page
 *
 * Story 5.6: Merchant Widget Settings UI
 * Story 10-2: FAQ Quick Buttons Configuration (AC5)
 *
 * Re-imagined with Mantis aesthetic.
 */

import React, { useEffect, useState } from 'react';
import { Save, Loader2, Palette, Code, Sparkles, Layout, Terminal, ThumbsUp } from 'lucide-react';
import { useWidgetSettingsStore } from '../stores/widgetSettingsStore';
import { useAuthStore } from '../stores/authStore';
import { EmbedCodePreview } from '../components/widget/EmbedCodePreview';
import { GlassCard } from '../components/ui/GlassCard';
import { FAQQuickButtonsConfig } from '../components/widget/FAQQuickButtonsConfig';
import { ContactOption } from '../widget/types/widget';
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

  const handleToggleFeedbackEnabled = () => {
    if (!config) return;
    setConfig({ feedbackEnabled: !config.feedbackEnabled });
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
      toast('Neural parameters invalid', 'error');
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
        feedbackEnabled: config.feedbackEnabled,
        contactOptions: config.contactOptions as ContactOption[], // Explicitly cast to ContactOption[]
      });
      toast('System calibration successful', 'success');
    } catch (err) {
      toast('Failed to synchronize parameters', 'error');
    }
  };

  const handleCancel = () => {
    if (hasUnsavedChanges) {
      if (window.confirm('Neural rollback? Current modifications will be purged.')) {
        resetDirty();
        fetchConfig();
      }
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <div className="w-12 h-12 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
        <span className="text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.3em]">Accessing Interface Node...</span>
      </div>
    );
  }

  if (error && !config) {
    return (
      <GlassCard accent="red" className="p-8 text-center max-w-lg mx-auto">
        <p className="text-red-500 font-bold mb-4">{error}</p>
        <button
          onClick={() => fetchConfig()}
          className="h-10 px-6 bg-red-500/10 border border-red-500/20 text-red-500 font-black text-[9px] uppercase tracking-widest rounded-xl hover:bg-red-500 hover:text-white transition-all"
        >
          Retry Neural Link
        </button>
      </GlassCard>
    );
  }

  if (!config) return null;

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-20 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/5 border border-emerald-500/10 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400">
            <Layout size={12} />
            Holographic Interface
          </div>
          <h1 className="text-5xl font-black tracking-tight text-white leading-none mantis-glow-text">
            Widget Settings
          </h1>
          <p className="text-lg text-emerald-900/40 font-medium max-w-xl">
            Calibrate the visual signature and deployment matrix of your neural assistant.
          </p>
        </div>

        <div className="flex gap-4">
          {hasUnsavedChanges && (
            <button
              onClick={handleCancel}
              className="h-14 px-8 bg-white/5 border border-white/10 text-white font-black text-[10px] uppercase tracking-[0.3em] rounded-2xl hover:bg-white/10 hover:border-white/20 transition-all duration-300"
            >
              Rollback
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={saving || hasValidationErrors(validationErrors)}
            className="h-14 px-8 bg-emerald-500 text-black font-black text-[10px] uppercase tracking-[0.3em] rounded-2xl hover:bg-emerald-400 transition-all duration-300 shadow-[0_0_30px_rgba(16,185,129,0.2)] flex items-center justify-center gap-3 disabled:opacity-50"
          >
            {saving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
            {saving ? 'Syncing...' : 'Commit Changes'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        <div className="lg:col-span-3 space-y-8">
          <GlassCard accent="mantis" className="border-emerald-500/10 bg-emerald-500/[0.01]">
            <div className="p-8 border-b border-white/[0.03] flex items-center gap-4 bg-white/[0.01]">
              <div className="p-2 bg-emerald-500/10 rounded-xl text-emerald-400 border border-emerald-500/20">
                <Palette size={20} />
              </div>
              <h2 className="text-lg font-black text-white uppercase tracking-tight">Visual Parameters</h2>
            </div>
            
            <div className="p-8 space-y-10">
              <div className="flex items-center justify-between p-6 bg-white/[0.02] border border-white/[0.05] rounded-3xl">
                <div>
                  <h4 className="text-white font-black uppercase tracking-widest text-[11px]">Neural Presence</h4>
                  <p className="text-[10px] text-emerald-900/40 font-bold uppercase tracking-widest mt-1">Activate/Deactivate widget node</p>
                </div>
                <button
                  type="button"
                  onClick={handleToggleEnabled}
                  className={`
                    relative inline-flex h-8 w-14 flex-shrink-0 cursor-pointer rounded-full border-4 border-transparent transition-all duration-500 
                    ${config.enabled ? 'bg-emerald-500' : 'bg-white/10'}
                  `}
                >
                  <span className={`
                    pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow-xl transition-all duration-500
                    ${config.enabled ? 'translate-x-6' : 'translate-x-0'}
                  `} />
                </button>
              </div>

              {/* Story 10-4 AC8: Feedback Rating Toggle (General Mode only) */}
              {merchant?.onboardingMode === 'general' && (
                <div className="flex items-center justify-between p-6 bg-white/[0.02] border border-white/[0.05] rounded-3xl">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-emerald-500/10 rounded-xl text-emerald-400 border border-emerald-500/20">
                      <ThumbsUp size={16} />
                    </div>
                    <div>
                      <h4 className="text-white font-black uppercase tracking-widest text-[11px]">Feedback Ratings</h4>
                      <p className="text-[10px] text-emerald-900/40 font-bold uppercase tracking-widest mt-1">Collect thumbs up/down on bot responses</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={handleToggleFeedbackEnabled}
                    className={`
                      relative inline-flex h-8 w-14 flex-shrink-0 cursor-pointer rounded-full border-4 border-transparent transition-all duration-500 
                      ${(config.feedbackEnabled ?? true) ? 'bg-emerald-500' : 'bg-white/10'}
                    `}
                  >
                    <span className={`
                      pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow-xl transition-all duration-500
                      ${(config.feedbackEnabled ?? true) ? 'translate-x-6' : 'translate-x-0'}
                    `} />
                  </button>
                </div>
              )}

              <div className="space-y-6">
                <div className="space-y-4">
                  <label className="text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.3em] ml-1">Spectral Signature (Color)</label>
                  <div className="flex items-center gap-4">
                    <div className="relative group">
                      <input
                        type="color"
                        value={config.theme.primaryColor}
                        onChange={handlePrimaryColorChange}
                        onBlur={() => handleFieldBlur('primaryColor')}
                        className="w-20 h-20 rounded-[28px] cursor-pointer bg-transparent border-4 border-white/[0.05] group-hover:border-emerald-500/40 transition-all p-1"
                      />
                      <div className="absolute inset-0 rounded-[28px] pointer-events-none border border-white/[0.05]" />
                    </div>
                    <div className="flex-1">
                      <input
                        type="text"
                        value={config.theme.primaryColor}
                        onChange={handlePrimaryColorChange}
                        onBlur={() => handleFieldBlur('primaryColor')}
                        className={`
                          w-full h-14 bg-white/5 border rounded-2xl px-6 text-white font-black text-sm uppercase tracking-widest transition-all
                          ${touched.primaryColor && validationErrors.primaryColor 
                            ? 'border-red-500/40 bg-red-500/5' 
                            : 'border-white/10 focus:border-emerald-500/40 focus:bg-emerald-500/[0.03]'}
                        `}
                      />
                      {touched.primaryColor && validationErrors.primaryColor && (
                        <p className="mt-2 text-[9px] font-black text-red-500 uppercase ml-2 tracking-widest">{validationErrors.primaryColor}</p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <label className="text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.3em] ml-1">Spatial Position</label>
                  <select
                    value={config.theme.position}
                    onChange={handlePositionChange}
                    onBlur={() => handleFieldBlur('position')}
                    className="w-full h-14 bg-white/5 border border-white/10 rounded-2xl px-6 text-white font-black text-sm uppercase tracking-widest appearance-none transition-all focus:border-emerald-500/40 focus:bg-emerald-500/[0.03]"
                  >
                    <option value="bottom-right">Vortex Alpha (Bottom Right)</option>
                    <option value="bottom-left">Vortex Beta (Bottom Left)</option>
                  </select>
                </div>
              </div>
            </div>
          </GlassCard>


          {/* Story 10-2 AC5: FAQ Quick Buttons Configuration (General Mode only) */}
          {merchant?.onboardingMode === 'general' && (
            <FAQQuickButtonsConfig merchantId={merchantId || 0} />
          )}

          <div className="grid grid-cols-2 gap-6">
            <a href="/bot-config" className="group">
              <GlassCard className="p-6 border-white/[0.03] bg-white/[0.01] group-hover:bg-emerald-500/[0.02] group-hover:border-emerald-500/20 transition-all duration-500">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/5 rounded-xl text-white/40 group-hover:text-emerald-400 transition-colors">
                    <Terminal size={18} />
                  </div>
                  <div className="space-y-0.5">
                    <p className="text-[9px] font-black text-emerald-900/40 uppercase tracking-widest">Neural ID</p>
                    <p className="text-[11px] font-black text-white uppercase tracking-tight">Bot Naming</p>
                  </div>
                </div>
              </GlassCard>
            </a>
            <a href="/personality" className="group">
              <GlassCard className="p-6 border-white/[0.03] bg-white/[0.01] group-hover:bg-emerald-500/[0.02] group-hover:border-emerald-500/20 transition-all duration-500">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/5 rounded-xl text-white/40 group-hover:text-emerald-400 transition-colors">
                    <Sparkles size={18} />
                  </div>
                  <div className="space-y-0.5">
                    <p className="text-[9px] font-black text-emerald-900/40 uppercase tracking-widest">Sentience</p>
                    <p className="text-[11px] font-black text-white uppercase tracking-tight">Personality</p>
                  </div>
                </div>
              </GlassCard>
            </a>
          </div>
        </div>

        <div className="lg:col-span-2">
          <GlassCard className="border-white/[0.03] bg-white/[0.01] h-fit">
            <div className="p-8 border-b border-white/[0.03] flex items-center gap-4">
              <div className="p-2 bg-white/5 rounded-xl text-white/40 border border-white/10">
                <Code size={20} />
              </div>
              <h2 className="text-lg font-black text-white uppercase tracking-tight">Neural Uplink</h2>
            </div>
            <div className="p-8">
              <EmbedCodePreview
                merchantId={merchantId}
                primaryColor={config.theme.primaryColor}
                enabled={config.enabled}
              />
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
