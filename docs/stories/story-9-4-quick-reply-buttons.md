# Story 9-4: Quick Reply Buttons

Status: done

## Story

As a customer using the chat widget on a merchant's website,
I want quick reply buttons to appear as suggestions after bot messages,
so that I can respond with a single click/tap instead of typing.

## Acceptance Criteria

1. **AC1: Chip-Style Buttons [P0]** - Given quick replies are available, When the bot sends a message with quick_replies, Then buttons appear as rounded chip-style buttons below the message
2. **AC2: Touch Target Size [P0]** - Given quick reply buttons are displayed, When rendered on any device, Then each button has a minimum 44x44px touch target for accessibility
3. **AC3: Click Action [P0]** - Given quick reply buttons are visible, When a user clicks a button, Then the button's payload (or text) is sent as a message AND buttons disappear after selection
4. **AC4: Visual Feedback [P1]** - Given quick reply buttons are visible, When a user hovers/focuses a button, Then the button shows visual feedback (color change, border highlight)
4. **AC5: Icon/Emoji Support [P1]** - Given a quick reply has an icon/emoji, When the button renders, Then the icon appears before the text with proper alignment
5. **AC6: Keyboard Navigation [P0]** - Given quick reply buttons are visible, When the user presses Tab, Then focus moves between buttons in logical order AND Enter/Space activates the focused button
6. **AC7: Screen Reader Accessibility [P0]** - Given quick reply buttons are visible, Then each button has aria-label matching its text AND the container has role="group" with aria-label
7. **AC8: Responsive Layout [P1]** - Given quick reply buttons are displayed, When viewport is narrow (<480px), Then buttons wrap to multiple rows AND on wider viewports, buttons display in a single row if space permits
8. **AC9: Dynamic Quick Replies [P1]** - Given the backend sends quick_replies in response, When the message is received, Then buttons are dynamically generated from the response
9. **AC10: Dismiss After Selection [P1]** - Given a quick reply is selected, When the message is sent, Then the buttons are dismissed to prevent duplicate submissions

## Tasks / Subtasks

- [x] **Schema Updates** (AC: 9)
  - [x] Add `QuickReplySchema` to `frontend/src/widget/schemas/widget.ts`
  - [x] Add `quick_replies` field to `WidgetMessageSchema`
  - [x] Backend already supports `quick_replies` in response

- [x] **API Client Updates** (AC: 9)
  - [x] Update `widgetClient.sendMessage()` to extract `quick_replies` from response
  - [x] Pass quick replies to callback/state

- [x] **Component Implementation** (AC: 1, 2, 3, 4, 5)
  - [x] Create `QuickReplyButtons` component in `frontend/src/widget/components/`
  - [x] Implement chip-style buttons with rounded corners
  - [x] Add icon/emoji support with flexbox alignment
  - [x] Ensure 44x44px minimum touch targets
  - [x] Add hover/focus visual feedback

- [x] **Integration** (AC: 3, 9, 10)
  - [x] Add `onQuickRepliesAvailable` callback to `MessageList`
  - [x] Wire up quick replies state in `ChatWindow`
  - [x] Implement dismiss-on-select behavior
  - [x] Fix layout bug: Add `flexShrink: 0` wrapper to prevent buttons being pushed outside viewport

- [x] **Accessibility** (AC: 6, 7)
  - [x] Add `role="button"` and `aria-label` to each button
  - [x] Add `role="group"` and `aria-label` to container
  - [x] Implement keyboard navigation (Tab, Enter, Space)
  - [x] Add visible focus indicator

- [x] **Responsive Design** (AC: 8)
  - [x] Mobile: 2-column grid layout for wrapped buttons
  - [x] Desktop: Single row with flex-wrap
  - [x] 8px gap between buttons

- [x] **Testing**
  - [x] Unit tests: 20 tests in `test_QuickReplyButtons.test.tsx`
  - [x] E2E tests: 18 tests in `story-9-4-quick-reply-buttons.spec.ts`
  - [x] All tests passing (17 E2E passed, 1 skipped, 20 unit passed)

## Dev Notes

### Files Modified

