/**
 * BusinessInfoFaqConfig Page Component
 *
 * Story 1.11: Business Info & FAQ Configuration
 * Story 3.10: Business Hours Configuration (moved from Settings)
 *
 * Main page for configuring business information, hours, and FAQ items.
 * Integrates BusinessInfoForm, BusinessHoursConfig, and FaqList components with:
 * - Save Configuration button for business info
 * - Auto-save for business hours (via BusinessHoursConfig)
 * - Automatic persistence for FAQ operations
 * - Loading states and error handling
 * - Navigation breadcrumbs
 *
 * WCAG 2.1 AA accessible.
 */

import * as React from 'react';
import { useEffect } from 'react';
import { Info, CheckCircle2, AlertCircle } from 'lucide-react';
import { useToast } from '../context/ToastContext';
import { useBusinessInfoStore } from '../stores/businessInfoStore';
import { useOnboardingPhaseStore } from '../stores/onboardingPhaseStore';
import { BusinessInfoForm } from '../components/business-info/BusinessInfoForm';
import { FaqList } from '../components/business-info/FaqList';
import { BusinessHoursConfig } from '../components/settings/BusinessHoursConfig';

/**
 * BusinessInfoFaqConfig Component
 *
 * Main configuration page for business information, hours, and FAQ items.
 *
 * Features:
 * - Business information form with save functionality
 * - Business hours configuration with auto-save
 * - FAQ list with add/edit/delete operations
 * - Automatic loading of existing configuration
 * - Success and error notifications
 */
