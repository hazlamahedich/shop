import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { KnowledgeEffectivenessWidget } from './KnowledgeEffectivenessWidget';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('KnowledgeEffectivenessWidget', () => {
  it('renders widget container with test id', () => {
    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <KnowledgeEffectivenessWidget />
      </Wrapper>
    );

    expect(screen.getByTestId('knowledge-effectiveness-widget')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    const Wrapper = createWrapper();
    render(
      <Wrapper>
        <KnowledgeEffectivenessWidget />
      </Wrapper>
    );

    expect(screen.getByText('Knowledge Effectiveness')).toBeInTheDocument();
  });
});
