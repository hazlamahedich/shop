import { describe, it, expect } from 'vitest';
import {
  clamp,
  sanitizeColor,
  sanitizeFontFamily,
  validatePosition,
  sanitizeTheme,
  THEME_CONSTRAINTS,
} from './themeValidation';
import type { WidgetTheme } from '../types/widget';

describe('clamp', () => {
  it('returns value within range', () => {
    expect(clamp(5, 0, 10)).toBe(5);
  });

  it('returns min when value below range', () => {
    expect(clamp(-5, 0, 10)).toBe(0);
  });

  it('returns max when value above range', () => {
    expect(clamp(15, 0, 10)).toBe(10);
  });

  it('handles min equal to max', () => {
    expect(clamp(5, 10, 10)).toBe(10);
  });
});

describe('sanitizeColor', () => {
  it('accepts valid hex colors', () => {
    expect(sanitizeColor('#6366f1')).toBe('#6366f1');
    expect(sanitizeColor('#ffffff')).toBe('#ffffff');
    expect(sanitizeColor('#000000')).toBe('#000000');
    expect(sanitizeColor('#aBcDeF')).toBe('#aBcDeF');
  });

  it('rejects invalid hex formats', () => {
    expect(sanitizeColor('red')).toBe('#6366f1');
    expect(sanitizeColor('#fff')).toBe('#6366f1');
    expect(sanitizeColor('#gggggg')).toBe('#6366f1');
    expect(sanitizeColor('rgb(255,0,0)')).toBe('#6366f1');
  });

  it('rejects XSS attempts', () => {
    expect(sanitizeColor('javascript:alert(1)')).toBe('#6366f1');
    expect(sanitizeColor('expression(alert(1))')).toBe('#6366f1');
  });
});

describe('sanitizeFontFamily', () => {
  it('preserves valid font families', () => {
    expect(sanitizeFontFamily('Inter, sans-serif')).toBe('Inter, sans-serif');
    expect(sanitizeFontFamily('Arial')).toBe('Arial');
    expect(sanitizeFontFamily('Georgia, serif')).toBe('Georgia, serif');
  });

  it('removes script tags', () => {
    expect(sanitizeFontFamily('<script>alert(1)</script>')).toBe('scriptalert(1)/script');
  });

  it('removes double quotes', () => {
    expect(sanitizeFontFamily('Arial"onclick=alert(1)')).toBe('Arialonclick=alert(1)');
  });

  it('removes single quotes', () => {
    expect(sanitizeFontFamily("Arial'onclick=alert(1)")).toBe('Arialonclick=alert(1)');
  });

  it('removes all dangerous characters', () => {
    expect(sanitizeFontFamily('<>"\'test')).toBe('test');
  });
});

describe('validatePosition', () => {
  it('accepts bottom-right', () => {
    expect(validatePosition('bottom-right')).toBe('bottom-right');
  });

  it('accepts bottom-left', () => {
    expect(validatePosition('bottom-left')).toBe('bottom-left');
  });

  it('defaults to bottom-right for invalid values', () => {
    expect(validatePosition('top-right')).toBe('bottom-right');
    expect(validatePosition('center')).toBe('bottom-right');
    expect(validatePosition('invalid')).toBe('bottom-right');
  });
});

