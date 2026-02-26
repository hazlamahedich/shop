import * as React from 'react';
import type { WidgetTheme, PersonalityType } from '../types/widget';

const CONSENT_MESSAGES: Record<PersonalityType, { title: string; description: string }> = {
  friendly: {
    title: 'Save your preferences?',
    description: 'I can remember your preferences to help you shop faster next time! 😊 Your data stays private and you can change this anytime.',
  },
  professional: {
    title: 'Save conversation data?',
    description: 'To provide personalized service in future conversations, I can save your preferences. Your data is handled according to privacy regulations.',
  },
  enthusiastic: {
    title: 'Remember me?! 🎉',
    description: 'Want me to remember your preferences so I can help you shop EVEN FASTER next time?! Your data stays safe and you can always change your mind!',
  },
};

export interface ConsentPromptProps {
  isOpen: boolean;
  isLoading: boolean;
  isTyping?: boolean;
  promptShown: boolean;
  consentGranted: boolean | null;
  theme: WidgetTheme;
  botName: string;
  personality?: PersonalityType;
  onConfirmConsent: (consented: boolean) => Promise<void>;
  onDismiss?: () => void;
}

export function ConsentPrompt({
  isOpen,
  isLoading,
  isTyping = false,
  promptShown,
  consentGranted,
  theme,
  botName,
  personality = 'friendly',
  onConfirmConsent,
  onDismiss,
}: ConsentPromptProps) {
  const [isProcessing, setIsProcessing] = React.useState(false);

  if (!isOpen || !promptShown || consentGranted !== null) {
    return null;
  }

  const handleConsent = async (consented: boolean) => {
    setIsProcessing(true);
    try {
      await onConfirmConsent(consented);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleOptIn = () => handleConsent(true);
  const handleOptOut = () => handleConsent(false);
  const handleDismiss = () => onDismiss?.();

  const disabled = isLoading || isTyping || isProcessing;
  const messages = CONSENT_MESSAGES[personality];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="consent-title"
      aria-describedby="consent-description"
      className="shopbot-consent-prompt"
      style={{
        padding: '16px',
        backgroundColor: theme.botBubbleColor,
        borderRadius: theme.borderRadius,
        margin: '8px 0',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
      }}
    >
      <div
        id="consent-title"
        style={{
          fontSize: '14px',
          fontWeight: 600,
          marginBottom: '8px',
          color: theme.textColor,
        }}
      >
        {messages.title}
      </div>
      <p
        id="consent-description"
        style={{
          fontSize: '13px',
          lineHeight: '1.5',
          marginBottom: '12px',
          color: theme.textColor,
          opacity: 0.9,
        }}
      >
        {messages.description.replace('{botName}', botName)}
      </p>
      <div
        style={{
          display: 'flex',
          gap: '8px',
          justifyContent: 'flex-end',
        }}
      >
        <button
          type="button"
          onClick={handleOptOut}
          disabled={disabled}
          style={{
            padding: '8px 16px',
            fontSize: '13px',
            fontWeight: 500,
            border: `1px solid ${theme.primaryColor}`,
            backgroundColor: 'transparent',
            color: theme.primaryColor,
            borderRadius: theme.borderRadius / 2,
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? 0.6 : 1,
            transition: 'all 0.2s ease',
          }}
          aria-label="Decline to save preferences"
        >
          No, don't save
        </button>
        <button
          type="button"
          onClick={handleOptIn}
          disabled={disabled}
          style={{
            padding: '8px 16px',
            fontSize: '13px',
            fontWeight: 500,
            border: 'none',
            backgroundColor: theme.primaryColor,
            color: 'white',
            borderRadius: theme.borderRadius / 2,
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? 0.6 : 1,
            transition: 'all 0.2s ease',
          }}
          aria-label="Agree to save preferences"
        >
          Yes, save my preferences
        </button>
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={handleDismiss}
          disabled={disabled}
          style={{
            position: 'absolute',
            top: '8px',
            right: '8px',
            padding: '4px',
            background: 'none',
            border: 'none',
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: 0.6,
            fontSize: '16px',
          }}
          aria-label="Close consent prompt"
        >
          ×
        </button>
      )}
    </div>
  );
}
