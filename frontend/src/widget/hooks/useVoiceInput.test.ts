import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useVoiceInput } from './useVoiceInput';

const mockStart = vi.fn();
const mockStop = vi.fn();
const mockAbort = vi.fn();

describe('useVoiceInput', () => {
  let originalSpeechRecognition: typeof window.SpeechRecognition;
  let originalWebkitSpeechRecognition: typeof window.webkitSpeechRecognition;

  beforeEach(() => {
    vi.clearAllMocks();
    
    originalSpeechRecognition = window.SpeechRecognition;
    originalWebkitSpeechRecognition = window.webkitSpeechRecognition;
  });

  afterEach(() => {
    window.SpeechRecognition = originalSpeechRecognition;
    window.webkitSpeechRecognition = originalWebkitSpeechRecognition;
  });

  const mockSpeechRecognition = () => {
    const instance = {
      continuous: false,
      interimResults: true,
      lang: 'en-US',
      onresult: null as ((event: unknown) => void) | null,
      onerror: null as ((event: unknown) => void) | null,
      onend: null as (() => void) | null,
      onstart: null as (() => void) | null,
      start: mockStart,
      stop: mockStop,
      abort: mockAbort,
    };
    
    const MockClass = vi.fn(() => instance) as unknown as typeof window.SpeechRecognition;
    window.SpeechRecognition = MockClass as unknown as typeof window.SpeechRecognition;
    window.webkitSpeechRecognition = MockClass as unknown as typeof window.SpeechRecognition;
    
    return instance;
  };

  describe('browser compatibility detection', () => {
    it('should detect when speech recognition is supported', () => {
      mockSpeechRecognition();
      const { result } = renderHook(() => useVoiceInput());
      expect(result.current.isSupported).toBe(true);
    });

    it('should detect when speech recognition is not supported', () => {
        window.SpeechRecognition = undefined as unknown as typeof window.SpeechRecognition;
        window.webkitSpeechRecognition = undefined as unknown as typeof window.SpeechRecognition;
        
        const { result } = renderHook(() => useVoiceInput());
        expect(result.current.isSupported).toBe(false);
    });
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      mockSpeechRecognition();
      const { result } = renderHook(() => useVoiceInput());
      
      expect(result.current.state.isListening).toBe(false);
      expect(result.current.state.isProcessing).toBe(false);
      expect(result.current.state.error).toBeNull();
      expect(result.current.state.interimTranscript).toBe('');
      expect(result.current.state.finalTranscript).toBe('');
    });
  });

  describe('startListening', () => {
    it('should call recognition.start() when starting', async () => {
      mockSpeechRecognition();
      const { result } = renderHook(() => useVoiceInput());
      
      await act(async () => {
        await result.current.startListening();
      });
      
      expect(mockStart).toHaveBeenCalledTimes(1);
    });

    it('should set error when not supported', async () => {
      window.SpeechRecognition = undefined as unknown as typeof window.SpeechRecognition;
      window.webkitSpeechRecognition = undefined as unknown as typeof window.SpeechRecognition;
      
      const { result } = renderHook(() => useVoiceInput());
      
      await act(async () => {
        await result.current.startListening();
      });
      
      expect(result.current.state.error).toBeTruthy();
    });
  });

  describe('stopListening', () => {
    it('should call recognition.stop()', async () => {
      mockSpeechRecognition();
      const { result } = renderHook(() => useVoiceInput());
      
      await act(async () => {
        await result.current.startListening();
      });
      
      act(() => {
        result.current.stopListening();
      });
      
      expect(mockStop).toHaveBeenCalledTimes(1);
    });
  });

  describe('cancelListening', () => {
    it('should call recognition.abort() and reset state', async () => {
        mockSpeechRecognition();
      const { result } = renderHook(() => useVoiceInput());
      
        await act(async () => {
          await result.current.startListening();
        });
        
        act(() => {
          result.current.cancelListening();
        });
        
        expect(mockAbort).toHaveBeenCalledTimes(1);
        expect(result.current.state.interimTranscript).toBe('');
      });
  });

  describe('cleanup', () => {
    it('should abort recognition on unmount', async () => {
      mockSpeechRecognition();
      const { result, unmount } = renderHook(() => useVoiceInput());
      
      await act(async () => {
        await result.current.startListening();
      });
      
      unmount();
      
      expect(mockAbort).toHaveBeenCalled();
    });
  });
});
