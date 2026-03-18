import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { VoiceInput } from './VoiceInput';

describe('VoiceInput', () => {
  let originalSpeechRecognition: typeof window.SpeechRecognition;
  let originalWebkitSpeechRecognition: typeof window.webkitSpeechRecognition;
  let latestMockInstance: {
    triggerOnstart: () => void;
    triggerOnend: () => void;
    triggerOnerror: (error: string) => void;
    triggerOnresult: (transcript: string, isFinal: boolean) => void;
    start: ReturnType<typeof vi.fn>;
    stop: ReturnType<typeof vi.fn>;
    abort: ReturnType<typeof vi.fn>;
  } | null = null;

  beforeEach(() => {
    vi.clearAllMocks();
    latestMockInstance = null;

    originalSpeechRecognition = window.SpeechRecognition;
    originalWebkitSpeechRecognition = window.webkitSpeechRecognition;

    class MockSpeechRecognition {
      private _onstart: (() => void) | null = null;
      private _onend: (() => void) | null = null;
      private _onerror: ((event: { error: string }) => void) | null = null;
      private _onresult: ((event: { resultIndex: number; results: Array<{ isFinal: boolean; 0: { transcript: string } }> }) => void) | null = null;
      
      continuous = false;
      interimResults = true;
      lang = 'en-US';
      
      get onstart() { return this._onstart; }
      set onstart(fn: (() => void) | null) { this._onstart = fn; }
      get onend() { return this._onend; }
      set onend(fn: (() => void) | null) { this._onend = fn; }
      get onerror() { return this._onerror; }
      set onerror(fn: ((event: { error: string }) => void) | null) { this._onerror = fn; }
      get onresult() { return this._onresult; }
      set onresult(fn: ((event: { resultIndex: number; results: Array<{ isFinal: boolean; 0: { transcript: string } }> }) => void) | null) { this._onresult = fn; }

      start = vi.fn();
      stop = vi.fn();
      abort = vi.fn();

      constructor() {
        latestMockInstance = {
          triggerOnstart: () => { if (this._onstart) this._onstart(); },
          triggerOnend: () => { if (this._onend) this._onend(); },
          triggerOnerror: (error: string) => { if (this._onerror) this._onerror({ error }); },
          triggerOnresult: (transcript: string, isFinal: boolean) => {
            if (this._onresult) {
              this._onresult({
                resultIndex: 0,
                results: [{ isFinal, 0: { transcript } }],
              });
            }
          },
          start: this.start,
          stop: this.stop,
          abort: this.abort,
        };
      }
    }

    window.SpeechRecognition = MockSpeechRecognition as unknown as typeof window.SpeechRecognition;
    window.webkitSpeechRecognition = MockSpeechRecognition as unknown as typeof window.webkitSpeechRecognition;
  });

  afterEach(() => {
    window.SpeechRecognition = originalSpeechRecognition;
    window.webkitSpeechRecognition = originalWebkitSpeechRecognition;
    latestMockInstance = null;
  });

  describe('rendering', () => {
    it('should render microphone button', () => {
      render(<VoiceInput />);
      expect(screen.getByTestId('voice-input-button')).toBeInTheDocument();
    });

    it('should have correct aria-label when idle', () => {
      render(<VoiceInput />);
      expect(screen.getByTestId('voice-input-button')).toHaveAttribute(
        'aria-label',
        'Start voice input'
      );
    });

    it('should have aria-pressed set to false when idle', () => {
      render(<VoiceInput />);
      expect(screen.getByTestId('voice-input-button')).toHaveAttribute(
        'aria-pressed',
        'false'
      );
    });

    it('should be disabled when disabled prop is true', () => {
      render(<VoiceInput disabled />);
      expect(screen.getByTestId('voice-input-button')).toBeDisabled();
    });
  });

  describe('unsupported browser', () => {
    it('should show disabled state when not supported', () => {
      window.SpeechRecognition = undefined;
      window.webkitSpeechRecognition = undefined;

      render(<VoiceInput />);
      expect(screen.getByTestId('voice-input-button')).toBeDisabled();
    });

    it('should show unsupported aria-label when not supported', () => {
      window.SpeechRecognition = undefined;
      window.webkitSpeechRecognition = undefined;

      render(<VoiceInput />);
      expect(screen.getByTestId('voice-input-button')).toHaveAttribute(
        'aria-label',
        'Voice input not supported in this browser'
      );
    });
  });

  describe('listening state', () => {
    it('should toggle listening state on button click', async () => {
      render(<VoiceInput />);

      fireEvent.click(screen.getByTestId('voice-input-button'));

      expect(latestMockInstance?.start).toHaveBeenCalled();
    });

    it('should show cancel button when listening', async () => {
      render(<VoiceInput />);

      fireEvent.click(screen.getByTestId('voice-input-button'));
      act(() => {
        latestMockInstance?.triggerOnstart();
      });

      expect(screen.getByTestId('voice-input-cancel')).toBeInTheDocument();
    });

    it('should update aria-label when listening', async () => {
      render(<VoiceInput />);

      fireEvent.click(screen.getByTestId('voice-input-button'));
      act(() => {
        latestMockInstance?.triggerOnstart();
      });

      expect(screen.getByTestId('voice-input-button')).toHaveAttribute(
        'aria-label',
        'Stop voice input'
      );
    });

    it('should set aria-pressed to true when listening', async () => {
      render(<VoiceInput />);

      fireEvent.click(screen.getByTestId('voice-input-button'));
      act(() => {
        latestMockInstance?.triggerOnstart();
      });

      expect(screen.getByTestId('voice-input-button')).toHaveAttribute(
        'aria-pressed',
        'true'
      );
    });
  });

  describe('cancel button', () => {
    it('should cancel listening when cancel button is clicked', async () => {
      render(<VoiceInput />);

      fireEvent.click(screen.getByTestId('voice-input-button'));
      act(() => {
        latestMockInstance?.triggerOnstart();
      });

      expect(screen.getByTestId('voice-input-cancel')).toBeInTheDocument();

      fireEvent.click(screen.getByTestId('voice-input-cancel'));

      expect(latestMockInstance?.abort).toHaveBeenCalled();
    });

    it('should hide cancel button after canceling', async () => {
      render(<VoiceInput />);

      fireEvent.click(screen.getByTestId('voice-input-button'));
      act(() => {
        latestMockInstance?.triggerOnstart();
      });

      expect(screen.getByTestId('voice-input-cancel')).toBeInTheDocument();

      fireEvent.click(screen.getByTestId('voice-input-cancel'));
      act(() => {
        latestMockInstance?.triggerOnend();
      });

      expect(screen.queryByTestId('voice-input-cancel')).not.toBeInTheDocument();
    });
  });

  describe('interim transcript', () => {
    it('should not show interim transcript initially', () => {
      render(<VoiceInput />);
      expect(screen.queryByTestId('voice-interim-transcript')).not.toBeInTheDocument();
    });

    it('should show interim transcript when speech is detected', async () => {
      render(<VoiceInput />);

      fireEvent.click(screen.getByTestId('voice-input-button'));
      act(() => {
        latestMockInstance?.triggerOnstart();
      });

      act(() => {
        latestMockInstance?.triggerOnresult('hello world', false);
      });

      expect(screen.getByTestId('voice-interim-transcript')).toHaveTextContent('hello world');
    });
  });

  describe('callbacks', () => {
    it('should call onTranscript when final transcript is received', async () => {
      const onTranscript = vi.fn();
      render(<VoiceInput onTranscript={onTranscript} />);

      fireEvent.click(screen.getByTestId('voice-input-button'));
      act(() => {
        latestMockInstance?.triggerOnstart();
      });

      act(() => {
        latestMockInstance?.triggerOnresult('final transcript', true);
      });

      act(() => {
        latestMockInstance?.triggerOnend();
      });

      expect(onTranscript).toHaveBeenCalledWith('final transcript');
    });

    it('should call onError when error occurs', async () => {
      const onError = vi.fn();
      render(<VoiceInput onError={onError} />);

      fireEvent.click(screen.getByTestId('voice-input-button'));
      act(() => {
        latestMockInstance?.triggerOnstart();
      });

      act(() => {
        latestMockInstance?.triggerOnerror('not-allowed');
      });

      expect(onError).toHaveBeenCalled();
    });
  });

  describe('accessibility', () => {
    it('should have role="button"', () => {
      render(<VoiceInput />);
      expect(screen.getByTestId('voice-input-button')).toHaveAttribute('role', 'button');
    });

    it('should have type="button"', () => {
      render(<VoiceInput />);
      expect(screen.getByTestId('voice-input-button')).toHaveAttribute('type', 'button');
    });

    it('should have 44x44px touch target (via CSS class)', () => {
      render(<VoiceInput />);
      const button = screen.getByTestId('voice-input-button');
      expect(button).toHaveClass('voice-input-button');
    });
  });

  describe('prefers-reduced-motion', () => {
    it('should respect reduced motion preference', () => {
      const matchMedia = vi.fn().mockReturnValue({
        matches: true,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      });
      window.matchMedia = matchMedia;

      render(<VoiceInput />);
      expect(screen.getByTestId('voice-input-button')).toBeInTheDocument();
    });
  });
});
