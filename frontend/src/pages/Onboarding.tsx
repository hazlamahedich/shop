import React, { useEffect, useState } from 'react';
import { onboardingStore } from '../stores/onboardingStore';
import { InteractiveTutorial } from '../components/onboarding/InteractiveTutorial';
import { PrerequisiteChecklist } from '../components/onboarding/PrerequisiteChecklist';
import { DeploymentWizard } from '../components/onboarding/DeploymentWizard';
import { FacebookConnection } from '../components/onboarding/FacebookConnection';
import { ShopifyConnection } from '../components/onboarding/ShopifyConnection';
import { LLMConfiguration } from '../components/onboarding/LLMConfiguration';
import { ModeSelection } from '../components/onboarding/ModeSelection';
import { ProgressBarWithMilestones } from '../components/onboarding/ProgressBarWithMilestones';
import { useDeploymentStore } from '../stores/deploymentStore';
import { useIntegrationsStore } from '../stores/integrationsStore';
import { useLLMStore } from '../stores/llmStore';
import { OnboardingMode, DEFAULT_ONBOARDING_MODE } from '../types/onboarding';
import { GlassCard } from '../components/ui/GlassCard';
import { Button } from '../components/ui/Button';
import { Check, Cpu, Zap, Rocket, Settings2, Sparkles, ListTodo, Cloud, Wrench } from 'lucide-react';

