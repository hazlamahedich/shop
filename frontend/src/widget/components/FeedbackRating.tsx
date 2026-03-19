import * as React from 'react';
import type { WidgetTheme, FeedbackRatingValue } from '../types/widget';
import { useReducedMotion } from '../hooks/useReducedMotion';

export interface FeedbackRatingProps {
  messageId: string;
  feedbackEnabled?: boolean;
  userRating?: FeedbackRatingValue;
  theme: WidgetTheme;
  onSubmit: (messageId: string, rating: FeedbackRatingValue, comment?: string) => Promise<void>;
}

const ThumbsUpIcon: React.FC<{ filled: boolean; color: string }> = ({ filled, color }) => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill={filled ? color : 'none'}
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
  </svg>
);

const ThumbsDownIcon: React.FC<{ filled: boolean; color: string }> = ({ filled, color }) => (
  <svg
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill={filled ? color : 'none'}
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17" />
  </svg>
);

export function FeedbackRating({
  messageId,
  feedbackEnabled = true,
  userRating,
  theme,
  onSubmit,
}: FeedbackRatingProps) {
  const [rating, setRating] = React.useState<FeedbackRatingValue | null>(userRating || null);
  const [showCommentForm, setShowCommentForm] = React.useState(false);
  const [comment, setComment] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [announcement, setAnnouncement] = React.useState('');
  const reducedMotion = useReducedMotion();
  const commentInputRef = React.useRef<HTMLTextAreaElement>(null);

  React.useEffect(() => {
    setRating(userRating || null);
  }, [userRating]);

  React.useEffect(() => {
    if (showCommentForm && commentInputRef.current) {
      commentInputRef.current.focus();
    }
  }, [showCommentForm]);

  const handleRatingClick = async (newRating: FeedbackRatingValue) => {
    if (isSubmitting) return;

    if (newRating === 'negative' && rating !== 'negative') {
      setRating(newRating);
      setShowCommentForm(true);
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(messageId, newRating);
      setRating(newRating);
      setShowCommentForm(false);
      setComment('');
      setAnnouncement(`Feedback submitted: ${newRating === 'positive' ? 'Helpful' : 'Not helpful'}`);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      setAnnouncement('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCommentSubmit = async () => {
    if (isSubmitting || !rating) return;

    setIsSubmitting(true);
    try {
      await onSubmit(messageId, rating, comment || undefined);
      setShowCommentForm(false);
      setComment('');
      setAnnouncement('Feedback submitted with comment');
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      setAnnouncement('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDismissComment = () => {
    setShowCommentForm(false);
    setComment('');
  };

  const handleKeyDown = (e: React.KeyboardEvent, ratingValue: FeedbackRatingValue) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleRatingClick(ratingValue);
    }
  };

  if (!feedbackEnabled) {
    return null;
  }

  const isDarkMode = theme.mode === 'dark';
  const buttonBaseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: '44px',
    minHeight: '44px',
    padding: '8px',
    border: '1px solid transparent',
    borderRadius: '22px',
    backgroundColor: 'transparent',
    cursor: isSubmitting ? 'wait' : 'pointer',
    transition: reducedMotion ? 'none' : 'background-color 150ms ease, transform 100ms ease',
    opacity: isSubmitting ? 0.5 : 1,
  };

  return (
    <div
      data-testid="feedback-rating"
      role="group"
      aria-label="Rate this response"
      className={`feedback-rating${isDarkMode ? ' feedback-rating--dark' : ''}`}
      style={{
        display: 'flex',
        gap: '8px',
        marginTop: '8px',
        padding: '0 12px',
        alignItems: 'flex-start',
        flexShrink: 0,
      }}
    >
      <button
        data-testid="feedback-up"
        type="button"
        role="button"
        aria-label="Rate as helpful"
        aria-pressed={rating === 'positive'}
        disabled={isSubmitting}
        onClick={() => handleRatingClick('positive')}
        onKeyDown={(e) => handleKeyDown(e, 'positive')}
        className={`feedback-button${rating === 'positive' ? ' feedback-button--selected' : ''}`}
        style={{
          ...buttonBaseStyle,
          backgroundColor: rating === 'positive' ? theme.primaryColor : 'transparent',
          color: rating === 'positive' ? '#fff' : theme.textColor,
        }}
      >
        <ThumbsUpIcon filled={rating === 'positive'} color={rating === 'positive' ? '#fff' : theme.textColor} />
      </button>

      <button
        data-testid="feedback-down"
        type="button"
        role="button"
        aria-label="Rate as not helpful"
        aria-pressed={rating === 'negative'}
        disabled={isSubmitting}
        onClick={() => handleRatingClick('negative')}
        onKeyDown={(e) => handleKeyDown(e, 'negative')}
        className={`feedback-button${rating === 'negative' ? ' feedback-button--selected' : ''}`}
        style={{
          ...buttonBaseStyle,
          backgroundColor: rating === 'negative' ? theme.primaryColor : 'transparent',
          color: rating === 'negative' ? '#fff' : theme.textColor,
        }}
      >
        <ThumbsDownIcon filled={rating === 'negative'} color={rating === 'negative' ? '#fff' : theme.textColor} />
      </button>

      {showCommentForm && (
        <div
          data-testid="feedback-comment-form"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            padding: '8px',
            backgroundColor: isDarkMode ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
            borderRadius: '12px',
            flex: 1,
            maxWidth: '300px',
          }}
        >
          <label htmlFor={`feedback-comment-${messageId}`} style={{ fontSize: '12px', color: theme.textColor }}>
            Tell us how we can improve (optional):
          </label>
          <textarea
            ref={commentInputRef}
            id={`feedback-comment-${messageId}`}
            data-testid="feedback-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value.slice(0, 500))}
            placeholder="What would have been more helpful?"
            maxLength={500}
            rows={2}
            style={{
              width: '100%',
              padding: '8px',
              border: `1px solid ${isDarkMode ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)'}`,
              borderRadius: '8px',
              backgroundColor: isDarkMode ? 'rgba(0, 0, 0, 0.2)' : '#fff',
              color: theme.textColor,
              fontFamily: theme.fontFamily,
              fontSize: '14px',
              resize: 'none',
            }}
          />
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <button
              type="button"
              onClick={handleDismissComment}
              disabled={isSubmitting}
              style={{
                padding: '6px 12px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: 'transparent',
                color: theme.textColor,
                fontSize: '14px',
                cursor: 'pointer',
                opacity: 0.7,
              }}
            >
              Skip
            </button>
            <button
              type="button"
              onClick={handleCommentSubmit}
              disabled={isSubmitting}
              style={{
                padding: '6px 12px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: theme.primaryColor,
                color: '#fff',
                fontSize: '14px',
                fontWeight: 500,
                cursor: 'pointer',
              }}
            >
              Submit
            </button>
          </div>
          <span style={{ fontSize: '11px', color: theme.textColor, opacity: 0.6 }}>
            {comment.length}/500 characters
          </span>
        </div>
      )}

      <div aria-live="polite" aria-atomic="true" style={{ position: 'absolute', left: '-9999px' }}>
        {announcement}
      </div>
    </div>
  );
}
