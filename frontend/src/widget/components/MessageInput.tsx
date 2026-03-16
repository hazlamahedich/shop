import * as React from 'react';
import type { WidgetTheme, VoiceInputConfig } from '../types/widget';
import { VoiceInput } from './VoiceInput';

export interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled: boolean;
  placeholder: string;
  inputRef?: React.Ref<HTMLInputElement>;
  theme: WidgetTheme;
  maxLength?: number;
  voiceInputConfig?: Partial<VoiceInputConfig>;
  showVoiceInput?: boolean;
}

export function MessageInput({
  value,
  onChange,
  onSend,
  disabled,
  placeholder,
  inputRef,
  theme,
  maxLength = 2000,
  voiceInputConfig,
  showVoiceInput = true,
}: MessageInputProps) {
  const [interimTranscript, setInterimTranscript] = React.useState('');
  
  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      console.warn('[MessageInput] Enter key pressed, calling onSend');
      event.preventDefault();
      onSend();
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    console.warn('[MessageInput] Form submitted, calling onSend');
    event.preventDefault();
    onSend();
  };
  
  const handleVoiceTranscript = (transcript: string) => {
    onChange(transcript);
    setInterimTranscript('');
    inputRef?.current?.focus();
  };
  
  const handleInterimTranscript = (transcript: string) => {
    setInterimTranscript(transcript);
  };

  return (
    <form
      className="message-input"
      onSubmit={handleSubmit}
      style={{
        display: 'flex',
        flexDirection: 'column',
        padding: 12,
        borderTop: '1px solid #e5e7eb',
        backgroundColor: theme.backgroundColor,
        borderRadius: `0 0 ${theme.borderRadius}px ${theme.borderRadius}px`,
        flexShrink: 0,
      }}
    >
      {interimTranscript && (
        <div
          data-testid="voice-interim-transcript"
          aria-live="polite"
          style={{
            fontStyle: 'italic',
            color: '#6b7280',
            fontSize: 13,
            padding: '4px 0',
            marginBottom: 8,
          }}
        >
          {interimTranscript}
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {showVoiceInput && (
          <VoiceInput
            config={voiceInputConfig}
            onTranscript={handleVoiceTranscript}
            onInterimTranscript={handleInterimTranscript}
            disabled={disabled}
            theme={{
              primaryColor: theme.primaryColor,
              backgroundColor: theme.backgroundColor,
              textColor: theme.textColor,
            }}
          />
        )}
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          aria-label="Type a message"
          maxLength={maxLength}
          style={{
            flex: 1,
            padding: '10px 14px',
            border: '1px solid #e5e7eb',
            borderRadius: 20,
            fontSize: theme.fontSize,
            fontFamily: theme.fontFamily,
            outline: 'none',
            backgroundColor: disabled ? '#f9fafb' : 'white',
          }}
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          style={{
            padding: '10px 16px',
            backgroundColor: disabled || !value.trim() ? '#e5e7eb' : theme.primaryColor,
            color: disabled || !value.trim() ? '#9ca3af' : 'white',
            border: 'none',
            borderRadius: 20,
            cursor: disabled || !value.trim() ? 'not-allowed' : 'pointer',
            fontSize: theme.fontSize,
            fontWeight: 500,
          }}
        >
          Send
        </button>
      </div>
    </form>
  );
}