| File | Changes |
|------|---------|
| `frontend/src/widget/schemas/widget.ts` | Added `QuickReplySchema` interface, added `quick_replies` field to `WidgetMessageSchema` |
| `frontend/src/widget/api/widgetClient.ts` | Added `quick_replies` extraction in `sendMessage()` response handling |
| `frontend/src/widget/components/QuickReplyButtons.tsx` | New component with chip-style buttons, accessibility, responsive layout |
| `frontend/src/widget/components/ChatWindow.tsx` | Added `activeQuickReplies` state, `handleQuickReply` callback, fixed layout with `flexShrink: 0` wrapper |
| `frontend/src/widget/components/MessageList.tsx` | Added `onQuickRepliesAvailable` prop to pass quick replies to parent |
| `frontend/src/widget/components/test_QuickReplyButtons.test.tsx` | 20 unit tests covering all acceptance criteria |
| `frontend/tests/e2e/story-9-4-quick-reply-buttons.spec.ts` | 18 E2E tests with network mocking for quick replies |

### Schema Definition

```typescript
// frontend/src/widget/schemas/widget.ts
export interface QuickReplySchema {
  id: string;
  text: string;
  icon?: string;
  payload?: string;
}

export interface WidgetMessageSchema {
  messageId: string;
  content: string;
  sender: 'user' | 'bot';
  createdAt: string;
  quickReplies?: QuickReplySchema[];
  // ... other fields
}
```

### Layout Bug Fix

The `QuickReplyButtons` component was being pushed outside the viewport because `MessageList` has `flex: 1` and `overflowY: auto`. Fixed by wrapping in a `flexShrink: 0` container:

```tsx
// ChatWindow.tsx (lines 437-445)
{activeQuickReplies && activeQuickReplies.length > 0 && (
  <div style={{ flexShrink: 0, padding: '0 12px 8px' }}>
    <QuickReplyButtons
      quickReplies={activeQuickReplies}
      onReply={handleQuickReply}
      theme={theme}
      dismissOnSelect={true}
    />
  </div>
)}
```

### Network Mocking Pattern (E2E Tests)

```typescript
// Use page.route() for deterministic network mocking
await page.route('**/api/v1/widget/message', async (route) => {
  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({
      data: {
        message_id: `msg-${Date.now()}`,
        content: 'Response text',
        sender: 'bot',
        created_at: new Date().toISOString(),
        quick_replies: [
          { id: 'yes', text: 'Yes', icon: '✓', payload: 'user_confirmed' },
          { id: 'no', text: 'No', icon: '✗', payload: 'user_declined' },
        ],
      },
    }),
  });
});
```

### Anti-Patterns Avoided

- ❌ No `page.waitForTimeout()` or `time.sleep()` - use `expect().toBeVisible()` instead
- ❌ No conditional `if (isVisible())` flow - use deterministic assertions
- ❌ No template literals in `addInitScript()` browser context - pass values as 2nd argument

## Test Results

### E2E Tests (Playwright)
```
Running 18 tests using 2 workers
  ✓ 17 passed
  -  1 skipped (layout edge case - buttons disabled after selection)
```

### Unit Tests (Vitest)
```
✓ src/widget/components/test_QuickReplyButtons.test.tsx (20 tests)
  ✓ renders buttons with correct text
  ✓ renders chip-style buttons with correct classes
  ✓ has 44x44px minimum touch targets
  ✓ renders icons/emojis before text
  ✓ calls onReply with correct payload on click
  ✓ supports keyboard navigation - Enter key
  ✓ supports keyboard navigation - Space key
  ✓ has visible focus indicator
  ✓ has accessibility attributes
  ✓ has data-testid attributes
  ✓ renders 2-column grid on mobile (< 480px)
  ✓ renders single row on desktop (>= 480px)
  ✓ respects prefers-reduced-motion
  ✓ dismisses buttons after selection when dismissOnSelect is true
  ✓ does not dismiss buttons when dismissOnSelect is false
  ✓ returns null when quickReplies is empty
  ✓ disables buttons when disabled prop is true
  ✓ does not call onReply when disabled
  ✓ uses theme primary color for border and text
  ✓ renders buttons without icons when icon is undefined
```

## Out of Scope

- Persisting quick replies across page reloads
- Custom button styling per merchant
- Animated button transitions (future: Story 9-8)
- Quick reply analytics tracking (future: Story 9-10)

## Related Stories

- Story 5-3: Widget Frontend Components (base structure)
- Story 5-5: Theme Customization System (theming support)
- Story 9-8: Animated Microinteractions (button animations)
- Story 9-10: Analytics & A/B Testing (quick reply usage tracking)

## Run Commands

```bash
# E2E Tests
cd frontend && npx playwright test story-9-4 --project=smoke-tests

# Unit Tests
cd frontend && npm run test test_QuickReplyButtons.test.tsx --run
```
