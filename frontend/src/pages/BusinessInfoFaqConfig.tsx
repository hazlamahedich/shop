/**
 * BusinessInfoFaqConfig Page Component
 *
 * Designed using "Mantis HUD" deep dark aesthetic.
 * Incorporates:
 * - Business Info Form
 * - Business Hours Configuration
 * - FAQ Database
 */

import * as React from 'react';
import { useEffect } from 'react';
import { useToast } from '../context/ToastContext';
import { useBusinessInfoStore } from '../stores/businessInfoStore';
import { useOnboardingPhaseStore } from '../stores/onboardingPhaseStore';
import { BusinessInfoForm } from '../components/business-info/BusinessInfoForm';
import { FaqList } from '../components/business-info/FaqList';
import { BusinessHoursConfig } from '../components/settings/BusinessHoursConfig';

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

  useEffect(() => {
    const loadConfig = async () => {
      try {
        await Promise.all([
          fetchBusinessInfo(),
        ]);
      } catch (err) {
        console.error('Failed to load configuration:', err);
        toast('Failed to load configuration', 'error');
      }
    };
    loadConfig();
  }, [fetchBusinessInfo, toast]);

  const handleSaveBusinessInfo = async () => {
    clearError();
    try {
      await updateBusinessInfo({
        businessName,
        businessDescription,
        businessHours,
      });
      markBotConfigComplete('businessInfo');
      toast('Business info saved successfully!', 'success');
    } catch (err) {
      console.error('Failed to save business info:', err);
      toast('Failed to save business info', 'error');
    }
  };

  const isLoading = loadingState === 'loading' || faqsLoadingState === 'loading';
  const hasConfig = !!(businessName || businessDescription || businessHours);

  return (
    <div className="min-h-screen bg-[#131318] text-[#e4e1e9] font-['Inter'] relative z-0 pb-20 overflow-x-hidden">
      {/* Background Ambience */}
      <div className="fixed top-[20%] right-[-10%] w-[50%] h-[30%] bg-[#00bbf9]/5 blur-[120px] pointer-events-none -z-10 rounded-full" />
      <div className="fixed bottom-[10%] left-[-10%] w-[40%] h-[20%] bg-[#00f5d4]/5 blur-[100px] pointer-events-none -z-10 rounded-full" />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-12 space-y-10">
        {/* Breadcrumb */}
        <nav className="flex items-center space-x-2 text-[10px] uppercase tracking-[0.15em] text-[#b9cac4]/60 font-['Inter']">
          <span>Primary Dashboard</span>
          <span className="material-symbols-outlined text-[12px]">chevron_right</span>
          <span className="text-[#00dfc1]">Intelligence Config & FAQ</span>
        </nav>

        {/* Page Header */}
        <section className="space-y-3">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <h1 className="text-4xl lg:text-5xl font-['Space_Grotesk'] font-bold tracking-tight text-[#e4e1e9] uppercase">
              Intelligence Engine
            </h1>
            <div className="flex items-center gap-1.5 px-3 py-1 bg-[#00f5d4]/10 border border-[#00f5d4]/20 rounded-sm w-fit shadow-[0_0_15px_rgba(0,245,212,0.1)]">
              <span className="material-symbols-outlined text-[16px] text-[#00f5d4]" style={{ fontVariationSettings: "'FILL' 1" }}>verified</span>
              <span className="text-[10px] font-bold text-[#00f5d4] uppercase tracking-widest">Verified Schema</span>
            </div>
          </div>
          <div className="flex items-center">
            <span className="text-[11px] font-['Inter'] text-[#b9cac4] bg-[#1f1f25] px-3 py-1.5 rounded border border-[#3a4a46]/30 shadow-sm">
              Reference Stories 1.11, 3.10
            </span>
          </div>
        </section>

        {/* Global Error Alert */}
        {error && (
          <div className="bg-[#1f1f25]/60 backdrop-blur-[12px] p-5 rounded-xl border border-[#3a4a46]/15 border-l-4 border-l-[#ffb4ab] flex items-center justify-between shadow-[0_0_15px_rgba(255,180,171,0.15)] animate-shake">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-[#ffb4ab]">warning</span>
              <span className="text-sm font-medium text-[#ffb4ab] uppercase tracking-wide">System Fault Detected: {error}</span>
            </div>
            <button
              onClick={clearError}
              className="text-[#b9cac4] hover:text-[#ffb4ab] transition-colors"
              aria-label="Dismiss error"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column */}
          <div className="lg:col-span-5 xl:col-span-4 space-y-6">
            
            {/* Business Info Section */}
            <section className="bg-[#1f1f25]/60 backdrop-blur-[12px] p-6 rounded-2xl border border-[#3a4a46]/15 shadow-xl space-y-6 hover:border-[#00f5d4]/20 transition-all duration-500 group">
              <div className="flex items-center justify-between">
                <h2 className="text-xs font-bold text-[#26fedc] uppercase tracking-[0.2em] font-['Space_Grotesk'] group-hover:drop-shadow-[0_0_8px_rgba(0,245,212,0.4)] transition-all">
                  Standard Heuristics
                </h2>
                {!isDirty && hasConfig && (
                  <span className="text-[10px] text-[#d7fff3]/60 font-['Inter'] italic">Status: Synchronized</span>
                )}
              </div>
              
              <div className="space-y-6">
                <BusinessInfoForm disabled={isLoading} />
                <button
                  type="button"
                  onClick={handleSaveBusinessInfo}
                  disabled={isLoading || !isDirty}
                  className="w-full py-3.5 bg-gradient-to-r from-[#26fedc] to-[#00f5d4] text-[#00201a] font-['Space_Grotesk'] font-bold uppercase tracking-widest rounded-xl shadow-[0_0_20px_rgba(0,245,212,0.25)] active:scale-[0.98] hover:shadow-[0_0_30px_rgba(0,245,212,0.4)] transition-all disabled:opacity-30 disabled:grayscale disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Syncing...' : 'Commit Business Schema'}
                </button>
              </div>
            </section>

            {/* Business Hours Section */}
            <section className="bg-[#1f1f25]/60 backdrop-blur-[12px] p-6 rounded-2xl border border-[#3a4a46]/15 shadow-xl space-y-5 hover:border-[#00bbf9]/20 transition-all duration-500">
              <h2 className="text-xs font-bold text-[#82d3ff] uppercase tracking-[0.2em] font-['Space_Grotesk']">
                Operating Hours
              </h2>
              <BusinessHoursConfig />
            </section>
          </div>

          {/* Right Column: FAQs */}
          <div className="lg:col-span-7 xl:col-span-8 flex flex-col">
            <section className="flex-1 bg-[#1f1f25]/40 backdrop-blur-[12px] p-8 rounded-2xl border border-[#3a4a46]/15 shadow-xl hover:border-white/10 transition-all duration-500 flex flex-col min-h-[500px]">
              <FaqList />
            </section>
          </div>
        </div>

        {/* Intelligence Protocol (Bottom Section) */}
        <section className="pt-10 pb-6 border-t border-[#3a4a46]/10">
          <h2 className="text-xs font-bold text-[#b9cac4] uppercase tracking-[0.3em] font-['Space_Grotesk'] text-center mb-6">
            Intelligence Protocols
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-[#1b1b20] p-6 rounded-xl flex flex-col items-center text-center space-y-4 border border-[#3a4a46]/20 shadow-lg hover:border-[#00f5d4]/20 hover:-translate-y-1 transition-all">
              <span className="material-symbols-outlined text-[#00dfc1] text-3xl drop-shadow-[0_0_12px_rgba(0,245,212,0.3)]">anchor</span>
              <h3 className="text-[11px] font-bold uppercase tracking-widest text-[#e4e1e9]">Context Hook</h3>
              <p className="text-xs text-[#b9cac4]/80 leading-relaxed max-w-[250px]">
                Business heuristics are deeply injected into the AI&apos;s reasoning cycles, defining base identity.
              </p>
            </div>
            <div className="bg-[#1b1b20] p-6 rounded-xl flex flex-col items-center text-center space-y-4 border border-[#3a4a46]/20 shadow-lg hover:border-[#00bbf9]/20 hover:-translate-y-1 transition-all">
              <span className="material-symbols-outlined text-[#79d1ff] text-3xl drop-shadow-[0_0_12px_rgba(121,209,255,0.3)]">account_tree</span>
              <h3 className="text-[11px] font-bold uppercase tracking-widest text-[#e4e1e9]">Operational Logic</h3>
              <p className="text-xs text-[#b9cac4]/80 leading-relaxed max-w-[250px]">
                Controls human handoff and fallback parameters intelligently based on specified operating windows.
              </p>
            </div>
            <div className="bg-[#1b1b20] p-6 rounded-xl flex flex-col items-center text-center space-y-4 border border-[#3a4a46]/20 shadow-lg hover:border-[#ffced1]/20 hover:-translate-y-1 transition-all">
              <span className="material-symbols-outlined text-[#ffb2b8] text-3xl drop-shadow-[0_0_12px_rgba(255,178,184,0.3)]">database</span>
              <h3 className="text-[11px] font-bold uppercase tracking-widest text-[#e4e1e9]">Instant Retrieval</h3>
              <p className="text-xs text-[#b9cac4]/80 leading-relaxed max-w-[250px]">
                Pre-defined datasets are indexed and deployed for sub-50ms contextual recovery during chat.
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default BusinessInfoFaqConfig;
