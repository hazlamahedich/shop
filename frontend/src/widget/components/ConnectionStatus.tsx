import React from 'react';
import { WifiOff, Loader2 } from 'lucide-react';
import type { ConnectionStatus } from '../api/widgetWsClient';
import type { ThemeMode } from '../types/widget';

interface ConnectionStatusProps {
  status: ConnectionStatus;
  themeMode?: ThemeMode;
}

export const ConnectionStatusIndicator: React.FC<ConnectionStatusProps> = ({ status, themeMode }) => {
  if (status === 'connected') {
    return null;
  }

  const isDark = themeMode === 'dark';

  const getStatusConfig = () => {
    switch (status) {
      case 'connecting':
        return {
          icon: Loader2,
          text: 'Connecting...',
          bgColor: isDark ? 'rgba(234, 179, 8, 0.15)' : '#fefce8',
          textColor: isDark ? '#fde047' : '#a16207',
          borderColor: isDark ? 'rgba(234, 179, 8, 0.3)' : '#fde68a',
          animate: true,
        };
      case 'disconnected':
        return {
          icon: WifiOff,
          text: 'Disconnected - Reconnecting...',
          bgColor: isDark ? 'rgba(249, 115, 22, 0.15)' : '#fff7ed',
          textColor: isDark ? '#fdba74' : '#c2410c',
          borderColor: isDark ? 'rgba(249, 115, 22, 0.3)' : '#fed7aa',
          animate: false,
        };
      case 'error':
        return {
          icon: WifiOff,
          text: 'Connection error',
          bgColor: isDark ? 'rgba(239, 68, 68, 0.15)' : '#fef2f2',
          textColor: isDark ? '#fca5a5' : '#b91c1c',
          borderColor: isDark ? 'rgba(239, 68, 68, 0.3)' : '#fecaca',
          animate: false,
        };
      default:
        return null;
    }
  };

  const config = getStatusConfig();
  if (!config) return null;

  const Icon = config.icon;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 12px',
        fontSize: '13px',
        backgroundColor: config.bgColor,
        color: config.textColor,
        border: `1px solid ${config.borderColor}`,
        borderRadius: '8px',
      }}
    >
      <Icon
        size={14}
        style={{
          animation: config.animate ? 'spin 1s linear infinite' : 'none',
          flexShrink: 0,
        }}
      />
      <span>{config.text}</span>
    </div>
  );
};

export default ConnectionStatusIndicator;
