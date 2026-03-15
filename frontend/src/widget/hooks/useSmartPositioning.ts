import * as React from 'react';
import type { WidgetPosition, PositioningConfig } from '../types/widget';
import { DEFAULT_POSITIONING_CONFIG } from '../types/widget';
import {
  detectImportantElements,
  getElementBounds,
  findOptimalPosition,
  constrainToViewport,
  isMobileDevice,
  getMobilePosition,
  debounce,
  type BoundingBox,
} from '../utils/smartPositioning';
import { getStoredPosition, setStoredPosition } from '../utils/storage';

interface UseSmartPositioningOptions {
  merchantId: string;
  widgetSize: { width: number; height: number };
  config?: Partial<PositioningConfig>;
  enabled?: boolean;
}

interface UseSmartPositioningReturn {
  position: WidgetPosition;
  updatePosition: (position: WidgetPosition) => void;
  reposition: () => void;
  isMobile: boolean;
}

const RESIZE_DEBOUNCE_MS = 250;

export function useSmartPositioning({
  merchantId,
  widgetSize,
  config,
  enabled = true,
}: UseSmartPositioningOptions): UseSmartPositioningReturn {
  const mergedConfig: PositioningConfig = React.useMemo(
    () => ({
      ...DEFAULT_POSITIONING_CONFIG,
      ...config,
    }),
    [config]
  );
  
  const [position, setPosition] = React.useState<WidgetPosition>(() => {
    if (typeof window === 'undefined') {
      return { x: 0, y: 0 };
    }
    
    const stored = getStoredPosition(merchantId);
    if (stored) {
      return constrainToViewport(stored, widgetSize, mergedConfig);
    }
    
    if (isMobileDevice()) {
      return getMobilePosition();
    }
    
    const elements = detectImportantElements(mergedConfig.avoidElements);
    const bounds = elements.map(getElementBounds);
    const optimal = findOptimalPosition(bounds, widgetSize, mergedConfig);
    return optimal;
  });
  
  const [isMobile, setIsMobile] = React.useState(() => isMobileDevice());
  
  const updatePosition = React.useCallback(
    (newPosition: WidgetPosition) => {
      const constrained = constrainToViewport(newPosition, widgetSize, mergedConfig);
      setPosition(constrained);
      setStoredPosition(merchantId, constrained);
    },
    [merchantId, widgetSize, mergedConfig]
  );
  
  const reposition = React.useCallback(() => {
    if (!enabled || typeof window === 'undefined') return;
    
    const mobile = isMobileDevice();
    setIsMobile(mobile);
    
    if (mobile) {
      const mobilePos = getMobilePosition();
      setPosition(mobilePos);
      return;
    }
    
    const elements = detectImportantElements(mergedConfig.avoidElements);
    const bounds: BoundingBox[] = elements.map(getElementBounds);
    const optimal = findOptimalPosition(bounds, widgetSize, mergedConfig);
    const constrained = constrainToViewport(optimal, widgetSize, mergedConfig);
    setPosition(constrained);
  }, [enabled, mergedConfig, widgetSize]);
  
  React.useEffect(() => {
    if (!enabled || typeof window === 'undefined') return;
    
    const handleResize = debounce(() => {
      reposition();
    }, RESIZE_DEBOUNCE_MS);
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [enabled, reposition]);
  
  React.useEffect(() => {
    if (!enabled || typeof window === 'undefined') return;
    
    const handleOrientationChange = () => {
      setTimeout(() => {
        reposition();
      }, 300);
    };
    
    window.addEventListener('orientationchange', handleOrientationChange);
    
    return () => {
      window.removeEventListener('orientationchange', handleOrientationChange);
    };
  }, [enabled, reposition]);
  
  return {
    position,
    updatePosition,
    reposition,
    isMobile,
  };
}
