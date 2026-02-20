/**
 * Widget Settings Validation Utilities
 *
 * Story 5.6: Merchant Widget Settings UI
 */



export function validateBotName(name: string): string | null {
  if (typeof name !== 'string') return 'Bot name is required';
  if (!name || !name.trim()) return 'Bot name is required';
  if (name.length > 50) return 'Max 50 characters';
  return null;
}

export function validateWelcomeMessage(msg: string): string | null {
  if (typeof msg !== 'string') return 'Welcome message is required';
  if (!msg || !msg.trim()) return 'Welcome message is required';
  if (msg.length > 500) return 'Max 500 characters';
  return null;
}

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
  botName?: string;
  welcomeMessage?: string;
  primaryColor?: string;
  position?: string;
}

export function validateWidgetSettings(values: {
  botName: string;
  welcomeMessage: string;
  primaryColor: string;
  position: string;
}): WidgetSettingsErrors {
  const errors: WidgetSettingsErrors = {};

  const botNameError = validateBotName(values.botName);
  if (botNameError) errors.botName = botNameError;

  const msgError = validateWelcomeMessage(values.welcomeMessage);
  if (msgError) errors.welcomeMessage = msgError;

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


