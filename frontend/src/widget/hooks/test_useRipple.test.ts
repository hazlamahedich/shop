/**
 * @vitest-environment jsdom
 * 
 * Story 9-8: Microinteractions & Animations
 * Test ID: 9.8-UNIT
 * Priority: P2 (Medium - UI Enhancement)
 *
 * Acceptance Criteria Covered:
 * - AC3: Button ripple effect on click
 *
 * Related Files:
 * - Source: frontend/src/widget/hooks/useRipple.ts
 * - CSS: frontend/src/widget/styles/animations.css
 * - E2E: frontend/tests/e2e/story-9-8-microinteractions.spec.ts
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useRipple } from './useRipple';

/**
 * Factory function to create mock click events for ripple testing
 * Reduces code duplication and allows easy customization via overrides
 */
function createMockClickEvent(overrides: Partial<{
  left: number;
  top: number;
  width: number;
  height: number;
  clientX: number;
  clientY: number;
}> = {}): React.MouseEvent<HTMLElement> {
  const defaults = {
    left: 0,
    top: 0,
    width: 100,
    height: 100,
    clientX: 50,
    clientY: 50,
  };
  const config = { ...defaults, ...overrides };

  return {
    currentTarget: {
      getBoundingClientRect: () => ({
        left: config.left,
        top: config.top,
        width: config.width,
        height: config.height,
      }),
    },
    clientX: config.clientX,
    clientY: config.clientY,
  } as React.MouseEvent<HTMLElement>;
}

describe('useRipple [9.8-UNIT] [P2]', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('[9.8-UNIT-001] [P2] should start with empty ripples array', () => {
    // Given: A useRipple hook is initialized
    const { result } = renderHook(() => useRipple());

    // When: No clicks have occurred
    // (no action needed - checking initial state)

    // Then: The ripples array should be empty
    expect(result.current.ripples).toEqual([]);
  });

  it('[9.8-UNIT-002] [P2] should create a ripple on click', () => {
    // Given: A useRipple hook is initialized
    const { result } = renderHook(() => useRipple());
    const mockEvent = createMockClickEvent({ clientX: 50, clientY: 50 });

    // When: createRipple is called with a click event
    act(() => {
      result.current.createRipple(mockEvent);
    });

    // Then: A ripple should be added at the click position
    expect(result.current.ripples).toHaveLength(1);
    expect(result.current.ripples[0].x).toBe(50);
    expect(result.current.ripples[0].y).toBe(50);
    expect(result.current.ripples[0].id).toBeDefined();
  });

  it('[9.8-UNIT-003] [P2] should clean up ripple after 600ms', () => {
    // Given: A ripple has been created
    const { result } = renderHook(() => useRipple());
    const mockEvent = createMockClickEvent({ clientX: 50, clientY: 50 });

    act(() => {
      result.current.createRipple(mockEvent);
    });
    expect(result.current.ripples).toHaveLength(1);

    // When: 600ms have passed (animation duration)
    act(() => {
      vi.advanceTimersByTime(600);
    });

    // Then: The ripple should be removed from the array
    expect(result.current.ripples).toHaveLength(0);
  });

  it('[9.8-UNIT-004] [P2] should handle multiple ripples', () => {
    // Given: A useRipple hook is initialized
    const { result } = renderHook(() => useRipple());
    const mockEvent1 = createMockClickEvent({ clientX: 25, clientY: 25 });
    const mockEvent2 = createMockClickEvent({ clientX: 75, clientY: 75 });

    // When: Multiple ripples are created in sequence
    act(() => {
      result.current.createRipple(mockEvent1);
    });

    act(() => {
      result.current.createRipple(mockEvent2);
    });

    // Then: Both ripples should exist with correct positions
    expect(result.current.ripples).toHaveLength(2);
    expect(result.current.ripples[0].x).toBe(25);
    expect(result.current.ripples[0].y).toBe(25);
    expect(result.current.ripples[1].x).toBe(75);
    expect(result.current.ripples[1].y).toBe(75);
  });

  it('[9.8-UNIT-005] [P2] should clean up ripples individually', () => {
    // Given: Two ripples are created at different times
    const { result } = renderHook(() => useRipple());
    const mockEvent1 = createMockClickEvent({ clientX: 25, clientY: 25 });

    // Create first ripple
    act(() => {
      result.current.createRipple(mockEvent1);
    });

    // Wait 300ms (half the animation time)
    act(() => {
      vi.advanceTimersByTime(300);
    });

    const mockEvent2 = createMockClickEvent({ clientX: 75, clientY: 75 });

    // Create second ripple
    act(() => {
      result.current.createRipple(mockEvent2);
    });

    expect(result.current.ripples).toHaveLength(2);

    // When: Another 300ms passes (total 600ms for first ripple)
    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Then: First ripple should be removed, second should remain
    expect(result.current.ripples).toHaveLength(1);
    expect(result.current.ripples[0].x).toBe(75);

    // When: Another 300ms passes (total 600ms for second ripple)
    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Then: Both ripples should be removed
    expect(result.current.ripples).toHaveLength(0);
  });

  it('[9.8-UNIT-006] [P2] should calculate ripple position relative to element', () => {
    // Given: A useRipple hook and a click on an offset element
    const { result } = renderHook(() => useRipple());
    const mockEvent = createMockClickEvent({
      left: 100,
      top: 100,
      width: 200,
      height: 200,
      clientX: 150, // 50px from left edge (150 - 100)
      clientY: 175, // 75px from top edge (175 - 100)
    });

    // When: createRipple is called
    act(() => {
      result.current.createRipple(mockEvent);
    });

    // Then: Ripple position should be relative to element bounds
    expect(result.current.ripples[0].x).toBe(50);
    expect(result.current.ripples[0].y).toBe(75);
  });
});
