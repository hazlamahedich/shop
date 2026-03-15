import type { WidgetTheme } from '../types/widget';

export function getTheme(theme: WidgetTheme): WidgetTheme {
  return theme;
}

export function applyTheme(root: HTMLElement, theme: WidgetTheme): void {
  root.style.setProperty('--widget-primary', theme.primaryColor);
  root.style.setProperty('--widget-bg', theme.backgroundColor);
  root.style.setProperty('--widget-text', theme.textColor);
  root.style.setProperty('--widget-bot-bubble', theme.botBubbleColor);
  root.style.setProperty('--widget-user-bubble', theme.userBubbleColor);
  root.style.setProperty('--widget-radius', `${theme.borderRadius}px`);
  root.style.setProperty('--widget-font', theme.fontFamily);
  root.style.setProperty('--widget-font-size', `${theme.fontSize}px`);
  
  root.style.setProperty('--widget-glass-blur', '16px');
  root.style.setProperty('--widget-glow-color', theme.primaryColor);
  
  const hexToRgb = (hex: string): string => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (result) {
      return `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`;
    }
    return '99, 102, 241';
  };
  root.style.setProperty('--widget-glow-color-rgb', hexToRgb(theme.primaryColor));
}
