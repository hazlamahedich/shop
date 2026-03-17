import * as React from 'react';

/**
 * Hook to detect if user prefers reduced motion
 * Used to disable or reduce animations for accessibility
 * 
 * @returns {boolean} true if user prefers reduced motion
 * 
 * @example
 * const reducedMotion = useReducedMotion();
 * const transition = reducedMotion ? 'none' : 'transform 200ms ease';
 */
export function useReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = React.useState(false);

  React.useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    // Set initial value
    setPrefersReducedMotion(mediaQuery.matches);

    // Listen for changes
    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    mediaQuery.addEventListener('change', handleChange);

    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }, []);

  return prefersReducedMotion;
}
