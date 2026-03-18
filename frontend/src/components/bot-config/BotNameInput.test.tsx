/**
 * Tests for BotNameInput Component
 *
 * Story 1.12: Bot Naming
 *
 * Tests component rendering, validation, character counting,
 * and user interactions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BotNameInput } from './BotNameInput';
import { useBotConfigStore } from '../../stores/botConfigStore';

// Mock the bot config store
vi.mock('../../stores/botConfigStore');

const mockUseBotConfigStore = vi.mocked(useBotConfigStore);

// Default mock return value
const createMockStore = () => ({
  botName: null,
  setBotName: vi.fn(),
  error: null,
  personality: 'friendly',
  clearError: vi.fn(),
});

describe('BotNameInput Component', () => {
  let mockStore: ReturnType<typeof createMockStore>;

  beforeEach(() => {
    vi.clearAllMocks();
    mockStore = createMockStore();
    mockUseBotConfigStore.mockReturnValue(mockStore);
  });

  describe('Rendering', () => {
    it('should render bot name input field', () => {
      render(<BotNameInput />);

      const input = screen.getByLabelText(/Bot Name/);
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('type', 'text');
      expect(input).toHaveAttribute('maxLength', '50');
    });

    it('should render with correct placeholder', () => {
      render(<BotNameInput />);

      const input = screen.getByPlaceholderText(/GearBot, ShopAssistant, Helper/);
      expect(input).toBeInTheDocument();
    });

    it('should render help text', () => {
      render(<BotNameInput />);

      const helpText = screen.getByText(
        /Give your bot a name that customers will see in their conversations/
      );
      expect(helpText).toBeInTheDocument();
    });

    it('should render character count showing 0/50 initially', () => {
      render(<BotNameInput />);

      const charCount = screen.getByText('0 / 50');
      expect(charCount).toBeInTheDocument();
    });

    it('should render live preview section', () => {
      render(<BotNameInput />);

      const preview = screen.getByText(/Preview: How customers see your bot/);
      expect(preview).toBeInTheDocument();
    });

    it('should render with friendly personality greeting', () => {
      mockStore.personality = 'friendly';
      mockUseBotConfigStore.mockReturnValue(mockStore);

      render(<BotNameInput />);

      const greeting = screen.getByText(/Hi! I'm your shopping assistant/);
      expect(greeting).toBeInTheDocument();
    });

    it('should render with professional personality greeting', () => {
      mockStore.personality = 'professional';
      mockUseBotConfigStore.mockReturnValue(mockStore);

      render(<BotNameInput />);

      const greeting = screen.getByText(/Good day\. I'm your shopping assistant/);
      expect(greeting).toBeInTheDocument();
    });

    it('should render with enthusiastic personality greeting', () => {
      mockStore.personality = 'enthusiastic';
      mockUseBotConfigStore.mockReturnValue(mockStore);

      render(<BotNameInput />);

      const greeting = screen.getByText(/Hey there!!! I'm your shopping assistant/);
      expect(greeting).toBeInTheDocument();
    });

    it('should be disabled when disabled prop is true', () => {
      render(<BotNameInput disabled={true} />);

      const input = screen.getByLabelText(/Bot Name/);
      expect(input).toBeDisabled();
    });
  });

  describe('Bot Name in Preview', () => {
    it('should include bot name in preview when set (friendly)', () => {
      mockStore.botName = 'GearBot';
      mockStore.personality = 'friendly';
      mockUseBotConfigStore.mockReturnValue(mockStore);

      render(<BotNameInput />);

      const greeting = screen.getByText(/Hi! I'm GearBot/);
      expect(greeting).toBeInTheDocument();
    });

    it('should include bot name in preview when set (professional)', () => {
      mockStore.botName = 'ShopAssistant';
      mockStore.personality = 'professional';
      mockUseBotConfigStore.mockReturnValue(mockStore);

      render(<BotNameInput />);

      const greeting = screen.getByText(/Good day\. I'm ShopAssistant/);
      expect(greeting).toBeInTheDocument();
    });

    it('should include bot name in preview when set (enthusiastic)', () => {
      mockStore.botName = 'HappyHelper';
      mockStore.personality = 'enthusiastic';
      mockUseBotConfigStore.mockReturnValue(mockStore);

      render(<BotNameInput />);

      const greeting = screen.getByText(/Hey there!!! I'm HappyHelper/);
      expect(greeting).toBeInTheDocument();
    });
  });

  describe('User Input Handling', () => {
    it('should call setBotName when user types', async () => {
      render(<BotNameInput />);

      const input = screen.getByLabelText(/Bot Name/) as HTMLInputElement;
      input.focus();
      await userEvent.paste('TestBot');

      expect(mockStore.setBotName).toHaveBeenCalledWith('TestBot');
    });

    it('should enforce max length of 50 characters', async () => {
      render(<BotNameInput />);

      const input = screen.getByLabelText(/Bot Name/) as HTMLInputElement;
      const longName = 'A'.repeat(60); // 60 characters

      input.focus();
      await userEvent.paste(longName);

      // Should be truncated to 50
      expect(mockStore.setBotName).toHaveBeenCalledWith('A'.repeat(50));
    });

    it('should update character count when name changes', () => {
      mockStore.botName = 'GearBot';
      mockUseBotConfigStore.mockReturnValue(mockStore);

      render(<BotNameInput />);

      const charCount = screen.getByText('7 / 50');
      expect(charCount).toBeInTheDocument();
    });

    it('should show warning color when approaching limit (35+ chars, 15 remaining)', () => {
      mockStore.botName = 'A'.repeat(35); // 35 characters, 15 remaining
      mockUseBotConfigStore.mockReturnValue(mockStore);

      render(<BotNameInput />);

      const charCount = screen.getByText('35 / 50');
      expect(charCount).toHaveClass('text-amber-600');
    });

    it('should show error color when near limit (45+ chars, 5 remaining)', () => {
      mockStore.botName = 'A'.repeat(45); // 45 characters, 5 remaining
      mockUseBotConfigStore.mockReturnValue(mockStore);

      render(<BotNameInput />);

      const charCount = screen.getByText('45 / 50');
      expect(charCount).toHaveClass('text-red-600');
    });
  });

  describe('Error Display', () => {
    it('should display error message when error exists', () => {
      mockStore.error = 'Failed to save bot name';
      mockUseBotConfigStore.mockReturnValue(mockStore);

      render(<BotNameInput />);

      const errorMessage = screen.getByText('Failed to save bot name');
      expect(errorMessage).toBeInTheDocument();
    });

    it('should not display error when error is null', () => {
      render(<BotNameInput />);

      const errorAlert = screen.queryByRole('alert');
      expect(errorAlert).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria-describedby for help text', () => {
      render(<BotNameInput />);

      const input = screen.getByLabelText(/Bot Name/);
      expect(input).toHaveAttribute('aria-describedby');
    });

    it('should be keyboard accessible', () => {
      render(<BotNameInput />);

      const input = screen.getByLabelText(/Bot Name/) as HTMLInputElement;
      input.focus();
      expect(input).toHaveFocus();
    });

    it('should have proper label association', () => {
      render(<BotNameInput />);

      const input = screen.getByLabelText(/Bot Name/);
      expect(input).toBeInTheDocument();
    });
  });
});
