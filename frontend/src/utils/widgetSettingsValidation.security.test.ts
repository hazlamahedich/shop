import { describe, it, expect } from 'vitest';
import {
  validatePrimaryColor,
  validateWidgetPosition,
} from './widgetSettingsValidation';

describe('Security: Color Picker Injection', () => {
  it('rejects JavaScript protocol in color', () => {
    expect(validatePrimaryColor('javascript:alert(1)')).toBe(
      'Invalid color format. Use #RRGGBB'
    );
  });

  it('rejects data URI in color', () => {
    expect(
      validatePrimaryColor('data:text/html,<script>alert(1)</script>')
    ).toBe('Invalid color format. Use #RRGGBB');
  });

  it('rejects vbscript in color', () => {
    expect(validatePrimaryColor('vbscript:alert(1)')).toBe(
      'Invalid color format. Use #RRGGBB'
    );
  });

  it('rejects expression() in color', () => {
    expect(validatePrimaryColor('expression(alert(1))')).toBe(
      'Invalid color format. Use #RRGGBB'
    );
  });

  it('rejects url() in color', () => {
    expect(validatePrimaryColor('url(http://evil.com)')).toBe(
      'Invalid color format. Use #RRGGBB'
    );
  });
});

describe('Security: Position Injection', () => {
  it('rejects JavaScript in position', () => {
    expect(validateWidgetPosition('javascript:alert(1)')).toBe('Invalid position');
  });

  it('rejects special characters in position', () => {
    expect(validateWidgetPosition('<script>')).toBe('Invalid position');
    expect(validateWidgetPosition('"; DROP TABLE')).toBe('Invalid position');
  });
});

describe('Security: Null and Undefined Handling', () => {
  it('handles null input gracefully for color', () => {
    expect(() => validatePrimaryColor(null as unknown as string)).not.toThrow();
  });

  it('handles undefined input gracefully for color', () => {
    expect(() => validatePrimaryColor(undefined as unknown as string)).not.toThrow();
  });

  it('handles null input gracefully for position', () => {
    expect(() => validateWidgetPosition(null as unknown as string)).not.toThrow();
  });

  it('handles undefined input gracefully for position', () => {
    expect(() => validateWidgetPosition(undefined as unknown as string)).not.toThrow();
  });

  it('handles number input gracefully for color', () => {
    expect(() => validatePrimaryColor(0xff0000 as unknown as string)).not.toThrow();
  });

  it('handles object input gracefully for color', () => {
    expect(() => validatePrimaryColor({ r: 255, g: 0, b: 0 } as unknown as string)).not.toThrow();
  });
});
