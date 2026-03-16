import type { WidgetTheme } from '../types/widget';

export interface MessageAvatarProps {
  sender: 'bot' | 'merchant';
  botName: string;
  theme: WidgetTheme;
  size?: number;
}

export function MessageAvatar({
  sender,
  botName,
  theme,
  size = 32,
}: MessageAvatarProps) {
  const displayName = sender === 'merchant' ? 'Merchant' : botName;
  const initials = displayName.slice(0, 2).toUpperCase();

  return (
    <div
      data-testid="message-avatar"
      aria-label={`${displayName} avatar`}
      role="img"
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        backgroundColor: theme.primaryColor,
        color: 'white',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: size * 0.4,
        fontWeight: 600,
        flexShrink: 0,
      }}
    >
      {initials}
    </div>
  );
}
