import * as React from 'react';
import type { WidgetTheme } from '../types/widget';

export interface MessageInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled: boolean;
  placeholder: string;
  inputRef?: React.Ref<HTMLInputElement>;
  theme: WidgetTheme;
  maxLength?: number;
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
}: MessageInputProps) {
  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      onSend();
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onSend();
  };

  return (
    <form
      className="message-input"
      onSubmit={handleSubmit}
      style={{
        display: 'flex',
        padding: 12,
        borderTop: '1px solid #e5e7eb',
        backgroundColor: theme.backgroundColor,
        borderRadius: `0 0 ${theme.borderRadius}px ${theme.borderRadius}px`,
      }}
    >
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
          marginLeft: 8,
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
    </form>
  );
}
