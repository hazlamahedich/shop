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

import React, { useEffect, useState } from 'react';
import { Save, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { usePersonalityStore, selectPersonality, selectCustomGreeting, selectPersonalityLoading, selectPersonalityError, selectPersonalityIsDirty, selectEffectiveGreeting } from '../stores/personalityStore';
import { PersonalityCard } from '../components/personality/PersonalityCard';
import { GreetingEditor } from '../components/personality/GreetingEditor';
import type { PersonalityType } from '../types/enums';
import { PersonalityDisplay, PersonalityDefaultGreetings } from '../types/enums';

const PersonalityConfig: React.FC = () => {
  // Store state
  const personality = usePersonalityStore(selectPersonality);
  const customGreeting = usePersonalityStore(selectCustomGreeting);
  const loading = usePersonalityStore(selectPersonalityLoading);
  const error = usePersonalityStore(selectPersonalityError);
  const isDirty = usePersonalityStore(selectPersonalityIsDirty);

  // Local state for UI
  const [selectedPersonality, setSelectedPersonality] = useState<PersonalityType | null>(null);
  const [greetingValue, setGreetingValue] = useState<string>('');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [localError, setLocalError] = useState<string | null>(null);

  const fetchPersonalityConfig = usePersonalityStore((state) => state.fetchPersonalityConfig);
  const updatePersonalityConfig = usePersonalityStore((state) => state.updatePersonalityConfig);
  const setPersonality = usePersonalityStore((state) => state.setPersonality);
  const setCustomGreeting = usePersonalityStore((state) => state.setCustomGreeting);
  const resetToDefault = usePersonalityStore((state) => state.resetToDefault);
  const clearError = usePersonalityStore((state) => state.clearError);

  // Initialize: fetch configuration on mount
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

  // Sync local state with store state
  useEffect(() => {
    if (personality) {
      setSelectedPersonality(personality);
    }
  }, [personality]);

  useEffect(() => {
    setGreetingValue(customGreeting || '');
  }, [customGreeting]);

  // Handle personality selection
  const handlePersonalitySelect = (newPersonality: PersonalityType) => {
    setSelectedPersonality(newPersonality);
    setPersonality(newPersonality);
    setSaveStatus('idle');
    setLocalError(null);
    clearError();
  };

  // Handle greeting change
  const handleGreetingChange = (value: string) => {
    setGreetingValue(value);
    setCustomGreeting(value);
    setSaveStatus('idle');
    setLocalError(null);
    clearError();
  };

  // Handle reset to default
  const handleResetGreeting = () => {
    setGreetingValue('');
    resetToDefault();
    setSaveStatus('idle');
  };

  // Handle save
  const handleSave = async () => {
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
      setSaveStatus('success');

      // Clear success message after 3 seconds
      setTimeout(() => {
        setSaveStatus('idle');
      }, 3000);
    } catch (err) {
      setSaveStatus('error');
      const errorMessage = err instanceof Error ? err.message : 'Failed to save configuration';
      setLocalError(errorMessage);
    }
  };

  // Get default greeting for current personality
  const getDefaultGreeting = (): string => {
    if (!selectedPersonality) return '';
    return PersonalityDefaultGreetings[selectedPersonality];
  };

  const effectiveGreeting = greetingValue || getDefaultGreeting();

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Bot Personality</h1>
        <p className="text-gray-600">
          Choose your bot's personality to match your brand voice. You can also customize the greeting message.
        </p>
      </div>

      {/* Error alert */}
      {(error || localError) && (
        <div
          className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3"
          role="alert"
        >
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-red-800">Error</h3>
            <p className="text-sm text-red-700 mt-1">{error || localError}</p>
          </div>
        </div>
      )}

      {/* Success alert */}
      {saveStatus === 'success' && (
        <div
          className="p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3"
          role="status"
          aria-live="polite"
        >
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-green-800">Success</h3>
            <p className="text-sm text-green-700 mt-1">
              Personality configuration saved successfully. Your bot will use the new personality for all future conversations.
            </p>
          </div>
        </div>
      )}

      {/* Personality Selection */}
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

      {/* Custom Greeting */}
      {selectedPersonality && (
        <section className="space-y-4 pt-6 border-t border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Customize Greeting</h2>
          <p className="text-sm text-gray-600 pointer-events-none">
            Optionally customize the first message your bot sends. Leave empty to use the default greeting for the {PersonalityDisplay[selectedPersonality].toLowerCase()} personality.
          </p>

          <GreetingEditor
            value={greetingValue}
            onChange={handleGreetingChange}
            defaultGreeting={getDefaultGreeting()}
            onReset={handleResetGreeting}
            disabled={loading}
          />

          {/* Current effective greeting display */}
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200 pointer-events-none">
            <p className="text-xs text-blue-700 font-medium mb-1">Current Greeting:</p>
            <p className="text-sm text-blue-900">"{effectiveGreeting}"</p>
          </div>
        </section>
      )}

      {/* Save button */}
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
          className={`
            inline-flex items-center gap-2 px-6 py-2.5 rounded-lg font-medium text-white
            transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
            disabled:opacity-50 disabled:cursor-not-allowed
            ${loading || saveStatus === 'saving'
              ? 'bg-gray-400 cursor-wait'
              : 'bg-primary hover:bg-blue-700'
            }
          `}
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
