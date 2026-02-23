/**
 * ConnectionStatus Component
 *
 * Displays the current WebSocket connection status in the widget.
 * Shows visual indicator for connected/connecting/disconnected states.
 */

import React from 'react';
import { Wifi, WifiOff, Loader2 } from 'lucide-react';
import type { ConnectionStatus } from '../api/widgetWsClient';

interface ConnectionStatusProps {
  status: ConnectionStatus;
}

export const ConnectionStatusIndicator: React.FC<ConnectionStatusProps> = ({ status }) => {
  // Don't show anything when connected (clean UI)
  if (status === 'connected') {
    return null;
  }

  const getStatusConfig = () => {
    switch (status) {
      case 'connecting':
        return {
          icon: Loader2,
          text: 'Connecting...',
          bgColor: 'bg-yellow-50',
          textColor: 'text-yellow-700',
          borderColor: 'border-yellow-200',
          animate: true,
        };
      case 'disconnected':
        return {
          icon: WifiOff,
          text: 'Disconnected - Reconnecting...',
          bgColor: 'bg-orange-50',
          textColor: 'text-orange-700',
          borderColor: 'border-orange-200',
          animate: false,
        };
      case 'error':
        return {
          icon: WifiOff,
          text: 'Connection error',
          bgColor: 'bg-red-50',
          textColor: 'text-red-700',
          borderColor: 'border-red-200',
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
      className={`
        flex items-center gap-2 px-3 py-2 text-sm
        ${config.bgColor} ${config.textColor} border ${config.borderColor}
        rounded-lg
      `}
    >
      <Icon
        size={14}
        className={config.animate ? 'animate-spin' : ''}
      />
      <span>{config.text}</span>
    </div>
  );
};

export default ConnectionStatusIndicator;
