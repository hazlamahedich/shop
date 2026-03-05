/**
 * @fileoverview Factory functions for retention test data
 * @description Reusable mock data generators with overrides for E2E tests
 */

import { faker } from '@faker-js/faker';

export type SchedulerHealth = {
  status: 'healthy' | 'running' | 'idle' | 'scheduled';
  last_run: string;
  next_run: string;
  jobs_processed: number;
  errors: number;
};

export type AuditLogEntry = {
  id: number;
  sessionId: string;
  merchantId: number;
  retentionPeriodDays: number;
  deletionTrigger: 'manual' | 'auto';
  requestedAt: string;
  completedAt: string;
  conversationsDeleted: number;
  messagesDeleted: number;
  redisKeysCleared: number;
  errorMessage: string | null;
};

export type AuditLogResponse = {
  logs: AuditLogEntry[];
  total: number;
};

export type AuthUser = {
  id: string;
  email: string;
  name: string;
  hasStoreConnected: boolean;
};

export type AuthState = {
  isAuthenticated: boolean;
  merchant: AuthUser;
  sessionExpiresAt: string;
  isLoading: boolean;
  error: string | null;
};

/**
 * Create mock scheduler health data
 */
export const createSchedulerHealth = (overrides: Partial<SchedulerHealth> = {}): SchedulerHealth => ({
  status: 'healthy',
  last_run: new Date(Date.now() - 3600000).toISOString(),
  next_run: new Date(Date.now() + 3600000).toISOString(),
  jobs_processed: faker.number.int({ min: 0, max: 10 }),
  errors: 0,
  ...overrides,
});

/**
 * Create mock audit log entry
 */
export const createAuditLogEntry = (overrides: Partial<AuditLogEntry> = {}): AuditLogEntry => ({
  id: faker.number.int({ min: 1, max: 1000 }),
  sessionId: faker.string.uuid(),
  merchantId: faker.number.int({ min: 1, max: 100 }),
  retentionPeriodDays: 30,
  deletionTrigger: faker.helpers.arrayElement(['manual', 'auto']),
  requestedAt: new Date(Date.now() - faker.number.int({ min: 1000000, max: 10000000 })).toISOString(),
  completedAt: new Date(Date.now() - faker.number.int({ min: 100000, max: 1000000 })).toISOString(),
  conversationsDeleted: faker.number.int({ min: 1, max: 10 }),
  messagesDeleted: faker.number.int({ min: 5, max: 50 }),
  redisKeysCleared: faker.number.int({ min: 1, max: 5 }),
  errorMessage: null,
  ...overrides,
});

/**
 * Create mock audit log response
 */
export const createAuditLogResponse = (overrides: Partial<AuditLogResponse> = {}): AuditLogResponse => {
  const logCount = overrides.logs?.length || faker.number.int({ min: 1, max: 5 });
  return {
    logs: overrides.logs || Array.from({ length: logCount }, () => createAuditLogEntry()),
    total: overrides.total || logCount,
    ...overrides,
  };
};

/**
 * Create mock authenticated user
 */
export const createAuthUser = (overrides: Partial<AuthUser> = {}): AuthUser => ({
  id: faker.string.uuid(),
  email: faker.internet.email(),
  name: faker.person.fullName(),
  hasStoreConnected: true,
  ...overrides,
});

/**
 * Create mock auth state for localStorage
 */
export const createAuthState = (overrides: Partial<AuthState> = {}): AuthState => {
  const merchant = overrides.merchant || createAuthUser();
  return {
    isAuthenticated: true,
    merchant,
    sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
    isLoading: false,
    error: null,
    ...overrides,
  };
};
