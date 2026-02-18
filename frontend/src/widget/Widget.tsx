import * as React from 'react';
import { createPortal } from 'react-dom';
import { WidgetProvider, useWidgetContext } from './context/WidgetContext';
import { ChatBubble } from './components/ChatBubble';
import { ChatWindow } from './components/ChatWindow';
import { WidgetErrorBoundary } from './components/WidgetErrorBoundary';
import type { WidgetTheme } from './types/widget';
import { createShadowContainer, injectStyles, injectTheme } from './utils/shadowDom';
// @ts-expect-error Vite raw import
import widgetCss from './styles/widget.css?raw';

interface WidgetInnerProps {
  theme?: Partial<WidgetTheme>;
}

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

function WidgetInner({ theme }: WidgetInnerProps) {
  const { state, toggleChat, initWidget, sendMessage, merchantId } = useWidgetContext();
  const mergedTheme = { ...defaultTheme, ...theme };
  const containerRef = React.useRef<HTMLDivElement>(null);
  const shadowRef = React.useRef<ShadowRoot | null>(null);
  const portalContainerRef = React.useRef<HTMLDivElement | null>(null);
  const [shadowReady, setShadowReady] = React.useState(false);

  React.useEffect(() => {
    if (containerRef.current && !shadowRef.current) {
      shadowRef.current = createShadowContainer(containerRef.current);
      injectTheme(shadowRef.current, mergedTheme);
      injectStyles(shadowRef.current, widgetCss);
      portalContainerRef.current = document.createElement('div');
      shadowRef.current.appendChild(portalContainerRef.current);
      setShadowReady(true);
    }
  }, []);

  React.useEffect(() => {
    initWidget(merchantId);
  }, [initWidget, merchantId]);

  if (!shadowReady || !portalContainerRef.current) {
    return <div ref={containerRef} className="widget-container" />;
  }

  const content = state.isLoading ? (
    <div className="widget-loading" aria-label="Loading chat widget">
      <div className="widget-spinner" />
    </div>
  ) : (
    <>
      <ChatBubble
        isOpen={state.isOpen}
        onClick={toggleChat}
        theme={mergedTheme}
      />
      <ChatWindow
        isOpen={state.isOpen}
        onClose={toggleChat}
        theme={mergedTheme}
        config={state.config}
        messages={state.messages}
        isTyping={state.isTyping}
        onSendMessage={sendMessage}
        error={state.error}
      />
    </>
  );

  return (
    <>
      <div ref={containerRef} className="widget-container" />
      {createPortal(content, portalContainerRef.current)}
    </>
  );
}

interface WidgetProps {
  merchantId: string;
  theme?: Partial<WidgetTheme>;
}

export function Widget({ merchantId, theme }: WidgetProps) {
  return (
    <WidgetErrorBoundary>
      <WidgetProvider merchantId={merchantId}>
        <WidgetInner theme={theme} />
      </WidgetProvider>
    </WidgetErrorBoundary>
  );
}
