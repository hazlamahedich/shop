import type { WidgetTheme } from '../types/widget';

export function useWidgetTheme(initialTheme?: WidgetTheme) {
  const defaultTheme: WidgetTheme = {
    primaryColor: '#6366f1',
    backgroundColor: '#ffffff',
    textColor: '#1f2937',
    botBubbleColor: '#f3f4f6',
    userBubbleColor: '#6366f1',
    position: 'bottom-right',
    borderRadius: 16,
    width: 380,
    height: 600,
    fontFamily: 'Inter, sans-serif',
    fontSize: 14,
  };

  const getTheme = (): WidgetTheme => {
    return initialTheme ?? defaultTheme;
  };

  const applyTheme = (theme: WidgetTheme): React.CSSProperties => {
    return {
      '--widget-primary': theme.primaryColor,
      '--widget-bg': theme.backgroundColor,
      '--widget-text': theme.textColor,
      '--widget-bot-bubble': theme.botBubbleColor,
      '--widget-user-bubble': theme.userBubbleColor,
      '--widget-radius': `${theme.borderRadius}px`,
      '--widget-font': theme.fontFamily,
      '--widget-font-size': `${theme.fontSize}px`,
    } as React.CSSProperties;
  };

  return {
    getTheme,
    applyTheme,
    defaultTheme,
  };
}
