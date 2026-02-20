import { describe, it, expect } from 'vitest';
import {
  validateBotName,
  validateWelcomeMessage,
  validatePrimaryColor,
  validateWidgetPosition,
  validateWidgetSettings,
  hasValidationErrors,
} from './widgetSettingsValidation';

describe('validateBotName', () => {
  it('returns null for valid bot name', () => {
    expect(validateBotName('Shopping Assistant')).toBeNull();
    expect(validateBotName('Bot')).toBeNull();
    expect(validateBotName('A')).toBeNull();
  });

  it('returns null for max length (50 chars)', () => {
    expect(validateBotName('A'.repeat(50))).toBeNull();
  });

  it('returns error for empty string', () => {
    expect(validateBotName('')).toBe('Bot name is required');
  });

  it('returns error for whitespace only', () => {
    expect(validateBotName('   ')).toBe('Bot name is required');
    expect(validateBotName('\t\n')).toBe('Bot name is required');
  });

  it('returns error for name over 50 characters', () => {
    expect(validateBotName('A'.repeat(51))).toBe('Max 50 characters');
    expect(validateBotName('A'.repeat(100))).toBe('Max 50 characters');
  });

  it('accepts bot name with special characters', () => {
    expect(validateBotName("Bot's Store!")).toBeNull();
    expect(validateBotName('Bot & Co.')).toBeNull();
    expect(validateBotName('Bot-123')).toBeNull();
  });

  it('accepts unicode characters', () => {
    expect(validateBotName('Shopping 🤖')).toBeNull();
    expect(validateBotName('ロボット')).toBeNull();
  });
});

describe('validateWelcomeMessage', () => {
  it('returns null for valid welcome message', () => {
    expect(validateWelcomeMessage('Hi! How can I help you today?')).toBeNull();
    expect(validateWelcomeMessage('Welcome!')).toBeNull();
  });

  it('returns null for max length (500 chars)', () => {
    expect(validateWelcomeMessage('A'.repeat(500))).toBeNull();
  });

  it('returns error for empty string', () => {
    expect(validateWelcomeMessage('')).toBe('Welcome message is required');
  });

  it('returns error for whitespace only', () => {
    expect(validateWelcomeMessage('   ')).toBe('Welcome message is required');
    expect(validateWelcomeMessage('\t\n\r')).toBe('Welcome message is required');
  });

  it('returns error for message over 500 characters', () => {
    expect(validateWelcomeMessage('A'.repeat(501))).toBe('Max 500 characters');
    expect(validateWelcomeMessage('A'.repeat(1000))).toBe('Max 500 characters');
  });

  it('accepts multi-line messages', () => {
    expect(validateWelcomeMessage('Hello!\n\nHow can I help?')).toBeNull();
    expect(validateWelcomeMessage('Line 1\nLine 2\nLine 3')).toBeNull();
  });

  it('accepts messages with special characters', () => {
    expect(validateWelcomeMessage("Hi! 👋 What's up?")).toBeNull();
    expect(validateWelcomeMessage('Welcome! <script>alert(1)</script>')).toBeNull();
  });
});

describe('validatePrimaryColor', () => {
  it('returns null for valid hex colors', () => {
    expect(validatePrimaryColor('#6366f1')).toBeNull();
    expect(validatePrimaryColor('#ffffff')).toBeNull();
    expect(validatePrimaryColor('#000000')).toBeNull();
    expect(validatePrimaryColor('#aBcDeF')).toBeNull();
    expect(validatePrimaryColor('#123456')).toBeNull();
  });

  it('returns error for missing # prefix', () => {
    expect(validatePrimaryColor('6366f1')).toBe('Invalid color format. Use #RRGGBB');
    expect(validatePrimaryColor('ffffff')).toBe('Invalid color format. Use #RRGGBB');
  });

  it('returns error for short hex format (#RGB)', () => {
    expect(validatePrimaryColor('#fff')).toBe('Invalid color format. Use #RRGGBB');
    expect(validatePrimaryColor('#abc')).toBe('Invalid color format. Use #RRGGBB');
  });

  it('returns error for 8-digit hex (#RRGGBBAA)', () => {
    expect(validatePrimaryColor('#6366f1ff')).toBe('Invalid color format. Use #RRGGBB');
  });

  it('returns error for invalid hex characters', () => {
    expect(validatePrimaryColor('#gggggg')).toBe('Invalid color format. Use #RRGGBB');
    expect(validatePrimaryColor('#xyz123')).toBe('Invalid color format. Use #RRGGBB');
  });

  it('returns error for named colors', () => {
    expect(validatePrimaryColor('red')).toBe('Invalid color format. Use #RRGGBB');
    expect(validatePrimaryColor('blue')).toBe('Invalid color format. Use #RRGGBB');
    expect(validatePrimaryColor('transparent')).toBe('Invalid color format. Use #RRGGBB');
  });

  it('returns error for rgb/rgba formats', () => {
    expect(validatePrimaryColor('rgb(255, 0, 0)')).toBe('Invalid color format. Use #RRGGBB');
    expect(validatePrimaryColor('rgba(255, 0, 0, 1)')).toBe('Invalid color format. Use #RRGGBB');
  });

  it('returns error for empty string', () => {
    expect(validatePrimaryColor('')).toBe('Invalid color format. Use #RRGGBB');
  });

  it('returns error for XSS attempts', () => {
    expect(validatePrimaryColor('javascript:alert(1)')).toBe('Invalid color format. Use #RRGGBB');
    expect(validatePrimaryColor('expression(alert(1))')).toBe('Invalid color format. Use #RRGGBB');
  });
});

