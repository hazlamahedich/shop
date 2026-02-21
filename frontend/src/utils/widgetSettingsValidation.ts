/**
 * Widget Settings Validation Utilities
 *
 * Story 5.6: Merchant Widget Settings UI
 *
 * Note: Only validates appearance settings.
 * Bot name and welcome message are validated in their respective config pages.
 */

export function validatePrimaryColor(color: string): string | null {
  if (typeof color !== 'string') return 'Invalid color format. Use #RRGGBB';
  if (!/^#[0-9a-fA-F]{6}$/.test(color)) {
    return 'Invalid color format. Use #RRGGBB';
  }
  return null;
}

export function validateWidgetPosition(position: string): string | null {
  if (typeof position !== 'string') return 'Invalid position';
  if (position !== 'bottom-right' && position !== 'bottom-left') {
    return 'Invalid position';
  }
  return null;
}

export interface WidgetSettingsErrors {
  primaryColor?: string;
  position?: string;
}

export function validateWidgetSettings(values: {
  primaryColor: string;
  position: string;
}): WidgetSettingsErrors {
  const errors: WidgetSettingsErrors = {};

  const colorError = validatePrimaryColor(values.primaryColor);
  if (colorError) errors.primaryColor = colorError;

  if (values.position !== 'bottom-right' && values.position !== 'bottom-left') {
    errors.position = 'Invalid position';
  }

  return errors;
}

export function hasValidationErrors(errors: WidgetSettingsErrors): boolean {
  return Object.keys(errors).length > 0;
}
