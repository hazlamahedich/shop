import * as React from 'react';

export interface SuccessCheckmarkProps {
  size?: number;
  isVisible: boolean;
  onComplete?: () => void;
}

/**
 * Animated checkmark component for success feedback
 * Uses SVG stroke animation to draw the checkmark
 * 
 * @param size - Size in pixels (default: 24)
 * @param isVisible - Whether the checkmark is visible
 * @param onComplete - Callback when animation completes (400ms)
 */
export function SuccessCheckmark({ size = 24, isVisible, onComplete }: SuccessCheckmarkProps) {
  React.useEffect(() => {
    if (isVisible && onComplete) {
      const timer = setTimeout(onComplete, 400);
      return () => clearTimeout(timer);
    }
  }, [isVisible, onComplete]);

  if (!isVisible) return null;

  return (
    <svg
      data-testid="success-checkmark"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-label="Success"
      role="img"
    >
      <path
        d="M5 13l4 4L19 7"
        stroke="#22c55e"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeDasharray="24"
        strokeDashoffset={isVisible ? 0 : 24}
        style={{
          animationName: isVisible ? 'checkmark-draw' : 'none',
          animationDuration: '400ms',
          animationTimingFunction: 'ease-out',
          animationFillMode: 'forwards',
        }}
      />
    </svg>
  );
}