describe('validateWidgetPosition', () => {
  it('returns null for bottom-right', () => {
    expect(validateWidgetPosition('bottom-right')).toBeNull();
  });

  it('returns null for bottom-left', () => {
    expect(validateWidgetPosition('bottom-left')).toBeNull();
  });

  it('returns error for invalid positions', () => {
    expect(validateWidgetPosition('top-right')).toBe('Invalid position');
    expect(validateWidgetPosition('top-left')).toBe('Invalid position');
    expect(validateWidgetPosition('center')).toBe('Invalid position');
    expect(validateWidgetPosition('invalid')).toBe('Invalid position');
  });

  it('returns error for empty string', () => {
    expect(validateWidgetPosition('')).toBe('Invalid position');
  });

  it('is case sensitive', () => {
    expect(validateWidgetPosition('BOTTOM-RIGHT')).toBe('Invalid position');
    expect(validateWidgetPosition('Bottom-Right')).toBe('Invalid position');
    expect(validateWidgetPosition('BOTTOM_RIGHT')).toBe('Invalid position');
  });

  it('rejects positions with extra whitespace', () => {
    expect(validateWidgetPosition(' bottom-right')).toBe('Invalid position');
    expect(validateWidgetPosition('bottom-right ')).toBe('Invalid position');
    expect(validateWidgetPosition('bottom-right\n')).toBe('Invalid position');
  });
});

describe('validateWidgetSettings', () => {
  it('returns empty object for valid settings', () => {
    const result = validateWidgetSettings({
      botName: 'Shopping Bot',
      welcomeMessage: 'Hello!',
      primaryColor: '#6366f1',
      position: 'bottom-right',
    });
    expect(result).toEqual({});
  });

  it('returns empty object for all valid positions', () => {
    expect(
      validateWidgetSettings({
        botName: 'Bot',
        welcomeMessage: 'Hi',
        primaryColor: '#000000',
        position: 'bottom-left',
      })
    ).toEqual({});
  });

  it('returns botName error for empty bot name', () => {
    const result = validateWidgetSettings({
      botName: '',
      welcomeMessage: 'Hello!',
      primaryColor: '#6366f1',
      position: 'bottom-right',
    });
    expect(result.botName).toBe('Bot name is required');
    expect(result.welcomeMessage).toBeUndefined();
  });

  it('returns welcomeMessage error for empty message', () => {
    const result = validateWidgetSettings({
      botName: 'Bot',
      welcomeMessage: '',
      primaryColor: '#6366f1',
      position: 'bottom-right',
    });
    expect(result.welcomeMessage).toBe('Welcome message is required');
    expect(result.botName).toBeUndefined();
  });

  it('returns primaryColor error for invalid color', () => {
    const result = validateWidgetSettings({
      botName: 'Bot',
      welcomeMessage: 'Hi',
      primaryColor: 'red',
      position: 'bottom-right',
    });
    expect(result.primaryColor).toBe('Invalid color format. Use #RRGGBB');
  });

  it('returns position error for invalid position', () => {
    const result = validateWidgetSettings({
      botName: 'Bot',
      welcomeMessage: 'Hi',
      primaryColor: '#6366f1',
      position: 'top-right',
    });
    expect(result.position).toBe('Invalid position');
  });

  it('returns multiple errors for multiple invalid fields', () => {
    const result = validateWidgetSettings({
      botName: '',
      welcomeMessage: '',
      primaryColor: 'invalid',
      position: 'invalid',
    });
    expect(result.botName).toBe('Bot name is required');
    expect(result.welcomeMessage).toBe('Welcome message is required');
    expect(result.primaryColor).toBe('Invalid color format. Use #RRGGBB');
    expect(result.position).toBe('Invalid position');
    expect(Object.keys(result)).toHaveLength(4);
  });

  it('returns error for botName over 50 chars', () => {
    const result = validateWidgetSettings({
      botName: 'A'.repeat(51),
      welcomeMessage: 'Hi',
      primaryColor: '#6366f1',
      position: 'bottom-right',
    });
    expect(result.botName).toBe('Max 50 characters');
  });

  it('returns error for welcomeMessage over 500 chars', () => {
    const result = validateWidgetSettings({
      botName: 'Bot',
      welcomeMessage: 'A'.repeat(501),
      primaryColor: '#6366f1',
      position: 'bottom-right',
    });
    expect(result.welcomeMessage).toBe('Max 500 characters');
  });
});

describe('hasValidationErrors', () => {
  it('returns false for empty errors object', () => {
    expect(hasValidationErrors({})).toBe(false);
  });

  it('returns true when there is one error', () => {
    expect(
      hasValidationErrors({
        botName: 'Bot name is required',
      })
    ).toBe(true);
  });

  it('returns true when there are multiple errors', () => {
    expect(
      hasValidationErrors({
        botName: 'Bot name is required',
        welcomeMessage: 'Welcome message is required',
      })
    ).toBe(true);
  });

  it('returns true even for undefined error values', () => {
    expect(
      hasValidationErrors({
        botName: undefined,
      })
    ).toBe(true);
  });

  it('returns true for empty string error', () => {
    expect(
      hasValidationErrors({
        botName: '',
      })
    ).toBe(true);
  });
});