export const BusinessInfoFaqConfig: React.FC = () => {
  const {
    businessName,
    businessDescription,
    businessHours,
    loadingState,
    faqsLoadingState,
    error,
    isDirty,
    fetchBusinessInfo,
    updateBusinessInfo,
    clearError,
  } = useBusinessInfoStore();

  const markBotConfigComplete = useOnboardingPhaseStore((state) => state.markBotConfigComplete);

  const { toast } = useToast();

  // Load configuration on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        await Promise.all([
          fetchBusinessInfo(),
          // FAQs are loaded by FaqList component
        ]);
      } catch (err) {
        console.error('Failed to load configuration:', err);
        toast('Failed to load configuration', 'error');
      }
    };

    loadConfig();
  }, [fetchBusinessInfo, toast]);

  // Handle save business info
  const handleSaveBusinessInfo = async () => {
    clearError();

    try {
      await updateBusinessInfo({
        businessName: businessName,
        businessDescription: businessDescription,
        businessHours: businessHours,
      });

      markBotConfigComplete('businessInfo');
      toast('Business info saved successfully!', 'success');
    } catch (err) {
      console.error('Failed to save business info:', err);
      toast('Failed to save business info', 'error');
    }
  };

  // Is any operation in progress?
  const isLoading = loadingState === 'loading' || faqsLoadingState === 'loading';
  const hasConfig = businessName || businessDescription || businessHours;

  return (
    <div className="min-h-screen bg-[#050505] text-emerald-50">
      {/* Breadcrumb Navigation */}
      <nav className="border-b border-emerald-500/10 bg-black/20 backdrop-blur-xl" aria-label="Breadcrumb">
        <div className="max-w-7xl mx-auto px-10 py-4">
          <ol className="flex items-center gap-3 text-[11px] font-black uppercase tracking-[0.2em]">
            <li>
              <a href="/dashboard" className="text-emerald-900/40 hover:text-emerald-400 transition-all duration-500">
                Primary Dashboard
              </a>
            </li>
            <li className="text-emerald-900/20">/</li>
            <li>
              <span className="text-emerald-400 mantis-glow-text">Intelligence Config & FAQ</span>
            </li>
          </ol>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-10 py-16 space-y-16">
        {/* Page Header */}
        <div className="relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500/20 to-blue-500/20 blur-3xl opacity-20 -z-10" />
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="space-y-4">
              <h1 className="text-6xl font-black tracking-tight text-white mantis-glow-text leading-none">
                Intelligence Engine
              </h1>
              <p className="text-xl text-emerald-900/60 font-medium max-w-2xl leading-relaxed">
                Configure your bot&apos;s primary knowledge base. Fine-tune business heuristics, operational hours, and rapid-response logic.
              </p>
            </div>
            <div className="flex items-center gap-3 px-6 py-2.5 bg-emerald-500/5 text-emerald-400 border border-emerald-500/10 rounded-2xl text-[10px] font-black uppercase tracking-[0.3em] backdrop-blur-md shadow-2xl">
              <Info size={14} className="text-emerald-500 shadow-glow" />
              <span>Reference Stories 1.11, 3.10</span>
            </div>
          </div>
        </div>

        {/* Error Display (page-level) */}
        {error && (
          <div
            role="alert"
            className="p-8 bg-red-500/5 border border-red-500/10 rounded-[32px] flex items-start gap-6 backdrop-blur-2xl animate-in shake duration-700 shadow-2xl relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/5 rounded-full -mr-16 -mt-16 blur-3xl" />
            <AlertCircle size={24} className="text-red-500 flex-shrink-0 mt-0.5 shadow-glow" />
            <div className="flex-1 space-y-1">
              <p className="text-[10px] font-black uppercase tracking-[0.3em] text-red-400">System Fault Detected</p>
              <p className="text-base text-red-400/80 font-medium leading-relaxed">{error}</p>
            </div>
            <button
              type="button"
              onClick={clearError}
              className="p-2 text-red-400/40 hover:text-red-400 transition-colors bg-white/5 rounded-xl border border-white/5"
              aria-label="Dismiss fault"
            >
              ×
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          {/* Left Column: Business Info + Hours */}
          <div className="lg:col-span-4 space-y-10">
            {/* Business Info Form */}
            <div className="bg-[#0a0a0a]/60 backdrop-blur-3xl rounded-[40px] border border-emerald-500/10 p-10 shadow-2xl relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-48 h-48 bg-emerald-500/5 rounded-full -mr-24 -mt-24 blur-3xl transition-all duration-700 group-hover:bg-emerald-500/10" />
              
              <div className="flex items-center justify-between mb-10 relative z-10">
                <h2 className="text-2xl font-black text-white tracking-tight">Standard Heuristics</h2>
                {hasConfig && (
                  <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-emerald-500/10 text-emerald-400 text-[10px] font-black uppercase tracking-[0.2em] rounded-xl border border-emerald-500/20 shadow-glow shadow-emerald-500/20">
                    <CheckCircle2 size={12} />
                    Verified
                  </span>
                )}
              </div>

              <div className="space-y-10 relative z-10">
                <div className="mantis-form-overrides">
                  <BusinessInfoForm disabled={isLoading} />
                </div>

                {/* Save Button */}
                <div className="pt-10 border-t border-white/5">
                  <button
                    type="button"
                    onClick={handleSaveBusinessInfo}
                    disabled={isLoading || !isDirty}
                    className="w-full px-8 py-4 text-[11px] font-black uppercase tracking-[0.25em] text-white bg-emerald-600 border border-transparent rounded-2xl hover:bg-emerald-500 disabled:opacity-30 disabled:grayscale transition-all shadow-2xl hover:shadow-emerald-500/40 relative overflow-hidden group/save"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover/save:animate-shimmer" />
                    <span className="relative z-10">
                      {isLoading ? (
                        <span className="flex items-center justify-center gap-3">
                          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          Syncing Data...
                        </span>
                      ) : (
                        'Commit Business Schema'
                      )}
                    </span>
                  </button>
                  {!isDirty && hasConfig && (
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-center text-emerald-900/40 mt-4 animate-pulse">
                      Status: Synchronized
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Business Hours Config (Story 3.10) */}
            <div className="mantis-hours-overrides">
              <BusinessHoursConfig />
            </div>
          </div>

          {/* FAQ List */}
          <div className="lg:col-span-8">
            <div className="bg-[#0a0a0a]/60 backdrop-blur-3xl rounded-[48px] border border-white/5 p-10 shadow-2xl relative overflow-hidden min-h-[600px] flex flex-col">
              <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-500/5 rounded-full -mr-48 -mt-48 blur-[120px] pointer-events-none" />
              <FaqList />
            </div>
          </div>
        </div>

        {/* Help Section */}
        <div className="p-10 bg-[#0a0a0a]/40 backdrop-blur-2xl border border-emerald-500/10 rounded-[40px] shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full -mr-16 -mt-16 blur-[60px]" />
          <h3 className="text-3xl font-black text-white tracking-tight mb-8 mantis-glow-text">Intelligence Protocol</h3>
          <div className="grid md:grid-cols-3 gap-10 text-base text-emerald-900/60 font-medium leading-relaxed">
            <div className="p-8 bg-white/[0.02] border border-white/5 rounded-3xl transition-all duration-700 hover:bg-white/[0.04] hover:-translate-y-2 group/card">
              <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-emerald-400 mb-4 flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-glow" />
                Context Hook
              </h4>
              <p>
                Dynamic business heuristics are automatically injected into the bot&apos;s reasoning cycle. Every response leverages your defined identity schema.
              </p>
            </div>
            <div className="p-8 bg-white/[0.02] border border-white/5 rounded-3xl transition-all duration-700 hover:bg-white/[0.04] hover:-translate-y-2 group/card">
              <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-blue-400 mb-4 flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                Operational Logic
              </h4>
              <p>
                Automated 운영 시간 control. The engine intelligently manages human handoff protocols based on your operational window and timezone synchronization.
              </p>
            </div>
            <div className="p-8 bg-white/[0.02] border border-white/5 rounded-3xl transition-all duration-700 hover:bg-white/[0.04] hover:-translate-y-2 group/card">
              <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-purple-400 mb-4 flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
                Instant Retrieval
              </h4>
              <p>
                FAQ primitives are indexed for high-speed pattern matching. The bot executes immediate recovery of pre-defined datasets for common query patterns.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default BusinessInfoFaqConfig;
