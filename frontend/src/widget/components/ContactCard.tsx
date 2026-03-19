import * as React from 'react';
import type { WidgetTheme, ContactOption } from '../types/widget';
import { useReducedMotion } from '../hooks/useReducedMotion';
import { logContactInteraction } from '../utils/analytics';
import { getBusinessHoursMessage, type BusinessHoursConfig } from '../utils/businessHours';

export interface ContactCardProps {
  contactOptions: ContactOption[];
  theme: WidgetTheme;
  conversationId?: string;
  businessHours?: BusinessHoursConfig | null;
  onContactClick?: (option: ContactOption) => void;
  onShowToast?: (message: string) => void;
}

export function ContactCard({
  contactOptions,
  theme,
  conversationId,
  businessHours,
  onContactClick,
  onShowToast,
}: ContactCardProps) {
  const isDarkMode = theme.mode === 'dark';
  const reducedMotion = useReducedMotion();

  const isMobile = React.useCallback((): boolean => {
    return /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
  }, []);

  const handlePhoneClick = async (option: ContactOption) => {
    try {
      if (isMobile()) {
        window.location.href = `tel:${option.value}`;
        logContactInteraction('phone', 'call');
      } else {
        await navigator.clipboard.writeText(option.value);
        logContactInteraction('phone', 'copy');
        onShowToast?.('Phone number copied to clipboard');
      }
      onContactClick?.(option);
    } catch (error) {
      console.error('[ContactCard] Phone click failed:', error);
    }
  };

  const handleEmailClick = (option: ContactOption) => {
    try {
      const subject = conversationId
        ? encodeURIComponent(`Support Request - Conversation ${conversationId}`)
        : encodeURIComponent('Support Request');
      window.location.href = `mailto:${option.value}?subject=${subject}`;
      logContactInteraction('email');
      onContactClick?.(option);
    } catch (error) {
      console.error('[ContactCard] Email click failed:', error);
    }
  };

  const handleCustomClick = (option: ContactOption) => {
    try {
      window.open(option.value, '_blank', 'noopener,noreferrer');
      logContactInteraction('custom', option.label);
      onContactClick?.(option);
    } catch (error) {
      console.error('[ContactCard] Custom click failed:', error);
    }
  };

  if (!contactOptions || contactOptions.length === 0) {
    return null;
  }

  const businessHoursMessage = getBusinessHoursMessage(businessHours || null);

  return (
    <div data-testid="contact-card" style={{ marginTop: 8 }}>
      <div 
        style={{ 
          fontSize: 12, 
          color: theme.textColor, 
          opacity: 0.7, 
          marginBottom: 8,
          fontWeight: 500
        }}
      >
        {businessHoursMessage}
      </div>
      <div 
        style={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          gap: 8 
        }}
      >
        {contactOptions.map((option) => (
          <button
            key={`${option.type}-${option.value}`}
            data-testid={`contact-${option.type}`}
            role="button"
            aria-label={option.label}
            onClick={() => {
              if (option.type === 'phone') {
                handlePhoneClick(option);
              } else if (option.type === 'email') {
                handleEmailClick(option);
              } else {
                handleCustomClick(option);
              }
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              minHeight: '44px',
              padding: '8px 16px',
              border: `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)'}`,
              borderRadius: '20px',
              backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
              cursor: 'pointer',
              transition: reducedMotion ? 'none' : 'all 150ms ease',
              color: theme.textColor,
              fontSize: 13,
              fontWeight: 500,
            }}
          >
            {option.icon && <span>{option.icon}</span>}
            <span>{option.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
