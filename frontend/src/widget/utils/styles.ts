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
}
