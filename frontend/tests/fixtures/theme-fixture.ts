/**
 * Theme Test Fixtures
 *
 * Story 5-5: Theme Customization System
 * Factory functions and fixtures for theme-related testing
 *
 * @tags fixture theme widget
 */

import type { WidgetTheme } from '@/widget/types/widget';
export { DEFAULT_THEME } from '@/widget/utils/themeDefaults';
export { THEME_CONSTRAINTS } from '@/widget/utils/themeValidation';
export { sanitizeTheme, clamp, sanitizeColor, sanitizeFontFamily, validatePosition } from '@/widget/utils/themeValidation';

export function createTheme(overrides: Partial<WidgetTheme> = {}): WidgetTheme {
  const { DEFAULT_THEME } = require('@/widget/utils/themeDefaults');
  return {
    ...DEFAULT_THEME,
    ...overrides,
  };
}

export function createMinimalTheme(): WidgetTheme {
  const { THEME_CONSTRAINTS } = require('@/widget/utils/themeValidation');
  return createTheme({
    borderRadius: THEME_CONSTRAINTS.borderRadius.min,
    width: THEME_CONSTRAINTS.width.min,
    height: THEME_CONSTRAINTS.height.min,
    fontSize: THEME_CONSTRAINTS.fontSize.min,
  });
}

export function createMaximalTheme(): WidgetTheme {
  const { THEME_CONSTRAINTS } = require('@/widget/utils/themeValidation');
  return createTheme({
    borderRadius: THEME_CONSTRAINTS.borderRadius.max,
    width: THEME_CONSTRAINTS.width.max,
    height: THEME_CONSTRAINTS.height.max,
    fontSize: THEME_CONSTRAINTS.fontSize.max,
  });
}

export function createInvalidColorTheme(): WidgetTheme {
  return createTheme({
    primaryColor: 'javascript:alert(1)',
    backgroundColor: 'red',
    textColor: 'rgb(255,0,0)',
  });
}

export function createXssTheme(): WidgetTheme {
  return createTheme({
    fontFamily: '<script>alert("xss")</script>',
    primaryColor: 'expression(alert(1))',
  });
}

export function createOutOfBoundsTheme(): WidgetTheme {
  return createTheme({
    borderRadius: 100,
    width: 1000,
    height: 2000,
    fontSize: 50,
  });
}

export function createBottomLeftTheme(): WidgetTheme {
  return createTheme({
    position: 'bottom-left',
  });
}

export function createBottomRightTheme(): WidgetTheme {
  return createTheme({
    position: 'bottom-right',
  });
}

export function createDarkTheme(): WidgetTheme {
  return createTheme({
    primaryColor: '#8b5cf6',
    backgroundColor: '#1f2937',
    textColor: '#f9fafb',
    botBubbleColor: '#374151',
    userBubbleColor: '#8b5cf6',
  });
}

export function createLightTheme(): WidgetTheme {
  return createTheme({
    primaryColor: '#6366f1',
    backgroundColor: '#ffffff',
    textColor: '#1f2937',
    botBubbleColor: '#f3f4f6',
    userBubbleColor: '#6366f1',
  });
}

export function isValidHexColor(color: string): boolean {
  return /^#[0-9a-fA-F]{6}$/.test(color);
}
