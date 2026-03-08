# Story 5.13: Draggable & Minimizable Widget

Status: done

## Story

As a customer using the chat widget on a merchant's website,
I want to drag the chat window to any position and minimize it when not in use,
so that I can continue browsing without the widget obstructing content and position it where it's most convenient for me.

## Acceptance Criteria

1. **Given** the chat window is open, **When** the user clicks and drags the header, **Then** the window moves to follow the cursor position **AND** the movement is smooth without jumping
2. **Given** the chat window is being dragged, **When** the user releases the mouse/touch, **Then** the window stays at the new position **AND** the position is saved to localStorage for persistence across sessions
3. **Given** the chat window is dragged near screen edges, **When** the position would go off-screen, **Then** the window is constrained to stay within viewport boundaries
4. **Given** the chat window is open, **When** the user clicks the minimize button (−) in the header, **Then** the window collapses to just the bubble **AND** the chat session remains active
5. **Given** the chat window is minimized, **When** new messages arrive from the bot/merchant, **Then** a red notification badge appears on the bubble showing the unread count
6. **Given** the chat window is minimized with unread messages, **When** the user clicks the bubble, **Then** the window expands at the last saved position **AND** the unread count is cleared
7. **Given** the widget is used on mobile devices, **When** the user touches and drags the header, **Then** touch events work correctly for dragging **AND** the minimize button is easily tappable

## Tasks / Subtasks

- [x] **State Management Updates** (AC: 1, 2, 4, 5)
  - [x] Add `position: { x: number; y: number }` to WidgetState
  - [x] Add `isDragging: boolean` to WidgetState
  - [x] Add `isMinimized: boolean` to WidgetState
  - [x] Add `unreadCount: number` to WidgetState
  - [x] Add action types: SET_POSITION, SET_DRAGGING, TOGGLE_MINIMIZED, SET_UNREAD_COUNT
  - [x] Update ADD_MESSAGE to increment unreadCount when minimized

- [x] **Storage Utilities** (AC: 2)
  - [x] Add `saveWidgetPosition()` function to storage.ts
  - [x] Add `loadWidgetPosition()` function to storage.ts
  - [x] Position persists in localStorage across sessions

- [x] **Drag Implementation** (AC: 1, 2, 3, 7)
  - [x] Add drag handlers to ChatWindow header
  - [x] Implement delta-based drag tracking (fixes jumping issue)
  - [x] Add boundary constraints to keep widget on screen
  - [x] Add touch event support for mobile
  - [x] Add grab/grabbing cursor styles
  - [x] Disable transitions during drag for responsiveness

- [x] **Minimize Implementation** (AC: 4, 5, 6)
  - [x] Add minimize button (−) to ChatWindow header
  - [x] Implement TOGGLE_MINIMIZED action
  - [x] When minimized, hide ChatWindow and show only bubble
  - [x] Add notification badge to ChatBubble with unread count
  - [x] Add pulse animation when there are unread messages
  - [x] Clear unread count when expanding from minimized state

- [x] **UI Polish** (AC: 4, 7)
  - [x] Style minimize button with semi-transparent background
  - [x] Add hover effects to header buttons
  - [x] Make buttons easily tappable on mobile (min 36px touch target)
  - [x] Add visual separation between buttons

- [x] **Testing & Verification**
  - [x] Rebuild widget bundle
  - [x] Test drag functionality
  - [x] Test minimize/expand functionality
  - [x] Test notification badge
  - [x] Test position persistence
  - [x] Verify on external site

## Dev Notes

### Files Modified

| File | Changes |
|------|---------|
| `types/widget.ts` | Added WidgetPosition type, position/isDragging/isMinimized/unreadCount to WidgetState, new action types |
| `utils/storage.ts` | Added saveWidgetPosition(), loadWidgetPosition() functions |
| `context/WidgetContext.tsx` | Added state initialization, reducer cases, updatePosition(), toggleMinimized() callbacks |
| `components/ChatWindow.tsx` | Added drag handlers on header, minimize button, dynamic positioning via transform |
| `components/ChatBubble.tsx` | Added unreadCount prop, notification badge with count display |
| `styles/widget.css` | Added drag cursor styles, pulse animation |
| `Widget.tsx` | Wired up drag event handlers, minimize toggle, bubble click handler |
| `api/widgetClient.ts` | Fixed pre-existing syntax errors (duplicate code, octal literal) |

### UX Decisions

1. **Minimize Style**: Collapse to bubble (not mini bar) - familiar pattern, minimal cognitive load
2. **Position Persistence**: Save to localStorage - remembers user's preferred position
3. **Drag Handle**: Header only - prevents accidental drags while scrolling messages
4. **Minimized State**: Always start expanded on page load - ensures users see messages

### Drag Implementation Details

```typescript
// Delta-based drag tracking (prevents jumping)
const dragStartRef = React.useRef({ x: 0, y: 0, windowX: 0, windowY: 0 });

const handleDragStart = (e) => {
  dragStartRef.current = {
    x: clientX,
    y: clientY,
    windowX: state.position.x,
    windowY: state.position.y,
  };
};

const handleMouseMove = (e) => {
  const deltaX = e.clientX - dragStartRef.current.x;
  const deltaY = e.clientY - dragStartRef.current.y;
  const newX = dragStartRef.current.windowX + deltaX;
  const newY = dragStartRef.current.windowY + deltaY;
  // Apply boundary constraints...
};
```

### CSS Classes Added

```css
.chat-header-drag-handle {
  cursor: grab;
}
.chat-header-drag-handle:active {
  cursor: grabbing;
}
.shopbot-chat-bubble.has-unread {
  animation: shopbot-pulse 2s ease-in-out infinite;
}
```

## Out of Scope

- Minimized state persistence across page loads (intentionally starts expanded)
- Snap-to-edge behavior
- Resize functionality
- Multiple widget instances

## Related Stories

- Story 5-3: Widget Frontend Components (base structure)
- Story 5-5: Theme Customization System (theming support)
- Story 5-8: Performance Optimization (lazy loading)
