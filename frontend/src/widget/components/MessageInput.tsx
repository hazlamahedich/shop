import * as React from 'react';
import type { WidgetTheme, VoiceInputConfig, ThemeMode } from '../types/widget';
import { VoiceInput } from './VoiceInput';
import { trackMessageSend } from '../utils/analytics';

export interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled: boolean;
  placeholder: string;
  inputRef?: React.Ref<HTMLInputElement>;
  theme: WidgetTheme;
  themeMode?: ThemeMode;
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
  themeMode,
  maxLength = 2000,
  voiceInputConfig,
  showVoiceInput = true,
}: MessageInputProps) {
  const [interimTranscript, setInterimTranscript] = React.useState('');
  const isDark = themeMode === 'dark';

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (value.trim()) {
      trackMessageSend(value.trim().length);
    }
    onSend();
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (value.trim()) {
        trackMessageSend(value.trim().length);
      }
      onSend();
    }
  };

  const handleVoiceTranscript = (transcript: string) => {
    onChange(transcript);
    setInterimTranscript('');
    if (inputRef && typeof inputRef !== 'function' && inputRef.current) {
      inputRef.current.focus();
    }
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
        borderTop: isDark ? '1px solid rgba(255,255,255,0.1)' : '1px solid #e5e7eb',
        backgroundColor: isDark ? 'rgba(15, 23, 42, 0.6)' : theme.backgroundColor,
        borderRadius: `0 0 ${theme.borderRadius}px ${theme.borderRadius}px`,
        flexShrink: 0,
      }}
    >
      <style>{`
        .shopbot-message-input::placeholder {
          color: ${isDark ? '#94a3b8' : theme.textColor};
          opacity: 0.5;
        }
      `}</style>
      {interimTranscript && (
        <div
          data-testid="voice-interim-transcript"
          aria-live="polite"
          style={{
            fontStyle: 'italic',
            color: isDark ? '#94a3b8' : '#6b7280',
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
          className="shopbot-message-input"
          data-testid="message-input"
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
            border: isDark ? '1px solid rgba(255,255,255,0.2)' : '1px solid rgba(0,0,0,0.2)',
            borderRadius: 20,
            fontSize: theme.fontSize,
            fontFamily: theme.fontFamily,
            outline: 'none',
            color: isDark ? '#f8fafc' : theme.textColor,
            backgroundColor: disabled
              ? (isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)')
              : 'transparent',
          }}
        />
        <button
          type="submit"
          data-testid="send-message-button"
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          style={{
            padding: '10px 16px',
            backgroundColor: disabled || !value.trim()
              ? (isDark ? 'rgba(255,255,255,0.1)' : '#e5e7eb')
              : theme.primaryColor,
            color: disabled || !value.trim()
              ? (isDark ? '#64748b' : '#9ca3af')
              : 'white',
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
