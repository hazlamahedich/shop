import type { WidgetTheme } from '../types/widget';
import { DEFAULT_THEME } from '../utils/themeDefaults';

export function useWidgetTheme(initialTheme?: WidgetTheme) {
  const getTheme = (): WidgetTheme => {
    return initialTheme ?? DEFAULT_THEME;
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
      '--widget-width': `${theme.width}px`,
      '--widget-height': `${theme.height}px`,
    } as React.CSSProperties;
  };

  return {
    getTheme,
    applyTheme,
    defaultTheme: DEFAULT_THEME,
  };
}
