import React, { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { onboardingStore } from '../stores/onboardingStore';
import { InteractiveTutorial } from '../components/onboarding/InteractiveTutorial';
import { PrerequisiteChecklist } from '../components/onboarding/PrerequisiteChecklist';
import { DeploymentWizard } from '../components/onboarding/DeploymentWizard';
import { FacebookConnection } from '../components/onboarding/FacebookConnection';
import { ShopifyConnection } from '../components/onboarding/ShopifyConnection';
import { LLMConfiguration } from '../components/onboarding/LLMConfiguration';
import { ModeSelection } from '../components/onboarding/ModeSelection';
import { useDeploymentStore } from '../stores/deploymentStore';
import { useIntegrationsStore } from '../stores/integrationsStore';
import { useLLMStore } from '../stores/llmStore';
import { OnboardingMode, DEFAULT_ONBOARDING_MODE } from '../types/onboarding';

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
        className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4"
        data-theme="onboarding"
      >
        <div className="max-w-4xl w-full">
          <InteractiveTutorial
            onComplete={() => (window.location.pathname = '/onboarding/success')}
          />
        </div>
      </div>
    );
  }

  return (
    <div
      className="min-h-screen bg-gray-50 flex flex-col items-center py-12 px-4"
      data-theme="onboarding"
    >
      <div className="max-w-4xl w-full">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900">Setting Up Your Shop Assistant</h1>
          <p className="text-gray-500 mt-2">
            {selectedMode === 'general'
              ? 'Follow these steps to get your AI chatbot running.'
              : 'Follow these steps to get your AI-powered commerce agent running.'}
          </p>
        </div>

        {/* Stepper */}
        <div className="flex items-center justify-center mb-12">
          {[
            { id: 0, label: 'Mode' },
            { id: 1, label: 'Prerequisites' },
            { id: 2, label: 'Deployment' },
            { id: 3, label: 'Configuration' },
          ].map((s, i) => (
            <React.Fragment key={s.id}>
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all shadow-sm ${
                    s.id <= wizardStep
                      ? 'bg-primary text-white scale-110'
                      : 'bg-gray-200 text-gray-400'
                  }`}
                >
                  {s.id < wizardStep ? '✓' : s.id}
                </div>
                <span
                  className={`mt-2 text-xs font-semibold uppercase tracking-wider transition-colors ${
                    s.id === wizardStep
                      ? 'text-primary font-bold'
                      : s.id < wizardStep
                        ? 'text-slate-600'
                        : 'text-gray-400'
                  }`}
                >
                  {s.label}
                </span>
                {s.id === wizardStep && (
                  <div className="absolute -bottom-4 w-1 h-1 bg-primary rounded-full" />
                )}
              </div>
              {i < 3 && (
                <div
                  className={`w-24 h-1 mx-4 -mt-6 transition-colors ${
                    s.id < wizardStep ? 'bg-primary' : 'bg-gray-200'
                  }`}
                ></div>
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Wizard Content */}
        <div className="transition-all duration-300">
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
            <div className="space-y-6">
              <PrerequisiteChecklist mode={selectedMode || DEFAULT_ONBOARDING_MODE} />
              {isComplete() && (
                <div className="flex justify-center">
                  <Button onClick={handlePrerequisitesDone} size="lg" className="px-12">
                    Move to Deployment
                  </Button>
                </div>
              )}
            </div>
          )}

          {wizardStep === 2 && (
            <div className="space-y-6">
              <DeploymentWizard />
              {(deploymentStatus === 'success' || merchantKey) && (
                <div className="flex justify-center">
                  <Button onClick={handleDeploymentDone} size="lg" className="px-12">
                    Configure Connections
                  </Button>
                </div>
              )}
            </div>
          )}

          {wizardStep === 3 && (
            <div className="space-y-8 pb-20">
              {isEcommerce && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card className="p-1">
                    <div className="p-6">
                      <FacebookConnection />
                    </div>
                  </Card>
                  <Card className="p-1">
                    <div className="p-6">
                      <ShopifyConnection />
                    </div>
                  </Card>
                </div>
              )}

              <LLMConfiguration />

              <Card className="bg-primary/5 border-primary/20">
                <div className="p-8 text-center space-y-4">
                  <h3 className="text-xl font-bold text-gray-900">Final Verification</h3>
                  <p className="text-sm text-gray-600 max-w-lg mx-auto">
                    {isEcommerce
                      ? "Once you've connected your platforms and tested the LLM, you're ready to start the interactive tour or jump straight into the dashboard."
                      : "Once you've tested the LLM, you're ready to start the interactive tour or jump straight into the dashboard."}
                  </p>
                  <div className="flex flex-col sm:flex-row justify-center gap-4 pt-4">
                    <Button
                      onClick={startTutorial}
                      variant="default"
                      size="lg"
                      disabled={!canStartTutorial}
                    >
                      Start Interactive Tutorial
                    </Button>
                    <Button
                      onClick={() => (window.location.pathname = '/onboarding/success')}
                      variant="outline"
                      size="lg"
                    >
                      Finish Onboarding
                    </Button>
                  </div>
                  {!canStartTutorial && (
                    <p className="text-xs text-amber-600 font-medium">
                      {isEcommerce
                        ? 'Note: Connecting platforms and LLM is recommended before starting the tutorial.'
                        : 'Note: Configuring LLM is recommended before starting the tutorial.'}
                    </p>
                  )}
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
