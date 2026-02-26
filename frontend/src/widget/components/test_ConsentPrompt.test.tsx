import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { ConsentPrompt } from './ConsentPrompt';
import type { WidgetTheme } from '../types/widget';

const mockTheme: WidgetTheme = {
  primaryColor: '#6366f1',
  backgroundColor: '#ffffff',
  textColor: '#333333',
  botBubbleColor: '#e0e0f0',
  userBubbleColor: '#3b82f7',
  position: 'bottom-right',
  borderRadius: 12,
  width: 380,
  height: 600,
  fontFamily: 'Inter, sans-serif',
  fontSize: 14,
};

describe('ConsentPrompt', () => {
  const mockOnConfirmConsent = vi.fn().mockResolvedValue(undefined);
  const mockOnDismiss = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders when isOpen, promptShown, and consentGranted is null', () => {
    render(
      <ConsentPrompt
        isOpen={true}
        isLoading={false}
        promptShown={true}
        consentGranted={null}
        theme={mockTheme}
        botName="Test Bot"
        onConfirmConsent={mockOnConfirmConsent}
      />
    );

    expect(screen.getByText('Save your preferences?')).toBeInTheDocument();
    expect(screen.getByText('Yes, save my preferences')).toBeInTheDocument();
    expect(screen.getByText("No, don't save")).toBeInTheDocument();
  });

  it('does not render when promptShown is false', () => {
    render(
      <ConsentPrompt
        isOpen={true}
        isLoading={false}
        promptShown={false}
        consentGranted={null}
        theme={mockTheme}
        botName="Test Bot"
        onConfirmConsent={mockOnConfirmConsent}
      />
    );

    expect(screen.queryByText('Save your preferences?')).not.toBeInTheDocument();
  });

  it('does not render when consentGranted is true', () => {
    render(
      <ConsentPrompt
        isOpen={true}
        isLoading={false}
        promptShown={true}
        consentGranted={true}
        theme={mockTheme}
        botName="Test Bot"
        onConfirmConsent={mockOnConfirmConsent}
      />
    );

    expect(screen.queryByText('Save your preferences?')).not.toBeInTheDocument();
  });

  it('does not render when consentGranted is false', () => {
    render(
      <ConsentPrompt
        isOpen={true}
        isLoading={false}
        promptShown={true}
        consentGranted={false}
        theme={mockTheme}
        botName="Test Bot"
        onConfirmConsent={mockOnConfirmConsent}
      />
    );

    expect(screen.queryByText('Save your preferences?')).not.toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(
      <ConsentPrompt
        isOpen={false}
        isLoading={false}
        promptShown={true}
        consentGranted={null}
        theme={mockTheme}
        botName="Test Bot"
        onConfirmConsent={mockOnConfirmConsent}
      />
    );

    expect(screen.queryByText('Save your preferences?')).not.toBeInTheDocument();
  });

  it('calls onConfirmConsent with true when "Yes" is clicked', async () => {
    render(
      <ConsentPrompt
        isOpen={true}
        isLoading={false}
        promptShown={true}
        consentGranted={null}
        theme={mockTheme}
        botName="Test Bot"
        onConfirmConsent={mockOnConfirmConsent}
      />
    );

    fireEvent.click(screen.getByText('Yes, save my preferences'));

    await waitFor(() => {
      expect(mockOnConfirmConsent).toHaveBeenCalledWith(true);
    });
  });

  it('calls onConfirmConsent with false when "No" is clicked', async () => {
    render(
      <ConsentPrompt
        isOpen={true}
        isLoading={false}
        promptShown={true}
        consentGranted={null}
        theme={mockTheme}
        botName="Test Bot"
        onConfirmConsent={mockOnConfirmConsent}
      />
    );

    fireEvent.click(screen.getByText("No, don't save"));

    await waitFor(() => {
      expect(mockOnConfirmConsent).toHaveBeenCalledWith(false);
    });
  });

  it('disables buttons while loading', () => {
    render(
      <ConsentPrompt
        isOpen={true}
        isLoading={true}
        promptShown={true}
        consentGranted={null}
        theme={mockTheme}
        botName="Test Bot"
        onConfirmConsent={mockOnConfirmConsent}
      />
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).toBeDisabled();
    });
  });

  it('disables buttons while typing', () => {
    render(
      <ConsentPrompt
        isOpen={true}
        isLoading={false}
        isTyping={true}
        promptShown={true}
        consentGranted={null}
        theme={mockTheme}
        botName="Test Bot"
        onConfirmConsent={mockOnConfirmConsent}
      />
    );

    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).toBeDisabled();
    });
  });

  it('disables buttons while processing consent', async () => {
    const slowConsent = vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    render(
      <ConsentPrompt
        isOpen={true}
        isLoading={false}
        promptShown={true}
        consentGranted={null}
        theme={mockTheme}
        botName="Test Bot"
        onConfirmConsent={slowConsent}
      />
    );

    const yesButton = screen.getByText('Yes, save my preferences');
    const noButton = screen.getByText("No, don't save");

    fireEvent.click(yesButton);

    expect(yesButton).toBeDisabled();
    expect(noButton).toBeDisabled();

    await waitFor(() => {
      expect(slowConsent).toHaveBeenCalled();
    });
  });

  it('calls onDismiss when dismiss button is clicked', () => {
    render(
      <ConsentPrompt
        isOpen={true}
        isLoading={false}
        promptShown={true}
        consentGranted={null}
        theme={mockTheme}
        botName="Test Bot"
        onConfirmConsent={mockOnConfirmConsent}
        onDismiss={mockOnDismiss}
      />
    );

    fireEvent.click(screen.getByLabelText('Close consent prompt'));

    expect(mockOnDismiss).toHaveBeenCalled();
  });

  it('displays bot name in description', () => {
    render(
      <ConsentPrompt
        isOpen={true}
        isLoading={false}
        promptShown={true}
        consentGranted={null}
        theme={mockTheme}
        botName="Custom Assistant"
        onConfirmConsent={mockOnConfirmConsent}
      />
    );

    expect(screen.getByText(/Custom Assistant can remember/)).toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    render(
      <ConsentPrompt
        isOpen={true}
        isLoading={false}
        promptShown={true}
        consentGranted={null}
        theme={mockTheme}
        botName="Test Bot"
        onConfirmConsent={mockOnConfirmConsent}
      />
    );

    expect(screen.getByRole('dialog')).toHaveAttribute('aria-modal', 'true');
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-labelledby', 'consent-title');
    expect(screen.getByRole('dialog')).toHaveAttribute('aria-describedby', 'consent-description');
  });
});
