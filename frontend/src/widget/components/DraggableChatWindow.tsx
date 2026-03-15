import * as React from 'react';
import type { WidgetPosition, PositioningConfig } from '../types/widget';
import { DEFAULT_POSITIONING_CONFIG } from '../types/widget';
import { snapToEdge, constrainToViewport, isMobileDevice } from '../utils/smartPositioning';

interface DraggableChatWindowProps {
  children: React.ReactNode;
  position: WidgetPosition;
  widgetSize: { width: number; height: number };
  onPositionChange: (position: WidgetPosition) => void;
  config?: Partial<PositioningConfig>;
  disabled?: boolean;
  className?: string;
}

export function DraggableChatWindow({
  children,
  position,
  widgetSize,
  onPositionChange,
  config,
  disabled = false,
  className = '',
}: DraggableChatWindowProps) {
  const mergedConfig: PositioningConfig = React.useMemo(
    () => ({
      ...DEFAULT_POSITIONING_CONFIG,
      ...config,
    }),
    [config]
  );
  
  const isDragging = React.useRef(false);
  const dragStart = React.useRef({ x: 0, y: 0, windowX: 0, windowY: 0 });
  const [isDraggingState, setIsDraggingState] = React.useState(false);
  const [isSnapping, setIsSnapping] = React.useState(false);
  
  const isMobile = isMobileDevice();
  
  const handleDragStart = React.useCallback(
    (e: React.MouseEvent | React.TouchEvent) => {
      if (disabled || isMobile) return;
      
      e.preventDefault();
      isDragging.current = true;
      setIsDraggingState(true);
      
      const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
      
      dragStart.current = {
        x: clientX,
        y: clientY,
        windowX: position.x,
        windowY: position.y,
      };
    },
    [disabled, isMobile, position]
  );
  
  const handleMouseMove = React.useCallback(
    (e: MouseEvent) => {
      if (!isDragging.current) return;
      
      const deltaX = e.clientX - dragStart.current.x;
      const deltaY = e.clientY - dragStart.current.y;
      
      const newX = dragStart.current.windowX + deltaX;
      const newY = dragStart.current.windowY + deltaY;
      
      const constrained = constrainToViewport(
        { x: newX, y: newY },
        widgetSize,
        mergedConfig
      );
      
      onPositionChange(constrained);
    },
    [widgetSize, mergedConfig, onPositionChange]
  );
  
  const handleTouchMove = React.useCallback(
    (e: TouchEvent) => {
      if (!isDragging.current) return;
      e.preventDefault();
      
      const touch = e.touches[0];
      const deltaX = touch.clientX - dragStart.current.x;
      const deltaY = touch.clientY - dragStart.current.y;
      
      const newX = dragStart.current.windowX + deltaX;
      const newY = dragStart.current.windowY + deltaY;
      
      const constrained = constrainToViewport(
        { x: newX, y: newY },
        widgetSize,
        mergedConfig
      );
      
      onPositionChange(constrained);
    },
    [widgetSize, mergedConfig, onPositionChange]
  );
  
  const applySnap = React.useCallback(() => {
    const snapped = snapToEdge(position, widgetSize, mergedConfig);
    
    if (snapped.x !== position.x || snapped.y !== position.y) {
      setIsSnapping(true);
      onPositionChange(snapped);
      
      // Haptic feedback only when actual snap occurs (AC5)
      if ('vibrate' in navigator) {
        navigator.vibrate(10);
      }
      
      setTimeout(() => {
        setIsSnapping(false);
      }, 200);
    }
  }, [position, widgetSize, mergedConfig, onPositionChange]);
  
  const handleDragEnd = React.useCallback(() => {
    if (!isDragging.current) return;
    
    isDragging.current = false;
    setIsDraggingState(false);
    applySnap();
  }, [applySnap]);
  
  React.useEffect(() => {
    if (!isDraggingState) return;
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleDragEnd);
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleDragEnd);
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleDragEnd);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleDragEnd);
    };
  }, [isDraggingState, handleMouseMove, handleTouchMove, handleDragEnd]);
  
  const containerStyle: React.CSSProperties = isMobile
    ? {
        position: 'fixed',
        left: '5%',
        top: '15%',
        width: '90%',
        height: '80%',
        zIndex: 2147483647,
      }
    : {
        position: 'fixed',
        left: position.x,
        top: position.y,
        zIndex: 2147483647,
        cursor: isDraggingState ? 'grabbing' : 'default',
        transition: isSnapping ? 'left 200ms ease-out, top 200ms ease-out' : 'none',
      };
  
  return (
    <div
      className={`draggable-chat-window ${className} ${isDraggingState ? 'dragging' : ''}`}
      style={containerStyle}
    >
      <div
        className="chat-header-drag-handle"
        onMouseDown={handleDragStart}
        onTouchStart={handleDragStart}
        style={{
          cursor: disabled || isMobile ? 'default' : isDraggingState ? 'grabbing' : 'grab',
          touchAction: 'none',
        }}
      >
        {children}
      </div>
    </div>
  );
}
