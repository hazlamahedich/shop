/**
 * Personality Configuration Page
 *
 * Story 1.10: Bot Personality Configuration
 *
 * Allows merchants to:
 * - Select their bot's personality from predefined options
 * - Customize the bot's greeting message
 * - Save and persist their configuration
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { Save, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { usePersonalityStore, selectPersonality, selectCustomGreeting, selectPersonalityLoading, selectPersonalityError, selectPersonalityIsDirty } from '../stores/personalityStore';
import { useOnboardingPhaseStore } from '../stores/onboardingPhaseStore';
import { useBotConfigStore } from '../stores/botConfigStore';
import { useBusinessInfoStore } from '../stores/businessInfoStore';
import { PersonalityCard } from '../components/personality/PersonalityCard';
import { GreetingConfig } from '../components/business-info/GreetingConfig';
import type { PersonalityType } from '../types/enums';
import { PersonalityDisplay, PersonalityDefaultGreetings } from '../types/enums';
import { hasToneMismatch, getToneMismatchMessage, isToneMatch } from '../utils/toneDetection';
import { merchantConfigApi } from '../services/merchantConfig';

const PersonalityConfig: React.FC = () => {
  const personality = usePersonalityStore(selectPersonality);
  const customGreeting = usePersonalityStore(selectCustomGreeting);
  const loading = usePersonalityStore(selectPersonalityLoading);
  const error = usePersonalityStore(selectPersonalityError);
  const isDirty = usePersonalityStore(selectPersonalityIsDirty);
  const markBotConfigComplete = useOnboardingPhaseStore((state) => state.markBotConfigComplete);
  const botName = useBotConfigStore((state) => state.botName);
  const businessName = useBusinessInfoStore((state) => state.businessName);
  const businessHours = useBusinessInfoStore((state) => state.businessHours);

  const [selectedPersonality, setSelectedPersonality] = useState<PersonalityType | null>(null);
  const [greetingValue, setGreetingValue] = useState<string>('');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [localError, setLocalError] = useState<string | null>(null);
  const [showToneWarning, setShowToneWarning] = useState(false);
  const [dismissedWarning, setDismissedWarning] = useState(false);
  const [transformLoading, setTransformLoading] = useState(false);
  const [transformedGreeting, setTransformedGreeting] = useState<string | null>(null);
  const [suggestionApplied, setSuggestionApplied] = useState(false);

  const fetchPersonalityConfig = usePersonalityStore((state) => state.fetchPersonalityConfig);
  const updatePersonalityConfig = usePersonalityStore((state) => state.updatePersonalityConfig);
  const setPersonality = usePersonalityStore((state) => state.setPersonality);
  const setCustomGreeting = usePersonalityStore((state) => state.setCustomGreeting);
  const resetToDefault = usePersonalityStore((state) => state.resetToDefault);
  const clearError = usePersonalityStore((state) => state.clearError);

  const prevGreetingRef = useRef<string>('');
  const prevPersonalityRef = useRef<PersonalityType | null>(null);

  useEffect(() => {
    const init = async () => {
      try {
        await fetchPersonalityConfig();
      } catch (err) {
        setLocalError('Failed to load personality configuration');
        console.error('Failed to initialize personality config:', err);
      }
    };
    init();
  }, [fetchPersonalityConfig]);

  useEffect(() => {
    if (personality) {
      setSelectedPersonality(personality);
    }
  }, [personality]);

  useEffect(() => {
    setGreetingValue(customGreeting || '');
  }, [customGreeting]);

  useEffect(() => {
    if (!selectedPersonality || !greetingValue || greetingValue.trim().length === 0) {
      setTransformedGreeting(null);
      return;
    }

    if (isToneMatch(greetingValue, selectedPersonality)) {
      setTransformedGreeting(null);
      return;
    }

    if (
      prevGreetingRef.current === greetingValue &&
      prevPersonalityRef.current === selectedPersonality
    ) {
      return;
    }

    prevGreetingRef.current = greetingValue;
    prevPersonalityRef.current = selectedPersonality;

    let cancelled = false;

    const transformExistingGreeting = async () => {
      setTransformLoading(true);
      setTransformedGreeting(null);
      setSuggestionApplied(false);

      try {
        const response = await merchantConfigApi.transformGreeting({
          custom_greeting: greetingValue,
          target_personality: selectedPersonality,
          bot_name: botName,
          business_name: businessName,
        });

        if (!cancelled) {
          if (response.transformed_greeting && response.transformed_greeting !== greetingValue) {
            setTransformedGreeting(response.transformed_greeting);
          } else {
            setTransformedGreeting(null);
          }
        }
      } catch (error) {
        console.error('[GreetingTransform] Failed:', error);
        if (!cancelled) {
          setTransformedGreeting(null);
        }
      } finally {
        if (!cancelled) {
          setTransformLoading(false);
        }
      }
    };

    transformExistingGreeting();

    return () => {
      cancelled = true;
    };
  }, [selectedPersonality, greetingValue, botName, businessName]);

  const handlePersonalitySelect = (newPersonality: PersonalityType) => {
    setSelectedPersonality(newPersonality);
    setPersonality(newPersonality);
    setSaveStatus('idle');
    setLocalError(null);
    clearError();
    setSuggestionApplied(false);
  };

  const handleGreetingChange = (value: string) => {
    setGreetingValue(value);
    setCustomGreeting(value);
    setSaveStatus('idle');
    setLocalError(null);
    clearError();
    setDismissedWarning(false);
    setShowToneWarning(false);
    setSuggestionApplied(false);
  };

  const handleResetGreeting = () => {
    setGreetingValue('');
    resetToDefault();
    setSaveStatus('idle');
    setShowToneWarning(false);
    setDismissedWarning(false);
    setTransformedGreeting(null);
    setSuggestionApplied(false);
  };

  const getSuggestedGreeting = useCallback((): string => {
    if (!selectedPersonality) return '';

    if (transformedGreeting) {
      return transformedGreeting;
    }

    const template = PersonalityDefaultGreetings[selectedPersonality];

    return template
      .replace(/{bot_name}/g, botName || 'your shopping assistant')
      .replace(/{business_name}/g, businessName || 'our store')
      .replace(/{business_hours}/g, businessHours || '');
  }, [selectedPersonality, botName, businessName, businessHours, transformedGreeting]);

  const handleApplySuggestion = () => {
    const suggested = getSuggestedGreeting();
    setGreetingValue(suggested);
    setCustomGreeting(suggested);
    setShowToneWarning(false);
    setDismissedWarning(false);
    setSaveStatus('idle');
    setTransformedGreeting(null);
    prevGreetingRef.current = suggested;
    setSuggestionApplied(true);
  };

  const handleDismissWarning = () => {
    setShowToneWarning(false);
    setDismissedWarning(true);
  };

  const handleSaveAnyway = () => {
    setShowToneWarning(false);
    performSave();
  };

  const performSave = async () => {
    if (!selectedPersonality) {
      setLocalError('Please select a personality');
      return;
    }

    setSaveStatus('saving');
    setLocalError(null);
    clearError();

    try {
      await updatePersonalityConfig({
        personality: selectedPersonality,
        custom_greeting: greetingValue || null,
      });
      markBotConfigComplete('personality');
      setSaveStatus('success');
      setShowToneWarning(false);
      setDismissedWarning(false);

      setTimeout(() => {
        setSaveStatus('idle');
      }, 3000);
    } catch (err) {
      setSaveStatus('error');
      const errorMessage = err instanceof Error ? err.message : 'Failed to save configuration';
      setLocalError(errorMessage);
    }
  };

  const handleSave = async () => {
    if (!selectedPersonality) {
      setLocalError('Please select a personality');
      return;
    }

    if (!dismissedWarning && hasToneMismatch(greetingValue, selectedPersonality)) {
      setShowToneWarning(true);
      return;
    }

    await performSave();
  };

  const getDefaultGreeting = (): string => {
    if (!selectedPersonality) return '';
    return PersonalityDefaultGreetings[selectedPersonality];
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Bot Personality</h1>
        <p className="text-gray-600">
          Choose your bot's personality to match your brand voice. You can also customize the greeting message.
        </p>
      </div>

      {(error || localError) && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3" role="alert">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-red-800">Error</h3>
            <p className="text-sm text-red-700 mt-1">{error || localError}</p>
          </div>
        </div>
      )}

      {saveStatus === 'success' && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3" role="status" aria-live="polite">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-green-800">Success</h3>
            <p className="text-sm text-green-700 mt-1">
              Personality configuration saved successfully. Your bot will use the new personality for all future conversations.
            </p>
          </div>
        </div>
      )}

      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-gray-900">Select a Personality</h2>
        <p className="text-sm text-gray-600">
          Choose the tone and style that best represents your brand. Click on a card to select it.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {(Object.keys(PersonalityDisplay) as PersonalityType[]).map((type) => (
            <PersonalityCard
              key={type}
              personality={type}
              isSelected={selectedPersonality === type}
              onSelect={handlePersonalitySelect}
            />
          ))}
        </div>
      </section>

      {selectedPersonality && (
        <section className="space-y-4 pt-6 border-t border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Customize Greeting</h2>
          <p className="text-sm text-gray-600 pointer-events-none">
            Optionally customize the first message your bot sends. Leave empty to use the default greeting for the {PersonalityDisplay[selectedPersonality].toLowerCase()} personality.
          </p>

          <GreetingConfig
            personality={selectedPersonality}
            greetingTemplate={greetingValue || null}
            useCustomGreeting={!!greetingValue}
            defaultTemplate={getDefaultGreeting()}
            availableVariables={['bot_name', 'business_name', 'business_hours']}
            botName={botName}
            businessName={businessName}
            businessHours={businessHours}
            onUpdate={(data) => {
              if (data.greeting_template !== undefined) {
                handleGreetingChange(data.greeting_template);
              }
            }}
            onReset={handleResetGreeting}
            disabled={loading}
            showSuggestion={!suggestionApplied && !!transformedGreeting}
            suggestedGreeting={getSuggestedGreeting()}
            suggestionLoading={transformLoading}
            onApplySuggestion={handleApplySuggestion}
            toneMismatchWarning={showToneWarning ? getToneMismatchMessage(greetingValue) : null}
            onDismissWarning={handleDismissWarning}
            onSaveAnyway={handleSaveAnyway}
          />
        </section>
      )}

      <div className="flex items-center justify-between pt-6 border-t border-gray-200">
        <p className="text-sm text-gray-500">
          {isDirty ? (
            <span className="text-amber-600">You have unsaved changes</span>
          ) : (
            'All changes saved'
          )}
        </p>
        <button
          type="button"
          onClick={handleSave}
          disabled={loading || !selectedPersonality || saveStatus === 'saving'}
          className="inline-flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium text-white transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400"
        >
          {saveStatus === 'saving' ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Configuration
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default PersonalityConfig;
