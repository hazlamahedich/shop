import { describe, it, expect } from 'vitest';
import { mergeThemes } from './themeMerge';
import { DEFAULT_THEME } from './themeDefaults';
import type { WidgetTheme } from '../types/widget';

describe('mergeThemes', () => {
  it('returns default theme when no overrides provided', () => {
    const result = mergeThemes();
    expect(result).toEqual(DEFAULT_THEME);
  });

  it('returns default theme when undefined provided', () => {
    const result = mergeThemes(undefined, undefined);
    expect(result).toEqual(DEFAULT_THEME);
  });

  it('merges merchant theme over defaults', () => {
    const merchantTheme = { primaryColor: '#ff0000', borderRadius: 20 };
    const result = mergeThemes(merchantTheme);
    expect(result.primaryColor).toBe('#ff0000');
    expect(result.borderRadius).toBe(20);
    expect(result.backgroundColor).toBe(DEFAULT_THEME.backgroundColor);
  });

  it('embed overrides take precedence over merchant config', () => {
    const merchantTheme = { primaryColor: '#ff0000', borderRadius: 20 };
    const embedOverrides = { primaryColor: '#00ff00', width: 500 };
    const result = mergeThemes(merchantTheme, embedOverrides);
    expect(result.primaryColor).toBe('#00ff00');
    expect(result.borderRadius).toBe(20);
    expect(result.width).toBe(500);
  });

  it('theme precedence: default < merchant < embed', () => {
    const merchantTheme: Partial<WidgetTheme> = {
      primaryColor: '#ff0000',
      backgroundColor: '#111111',
      borderRadius: 20,
    };
    const embedOverrides: Partial<WidgetTheme> = {
      primaryColor: '#00ff00',
    };
    const result = mergeThemes(merchantTheme, embedOverrides);
    expect(result.primaryColor).toBe('#00ff00');
    expect(result.backgroundColor).toBe('#111111');
    expect(result.borderRadius).toBe(20);
    expect(result.textColor).toBe(DEFAULT_THEME.textColor);
  });

  it('sanitizes merchant theme values', () => {
    const merchantTheme = {
      primaryColor: 'invalid',
      borderRadius: 100,
      fontFamily: '<script>alert(1)</script>',
    };
    const result = mergeThemes(merchantTheme);
    expect(result.primaryColor).toBe('#6366f1');
    expect(result.borderRadius).toBe(24);
    expect(result.fontFamily).toBe('scriptalert(1)/script');
  });

  it('sanitizes embed override values', () => {
    const embedOverrides = {
      primaryColor: 'red',
      position: 'top-right',
      width: 1000,
    };
    const result = mergeThemes(undefined, embedOverrides);
    expect(result.primaryColor).toBe('#6366f1');
    expect(result.position).toBe('bottom-right');
    expect(result.width).toBe(600);
  });

  it('sanitizes both merchant and embed themes', () => {
    const merchantTheme = { borderRadius: -10 };
    const embedOverrides = { width: 50 };
    const result = mergeThemes(merchantTheme, embedOverrides);
    expect(result.borderRadius).toBe(0);
    expect(result.width).toBe(280);
  });

  it('returns complete WidgetTheme with all 11 fields', () => {
    const result = mergeThemes();
    expect(result).toHaveProperty('primaryColor');
    expect(result).toHaveProperty('backgroundColor');
    expect(result).toHaveProperty('textColor');
    expect(result).toHaveProperty('botBubbleColor');
    expect(result).toHaveProperty('userBubbleColor');
    expect(result).toHaveProperty('position');
    expect(result).toHaveProperty('borderRadius');
    expect(result).toHaveProperty('width');
    expect(result).toHaveProperty('height');
    expect(result).toHaveProperty('fontFamily');
    expect(result).toHaveProperty('fontSize');
  });

  it('handles complete theme override', () => {
    const fullTheme: Partial<WidgetTheme> = {
      primaryColor: '#ff0000',
      backgroundColor: '#000000',
      textColor: '#ffffff',
      botBubbleColor: '#111111',
      userBubbleColor: '#222222',
      position: 'bottom-left',
      borderRadius: 24,
      width: 600,
      height: 900,
      fontFamily: 'Arial, sans-serif',
      fontSize: 20,
    };
    const result = mergeThemes(fullTheme);
    expect(result).toEqual(fullTheme);
  });
});
