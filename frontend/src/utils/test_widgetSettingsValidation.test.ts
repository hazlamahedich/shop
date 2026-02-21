import { describe, it, expect } from 'vitest';
import {
  validatePrimaryColor,
  validateWidgetPosition,
  validateWidgetSettings,
  hasValidationErrors,
} from './widgetSettingsValidation';

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
      primaryColor: '#6366f1',
      position: 'bottom-right',
    });
    expect(result).toEqual({});
  });

  it('returns empty object for all valid positions', () => {
    expect(
      validateWidgetSettings({
        primaryColor: '#000000',
        position: 'bottom-left',
      })
    ).toEqual({});
  });

  it('returns primaryColor error for invalid color', () => {
    const result = validateWidgetSettings({
      primaryColor: 'red',
      position: 'bottom-right',
    });
    expect(result.primaryColor).toBe('Invalid color format. Use #RRGGBB');
  });

  it('returns position error for invalid position', () => {
    const result = validateWidgetSettings({
      primaryColor: '#6366f1',
      position: 'top-right',
    });
    expect(result.position).toBe('Invalid position');
  });

  it('returns multiple errors for multiple invalid fields', () => {
    const result = validateWidgetSettings({
      primaryColor: 'invalid',
      position: 'invalid',
    });
    expect(result.primaryColor).toBe('Invalid color format. Use #RRGGBB');
    expect(result.position).toBe('Invalid position');
    expect(Object.keys(result)).toHaveLength(2);
  });
});

describe('hasValidationErrors', () => {
  it('returns false for empty errors object', () => {
    expect(hasValidationErrors({})).toBe(false);
  });

  it('returns true when there is one error', () => {
    expect(
      hasValidationErrors({
        primaryColor: 'Invalid color format. Use #RRGGBB',
      })
    ).toBe(true);
  });

  it('returns true when there are multiple errors', () => {
    expect(
      hasValidationErrors({
        primaryColor: 'Invalid color format. Use #RRGGBB',
        position: 'Invalid position',
      })
    ).toBe(true);
  });

  it('returns true even for undefined error values', () => {
    expect(
      hasValidationErrors({
        primaryColor: undefined,
      })
    ).toBe(true);
  });

  it('returns true for empty string error', () => {
    expect(
      hasValidationErrors({
        primaryColor: '',
      })
    ).toBe(true);
  });
});
