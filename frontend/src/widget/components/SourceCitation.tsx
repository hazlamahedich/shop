import * as React from 'react';
import type { SourceCitation as SourceCitationType, WidgetTheme } from '../types/widget';
import { useReducedMotion } from '../hooks/useReducedMotion';
import '../styles/source-citation.css';

export interface SourceCitationProps {
  sources: SourceCitationType[];
  theme: WidgetTheme;
  maxVisible?: number;
}

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
}: SourceCitationProps) {
  const reducedMotion = useReducedMotion();

  if (!sources || sources.length === 0) {
    return null;
  }

  const topSource = React.useMemo(() => {
    return sources.reduce((best, current) => 
      current.relevanceScore > best.relevanceScore ? current : best
    , sources[0]);
  }, [sources]);

  const handleSourceClick = () => {
    if (topSource.url) {
      window.open(topSource.url, '_blank', 'noopener,noreferrer');
    }
  };

  const isClickable = !!topSource.url;

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
          opacity: 0.85,
          marginBottom: 6,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}
      >
        Source
      </div>
      <button
        data-testid="source-card"
        className={`source-card ${isClickable ? 'source-card--clickable' : ''}`}
        onClick={handleSourceClick}
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
        aria-label={`${topSource.filename || topSource.title} - ${formatScore(topSource.relevanceScore)} relevance`}
      >
        <span
          className="source-card__title"
          style={{
            flex: 1,
            fontSize: 12,
            fontWeight: 500,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            color: theme.textColor,
          }}
          title={topSource.filename || topSource.title}
        >
          {topSource.filename || topSource.title}
        </span>
        <span
          className="source-card__score"
          style={{
            fontSize: 10,
            padding: '2px 6px',
            borderRadius: 4,
            background: getScoreColor(topSource.relevanceScore),
            color: 'white',
            flexShrink: 0,
          }}
        >
          {formatScore(topSource.relevanceScore)}
        </span>
      </button>
    </div>
  );
}
