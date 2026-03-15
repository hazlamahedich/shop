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

export const positioningStyles = `
.draggable-chat-window {
  position: absolute;
  transition: left 200ms ease-out, top 200ms ease-out;
  will-change: left, top;
}

.draggable-chat-window.dragging {
  transition: none;
  user-select: none;
}

.chat-header-drag-handle {
  cursor: grab;
  touch-action: none;
}

.chat-header-drag-handle:active {
  cursor: grabbing;
}

@supports (padding: env(safe-area-inset-bottom)) {
  .draggable-chat-window {
    padding-bottom: env(safe-area-inset-bottom);
    padding-left: env(safe-area-inset-left);
    padding-right: env(safe-area-inset-right);
  }
}

@media (max-width: 767px) {
  .draggable-chat-window {
    position: fixed;
    left: 5% !important;
    top: 15% !important;
    width: 90%;
    height: 80%;
    transition: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .draggable-chat-window {
    transition: none !important;
  }
}
`;
