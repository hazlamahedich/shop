import * as React from 'react';
import { createPortal } from 'react-dom';
import { WidgetProvider, useWidgetContext } from './context/WidgetContext';
import { ChatBubble } from './components/ChatBubble';
import { WidgetErrorBoundary } from './components/WidgetErrorBoundary';
import { LoadingSpinner } from './components/LoadingSpinner';
import type { WidgetTheme } from './types/widget';
import { createShadowContainer, injectStyles, injectTheme } from './utils/shadowDom';
import { mergeThemes } from './utils/themeMerge';
// @ts-expect-error Vite raw import
import widgetCss from './styles/widget.css?raw';

const ChatWindow = React.lazy(() => import('./components/ChatWindow'));

interface WidgetInnerProps {
  theme?: Partial<WidgetTheme>;
}

function WidgetInner({ theme }: WidgetInnerProps) {
  const { state, toggleChat, initWidget, sendMessage, merchantId } = useWidgetContext();
  const merchantTheme = state.config?.theme;
  const mergedTheme = React.useMemo(
    () => mergeThemes(merchantTheme, theme),
    [merchantTheme, theme]
  );
  const containerRef = React.useRef<HTMLDivElement>(null);
  const shadowRef = React.useRef<ShadowRoot | null>(null);
  const portalContainerRef = React.useRef<HTMLDivElement | null>(null);
  const [shadowReady, setShadowReady] = React.useState(false);

  const prefetchChatWindow = React.useCallback(() => {
    import('./components/ChatWindow');
  }, []);

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
    if (shadowRef.current) {
      injectTheme(shadowRef.current, mergedTheme);
    }
  }, [mergedTheme]);

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
        onPrefetch={prefetchChatWindow}
      />
      {state.isOpen && (
        <WidgetErrorBoundary fallback={<div>Failed to load chat. Please refresh.</div>}>
          <React.Suspense fallback={<LoadingSpinner />}>
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
          </React.Suspense>
        </WidgetErrorBoundary>
      )}
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
