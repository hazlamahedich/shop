/**
 * Tests for MessageBubble Component
 *
 * Story 1.13: Bot Preview Mode
 *
 * Tests individual message bubble display with user/bot distinction.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MessageBubble } from '../MessageBubble';
import type { PreviewMessage } from '../../../stores/previewStore';

describe('MessageBubble', () => {
  const baseTimestamp = new Date('2026-02-11T12:00:00Z');

  describe('user messages', () => {
    it('should display user message correctly', () => {
      const userMessage: PreviewMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'What shoes do you have?',
        timestamp: baseTimestamp,
      };

      render(<MessageBubble message={userMessage} botName="GearBot" />);

      expect(screen.getByText('What shoes do you have?')).toBeInTheDocument();
    });

    it('should not show bot name for user messages', () => {
      const userMessage: PreviewMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Test message',
        timestamp: baseTimestamp,
      };

      render(<MessageBubble message={userMessage} botName="GearBot" />);

      expect(screen.queryByText('GearBot')).not.toBeInTheDocument();
    });

    it('should not show confidence for user messages', () => {
      const userMessage: PreviewMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Test message',
        timestamp: baseTimestamp,
        confidence: 85,
        confidenceLevel: 'high',
      };

      render(<MessageBubble message={userMessage} botName="GearBot" />);

      expect(screen.queryByText(/Confidence:/)).not.toBeInTheDocument();
    });
  });

  describe('bot messages', () => {
    it('should display bot message correctly', () => {
      const botMessage: PreviewMessage = {
        id: 'msg-2',
        role: 'bot',
        content: 'I found several shoes for you!',
        timestamp: baseTimestamp,
      };

      render(<MessageBubble message={botMessage} botName="GearBot" />);

      expect(screen.getByText('I found several shoes for you!')).toBeInTheDocument();
      expect(screen.getByText('GearBot')).toBeInTheDocument();
    });

    it('should display confidence indicator for bot messages', () => {
      const botMessage: PreviewMessage = {
        id: 'msg-2',
        role: 'bot',
        content: 'Here are some shoes!',
        timestamp: baseTimestamp,
        confidence: 85,
        confidenceLevel: 'high',
        metadata: {
          intent: 'product_search',
          faqMatched: false,
          productsFound: 3,
          llmProvider: 'ollama',
        },
      };

      render(<MessageBubble message={botMessage} botName="GearBot" />);

      expect(screen.getByText(/Confidence:/)).toBeInTheDocument();
      expect(screen.getByText(/85%/)).toBeInTheDocument();
    });

    it('should not display confidence if not provided', () => {
      const botMessage: PreviewMessage = {
        id: 'msg-2',
        role: 'bot',
        content: 'Here are some shoes!',
        timestamp: baseTimestamp,
      };

      render(<MessageBubble message={botMessage} botName="GearBot" />);

      expect(screen.queryByText(/Confidence:/)).not.toBeInTheDocument();
    });
  });

  describe('timestamps', () => {
    it('should format timestamp correctly', () => {
      const message: PreviewMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Test',
        timestamp: new Date('2026-02-11T14:30:00Z'),
      };

      render(<MessageBubble message={message} botName="GearBot" />);

      // Check that a timestamp is displayed (format may vary by locale)
      const timeElement = document.querySelector('.text-xs');
      expect(timeElement?.textContent).toBeTruthy();
      expect(timeElement?.textContent).not.toBe('Test');
    });
  });

  describe('message list role', () => {
    it('should have listitem role', () => {
      const message: PreviewMessage = {
        id: 'msg-1',
        role: 'user',
        content: 'Test message',
        timestamp: baseTimestamp,
      };

      render(<MessageBubble message={message} botName="GearBot" />);

      const listItem = document.querySelector('[role="listitem"]');
      expect(listItem).toBeInTheDocument();
    });
  });
});
