import * as React from 'react';

interface RippleProps {
  x: number;
  y: number;
  id: number;
}

/**
 * Hook to create ripple effect on button clicks
 * Creates a visual ripple animation emanating from click point
 * 
 * @returns {Object} { ripples, createRipple } - ripple elements and trigger function
 * 
 * @example
 * const { ripples, createRipple } = useRipple();
 * 
 * <button onClick={createRipple}>
 *   Click me
 *   {ripples.map(ripple => (
 *     <span key={ripple.id} style={{ left: ripple.x, top: ripple.y }} />
 *   ))}
 * </button>
 */
export function useRipple() {
  const [ripples, setRipples] = React.useState<RippleProps[]>([]);

  const createRipple = (event: React.MouseEvent<HTMLElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const id = Date.now();
    
    setRipples(prev => [...prev, { x, y, id }]);
    
    // Remove ripple after animation completes (600ms)
    setTimeout(() => {
      setRipples(prev => prev.filter(r => r.id !== id));
    }, 600);
  };

  return { ripples, createRipple };
}
