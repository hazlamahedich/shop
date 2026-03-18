import * as React from 'react';
import type { SourceCitation as SourceCitationType, WidgetTheme } from '../types/widget';
import { useReducedMotion } from '../hooks/useReducedMotion';
import '../styles/source-citation.css';

export interface SourceCitationProps {
  sources: SourceCitationType[];
  theme: WidgetTheme;
  maxVisible?: number;
}

const DocumentIcon: React.FC<{ type: 'pdf' | 'url' | 'text' }> = ({ type }) => {
  if (type === 'pdf') {
    return (
      <svg viewBox="0 0 24 24" className="source-card__icon" aria-hidden="true">
        <path
          fill="currentColor"
          d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zm-3 9h2v1h-1v1h1v1h-1v2H9v-5zm4 0h1.5c.27 0 .5.22.5.5v2c0 .28-.23.5-.5.5H14v2h-1v-5h1zm3 0h2v1h-1v.5h1v1h-1v.5h1v1h-2v-4zm-6 1v1h.5v-1H12zm4 0v1h.5v-1H16z"
        />
      </svg>
    );
  }

  if (type === 'url') {
    return (
      <svg viewBox="0 0 24 24" className="source-card__icon" aria-hidden="true">
        <path
          fill="currentColor"
          d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z"
        />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" className="source-card__icon" aria-hidden="true">
      <path
        fill="currentColor"
        d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 2l5 5h-5V4zM6 20V4h6v6h6v10H6zm2-8h8v2H8v-2zm0 4h8v2H8v-2z"
      />
    </svg>
  );
};

const formatScore = (score: number): string => {
  return `${Math.round(score * 100)}%`;
};

const getScoreColor = (score: number): string => {
  if (score >= 0.9) return '#22c55e';
  if (score >= 0.7) return '#3b82f6';
  return '#6b7280';
};

export function SourceCitation({
  sources,
  theme,
  maxVisible = 3,
}: SourceCitationProps) {
  const [expanded, setExpanded] = React.useState(false);
  const reducedMotion = useReducedMotion();

  if (!sources || sources.length === 0) {
    return null;
  }

  const visibleSources = expanded ? sources : sources.slice(0, maxVisible);
  const hasMore = sources.length > maxVisible;
  const remainingCount = sources.length - maxVisible;

  const handleSourceClick = (source: SourceCitationType) => {
    if (source.url) {
      window.open(source.url, '_blank', 'noopener,noreferrer');
    }
  };

  const handleToggle = () => {
    setExpanded(!expanded);
  };

  return (
    <div
      data-testid="source-citation"
      className={`source-citation ${reducedMotion ? 'source-citation--reduced-motion' : ''}`}
      style={{ marginTop: 8 }}
    >
      <div
        className="source-citation__header"
        style={{
          fontSize: 11,
          fontWeight: 600,
          color: theme.textColor,
          opacity: 0.7,
          marginBottom: 6,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}
      >
        Sources
      </div>
      <div className="source-citation__list" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {visibleSources.map((source, index) => {
          const isClickable = !!source.url;
          return (
            <button
              key={`${source.documentId}-${index}`}
              data-testid="source-card"
              className={`source-card ${isClickable ? 'source-card--clickable' : ''}`}
              onClick={() => handleSourceClick(source)}
              disabled={!isClickable}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '6px 8px',
                borderRadius: 6,
                cursor: isClickable ? 'pointer' : 'default',
                transition: reducedMotion ? 'none' : 'background-color 150ms ease',
                border: 'none',
                background: 'transparent',
                width: '100%',
                textAlign: 'left',
              }}
              aria-label={`${source.title} - ${formatScore(source.relevanceScore)} relevance`}
            >
              <DocumentIcon type={source.documentType} />
              <span
                className="source-card__title"
                style={{
                  flex: 1,
                  fontSize: 12,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                  color: theme.textColor,
                }}
                title={source.title}
              >
                {source.title}
              </span>
              <span
                className="source-card__score"
                style={{
                  fontSize: 10,
                  padding: '2px 6px',
                  borderRadius: 4,
                  background: getScoreColor(source.relevanceScore),
                  color: 'white',
                  flexShrink: 0,
                }}
              >
                {formatScore(source.relevanceScore)}
              </span>
            </button>
          );
        })}
      </div>
      {hasMore && (
        <button
          data-testid="source-toggle"
          className="source-citation__toggle"
          onClick={handleToggle}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 4,
            width: '100%',
            padding: '6px 8px',
            marginTop: 6,
            border: 'none',
            borderRadius: 6,
            background: 'transparent',
            color: theme.primaryColor,
            fontSize: 11,
            fontWeight: 500,
            cursor: 'pointer',
            transition: reducedMotion ? 'none' : 'background-color 150ms ease',
          }}
          aria-expanded={expanded}
          aria-label={expanded ? 'Show fewer sources' : `Show ${remainingCount} more sources`}
        >
          {expanded ? (
            <>
              <span>Show less</span>
              <svg width="12" height="12" viewBox="0 0 24 24" aria-hidden="true">
                <path fill="currentColor" d="M7.41 15.41L12 10.83l4.59 4.58L18 14l-6-6-6 6z" />
              </svg>
            </>
          ) : (
            <>
              <span>View {remainingCount} more</span>
              <svg width="12" height="12" viewBox="0 0 24 24" aria-hidden="true">
                <path fill="currentColor" d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6z" />
              </svg>
            </>
          )}
        </button>
      )}
    </div>
  );
}
