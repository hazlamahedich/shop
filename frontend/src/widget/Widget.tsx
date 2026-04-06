import * as React from 'react';
import { WidgetProvider, useWidgetContext } from './context/WidgetContext';
import { ChatBubble } from './components/ChatBubble';
import { WidgetErrorBoundary } from './components/WidgetErrorBoundary';
import { LoadingSpinner } from './components/LoadingSpinner';
import { ProactiveModal } from './components/ProactiveModal';
import { useProactiveTriggers } from './hooks/useProactiveTriggers';
import type { WidgetTheme, ProactiveTriggerAction, FeedbackRatingValue, FAQQuickButton } from './types/widget';
import { DEFAULT_PROACTIVE_CONFIG } from './types/widget';
import { mergeThemes } from './utils/themeMerge';
import { useThemeDetection } from './hooks/useThemeDetection';
import { GlassmorphismChatWindow } from './components/GlassmorphismChatWindow';
import { getNextThemeMode } from './components/ThemeToggle';
import { positioningStyles } from './utils/styles';
import { widgetClient } from './api/widgetClient';

import ChatWindow from './components/ChatWindow';

interface WidgetInnerProps {
  theme?: Partial<WidgetTheme>;
}

function WidgetInner({ theme }: WidgetInnerProps) {
  const {
    state,
    dispatch,
    toggleChat,
    initWidget,
    sendMessage,
    merchantId,
    addToCart,
    removeFromCart,
    checkout,
    addingProductId,
    removingItemId,
    isCheckingOut,
    dismissError,
    retryLastAction,
    recordConsent,
    clearHistory,
    toggleMinimized,
    setThemeMode,
  } = useWidgetContext();
  const { systemTheme } = useThemeDetection();
  const merchantTheme = state.config?.theme;
  const mergedTheme = React.useMemo(
    () => mergeThemes(merchantTheme, theme),
    [merchantTheme, theme]
  );

  const [prePopulatedMessage, setPrePopulatedMessage] = React.useState<string | null>(null);
  
  const productViewCount = React.useMemo(() => {
    const productIds = new Set<string>();
    state.messages.forEach((m) => {
      m.products?.forEach((p) => {
        const id = p.id || p.variantId;
        if (id) productIds.add(id);
      });
    });
    return productIds.size;
  }, [state.messages]);

  const proactiveConfig = state.config?.proactiveEngagementConfig ?? DEFAULT_PROACTIVE_CONFIG;


  const cartHasItems = React.useMemo(() => {
    return state.messages.some((m) => (m.cart?.items?.length ?? 0) > 0);
  }, [state.messages]);

  const {
    activeTrigger,
    dismissTrigger: dismissProactive,
    isActive: isProactiveActive,
  } = useProactiveTriggers({
    config: proactiveConfig,
    productViewCount,
    cartHasItems,
  });

  const handleProactiveAction = React.useCallback(
    (action: ProactiveTriggerAction) => {
      if (action.prePopulatedMessage) {
        setPrePopulatedMessage(action.prePopulatedMessage);
      }
      if (!state.isOpen) {
        toggleChat();
      }
      dismissProactive();
    },
    [state.isOpen, toggleChat, dismissProactive]
  );


  React.useEffect(() => {
    if (prePopulatedMessage && state.isOpen) {
      const timer = setTimeout(() => {
        setPrePopulatedMessage(null);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [prePopulatedMessage, state.isOpen]);

  const handleThemeToggle = React.useCallback(() => {
    const nextMode = getNextThemeMode(state.themeMode);
    setThemeMode(nextMode);
  }, [state.themeMode, setThemeMode]);

  const handleFeedbackSubmit = React.useCallback(
    async (messageId: string, rating: FeedbackRatingValue, comment?: string) => {
      const sessionId = state.session?.sessionId;
      if (!sessionId) {
        console.error('[Widget] Cannot submit feedback: no session ID');
        return;
      }
      try {
        await widgetClient.submitFeedback(messageId, rating, sessionId, merchantId, comment);
        // Update local state to reflect the feedback
        dispatch({ type: 'UPDATE_MESSAGE_FEEDBACK', payload: { messageId, rating } });
      } catch (error) {
        console.error('[Widget] Failed to submit feedback:', error);
        throw error;
      }
    },
    [state.session?.sessionId, merchantId, dispatch]
  );

  const handleFaqButtonClick = React.useCallback(
    async (button: FAQQuickButton) => {
      const sessionId = state.session?.sessionId;
      if (!sessionId) {
        console.error('[Widget] Cannot track FAQ click: no session ID');
        // Still send the message even if tracking fails
        await sendMessage(button.question);
        return;
      }

      try {
        // Track the FAQ click in the background
        widgetClient.trackFaqClick(button.id, sessionId, merchantId).catch((error) => {
          console.error('[Widget] Failed to track FAQ click:', error);
          // Don't throw - we still want to send the message even if tracking fails
        });
      } catch (error) {
        console.error('[Widget] FAQ click tracking error:', error);
        // Continue anyway - the user experience is more important
      }

      // Send the FAQ question as a message
      await sendMessage(button.question);
    },
    [state.session?.sessionId, merchantId, sendMessage]
  );

  const prefetchChatWindow = React.useCallback(() => {
    import('./components/ChatWindow');
  }, []);

  React.useEffect(() => {
    console.log('[Widget.tsx] useEffect triggered, calling initWidget for merchantId:', merchantId);
    initWidget(merchantId);
  }, [merchantId]);

  const handleBubbleClick = React.useCallback(() => {
    if (state.isMinimized) {
      toggleMinimized();
    } else {
      toggleChat();
    }
  }, [state.isMinimized, toggleMinimized, toggleChat]);

  console.log('[Widget] Rendering WidgetInner:', {
    merchantId,
    isOpen: state.isOpen,
    isMinimized: state.isMinimized,
    isLoading: state.isLoading,
    position: state.position,
    themePosition: mergedTheme.position,
    viewport: `${window.innerWidth}x${window.innerHeight}`
  });

  return (
    <>
      <style>{`
        /* CSS ISOLATION: Protect widget from parent page styles */
        .shopbot-widget-root {
          font-family: var(--widget-font, Inter, sans-serif) !important;
          font-size: var(--widget-font-size, 14px) !important;
          color: var(--widget-text, #1f2937) !important;
          line-height: 1.5 !important;
          text-shadow: none !important;
        }

        /* Reset common inherited properties that cause conflicts */
        .shopbot-widget-root *,
        .shopbot-widget-root *::before,
        .shopbot-widget-root *::after {
          box-sizing: border-box !important;
        }

        /* Quick Reply Button Contrast Fix */
        .shopbot-widget-root .quick-reply-button {
          color: var(--widget-primary, #6366f1) !important;
          border-color: var(--widget-primary, #6366f1) !important;
          background-color: transparent !important;
          font-weight: 500 !important;
          opacity: 1 !important;
          visibility: visible !important;
        }
        .shopbot-widget-root .quick-reply-button:hover:not(:disabled) {
          background-color: rgba(99, 102, 241, 0.1) !important;
        }

        /* Typing Indicator Visibility Fix */
        .shopbot-widget-root .typing-indicator {
          color: var(--widget-text, #1f2937) !important;
          opacity: 1 !important;
          visibility: visible !important;
        }
        .shopbot-widget-root .typing-dot {
          background-color: var(--widget-primary, #6366f1) !important;
          opacity: 1 !important;
          visibility: visible !important;
        }

        /* FAQ Quick Buttons Visibility Fix */
        .shopbot-widget-root .faq-quick-button {
          color: var(--widget-primary, #6366f1) !important;
          border-color: var(--widget-primary, #6366f1) !important;
          background-color: transparent !important;
          opacity: 1 !important;
          visibility: visible !important;
        }
        .shopbot-widget-root .faq-quick-button:hover:not(:disabled) {
          background-color: rgba(99, 102, 241, 0.1) !important;
        }

        /* Message visibility */
        .shopbot-widget-root .message-bubble {
          color: var(--widget-text, #1f2937) !important;
          opacity: 1 !important;
        }
        .shopbot-widget-root .message-bubble--bot {
          background-color: var(--widget-bot-bubble, #f3f4f6) !important;
        }
        .shopbot-widget-root .message-bubble--user {
          background-color: var(--widget-user-bubble, #6366f1) !important;
          color: white !important;
        }

        /* Input visibility */
        .shopbot-widget-root input,
        .shopbot-widget-root textarea {
          color: var(--widget-text, #1f2937) !important;
          background-color: white !important;
          opacity: 1 !important;
        }
        .shopbot-widget-root input::placeholder,
        .shopbot-widget-root textarea::placeholder {
          color: rgba(0, 0, 0, 0.5) !important;
        }

        /* Button visibility */
        .shopbot-widget-root button {
          color: inherit !important;
        }

        .shopbot-widget-root * {
          box-sizing: border-box;
        }
        .shopbot-chat-bubble:hover {
          transform: scale(1.05);
          box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2) !important;
        }
        .shopbot-chat-bubble:active {
          transform: scale(0.95);
        }
        .shopbot-chat-window {
          animation: shopbot-slideUp 0.2s ease-out;
        }
        .shopbot-chat-window.dragging {
          animation: none;
        }
        @keyframes shopbot-slideUp {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes shopbot-pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }
        .shopbot-chat-bubble.has-unread {
          animation: shopbot-pulse 2s ease-in-out infinite;
        }
        .chat-header-drag-handle {
          cursor: grab;
        }
        .chat-header-drag-handle:active {
          cursor: grabbing;
        }
        
        .shopbot-chat-window.is-default-position {
          position: fixed !important;
          bottom: 90px !important;
          right: ${mergedTheme.position === 'bottom-left' ? 'auto' : '20px'} !important;
          left: ${mergedTheme.position === 'bottom-left' ? '20px' : 'auto'} !important;
          top: auto !important;
          transform: none !important;
        }

        @media (max-width: 767px) {
          .shopbot-chat-window.is-default-position {
            bottom: 0 !important;
            right: 0 !important;
            width: 100% !important;
            height: 100% !important;
            border-radius: 0 !important;
          }
        }
        
        /* Smart Positioning Styles */
        ${positioningStyles}
        
        /* Glassmorphism Styles */
        .glassmorphism-wrapper.dark-mode .shopbot-chat-window {
          background: rgba(15, 23, 42, 0.8) !important;
          -webkit-backdrop-filter: blur(16px);
          backdrop-filter: blur(16px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          color: #f8fafc !important;
        }
        .glassmorphism-wrapper.dark-mode .chat-header {
          background: rgba(15, 23, 42, 0.6) !important;
          -webkit-backdrop-filter: blur(8px);
          backdrop-filter: blur(8px);
        }
        .glassmorphism-wrapper.dark-mode .message-timestamp {
          color: #94a3b8 !important;
        }
        .glassmorphism-wrapper.light-mode .shopbot-chat-window {
          background: rgba(255, 255, 255, 0.7) !important;
          -webkit-backdrop-filter: blur(16px);
          backdrop-filter: blur(16px);
          border: 1px solid rgba(0, 0, 0, 0.05);
          color: #1e293b !important;
        }
        .glassmorphism-wrapper.light-mode .chat-header {
          background: rgba(255, 255, 255, 0.5) !important;
          -webkit-backdrop-filter: blur(8px);
          backdrop-filter: blur(8px);
        }
        .glassmorphism-wrapper.light-mode .message-timestamp {
          color: #64748b !important;
        }
        .glassmorphism-wrapper .shopbot-chat-window,
        .glassmorphism-wrapper .shopbot-chat-window * {
          transition: background 300ms ease, color 300ms ease, border-color 300ms ease, box-shadow 300ms ease;
        }
        @media (prefers-reduced-motion: reduce) {
          .glassmorphism-wrapper .shopbot-chat-window,
          .glassmorphism-wrapper .shopbot-chat-window * {
            transition: none !important;
            animation: none !important;
          }
        }
        @supports not (backdrop-filter: blur(1px)) {
          .glassmorphism-wrapper.dark-mode .shopbot-chat-window {
            background: rgba(15, 23, 42, 0.95);
          }
          .glassmorphism-wrapper.light-mode .shopbot-chat-window {
            background: rgba(255, 255, 255, 0.95);
          }
        }
        .shopbot-theme-toggle {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          background: rgba(255, 255, 255, 0.2);
          border: none;
          border-radius: 4px;
          cursor: pointer;
          color: white;
          transition: background 0.15s ease;
          padding: 0;
        }
        .shopbot-theme-toggle:hover {
          background: rgba(255, 255, 255, 0.3);
        }
        .shopbot-theme-toggle:focus-visible {
          outline: 2px solid rgba(255, 255, 255, 0.5);
          outline-offset: 2px;
        }
        .shopbot-theme-toggle svg {
          width: 18px;
          height: 18px;
        }
        
        /* Product Carousel Styles */
        .product-carousel {
          display: flex;
          overflow-x: auto;
          scroll-snap-type: x mandatory;
          scroll-behavior: smooth;
          -webkit-overflow-scrolling: touch;
          scrollbar-width: none;
          gap: 12px;
          padding: 4px 0;
          margin: 0 -4px;
        }
        .product-carousel::-webkit-scrollbar {
          display: none;
        }
        .carousel-card {
          scroll-snap-align: start;
          flex-shrink: 0;
          width: 140px;
          border-radius: 8px;
          background: #ffffff;
          border: 1px solid rgba(0, 0, 0, 0.1);
          overflow: hidden;
          transition: transform 200ms ease, box-shadow 200ms ease;
          cursor: pointer;
        }
        .carousel-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }
        .carousel-card:focus-visible {
          outline: 2px solid var(--widget-primary, #6366f1);
          outline-offset: 2px;
        }
        .carousel-card-image {
          position: relative;
          width: 100%;
          padding-bottom: 100%;
          background: #f1f5f9;
          overflow: hidden;
        }
        .carousel-card-image img {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          object-fit: cover;
          transition: opacity 200ms ease;
        }
        .carousel-card-image img.loading {
          opacity: 0;
        }
        .carousel-card-skeleton {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
          background-size: 200% 100%;
          animation: skeleton-shimmer 1.5s infinite;
        }
        @keyframes skeleton-shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        .carousel-card-content {
          padding: 8px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        .carousel-card-title {
          font-size: 13px;
          font-weight: 500;
          line-height: 1.3;
          color: #1e293b;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
          text-overflow: ellipsis;
          margin: 0;
          min-height: 34px;
        }
        .carousel-card-price {
          font-size: 14px;
          font-weight: 600;
          color: #6366f1;
          margin: 0;
        }
        .carousel-card-button {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          padding: 6px 8px;
          margin-top: 4px;
          font-size: 12px;
          font-weight: 500;
          color: white;
          background: #6366f1;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          transition: background 150ms ease, opacity 150ms ease;
        }
        .carousel-card-button:hover {
          background: #4f46e5;
        }
        .carousel-card-button:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }
        .carousel-card-button:focus-visible {
          outline: 2px solid #6366f1;
          outline-offset: 2px;
        }
        .carousel-arrows {
          position: absolute;
          top: 50%;
          left: 0;
          right: 0;
          transform: translateY(-50%);
          display: flex;
          justify-content: space-between;
          pointer-events: none;
          padding: 0 4px;
          opacity: 0;
          transition: opacity 200ms ease;
        }
        .product-carousel-wrapper:hover .carousel-arrows {
          opacity: 1;
        }
        .carousel-arrow {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 32px;
          height: 32px;
          background: #ffffff;
          border: 1px solid rgba(0, 0, 0, 0.1);
          border-radius: 50%;
          cursor: pointer;
          pointer-events: auto;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          transition: background 150ms ease, box-shadow 150ms ease;
          color: #1e293b;
        }
        .carousel-arrow:hover {
          background: #f8fafc;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        .carousel-arrow:disabled {
          opacity: 0.3;
          cursor: not-allowed;
        }
        .carousel-arrow:focus-visible {
          outline: 2px solid #6366f1;
          outline-offset: 2px;
        }
        .carousel-dots {
          display: flex;
          justify-content: center;
          gap: 6px;
          padding: 8px 0 4px;
        }
        .carousel-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: rgba(0, 0, 0, 0.2);
          border: none;
          padding: 0;
          cursor: pointer;
          transition: background 150ms ease, transform 150ms ease;
        }
        .carousel-dot:hover {
          background: rgba(0, 0, 0, 0.4);
        }
        .carousel-dot.active {
          width: 10px;
          height: 10px;
          background: #6366f1;
        }
        .carousel-dot:focus-visible {
          outline: 2px solid #6366f1;
          outline-offset: 2px;
        }
        .product-carousel-wrapper {
          position: relative;
          width: 100%;
        }
        @media (prefers-reduced-motion: reduce) {
          .carousel-card:hover {
            transform: none;
          }
          .product-carousel {
            scroll-behavior: auto;
          }
          .carousel-card-skeleton {
            animation: none;
          }
          .carousel-card,
          .carousel-arrow,
          .carousel-dot,
          .carousel-card-image img,
          .carousel-arrows {
            transition: none;
          }
        }
        
        /* Quick Reply Buttons Styles */
        .quick-reply-buttons {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          padding: 8px 16px;
        }
        .quick-reply-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          min-height: 44px;
          min-width: 44px;
          padding: 10px 16px;
          border: 1px solid var(--widget-primary, #6366f1);
          border-radius: 20px;
          background-color: transparent;
          color: var(--widget-primary, #6366f1);
          font-weight: 500;
          font-size: 14px;
          cursor: pointer;
          transition: transform 100ms ease, background-color 150ms ease, opacity 150ms ease, border-color 150ms ease;
          white-space: nowrap;
        }
        .quick-reply-button:hover:not(:disabled) {
          background-color: rgba(99, 102, 241, 0.1);
        }
        .quick-reply-button:active:not(:disabled) {
          transform: scale(0.95);
          background-color: rgba(99, 102, 241, 0.15);
        }
        .quick-reply-button:focus-visible {
          outline: 2px solid var(--widget-primary, #6366f1);
          outline-offset: 2px;
        }
        .quick-reply-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        @media (max-width: 479px) {
          .quick-reply-buttons {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
          }
          .quick-reply-button {
            width: 100%;
          }
        }
        @media (min-width: 480px) {
          .quick-reply-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }
        }
        @media (prefers-reduced-motion: reduce) {
          .quick-reply-button {
            transition: none;
          }
          .quick-reply-button:active:not(:disabled) {
            transform: none;
          }
        }
        
        /* Voice Input Styles */
        .voice-input-container {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .voice-input-button {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 44px;
          height: 44px;
          min-width: 44px;
          min-height: 44px;
          border: none;
          border-radius: 50%;
          background-color: var(--widget-primary, #6366f1);
          color: white;
          cursor: pointer;
          transition: background-color 150ms ease, opacity 150ms ease;
        }
        .voice-input-button:hover:not(:disabled) {
          background-color: color-mix(in srgb, var(--widget-primary, #6366f1) 85%, black);
        }
        .voice-input-button:active:not(:disabled) {
          transform: scale(0.95);
        }
        .voice-input-button:focus-visible {
          outline: 2px solid var(--widget-primary, #6366f1);
          outline-offset: 2px;
        }
        .voice-input-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .voice-input-button.listening {
          background-color: #ef4444;
          animation: voice-pulse 1.5s ease-in-out infinite;
        }
        @keyframes voice-pulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
          50% { box-shadow: 0 0 0 12px rgba(239, 68, 68, 0); }
        }
        .voice-input-button.processing {
          background-color: var(--widget-primary, #6366f1);
        }
        .voice-input-button.error {
          background-color: #ef4444;
        }
        .waveform-container {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 3px;
          height: 24px;
        }
        .waveform-bar {
          width: 3px;
          height: 24px;
          background-color: white;
          border-radius: 2px;
          animation: waveform-pulse 1s ease-in-out infinite;
        }
        .waveform-bar:nth-child(1) { animation-delay: 0s; }
        .waveform-bar:nth-child(2) { animation-delay: 0.15s; }
        .waveform-bar:nth-child(3) { animation-delay: 0.3s; }
        .waveform-bar:nth-child(4) { animation-delay: 0.15s; }
        .waveform-bar:nth-child(5) { animation-delay: 0s; }
        @keyframes waveform-pulse {
          0%, 100% { transform: scaleY(0.5); }
          50% { transform: scaleY(1); }
        }
        .voice-interim-transcript {
          font-style: italic;
          color: #6b7280;
          font-size: 14px;
          padding: 4px 12px;
          min-height: 24px;
        }
        .voice-error-message {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background-color: #fef2f2;
          border: 1px solid #fecaca;
          border-radius: 8px;
          color: #dc2626;
          font-size: 13px;
        }
        .voice-cancel-button {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
          border: none;
          border-radius: 50%;
          background-color: #f3f4f6;
          color: #6b7280;
          cursor: pointer;
          transition: background-color 150ms ease;
        }
        .voice-cancel-button:hover {
          background-color: #e5e7eb;
        }
        .voice-cancel-button:focus-visible {
          outline: 2px solid var(--widget-primary, #6366f1);
          outline-offset: 2px;
        }
        .voice-spinner {
          width: 24px;
          height: 24px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: voice-spin 0.8s linear infinite;
        }
        @keyframes voice-spin {
          to { transform: rotate(360deg); }
        }
        @media (prefers-reduced-motion: reduce) {
          .voice-input-button,
          .voice-cancel-button,
          .waveform-bar,
          .voice-spinner {
            animation: none !important;
            transition: none !important;
          }
          .voice-input-button:active:not(:disabled) {
            transform: none;
          }
          .voice-input-button.listening {
            animation: none;
          }
          .waveform-bar {
            transform: scaleY(0.75);
          }
        }
        
        /* Proactive Modal Styles */
        .proactive-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 2147483646;
          animation: proactive-fade-in 0.2s ease-out;
        }
        .proactive-modal-container {
          background-color: var(--widget-bg, #ffffff);
          border-radius: var(--widget-radius, 16px);
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
          max-width: 400px;
          width: 90%;
          padding: 24px;
          position: relative;
          color: var(--widget-text, #1f2937);
          animation: proactive-scale-in 0.2s ease-out;
        }
        .proactive-modal-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 48px;
          height: 48px;
          margin: 0 auto 16px;
          border-radius: 50%;
          background-color: var(--widget-primary, #6366f1);
          color: white;
        }
        @keyframes proactive-fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes proactive-scale-in {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        .proactive-modal-close {
          position: absolute;
          top: 12px;
          right: 12px;
          width: 32px;
          height: 32px;
          min-width: 32px;
          min-height: 32px;
          border: none;
          border-radius: 50%;
          background-color: transparent;
          color: var(--widget-text, #6b7280);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background-color 150ms ease;
        }
        .proactive-modal-close:hover {
          background-color: rgba(0, 0, 0, 0.05);
        }
        .proactive-modal-close:focus-visible {
          outline: 2px solid var(--widget-primary, #6366f1);
          outline-offset: 2px;
        }
        .proactive-modal-title {
          font-size: 18px;
          font-weight: 600;
          margin: 0 0 12px 0;
          padding-right: 32px;
          color: inherit;
        }
        .proactive-modal-message {
          font-size: 14px;
          line-height: 1.5;
          margin: 0 0 20px 0;
          color: inherit;
        }
        .proactive-modal-actions {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }
        .proactive-action-button {
          flex: 1;
          min-width: 100px;
          min-height: 44px;
          padding: 12px 16px;
          border: 1px solid var(--widget-primary, #6366f1);
          border-radius: 8px;
          background-color: var(--widget-primary, #6366f1);
          color: white;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 150ms ease, transform 100ms ease;
        }
        .proactive-action-button:hover:not(:disabled) {
          background-color: color-mix(in srgb, var(--widget-primary, #6366f1) 85%, black);
        }
        .proactive-action-button:active:not(:disabled) {
          transform: scale(0.95);
        }
        .proactive-action-button:focus-visible {
          outline: 2px solid var(--widget-primary, #6366f1);
          outline-offset: 2px;
        }
        .proactive-action-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .proactive-action-button.proactive-action-secondary {
          background-color: transparent;
          color: var(--widget-primary, #6366f1);
        }
        .proactive-action-button.proactive-action-secondary:hover:not(:disabled) {
          background-color: rgba(99, 102, 241, 0.1);
        }
        @media (max-width: 479px) {
          .proactive-modal-container {
            max-width: 90%;
            padding: 20px;
            margin: 16px;
          }
          .proactive-modal-actions {
            flex-direction: column;
          }
          .proactive-action-button {
            width: 100%;
          }
        }
        @media (prefers-reduced-motion: reduce) {
          .proactive-modal-overlay,
          .proactive-modal-container {
            animation: none;
          }
          .proactive-modal-close,
          .proactive-action-button {
            transition: none;
          }
          .proactive-action-button:active:not(:disabled) {
            transform: none;
          }
        }
        
        /* Message Grouping Styles */
        /* NOTE: These inline styles are the primary implementation. External CSS in
         * message-grouping.css + injectMessageGroupingStyles() are prepared for future
         * Shadow DOM support but not currently used (widget renders to regular DOM). */
        .message-group {
          margin-bottom: 12px;
        }
        .message-group__row {
          display: flex;
          align-items: flex-end;
          gap: 8px;
        }
        .message-group__row--user {
          flex-direction: row-reverse;
        }
        .message-group__avatar {
          flex-shrink: 0;
        }
        .message-group__content {
          display: flex;
          flex-direction: column;
          gap: 4px;
          max-width: 75%;
        }
        .message-bubble {
          padding: 10px 14px;
          word-break: break-word;
          animation: message-fade-in 0.2s ease-out;
        }
        .message-bubble--first.message-bubble--bot {
          border-radius: 16px 16px 16px 4px;
        }
        .message-bubble--first.message-bubble--user {
          border-radius: 16px 16px 4px 16px;
        }
        .message-bubble--middle.message-bubble--bot,
        .message-bubble--middle.message-bubble--user {
          border-radius: 4px;
        }
        .message-bubble--last.message-bubble--bot {
          border-radius: 4px 4px 16px 16px;
        }
        .message-bubble--last.message-bubble--user {
          border-radius: 16px 4px 4px 16px;
        }
        .message-bubble--single.message-bubble--bot,
        .message-bubble--single.message-bubble--user {
          border-radius: 16px;
        }
        .message-bubble--system {
          background-color: transparent;
          color: var(--widget-text);
          opacity: 0.7;
          font-size: 12px;
          text-align: center;
          padding: 4px 8px;
        }
        .message-bubble__sender {
          font-size: 11px;
          font-weight: 600;
          margin-bottom: 4px;
          opacity: 0.8;
        }
        .message-bubble__content {
          white-space: pre-wrap;
          word-break: break-word;
        }
        .message-bubble__timestamp {
          font-size: 10px;
          color: var(--widget-text);
          opacity: 0.5;
          margin-top: 2px;
        }
        .message-bubble__timestamp--user {
          text-align: right;
          margin-right: 4px;
        }
        .message-bubble__timestamp--bot {
          text-align: left;
          margin-left: 4px;
        }
        .message-bubble__rich-content {
          max-width: 100%;
          margin-top: 8px;
        }
        @keyframes message-fade-in {
          from {
            opacity: 0;
            transform: translateY(8px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        /* Animation Keyframes for Microinteractions */
        @keyframes typing-dot-bounce {
          0%, 60%, 100% {
            transform: translateY(0);
          }
          30% {
            transform: translateY(-8px);
          }
        }
        
        @keyframes message-send {
          0% {
            opacity: 0;
            transform: scale(0.8);
          }
          100% {
            opacity: 1;
            transform: scale(1);
          }
        }
        
        @keyframes ripple {
          0% {
            transform: translate(-50%, -50%) scale(0);
            opacity: 0.3;
          }
          100% {
            transform: translate(-50%, -50%) scale(4);
            opacity: 0;
          }
        }
        
        @keyframes checkmark-draw {
          0% {
            stroke-dashoffset: 24;
          }
          100% {
            stroke-dashoffset: 0;
          }
        }
        
        @keyframes badge-pulse {
          0%, 100% {
            transform: scale(1);
          }
          50% {
            transform: scale(1.1);
          }
        }
        
        @keyframes streaming-pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.3;
          }
        }
        
        @media (prefers-reduced-motion: reduce) {
          .message-bubble {
            animation: none;
          }
          .typing-dot,
          .bubble-badge,
          .ripple-effect {
            animation: none !important;
          }
        }
        
        /* Feedback Rating Styles */
        .feedback-rating {
          display: flex;
          gap: 8px;
          margin-top: 8px;
          padding: 0 12px;
          flex-shrink: 0;
        }

        .feedback-button {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 44px;
          min-height: 44px;
          padding: 10px;
          border: 1.5px solid rgba(0, 0, 0, 0.15);
          border-radius: 22px;
          background-color: rgba(0, 0, 0, 0.03);
          color: #4b5563;
          cursor: pointer;
          transition: all 150ms ease;
        }

        .feedback-button-icon {
          width: 22px;
          height: 22px;
          fill: none;
          stroke: currentColor;
          stroke-width: 2;
          stroke-linecap: round;
          stroke-linejoin: round;
          transition: fill 150ms ease, stroke 150ms ease;
        }

        .feedback-button--selected .feedback-button-icon {
          fill: currentColor;
        }

        .feedback-button:hover {
          background-color: rgba(0, 0, 0, 0.08);
          border-color: rgba(0, 0, 0, 0.25);
          transform: scale(1.05);
        }

        .feedback-button:active {
          transform: scale(0.95);
        }

        .feedback-button:focus {
          outline: none;
          box-shadow: 0 0 0 3px var(--widget-primary, #4f46e5);
        }

        .feedback-button--selected {
          background-color: var(--widget-primary, #4f46e5);
          color: #ffffff;
          border-color: var(--widget-primary, #4f46e5);
        }

        .feedback-button--selected:hover {
          background-color: var(--widget-primary, #4f46e5);
          opacity: 0.9;
        }

        .feedback-button:disabled {
          cursor: wait;
          opacity: 0.5;
        }

        .feedback-rating--dark .feedback-button {
          color: rgba(255, 255, 255, 0.85);
          border-color: rgba(255, 255, 255, 0.2);
          background-color: rgba(255, 255, 255, 0.05);
        }

        .feedback-rating--dark .feedback-button:hover {
          background-color: rgba(255, 255, 255, 0.15);
          border-color: rgba(255, 255, 255, 0.35);
        }

        .feedback-comment-form {
          display: flex;
          flex-direction: column;
          gap: 8px;
          padding: 8px;
          background-color: rgba(0, 0, 0, 0.02);
          border-radius: 12px;
          flex: 1;
          max-width: 300px;
        }

        .feedback-rating--dark .feedback-comment-form {
          background-color: rgba(255, 255, 255, 0.05);
        }

        .feedback-comment-label {
          font-size: 12px;
          color: var(--widget-text, #1f2937);
        }

        .feedback-comment-textarea {
          width: 100%;
          padding: 8px;
          border: 1px solid rgba(0, 0, 0, 0.1);
          border-radius: 8px;
          background-color: white;
          color: var(--widget-text, #1f2937);
          font-family: var(--widget-font, inherit);
          font-size: 14px;
          resize: none;
        }

        .feedback-rating--dark .feedback-comment-textarea {
          border-color: rgba(255, 255, 255, 0.2);
          background-color: rgba(0, 0, 0, 0.2);
        }

        .feedback-comment-actions {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
        }

        .feedback-comment-skip {
          padding: 6px 12px;
          border: none;
          border-radius: 6px;
          background-color: transparent;
          color: var(--widget-text, #1f2937);
          font-size: 14px;
          cursor: pointer;
          opacity: 0.7;
        }

        .feedback-comment-skip:hover {
          opacity: 1;
        }

        .feedback-comment-submit {
          padding: 6px 12px;
          border: none;
          border-radius: 6px;
          background-color: var(--widget-primary, #4f46e5);
          color: white;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
        }

        .feedback-comment-submit:hover {
          opacity: 0.9;
        }

        .feedback-comment-count {
          font-size: 11px;
          color: var(--widget-text, #1f2937);
          opacity: 0.6;
        }

        @media (prefers-reduced-motion: reduce) {
          .feedback-button {
            transition: none;
          }
        }
      `}</style>
      {state.isLoading ? (
        <div style={{
          position: 'fixed',
          bottom: 20,
          right: mergedTheme.position === 'bottom-left' ? undefined : 20,
          left: mergedTheme.position === 'bottom-left' ? 20 : undefined,
          width: 60,
          height: 60,
          borderRadius: '50%',
          backgroundColor: mergedTheme.primaryColor,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 2147483647,
        }}>
          <LoadingSpinner />
        </div>
      ) : (
        <>
          <ChatBubble
            isOpen={state.isOpen && !state.isMinimized}
            onClick={handleBubbleClick}
            theme={mergedTheme}
            onPrefetch={prefetchChatWindow}
            unreadCount={state.unreadCount}
          />
          <ProactiveModal
            trigger={activeTrigger!}
            isOpen={isProactiveActive && !state.isOpen}
            onAction={handleProactiveAction}
            onDismiss={dismissProactive}
            theme={{
              primaryColor: mergedTheme.primaryColor,
              backgroundColor: mergedTheme.backgroundColor,
              textColor: mergedTheme.textColor,
            }}
          />
          {state.isOpen && !state.isMinimized && (
            <WidgetErrorBoundary fallback={<div style={{position:'fixed',bottom:100,right:20,zIndex:2147483647}}>Failed to load chat.</div>}>
              <React.Suspense fallback={<LoadingSpinner />}>
                <GlassmorphismChatWindow
                  themeMode={state.themeMode}
                  systemTheme={systemTheme}
                >
                  <ChatWindow
                    isOpen={state.isOpen && !state.isMinimized}
                    onClose={toggleChat}
                    theme={mergedTheme}
                    config={state.config}
                    messages={state.messages}
                    isTyping={state.isTyping}
                    onSendMessage={sendMessage}
                    error={state.error}
                    errors={state.errors}
                    onDismissError={dismissError}
                    onRetryError={retryLastAction}
                    onAddToCart={addToCart}
                    onRemoveFromCart={removeFromCart}
                    onCheckout={checkout}
                    addingProductId={addingProductId}
                    removingItemId={removingItemId}
                    isCheckingOut={isCheckingOut}
                    sessionId={state.session?.sessionId}
                    connectionStatus={state.connectionStatus}
                    consentState={state.consentState}
                    onRecordConsent={recordConsent}
                    onClearHistory={clearHistory}
                    position={state.position}
                    isDragging={state.isDragging}
                    isMinimized={state.isMinimized}
                    onDragStart={() => {}}
                    onMinimize={toggleMinimized}
                    themeMode={state.themeMode}
                    onThemeToggle={handleThemeToggle}
                    faqQuickButtons={state.faqQuickButtons}
                    onFaqButtonClick={handleFaqButtonClick}
                    onFeedbackSubmit={handleFeedbackSubmit}
                    isStreaming={state.isStreaming}
                    streamingError={state.streamingError}
                  />
                </GlassmorphismChatWindow>
              </React.Suspense>
            </WidgetErrorBoundary>
          )}
        </>
      )}
    </>
  );
}

interface WidgetProps {
  merchantId: string;
  theme?: Partial<WidgetTheme>;
  initialSessionId?: string;
}

export function Widget({ merchantId, theme, initialSessionId }: WidgetProps) {
  return (
    <WidgetErrorBoundary>
      <WidgetProvider merchantId={merchantId} initialSessionId={initialSessionId}>
        <WidgetInner theme={theme} />
      </WidgetProvider>
    </WidgetErrorBoundary>
  );
}
