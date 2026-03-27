import * as React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { SourceCitation } from './SourceCitation';
import type { SourceCitation as SourceCitationType, WidgetTheme } from '../types/widget';

const mockTheme: WidgetTheme = {
  primaryColor: '#6366f1',
  backgroundColor: '#ffffff',
  textColor: '#1f2937',
  botBubbleColor: '#f3f4f6',
  userBubbleColor: '#6366f1',
  position: 'bottom-right',
  borderRadius: 16,
  width: 380,
  height: 600,
  fontFamily: 'Inter, sans-serif',
  fontSize: 14,
};

const mockSources: SourceCitationType[] = [
  {
    documentId: 1,
    title: 'Product Manual.pdf',
    documentType: 'pdf',
    relevanceScore: 0.95,
    chunkIndex: 5,
  },
  {
    documentId: 2,
    title: 'FAQ Page - Returns',
    documentType: 'url',
    relevanceScore: 0.88,
    url: 'https://example.com/faq/returns',
  },
  {
    documentId: 3,
    title: 'Warranty Information.txt',
    documentType: 'text',
    relevanceScore: 0.82,
    chunkIndex: 2,
  },
];

describe('SourceCitation', () => {
  let windowOpenSpy: any;

  beforeEach(() => {
    windowOpenSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
  });

  afterEach(() => {
    windowOpenSpy.mockRestore();
  });

  it('should render the top source only', () => {
    render(<SourceCitation sources={mockSources} theme={mockTheme} />);

    expect(screen.getByTestId('source-citation')).toBeInTheDocument();
    expect(screen.getByText('Source')).toBeInTheDocument();
    expect(screen.getAllByTestId('source-card')).toHaveLength(1);
  });

  it('should display the source with highest relevance score', () => {
    render(<SourceCitation sources={mockSources} theme={mockTheme} />);

    const sourceCard = screen.getByTestId('source-card');
    expect(sourceCard).toHaveTextContent('Product Manual.pdf');
    expect(sourceCard).toHaveTextContent('95%');
  });

  it('should open URL in new tab when clickable source clicked', () => {
    const sourcesWithUrlFirst: SourceCitationType[] = [
      {
        documentId: 2,
        title: 'FAQ Page - Returns',
        documentType: 'url',
        relevanceScore: 0.95,
        url: 'https://example.com/faq/returns',
      },
      {
        documentId: 1,
        title: 'Product Manual.pdf',
        documentType: 'pdf',
        relevanceScore: 0.80,
      },
    ];

    render(<SourceCitation sources={sourcesWithUrlFirst} theme={mockTheme} />);

    const sourceCard = screen.getByTestId('source-card');
    fireEvent.click(sourceCard);

    expect(windowOpenSpy).toHaveBeenCalledWith(
      'https://example.com/faq/returns',
      '_blank',
      'noopener,noreferrer'
    );
  });

  it('should not open new tab for source without URL', () => {
    render(<SourceCitation sources={[mockSources[0]]} theme={mockTheme} />);

    const sourceCard = screen.getByTestId('source-card');
    fireEvent.click(sourceCard);

    expect(windowOpenSpy).not.toHaveBeenCalled();
  });

  it('should not render when sources array is empty', () => {
    const { container } = render(<SourceCitation sources={[]} theme={mockTheme} />);
    expect(container.firstChild).toBeNull();
  });

  it('should not render when sources is undefined', () => {
    const { container } = render(
      <SourceCitation sources={undefined as any} theme={mockTheme} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('should have correct aria-label for accessibility', () => {
    render(<SourceCitation sources={[mockSources[0]]} theme={mockTheme} />);

    const sourceCard = screen.getByTestId('source-card');
    expect(sourceCard).toHaveAttribute('aria-label', 'Product Manual.pdf - 95% relevance');
  });

  it('should display filename instead of title when available', () => {
    const sourceWithFilename: SourceCitationType = {
      ...mockSources[0],
      filename: 'actual_file_name.pdf',
      title: 'Short Summary Title',
    };
    render(<SourceCitation sources={[sourceWithFilename]} theme={mockTheme} />);

    const sourceCard = screen.getByTestId('source-card');
    expect(sourceCard).toHaveTextContent('actual_file_name.pdf');
    expect(sourceCard).not.toHaveTextContent('Short Summary Title');
    expect(sourceCard).toHaveAttribute('aria-label', 'actual_file_name.pdf - 95% relevance');
  });

  it('should select the highest scoring source from duplicates', () => {
    const duplicateSources: SourceCitationType[] = [
      {
        documentId: 1,
        title: 'Resume',
        filename: 'resume.pdf',
        documentType: 'pdf',
        relevanceScore: 0.59,
        chunkIndex: 1,
      },
      {
        documentId: 1,
        title: 'Resume',
        filename: 'resume.pdf',
        documentType: 'pdf',
        relevanceScore: 0.95,
        chunkIndex: 2,
      },
      {
        documentId: 2,
        title: 'Other Doc',
        filename: 'other.pdf',
        documentType: 'pdf',
        relevanceScore: 0.80,
      },
    ];

    render(<SourceCitation sources={duplicateSources} theme={mockTheme} />);

    const sourceCards = screen.getAllByTestId('source-card');
    expect(sourceCards).toHaveLength(1);
    expect(sourceCards[0]).toHaveTextContent('95%');
  });
});
