import type { WidgetTheme } from '../types/widget';
import glassmorphismStyles from '../styles/glassmorphism.css?inline';
import carouselStyles from '../styles/carousel.css?inline';
import quickReplyStyles from '../styles/quick-reply.css?inline';

const THEME_STYLE_ID = 'widget-theme-variables';
const GLASSMORPHISM_STYLE_ID = 'widget-glassmorphism-styles';
const CAROUSEL_STYLE_ID = 'widget-carousel-styles';
const QUICK_REPLY_STYLE_ID = 'widget-quick-reply-styles';

export function createShadowContainer(target: HTMLElement): ShadowRoot {
  return target.attachShadow({ mode: 'open' });
}

export function injectStyles(shadow: ShadowRoot, cssContent: string): void {
  const style = document.createElement('style');
  style.textContent = cssContent;
  shadow.appendChild(style);
}

export function injectGlassmorphismStyles(shadow: ShadowRoot): void {
  const existingStyle = shadow.querySelector(`style[data-id="${GLASSMORPHISM_STYLE_ID}"]`);
  const style = document.createElement('style');
  style.setAttribute('data-id', GLASSMORPHISM_STYLE_ID);
  style.textContent = glassmorphismStyles;
  if (existingStyle) {
    existingStyle.replaceWith(style);
  } else {
    shadow.appendChild(style);
  }
}

export function injectCarouselStyles(shadow: ShadowRoot): void {
  const existingStyle = shadow.querySelector(`style[data-id="${CAROUSEL_STYLE_ID}"]`);
  const style = document.createElement('style');
  style.setAttribute('data-id', CAROUSEL_STYLE_ID);
  style.textContent = carouselStyles;
  if (existingStyle) {
    existingStyle.replaceWith(style);
  } else {
    shadow.appendChild(style);
  }
}

export function injectQuickReplyStyles(shadow: ShadowRoot): void {
  const existingStyle = shadow.querySelector(`style[data-id="${QUICK_REPLY_STYLE_ID}"]`);
  const style = document.createElement('style');
  style.setAttribute('data-id', QUICK_REPLY_STYLE_ID);
  style.textContent = quickReplyStyles;
  if (existingStyle) {
    existingStyle.replaceWith(style);
  } else {
    shadow.appendChild(style);
  }
}

export function injectTheme(shadow: ShadowRoot, theme: WidgetTheme): void {
  const existingThemeStyle = shadow.querySelector(`style[data-id="${THEME_STYLE_ID}"]`);
  
  const hexToRgb = (hex: string): string => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (result) {
      return `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`;
    }
    return '99, 102, 241';
  };
  
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
      --widget-glass-blur: 16px;
      --widget-glass-bg-dark: rgba(15, 23, 42, 0.8);
      --widget-glass-bg-light: rgba(255, 255, 255, 0.7);
      --widget-glass-border-dark: rgba(255, 255, 255, 0.1);
      --widget-glass-border-light: rgba(0, 0, 0, 0.05);
      --widget-glow-color: ${theme.primaryColor};
      --widget-glow-color-rgb: ${hexToRgb(theme.primaryColor)};
    }
  `;
  if (existingThemeStyle) {
    existingThemeStyle.replaceWith(themeStyle);
  } else {
    shadow.appendChild(themeStyle);
  }
}
