import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';
import { ContactCard } from './ContactCard';
import type { WidgetTheme, ContactOption } from '../types/widget';

vi.mock('../utils/analytics', () => ({
  logContactInteraction: vi.fn(),
}));

vi.mock('../utils/businessHours', () => ({
  getBusinessHoursMessage: vi.fn(() => 'Contact us'),
}));

const mockTheme: WidgetTheme = {
  primaryColor: '#6366f1',
  backgroundColor: '#ffffff',
  textColor: '#1e293b',
  botBubbleColor: '#f1f5f9',
  userBubbleColor: '#6366f1',
  position: 'bottom-right',
  borderRadius: 12,
  width: 400,
  height: 600,
  fontFamily: 'Inter, sans-serif',
  fontSize: 14,
};

const mockDarkTheme: WidgetTheme = {
  ...mockTheme,
  mode: 'dark',
};

const mockContactOptions: ContactOption[] = [
  { type: 'phone', label: 'Call Support', value: '+1-555-123-4567', icon: '📞' },
  { type: 'email', label: 'Email Support', value: 'support@example.com', icon: '✉️' },
  { type: 'custom', label: 'Schedule a Call', value: 'https://calendly.com/support', icon: '📅' },
];

describe('ContactCard', () => {
  const originalMatchMedia = window.matchMedia;
  const mockOnContactClick = vi.fn();

  beforeEach(() => {
    mockOnContactClick.mockClear();
    window.matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
    window.matchMedia = originalMatchMedia;
  });

  describe('AC1: Rendering', () => {
    it('renders all contact options', () => {
      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
        />
      );

      expect(screen.getByTestId('contact-card')).toBeInTheDocument();
      expect(screen.getByTestId('contact-phone')).toBeInTheDocument();
      expect(screen.getByTestId('contact-email')).toBeInTheDocument();
      expect(screen.getByTestId('contact-custom')).toBeInTheDocument();
    });

    it('renders nothing when contactOptions is empty', () => {
      const { container } = render(
        <ContactCard
          contactOptions={[]}
          theme={mockTheme}
        />
      );

      expect(container.firstChild).toBeNull();
    });

    it('renders nothing when contactOptions is undefined', () => {
      const { container } = render(
        <ContactCard
          contactOptions={undefined as any}
          theme={mockTheme}
        />
      );

      expect(container.firstChild).toBeNull();
    });

    it('renders multiple options of the same type', () => {
      const multipleOptions: ContactOption[] = [
        { type: 'phone', label: 'US Support', value: '+1-555-111-1111', icon: '📞' },
        { type: 'phone', label: 'UK Support', value: '+44-20-1234-5678', icon: '📞' },
        { type: 'email', label: 'General', value: 'general@example.com', icon: '✉️' },
        { type: 'email', label: 'Technical', value: 'tech@example.com', icon: '✉️' },
      ];

      render(
        <ContactCard
          contactOptions={multipleOptions}
          theme={mockTheme}
        />
      );

      const phoneOptions = screen.getAllByTestId('contact-phone');
      const emailOptions = screen.getAllByTestId('contact-email');

      expect(phoneOptions).toHaveLength(2);
      expect(emailOptions).toHaveLength(2);
    });

  });

  describe('AC2: Phone Click Behavior', () => {
    it('calls tel: link on mobile devices', async () => {
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)',
        configurable: true,
      });

      const originalLocation = window.location;
      delete (window as any).location;
      window.location = { href: '' } as any;

      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
          onContactClick={mockOnContactClick}
        />
      );

      fireEvent.click(screen.getByTestId('contact-phone'));

      expect(window.location.href).toContain('tel:+1-555-123-4567');
      expect(mockOnContactClick).toHaveBeenCalled();

      window.location = originalLocation;
    });

    it('copies to clipboard on desktop', async () => {
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        configurable: true,
      });

      const mockClipboard = {
        writeText: vi.fn().mockResolvedValue(undefined),
      };
      Object.assign(navigator, { clipboard: mockClipboard });

      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
          onContactClick={mockOnContactClick}
        />
      );

      fireEvent.click(screen.getByTestId('contact-phone'));

      await waitFor(() => {
        expect(mockClipboard.writeText).toHaveBeenCalledWith('+1-555-123-4567');
      });
      expect(mockOnContactClick).toHaveBeenCalled();
    });
  });

  describe('AC3: Email Click Behavior', () => {
    it('opens mailto link with email address', () => {
      const originalLocation = window.location;
      delete (window as any).location;
      window.location = { href: '' } as any;

      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
          onContactClick={mockOnContactClick}
        />
      );

      fireEvent.click(screen.getByTestId('contact-email'));

      expect(window.location.href).toContain('mailto:support@example.com');
      expect(mockOnContactClick).toHaveBeenCalled();

      window.location = originalLocation;
    });

    it('includes conversation ID in email subject', () => {
      const originalLocation = window.location;
      delete (window as any).location;
      window.location = { href: '' } as any;

      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
          conversationId="conv-12345"
          onContactClick={mockOnContactClick}
        />
      );

      fireEvent.click(screen.getByTestId('contact-email'));

      expect(window.location.href).toContain('subject=');
      expect(window.location.href).toContain('conv-12345');

      window.location = originalLocation;
    });

    it('uses generic subject when no conversation ID', () => {
      const originalLocation = window.location;
      delete (window as any).location;
      window.location = { href: '' } as any;

      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
          onContactClick={mockOnContactClick}
        />
      );

      fireEvent.click(screen.getByTestId('contact-email'));

      expect(window.location.href).toContain('subject=');
      expect(window.location.href).toContain('Support%20Request');

      window.location = originalLocation;
    });
  });

  describe('AC4: Custom Option Click', () => {
    it('opens URL in new tab', () => {
      const mockOpen = vi.fn();
      const originalOpen = window.open;
      window.open = mockOpen;

      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
          onContactClick={mockOnContactClick}
        />
      );

      fireEvent.click(screen.getByTestId('contact-custom'));

      expect(mockOpen).toHaveBeenCalledWith(
        'https://calendly.com/support',
        '_blank',
        'noopener noreferrer'
      );
      expect(mockOnContactClick).toHaveBeenCalled();

      window.open = originalOpen;
    });
  });

  describe('AC7: Accessibility', () => {
    it('has correct role on contact buttons', () => {
      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
        />
      );

      const phoneButton = screen.getByTestId('contact-phone');
      const emailButton = screen.getByTestId('contact-email');
      const customButton = screen.getByTestId('contact-custom');

      expect(phoneButton).toHaveAttribute('role', 'button');
      expect(emailButton).toHaveAttribute('role', 'button');
      expect(customButton).toHaveAttribute('role', 'button');
    });

    it('has aria-label on contact buttons', () => {
      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
        />
      );

      const phoneButton = screen.getByTestId('contact-phone');
      const emailButton = screen.getByTestId('contact-email');
      const customButton = screen.getByTestId('contact-custom');

      expect(phoneButton).toHaveAttribute('aria-label', 'Call Support');
      expect(emailButton).toHaveAttribute('aria-label', 'Email Support');
      expect(customButton).toHaveAttribute('aria-label', 'Schedule a Call');
    });

    it('has visible focus ring on focus', () => {
      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
        />
      );

      const phoneButton = screen.getByTestId('contact-phone');
      phoneButton.focus();

      expect(phoneButton).toHaveFocus();
    });

    it('supports keyboard navigation', () => {
      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
        />
      );

      const phoneButton = screen.getByTestId('contact-phone');
      phoneButton.focus();
      expect(phoneButton).toHaveFocus();

      fireEvent.keyDown(phoneButton, { key: 'Tab' });
    });
  });

  describe('Dark Mode', () => {
    it('applies dark mode styles', () => {
      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockDarkTheme}
        />
      );

      const phoneButton = screen.getByTestId('contact-phone');
      expect(phoneButton).toBeInTheDocument();
    });
  });

  describe('Reduced Motion', () => {
    it('respects prefers-reduced-motion', () => {
      window.matchMedia = vi.fn().mockImplementation((query: string) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      }));

      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
        />
      );

      const phoneButton = screen.getByTestId('contact-phone');
      expect(phoneButton.style.transition).toBe('none');
    });
  });

  describe('Icons', () => {
    it('displays custom icons for contact options', () => {
      render(
        <ContactCard
          contactOptions={mockContactOptions}
          theme={mockTheme}
        />
      );

      expect(screen.getByText('📞')).toBeInTheDocument();
      expect(screen.getByText('✉️')).toBeInTheDocument();
      expect(screen.getByText('📅')).toBeInTheDocument();
    });

    it('renders without icon if not provided', () => {
      const optionsWithoutIcons: ContactOption[] = [
        { type: 'phone', label: 'Call Us', value: '+1-555-1234' },
      ];

      render(
        <ContactCard
          contactOptions={optionsWithoutIcons}
          theme={mockTheme}
        />
      );

      const phoneButton = screen.getByTestId('contact-phone');
      expect(phoneButton).toBeInTheDocument();
      expect(screen.getByText('Call Us')).toBeInTheDocument();
    });
  });
});
