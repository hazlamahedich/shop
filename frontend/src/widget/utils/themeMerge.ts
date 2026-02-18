import type { WidgetTheme } from '../types/widget';
import { DEFAULT_THEME } from './themeDefaults';
import { sanitizeTheme } from './themeValidation';

export function mergeThemes(
  merchantTheme?: Partial<WidgetTheme>,
  embedOverrides?: Partial<WidgetTheme>
): WidgetTheme {
  const sanitizedMerchant = merchantTheme ? sanitizeTheme(merchantTheme) : {};
  const sanitizedEmbed = embedOverrides ? sanitizeTheme(embedOverrides) : {};

  return {
    ...DEFAULT_THEME,
    ...sanitizedMerchant,
    ...sanitizedEmbed,
  } as WidgetTheme;
}
