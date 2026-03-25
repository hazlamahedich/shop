import * as React from 'react';
import { useVoiceInput } from '../hooks/useVoiceInput';
import type { VoiceInputConfig } from '../types/widget';
import { trackVoiceInput } from '../utils/analytics';

export interface VoiceInputProps {
  config?: Partial<VoiceInputConfig>;
  onTranscript?: (transcript: string) => void;
  onInterimTranscript?: (transcript: string) => void;
  onError?: (error: string) => void;
  disabled?: boolean;
  theme?: {
    primaryColor?: string;
    backgroundColor?: string;
    textColor?: string;
  };
  onLanguageChange?: (language: string) => void;
}

function MicrophoneIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" x2="12" y1="19" y2="22" />
    </svg>
  );
}

function WaveformAnimation() {
  return (
    <div className="waveform-container">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="waveform-bar" />
      ))}
    </div>
  );
}

function Spinner() {
  return <div className="voice-spinner" />;
}

function ErrorIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <line x1="12" x2="12" y1="8" y2="12" />
      <line x1="12" x2="12.01" y1="16" y2="16" />
    </svg>
  );
}

export function VoiceInput({
  config,
  onTranscript,
  onInterimTranscript,
  onError,
  disabled = false,
  theme: _theme,
  onLanguageChange,
}: VoiceInputProps) {
  const { state, isSupported, startListening, stopListening, cancelListening, setLanguage } = useVoiceInput(config);
  const [showError, setShowError] = React.useState(false);
  const [startTime, setStartTime] = React.useState<number | null>(null);
  
  // Expose setLanguage for parent components
  React.useEffect(() => {
    if (onLanguageChange) {
      // Create a handler that can be called externally
      (window as unknown as { __voiceInputSetLanguage?: (lang: string) => void }).__voiceInputSetLanguage = setLanguage;
    }
  }, [onLanguageChange, setLanguage]);
  
  React.useEffect(() => {
    if (state.error) {
      setShowError(true);
      onError?.(state.error);
    }
  }, [state.error, onError]);
  
  React.useEffect(() => {
    onInterimTranscript?.(state.interimTranscript);
  }, [state.interimTranscript, onInterimTranscript]);
  
  const transcriptProcessedRef = React.useRef<string | null>(null);

  React.useEffect(() => {
    if (state.finalTranscript && !state.isListening) {
      if (transcriptProcessedRef.current === state.finalTranscript) {
        return;
      }
      transcriptProcessedRef.current = state.finalTranscript;
      const durationMs = startTime ? Date.now() - startTime : 0;
      trackVoiceInput(durationMs, true);
      onTranscript?.(state.finalTranscript);
      setStartTime(null);
    }
  }, [state.finalTranscript, state.isListening, startTime, onTranscript]);
  
  const handleToggle = async () => {
    if (state.isListening) {
      stopListening();
    } else {
      setShowError(false);
      setStartTime(Date.now());
      await startListening();
    }
  };
  
  const handleCancel = () => {
    cancelListening();
  };
  
  const handleDismissError = () => {
    setShowError(false);
  };
  
  const getButtonState = () => {
    if (!isSupported) return 'unsupported';
    if (state.error) return 'error';
    if (state.isProcessing) return 'processing';
    if (state.isListening) return 'listening';
    return 'idle';
  };
  
  const buttonState = getButtonState();
  const isDisabled = disabled || !isSupported;
  
  const getAriaLabel = () => {
    if (!isSupported) return 'Voice input not supported in this browser';
    if (state.isListening) return 'Stop voice input';
    return 'Start voice input';
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape' && state.isListening) {
      e.preventDefault();
      cancelListening();
    }
  };
  
  return (
    <div className="voice-input-container">
      <button
        data-testid="voice-input-button"
        type="button"
        role="button"
        aria-label={getAriaLabel()}
        aria-pressed={state.isListening}
        disabled={isDisabled}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        className={`voice-input-button ${buttonState}`}
        title={!isSupported ? 'Voice input not supported in this browser' : undefined}
      >
        {buttonState === 'listening' && <WaveformAnimation />}
        {buttonState === 'processing' && <Spinner />}
        {buttonState === 'error' && <ErrorIcon />}
        {buttonState === 'unsupported' && <MicrophoneIcon />}
        {buttonState === 'idle' && <MicrophoneIcon />}
      </button>
      
      {state.isListening && (
        <button
          data-testid="voice-input-cancel"
          type="button"
          aria-label="Cancel voice input"
          onClick={handleCancel}
          className="voice-cancel-button"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" x2="6" y1="6" y2="18" />
            <line x1="6" x2="18" y1="6" y2="18" />
          </svg>
        </button>
      )}
      
      {state.interimTranscript && state.isListening && (
        <div
          data-testid="voice-interim-transcript"
          aria-live="polite"
          aria-label="Interim transcript"
          className="voice-interim-transcript"
        >
          {state.interimTranscript}
        </div>
      )}
      
      {showError && state.error && !state.isListening && (
        <div
          data-testid="voice-error-message"
          role="alert"
          className="voice-error-message"
        >
          <ErrorIcon />
          <span>{state.error}</span>
          {state.error.toLowerCase().includes('permission') && (
            <div
              data-testid="voice-permission-instructions"
              className="voice-permission-instructions"
              style={{ fontSize: '0.75rem', marginTop: '4px' }}
            >
              To enable microphone access, please check your browser settings and allow microphone permissions for this site.
            </div>
          )}
          <button
            type="button"
            onClick={handleDismissError}
            aria-label="Dismiss error"
            style={{
              marginLeft: 'auto',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px',
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <line x1="18" x2="6" y1="6" y2="18" />
              <line x1="6" x2="18" y1="6" y2="18" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
