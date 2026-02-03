/** App component tests. */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { App } from './App';

describe('App', () => {
  it('renders header with title', () => {
    const { container } = render(<App />);
    expect(container.textContent).toContain('Shopping Assistant Bot');
  });

  it('renders main content area', () => {
    const { container } = render(<App />);
    expect(container.textContent).toContain('Merchant Onboarding');
  });
});
