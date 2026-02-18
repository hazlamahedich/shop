import type { WidgetTheme } from '../types/widget';

export const THEME_CONSTRAINTS = {
  borderRadius: { min: 0, max: 24 },
  width: { min: 280, max: 600 },
  height: { min: 400, max: 900 },
  fontSize: { min: 12, max: 20 },
  positions: ['bottom-right', 'bottom-left'] as const,
};

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function sanitizeColor(color: string): string {
  if (/^#[0-9a-fA-F]{6}$/.test(color)) {
    return color;
  }
  return '#6366f1';
}

export function sanitizeFontFamily(font: string): string {
  return font.replace(/[<>"']/g, '');
}

export function validatePosition(position: string): 'bottom-right' | 'bottom-left' {
  if (position === 'bottom-left') return 'bottom-left';
  return 'bottom-right';
}

export function sanitizeTheme(theme: Partial<WidgetTheme>): Partial<WidgetTheme> {
  const sanitized: Partial<WidgetTheme> = {};

  if (theme.primaryColor !== undefined) sanitized.primaryColor = sanitizeColor(theme.primaryColor);
  if (theme.backgroundColor !== undefined) sanitized.backgroundColor = sanitizeColor(theme.backgroundColor);
  if (theme.textColor !== undefined) sanitized.textColor = sanitizeColor(theme.textColor);
  if (theme.botBubbleColor !== undefined) sanitized.botBubbleColor = sanitizeColor(theme.botBubbleColor);
  if (theme.userBubbleColor !== undefined) sanitized.userBubbleColor = sanitizeColor(theme.userBubbleColor);
  if (theme.position !== undefined) sanitized.position = validatePosition(theme.position);
  if (typeof theme.borderRadius === 'number') {
    sanitized.borderRadius = clamp(
      theme.borderRadius,
      THEME_CONSTRAINTS.borderRadius.min,
      THEME_CONSTRAINTS.borderRadius.max
    );
  }
  if (typeof theme.width === 'number') {
    sanitized.width = clamp(theme.width, THEME_CONSTRAINTS.width.min, THEME_CONSTRAINTS.width.max);
  }
  if (typeof theme.height === 'number') {
    sanitized.height = clamp(
      theme.height,
      THEME_CONSTRAINTS.height.min,
      THEME_CONSTRAINTS.height.max
    );
  }
  if (theme.fontFamily !== undefined) sanitized.fontFamily = sanitizeFontFamily(theme.fontFamily);
  if (typeof theme.fontSize === 'number') {
    sanitized.fontSize = clamp(
      theme.fontSize,
      THEME_CONSTRAINTS.fontSize.min,
      THEME_CONSTRAINTS.fontSize.max
    );
  }

  return sanitized;
}
