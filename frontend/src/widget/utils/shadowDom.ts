export function createShadowContainer(target: HTMLElement): ShadowRoot {
  return target.attachShadow({ mode: 'open' });
}

export function injectStyles(shadow: ShadowRoot, cssContent: string): void {
  const style = document.createElement('style');
  style.textContent = cssContent;
  shadow.appendChild(style);
}

export function injectTheme(shadow: ShadowRoot, theme: {
  primaryColor: string;
  backgroundColor: string;
  textColor: string;
  botBubbleColor: string;
  userBubbleColor: string;
  borderRadius: number;
  fontFamily: string;
  fontSize: number;
}): void {
  const themeStyle = document.createElement('style');
  themeStyle.textContent = `
    :host {
      --widget-primary: ${theme.primaryColor};
      --widget-bg: ${theme.backgroundColor};
      --widget-text: ${theme.textColor};
      --widget-bot-bubble: ${theme.botBubbleColor};
      --widget-user-bubble: ${theme.userBubbleColor};
      --widget-radius: ${theme.borderRadius}px;
      --widget-font: ${theme.fontFamily};
      --widget-font-size: ${theme.fontSize}px;
    }
  `;
  shadow.appendChild(themeStyle);
}
