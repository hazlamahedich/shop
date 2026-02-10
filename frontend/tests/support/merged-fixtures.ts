import { mergeTests } from '@playwright/test';
import { test as apiRequestFixture } from './fixtures/api-request';
import { test as authFixture } from './fixtures/auth-session';
import { test as interceptFixture } from './fixtures/intercept-network-call';

export const test = mergeTests(apiRequestFixture, authFixture, interceptFixture);
export { expect } from '@playwright/test';
