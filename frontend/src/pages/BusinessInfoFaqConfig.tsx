/**
 * BusinessInfoFaqConfig Page Component
 */

import * as React from 'react';
import { useEffect } from 'react';
import { useToast } from '../context/ToastContext';
import { useBusinessInfoStore } from '../stores/businessInfoStore';
import { useWidgetSettingsStore } from '../stores/widgetSettingsStore';
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

  const { fetchConfig, updateConfig, config: widgetConfig } = useWidgetSettingsStore();

  const markBotConfigComplete = useOnboardingPhaseStore((state) => state.markBotConfigComplete);
  const { toast } = useToast();

  useEffect(() => {
    const loadData = async () => {
      try {
        await Promise.all([
          fetchBusinessInfo(),
          fetchConfig()
        ]);
      } catch (err) {
        console.error('Failed to load configuration:', err);
        toast('Failed to load configuration', 'error');
      }
    };
    loadData();
  }, [fetchBusinessInfo, fetchConfig, toast]);

  const handleSaveBusinessInfo = async () => {
    clearError();
    try {
      await updateBusinessInfo({
        businessName,
        businessDescription,
        businessHours,
      });

      // Also save widget config if it exists (for contact options)
      if (widgetConfig) {
        await updateConfig({
          contactOptions: widgetConfig.contactOptions
        });
      }

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
        <nav className="flex items-center space-x-2 text-[10px] uppercase tracking-[0.15em] text-[#b9cac4]/60 font-['Inter']">
          <span>Primary Dashboard</span>
          <span className="material-symbols-outlined text-[12px]">chevron_right</span>
          <span className="text-[#00dfc1]">Intelligence Config & FAQ</span>
        </nav>

        <section className="space-y-3">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <h1 className="text-4xl lg:text-5xl font-['Space_Grotesk'] font-bold tracking-tight text-[#e4e1e9] uppercase">
              Intelligence Engine
            </h1>
          </div>
        </section>

        {error && (
          <div className="bg-[#1f1f25]/60 backdrop-blur-[12px] p-5 rounded-xl border border-[#3a4a46]/15 border-l-4 border-l-[#ffb4ab] flex items-center justify-between shadow-[0_0_15px_rgba(255,180,171,0.15)] animate-shake">
            <div className="flex items-center gap-3">
              <span className="material-symbols-outlined text-[#ffb4ab]">warning</span>
              <span className="text-sm font-medium text-[#ffb4ab] uppercase tracking-wide">System Fault Detected: {error}</span>
            </div>
            <button onClick={clearError} className="text-[#b9cac4] hover:text-[#ffb4ab] transition-colors">
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-5 xl:col-span-4 space-y-6">
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

            <section className="bg-[#1f1f25]/60 backdrop-blur-[12px] p-6 rounded-2xl border border-[#3a4a46]/15 shadow-xl space-y-5 hover:border-[#00bbf9]/20 transition-all duration-500">
              <h2 className="text-xs font-bold text-[#82d3ff] uppercase tracking-[0.2em] font-['Space_Grotesk']">
                Operating Hours
              </h2>
              <BusinessHoursConfig />
            </section>
          </div>

          <div className="lg:col-span-7 xl:col-span-8 flex flex-col">
            <section className="flex-1 bg-[#1f1f25]/40 backdrop-blur-[12px] p-8 rounded-2xl border border-[#3a4a46]/15 shadow-xl hover:border-white/10 transition-all duration-500 flex flex-col min-h-[500px]">
              <FaqList />
            </section>
          </div>
        </div>
      </main>
    </div>
  );
};

export default BusinessInfoFaqConfig;
