import type { WidgetTheme } from '../types/widget';

const THEME_STYLE_ID = 'widget-theme-variables';

export function createShadowContainer(target: HTMLElement): ShadowRoot {
  return target.attachShadow({ mode: 'open' });
}

export function injectStyles(shadow: ShadowRoot, cssContent: string): void {
  const style = document.createElement('style');
  style.textContent = cssContent;
  shadow.appendChild(style);
}

export function injectTheme(shadow: ShadowRoot, theme: WidgetTheme): void {
  const existingThemeStyle = shadow.querySelector(`style[data-id="${THEME_STYLE_ID}"]`);
  const themeStyle = document.createElement('style');
  themeStyle.setAttribute('data-id', THEME_STYLE_ID);
  themeStyle.textContent = `
    :host {
      --widget-primary: ${theme.primaryColor};
      --widget-bg: ${theme.backgroundColor};
      --widget-text: ${theme.textColor};
      --widget-bot-bubble: ${theme.botBubbleColor};
      --widget-user-bubble: ${theme.userBubbleColor};
      --widget-radius: ${theme.borderRadius}px;
      --widget-width: ${theme.width}px;
      --widget-height: ${theme.height}px;
      --widget-font: ${theme.fontFamily};
      --widget-font-size: ${theme.fontSize}px;
    }
  `;
  if (existingThemeStyle) {
    existingThemeStyle.replaceWith(themeStyle);
  } else {
    shadow.appendChild(themeStyle);
  }
}