const Onboarding = () => {
  const { isComplete, loadFromBackend, onboardingMode, setOnboardingMode } = onboardingStore();
  const { status: deploymentStatus, merchantKey } = useDeploymentStore();
  const { facebookConnection, shopifyConnection } = useIntegrationsStore();
  const { configuration: llmConfig } = useLLMStore();

  const [wizardStep, setWizardStep] = useState(0);
  const [showTutorial, setShowTutorial] = useState(false);
  const [selectedMode, setSelectedMode] = useState<OnboardingMode | null>(null);
  const [modeSelected, setModeSelected] = useState(false);
  const [isModeLoading, setIsModeLoading] = useState(false);
  const [modeError, setModeError] = useState<string | null>(null);

  useEffect(() => {
    loadFromBackend();
  }, [loadFromBackend]);

  // Check if mode already selected from store
  useEffect(() => {
    if (onboardingMode) {
      setSelectedMode(onboardingMode);
      setModeSelected(true);
    }
  }, [onboardingMode]);

  // Determine current wizard step based on state if not manually set
  useEffect(() => {
    if (modeSelected && isComplete()) {
      if (merchantKey || deploymentStatus === 'success') {
        setWizardStep(3);
      } else {
        setWizardStep(2);
      }
    } else if (modeSelected) {
      setWizardStep(1);
    } else {
      setWizardStep(0);
    }
  }, [isComplete, deploymentStatus, merchantKey, modeSelected]);

  // Transitions
  const handleModeSelect = (mode: OnboardingMode) => {
    setSelectedMode(mode);
  };

  const handleModeContinue = async () => {
    if (selectedMode) {
      setIsModeLoading(true);
      setModeError(null);
      try {
        await setOnboardingMode(selectedMode);
        // Only navigate to next step if API succeeds
        setModeSelected(true);
      } catch (error) {
        setModeError(
          error instanceof Error
            ? error.message
            : 'Failed to save mode selection. Please try again.'
        );
      } finally {
        setIsModeLoading(false);
      }
    }
  };

  const handleModeRetry = () => {
    setModeError(null);
    handleModeContinue();
  };

  const handlePrerequisitesDone = () => setWizardStep(2);
  const handleDeploymentDone = () => setWizardStep(3);
  const startTutorial = () => setShowTutorial(true);

  // Determine if e-commerce connections are required based on mode
  const isEcommerce = selectedMode === 'ecommerce';
  const canStartTutorial = isEcommerce
    ? facebookConnection.connected && shopifyConnection.connected && llmConfig.provider
    : llmConfig.provider;

  if (showTutorial) {
    return (
      <div
        className="min-h-screen bg-[#050505] flex flex-col items-center justify-center p-4 overflow-hidden relative"
      >
        <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/5 to-transparent opacity-20" />
        <div className="max-w-4xl w-full relative z-10">
          <InteractiveTutorial
            onComplete={() => (window.location.pathname = '/onboarding/success')}
          />
        </div>
      </div>
    );
  }

  const steps = [
    { id: 0, label: 'Choose Type', name: 'Choose Your Assistant', icon: Cpu, minutes: 2 },
    { id: 1, label: 'Get Ready', name: 'Complete Requirements', icon: ListTodo, minutes: 15 },
    { id: 2, label: 'Go Live', name: 'Set Up Your Assistant', icon: Rocket, minutes: 10 },
    { id: 3, label: 'Connect', name: 'Configure Services', icon: Settings2, minutes: 8 },
  ];

  return (
    <div className="min-h-screen bg-[#050505] flex flex-col items-center py-12 px-4 md:px-6 relative overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[500px] bg-emerald-500/10 blur-[120px] rounded-full -z-10 opacity-30" />

      <div className="max-w-6xl w-full space-y-8 relative z-10">
        {/* Header */}
        <div className="text-center space-y-4 max-w-2xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-black tracking-tight text-white leading-tight">
            {selectedMode === 'general'
              ? 'Set Up Your Customer Assistant'
              : 'Set Up Your Store Assistant'}
          </h1>
          <p className="text-base md:text-lg text-white/70 leading-relaxed">
            {selectedMode === 'general'
              ? 'Get your AI assistant ready to answer customer questions in just a few steps.'
              : 'Get your AI assistant ready to help customers browse and buy products.'}
          </p>
        </div>

        {/* Progress Bar with Milestones */}
        <div className="max-w-3xl mx-auto">
          <ProgressBarWithMilestones
            currentStep={wizardStep + 1}
            totalSteps={4}
            stepName={steps[wizardStep]?.name || ''}
            totalMinutes={35}
          />
        </div>

        {/* Wizard Content */}
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
          {wizardStep === 0 && (
            <ModeSelection
              selectedMode={selectedMode}
              onModeSelect={handleModeSelect}
              onContinue={handleModeContinue}
              isLoading={isModeLoading}
              error={modeError}
              onRetry={handleModeRetry}
            />
          )}

          {wizardStep === 1 && (
            <div className="space-y-12">
              <GlassCard accent="mantis" className="p-10 border-emerald-500/10 bg-emerald-500/[0.01]">
                <PrerequisiteChecklist mode={selectedMode || DEFAULT_ONBOARDING_MODE} />
              </GlassCard>
              {isComplete() && (
                <div className="flex justify-center">
                  <button
                    onClick={handlePrerequisitesDone}
                    className="h-16 px-16 bg-emerald-500 text-black font-black text-[11px] uppercase tracking-[0.3em] rounded-2xl hover:bg-emerald-400 transition-all duration-500 shadow-[0_0_40px_rgba(16,185,129,0.2)] hover:shadow-[0_0_50px_rgba(16,185,129,0.4)] hover:-translate-y-1"
                  >
                    Proceed to Deployment
                  </button>
                </div>
              )}
            </div>
          )}

          {wizardStep === 2 && (
            <div className="space-y-12">
              <GlassCard accent="mantis" className="p-10 border-emerald-500/10 bg-emerald-500/[0.01]">
                <DeploymentWizard />
              </GlassCard>
              {(deploymentStatus === 'success' || merchantKey) && (
                <div className="flex justify-center">
                  <button
                    onClick={handleDeploymentDone}
                    className="h-14 px-12 bg-emerald-500 text-black font-bold text-sm uppercase tracking-wide rounded-xl hover:bg-emerald-400 transition-all duration-300 shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                  >
                    Continue to Setup
                  </button>
                </div>
              )}
            </div>
          )}

          {wizardStep === 3 && (
            <div className="space-y-12 pb-20">
              {isEcommerce && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <GlassCard className="p-8 border-white/[0.03] bg-white/[0.01]">
                    <FacebookConnection />
                  </GlassCard>
                  <GlassCard className="p-8 border-white/[0.03] bg-white/[0.01]">
                    <ShopifyConnection />
                  </GlassCard>
                </div>
              )}

              <GlassCard accent="mantis" className="p-10 border-emerald-500/10 bg-emerald-500/[0.01]">
                <LLMConfiguration />
              </GlassCard>

              <GlassCard className="bg-emerald-500/[0.02] border-emerald-500/10 relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-r from-emerald-500/[0.05] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
                <div className="p-12 text-center space-y-8 relative z-10">
                  <div className="space-y-4">
                    <h3 className="text-2xl md:text-3xl font-black text-white tracking-tight">You're Almost Done!</h3>
                    <p className="text-base text-white/70 max-w-2xl mx-auto">
                      {isEcommerce
                        ? "Your store assistant is ready! Complete the final connections to start selling."
                        : "Your assistant is ready! Complete the setup to start helping customers."}
                    </p>
                  </div>

                  <div className="flex flex-col sm:flex-row justify-center gap-4 pt-4">
                    <button
                      onClick={startTutorial}
                      disabled={!canStartTutorial}
                      className={`
                        h-14 px-8 rounded-xl flex items-center justify-center gap-3 font-bold text-sm uppercase tracking-wide transition-all duration-300
                        ${canStartTutorial
                          ? 'bg-emerald-500 text-black hover:bg-emerald-400 shadow-lg hover:shadow-xl'
                          : 'bg-white/5 border border-white/10 text-white/30 cursor-not-allowed'}
                      `}
                    >
                      <Sparkles size={16} />
                      Start Tutorial
                    </button>
                    <button
                      onClick={() => (window.location.pathname = '/onboarding/success')}
                      className="h-14 px-8 rounded-xl bg-white/5 border border-white/10 text-white font-bold text-sm uppercase tracking-wide hover:bg-white/10 transition-all duration-300"
                    >
                      Go to Dashboard
                    </button>
                  </div>

                  {!canStartTutorial && (
                    <div className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs font-bold text-amber-400">
                      <Settings2 size={14} />
                      Complete the setup above first
                    </div>
                  )}
                </div>
              </GlassCard>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
