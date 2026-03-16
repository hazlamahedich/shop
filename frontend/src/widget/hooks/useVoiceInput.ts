import * as React from 'react';
import type { VoiceInputState, VoiceInputConfig } from '../types/widget';
import { DEFAULT_VOICE_CONFIG } from '../types/widget';

interface UseVoiceInputReturn {
  state: VoiceInputState;
  isSupported: boolean;
  startListening: () => Promise<void>;
  stopListening: () => void;
  cancelListening: () => void;
  setLanguage: (language: string) => void;
}

interface SpeechRecognitionEvent {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognitionErrorEvent {
  error: string;
  message?: string;
}

interface SpeechRecognitionInterface {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionInterface;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

const VOICE_LANGUAGE_STORAGE_KEY = 'widget-voice-language';

function getStoredLanguage(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    return localStorage.getItem(VOICE_LANGUAGE_STORAGE_KEY);
  } catch {
    return null;
  }
}

function setStoredLanguage(language: string): void {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(VOICE_LANGUAGE_STORAGE_KEY, language);
  } catch {
    // localStorage not available
  }
}

export function useVoiceInput(config: Partial<VoiceInputConfig> = {}): UseVoiceInputReturn {
  // Load language from localStorage if not explicitly provided
  const storedLanguage = React.useMemo(() => getStoredLanguage(), []);
  const mergedConfig: VoiceInputConfig = React.useMemo(() => {
    const base = { ...DEFAULT_VOICE_CONFIG, ...config };
    // Use stored language if not explicitly provided in config
    if (!config.language && storedLanguage) {
      base.language = storedLanguage;
    }
    return base;
  }, [config, storedLanguage]);
  
  const [state, setState] = React.useState<VoiceInputState>({
    isListening: false,
    isProcessing: false,
    error: null,
    interimTranscript: '',
    finalTranscript: '',
  });
  
  const recognitionRef = React.useRef<SpeechRecognitionInterface | null>(null);
  
  const isSupported = React.useMemo(() => {
    if (typeof window === 'undefined') return false;
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }, []);
  
  const getSpeechRecognition = React.useCallback((): SpeechRecognitionConstructor | null => {
    if (typeof window === 'undefined') return null;
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
  }, []);
  
  const startListening = React.useCallback(async (): Promise<void> => {
    if (!isSupported) {
      setState(prev => ({
        ...prev,
        error: 'Voice input is not supported in this browser. Please use Chrome, Edge, or Safari.',
      }));
      return;
    }
    
    const SpeechRecognitionConstructor = getSpeechRecognition();
    if (!SpeechRecognitionConstructor) {
      setState(prev => ({
        ...prev,
        error: 'Speech recognition is not available.',
      }));
      return;
    }
    
    try {
      const recognition = new SpeechRecognitionConstructor();
      recognition.continuous = mergedConfig.continuous;
      recognition.interimResults = mergedConfig.interimResults;
      recognition.lang = mergedConfig.language;
      
      recognition.onstart = () => {
        setState(prev => ({
          ...prev,
          isListening: true,
          isProcessing: false,
          error: null,
          interimTranscript: '',
          finalTranscript: '',
        }));
      };
      
      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let interimTranscript = '';
        let finalTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        setState(prev => ({
          ...prev,
          interimTranscript,
          finalTranscript: prev.finalTranscript + finalTranscript,
        }));
      };
      
      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        let errorMessage = 'An error occurred during speech recognition.';
        
        switch (event.error) {
          case 'not-allowed':
          case 'permission-denied':
            errorMessage = 'Microphone permission denied. Please allow microphone access in your browser settings.';
            break;
          case 'no-speech':
            errorMessage = 'No speech detected. Please try again.';
            break;
          case 'network':
            errorMessage = 'Network error occurred. Please check your internet connection.';
            break;
          case 'audio-capture':
            errorMessage = 'No microphone found. Please connect a microphone and try again.';
            break;
          case 'aborted':
            errorMessage = 'Speech recognition was aborted.';
            break;
          case 'service-not-allowed':
            errorMessage = 'Speech recognition service is not allowed.';
            break;
          case 'language-not-supported':
            errorMessage = `Language "${mergedConfig.language}" is not supported.`;
            break;
        }
        
        setState(prev => ({
          ...prev,
          isListening: false,
          isProcessing: false,
          error: errorMessage,
        }));
      };
      
      recognition.onend = () => {
        setState(prev => ({
          ...prev,
          isListening: false,
          isProcessing: false,
        }));
      };
      
      recognitionRef.current = recognition;
      recognition.start();
    } catch (error) {
      setState(prev => ({
        ...prev,
        isListening: false,
        isProcessing: false,
        error: 'Failed to start speech recognition. Please try again.',
      }));
    }
  }, [isSupported, getSpeechRecognition, mergedConfig]);
  
  const setLanguage = React.useCallback((language: string) => {
    setStoredLanguage(language);
    // Update recognition instance if active
    if (recognitionRef.current) {
      recognitionRef.current.lang = language;
    }
  }, []);
  
  const stopListening = React.useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
  }, []);
  
  const cancelListening = React.useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.abort();
        recognitionRef.current = null;
    }
    setState(prev => ({
      ...prev,
      isListening: false,
      isProcessing: false,
      interimTranscript: '',
    }));
  }, []);
  
  React.useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
        recognitionRef.current = null;
      }
    };
  }, []);
  
  return {
    state,
    isSupported,
    startListening,
    stopListening,
    cancelListening,
    setLanguage,
  };
}