describe('sanitizeTheme', () => {
  it('returns empty object for empty input', () => {
    expect(sanitizeTheme({})).toEqual({});
  });

  it('sanitizes all color fields', () => {
    const theme = sanitizeTheme({
      primaryColor: 'invalid',
      backgroundColor: '#ffffff',
      textColor: '#000000',
      botBubbleColor: '#f3f4f6',
      userBubbleColor: '#6366f1',
    });
    expect(theme.primaryColor).toBe('#6366f1');
    expect(theme.backgroundColor).toBe('#ffffff');
    expect(theme.textColor).toBe('#000000');
    expect(theme.botBubbleColor).toBe('#f3f4f6');
    expect(theme.userBubbleColor).toBe('#6366f1');
  });

  it('clamps borderRadius to 0-24', () => {
    expect(sanitizeTheme({ borderRadius: -5 }).borderRadius).toBe(0);
    expect(sanitizeTheme({ borderRadius: 12 }).borderRadius).toBe(12);
    expect(sanitizeTheme({ borderRadius: 30 }).borderRadius).toBe(24);
  });

  it('clamps width to 280-600', () => {
    expect(sanitizeTheme({ width: 200 }).width).toBe(280);
    expect(sanitizeTheme({ width: 400 }).width).toBe(400);
    expect(sanitizeTheme({ width: 700 }).width).toBe(600);
  });

  it('clamps height to 400-900', () => {
    expect(sanitizeTheme({ height: 300 }).height).toBe(400);
    expect(sanitizeTheme({ height: 500 }).height).toBe(500);
    expect(sanitizeTheme({ height: 1000 }).height).toBe(900);
  });

  it('clamps fontSize to 12-20', () => {
    expect(sanitizeTheme({ fontSize: 10 }).fontSize).toBe(12);
    expect(sanitizeTheme({ fontSize: 14 }).fontSize).toBe(14);
    expect(sanitizeTheme({ fontSize: 25 }).fontSize).toBe(20);
  });

  it('sanitizes fontFamily', () => {
    expect(sanitizeTheme({ fontFamily: '<script>alert(1)</script>' }).fontFamily).toBe(
      'scriptalert(1)/script'
    );
  });

  it('validates position', () => {
    expect(sanitizeTheme({ position: 'bottom-left' }).position).toBe('bottom-left');
    expect(sanitizeTheme({ position: 'top-right' }).position).toBe('bottom-right');
  });

  it('handles complete theme with invalid values', () => {
    const theme = sanitizeTheme({
      primaryColor: 'red',
      backgroundColor: '#ffffff',
      textColor: '#000000',
      botBubbleColor: '#f3f4f6',
      userBubbleColor: '#6366f1',
      position: 'invalid',
      borderRadius: 100,
      width: 1000,
      height: 50,
      fontFamily: '<script>xss</script>',
      fontSize: 50,
    });
    expect(theme.primaryColor).toBe('#6366f1');
    expect(theme.position).toBe('bottom-right');
    expect(theme.borderRadius).toBe(24);
    expect(theme.width).toBe(600);
    expect(theme.height).toBe(400);
    expect(theme.fontFamily).toBe('scriptxss/script');
    expect(theme.fontSize).toBe(20);
  });

  it('preserves valid theme values', () => {
    const validTheme: Partial<WidgetTheme> = {
      primaryColor: '#ff0000',
      backgroundColor: '#000000',
      textColor: '#ffffff',
      botBubbleColor: '#111111',
      userBubbleColor: '#222222',
      position: 'bottom-left',
      borderRadius: 20,
      width: 500,
      height: 700,
      fontFamily: 'Georgia, serif',
      fontSize: 16,
    };
    const result = sanitizeTheme(validTheme);
    expect(result).toEqual(validTheme);
  });

  it('handles empty strings by returning default color', () => {
    const theme = sanitizeTheme({
      primaryColor: '',
      backgroundColor: '',
      textColor: '',
    });
    expect(theme.primaryColor).toBe('#6366f1');
    expect(theme.backgroundColor).toBe('#6366f1');
    expect(theme.textColor).toBe('#6366f1');
  });

  it('handles empty fontFamily string', () => {
    const theme = sanitizeTheme({ fontFamily: '' });
    expect(theme.fontFamily).toBe('');
  });
});

describe('THEME_CONSTRAINTS', () => {
  it('has correct borderRadius range', () => {
    expect(THEME_CONSTRAINTS.borderRadius).toEqual({ min: 0, max: 24 });
  });

  it('has correct width range', () => {
    expect(THEME_CONSTRAINTS.width).toEqual({ min: 280, max: 600 });
  });

  it('has correct height range', () => {
    expect(THEME_CONSTRAINTS.height).toEqual({ min: 400, max: 900 });
  });

  it('has correct fontSize range', () => {
    expect(THEME_CONSTRAINTS.fontSize).toEqual({ min: 12, max: 20 });
  });

  it('has correct positions', () => {
    expect(THEME_CONSTRAINTS.positions).toEqual(['bottom-right', 'bottom-left']);
  });
});
