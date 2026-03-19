import { faker } from '@faker-js/faker';

export type ContactOptionType = 'phone' | 'email' | 'custom';

export interface ContactOption {
  type: ContactOptionType;
  label: string;
  value: string;
  icon?: string;
}

export interface BusinessHoursConfig {
  timezone?: string;
  hours?: Record<string, { open: string; close: string } | null>;
}

const DEFAULT_ICONS: Record<ContactOptionType, string> = {
  phone: '📞',
  email: '✉️',
  custom: '📅',
};

const DEFAULT_LABELS: Record<ContactOptionType, string> = {
  phone: 'Call Support',
  email: 'Email Support',
  custom: 'Schedule a Call',
};

export function createContactOption(overrides: Partial<ContactOption> = {}): ContactOption {
  const types: ContactOptionType[] = ['phone', 'email', 'custom'];
  const type = overrides.type || types[Math.floor(Math.random() * types.length)];

  const valueDefaults: Record<ContactOptionType, string> = {
    phone: faker.phone.number(),
    email: faker.internet.email(),
    custom: faker.internet.url(),
  };

  return {
    type,
    label: DEFAULT_LABELS[type],
    value: valueDefaults[type],
    icon: DEFAULT_ICONS[type],
    ...overrides,
  };
}

export function createPhoneOption(overrides: Partial<ContactOption> = {}): ContactOption {
  return createContactOption({ type: 'phone', ...overrides });
}

export function createEmailOption(overrides: Partial<ContactOption> = {}): ContactOption {
  return createContactOption({ type: 'email', ...overrides });
}

export function createCustomOption(overrides: Partial<ContactOption> = {}): ContactOption {
  return createContactOption({ type: 'custom', ...overrides });
}

export function createContactOptions(count: number = 3): ContactOption[] {
  return Array.from({ length: count }, () => createContactOption());
}

export function createDefaultContactOptions(): ContactOption[] {
  return [
    createPhoneOption({ value: '+1-555-123-4567' }),
    createEmailOption({ value: 'support@example.com' }),
    createCustomOption({ label: 'Schedule a Call', value: 'https://calendly.com/support' }),
  ];
}

export function createBusinessHours(overrides: Partial<BusinessHoursConfig> = {}): BusinessHoursConfig {
  return {
    timezone: 'America/New_York',
    hours: {
      monday: { open: '09:00', close: '17:00' },
      tuesday: { open: '09:00', close: '17:00' },
      wednesday: { open: '09:00', close: '17:00' },
      thursday: { open: '09:00', close: '17:00' },
      friday: { open: '09:00', close: '17:00' },
    },
    ...overrides,
  };
}

export const createStandardBusinessHours = createBusinessHours;
