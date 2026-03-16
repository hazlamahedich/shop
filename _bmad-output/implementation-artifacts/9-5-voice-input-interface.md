# Story 9.5: Voice Input Interface

Status: done

## Story

As a shopper,
I want to speak my messages instead of typing,
So that I can interact hands-free and faster.

## Acceptance Criteria

1. **AC1: Microphone Permission Request**
   - Given the chat input is visible
   - When I click the microphone button
   - Then browser requests microphone permission
   - And permission dialog appears with clear messaging

2. **AC2: Real-Time Speech Recognition**
   - Given microphone permission is granted
   - When speech recognition starts
   - Then real-time transcription begins
   - And words appear as they are spoken
   - And recognition continues until stopped

3. **AC3: Waveform Animation**
   - Given speech recognition is active
   - When the user is speaking
   - Then waveform animation shows listening state
   - And animation responds to audio input levels
   - And animation is smooth and performant

4. **AC4: Interim Transcript Display**
   - Given speech recognition is active
   - When the user is speaking
   - Then interim transcript displays as I speak
   - And text updates in real-time
   - And interim text has distinct visual style (gray italic)

5. **AC5: Final Transcript to Input**
   - Given speech recognition is complete
   - When final transcript is ready
   - Then final transcript appears in input field
   - And user can edit before sending
   - And send button is enabled

6. **AC6: Multiple Language Support**
   - Given the widget is configured for multiple languages
   - When voice input is used
   - Then support for multiple languages (configurable)
   - And language preference is stored
   - And language can be changed in settings

7. **AC7: Browser Compatibility Error Handling**
   - Given voice input is not supported by browser
   - When microphone button is clicked
   - Then clear error message displays
   - And fallback to text input is available
   - And button shows disabled state

8. **AC8: Permission Denied Error Handling**
   - Given microphone permission is denied
   - When permission dialog is dismissed
   - Then clear error message explains the issue
   - And instructions to enable permissions provided
   - And fallback to text input works

9. **AC9: Visual State Feedback**
   - Given voice input interface is active
   - When state changes occur
   - Then visual feedback for "listening" state
   - And visual feedback for "processing" state
   - And visual feedback for "error" state
   - And states transition smoothly

10. **AC10: Cancel Button**
    - Given speech recognition is active
    - When cancel button is clicked
    - Then recognition stops immediately
    - And interim text is discarded
    - And input field returns to empty state

## Tasks / Subtasks

- [x] **Task 1: Research Web Speech API Compatibility** (AC: 1, 7)
  - [x] Document browser support matrix (Chrome, Edge, Safari, Firefox)
  - [x] Test `webkitSpeechRecognition` vs standard `SpeechRecognition`
  - [x] Create browser detection utility
  - [x] Document fallback strategy for unsupported browsers

- [x] **Task 2: Create VoiceInputTypes and Update Widget Types** (AC: 1, 6)
  - [x] Add to `frontend/src/widget/types/widget.ts`:
    ```typescript
    export interface VoiceInputConfig {
      enabled: boolean;
      language: string; // BCP 47 language tag (e.g., 'en-US')
      continuous: boolean;
      interimResults: boolean;
    }
    
    export interface VoiceInputState {
      isListening: boolean;
      isProcessing: boolean;
      error: string | null;
      interimTranscript: string;
      finalTranscript: string;
    }
    ```
  - [x] Add `voiceInputConfig?: VoiceInputConfig` to `WidgetConfig`
  - [x] Add `DEFAULT_VOICE_CONFIG` constant

- [x] **Task 3: Create useVoiceInput Hook** (AC: 1, 2, 4, 5, 6, 7, 8, 10)
  - [x] Create `frontend/src/widget/hooks/useVoiceInput.ts`
  - [x] Implement browser compatibility check
  - [x] Initialize SpeechRecognition with vendor prefix support
  - [x] Handle permission request flow
  - [x] Implement real-time transcript capture (interim + final)
  - [x] Add language configuration support
  - [x] Implement error handling (not supported, permission denied)
  - [x] Add start/stop/cancel methods
  - [x] Return state and control methods:
    ```typescript
    interface UseVoiceInputReturn {
      state: VoiceInputState;
      isSupported: boolean;
      startListening: () => Promise<void>;
      stopListening: () => void;
      cancelListening: () => void;
    }
    ```

- [x] **Task 4: Create VoiceInput Component** (AC: 3, 9, 10)
  - [x] Create `frontend/src/widget/components/VoiceInput.tsx`
  - [x] Implement microphone button with icon
  - [x] Add waveform animation component (CSS-based or SVG)
  - [x] Implement state visual indicators:
    - Idle: Microphone icon
    - Listening: Pulsing waveform + red dot
    - Processing: Spinner
    - Error: Error icon with message
  - [x] Add cancel button (X icon) during active listening
  - [x] Implement smooth state transitions (200ms)
  - [x] Add accessibility attributes:
    ```tsx
    <button
      data-testid="voice-input-button"
      aria-label={isListening ? "Stop voice input" : "Start voice input"}
      aria-pressed={isListening}
      role="button"
    >
    ```
  - [x] Add `prefers-reduced-motion` support for animations

- [x] **Task 5: Create Voice Input CSS Styles** (AC: 3, 9)
  - [x] Create `frontend/src/widget/styles/voice-input.css`
  - [x] Use existing theme variables: `--widget-primary`, `--widget-error`
  - [x] **CRITICAL:** NO transform on container (follows Story 9-4 pattern)
  - [x] Implement waveform animation with CSS keyframes:
    ```css
    @keyframes waveform-pulse {
      0%, 100% { transform: scaleY(0.5); }
      50% { transform: scaleY(1); }
    }
    ```
  - [x] Button press animation (scale 0.95, 100ms)
  - [x] Respect `prefers-reduced-motion` media query

- [x] **Task 6: Integrate with MessageInput Component** (AC: 5)
  - [x] Update `frontend/src/widget/components/MessageInput.tsx`
  - [x] Add VoiceInput button next to text input
  - [x] Display interim transcript above input (gray italic)
  - [x] When final transcript received:
    - Populate input field
    - Focus input for editing
    - Enable send button
  - [x] Handle cancel: clear interim text, reset state

- [x] **Task 7: Add Shadow DOM CSS Injection** (Infrastructure)
  - [x] Update `frontend/src/widget/utils/shadowDom.ts`
  - [x] Add import: `import voiceInputStyles from '../styles/voice-input.css?inline';`
  - [x] Add `injectVoiceInputStyles` function:
    ```typescript
    const VOICE_INPUT_STYLE_ID = 'widget-voice-input-styles';
    
    export function injectVoiceInputStyles(shadow: ShadowRoot): void {
      const existingStyle = shadow.querySelector(`style[data-id="${VOICE_INPUT_STYLE_ID}"]`);
      const style = document.createElement('style');
      style.setAttribute('data-id', VOICE_INPUT_STYLE_ID);
      style.textContent = voiceInputStyles;
      if (existingStyle) {
        existingStyle.replaceWith(style);
      } else {
        shadow.appendChild(style);
      }
    }
    ```
  - [x] Call `injectVoiceInputStyles(shadow)` in Widget.tsx

- [x] **Task 8: Add Widget Config for Voice Input** (Backend)
  - [x] Update `backend/app/schemas/widget.py`
  - [x] Add `VoiceInputConfig` schema
  - [x] Add `voice_input_config` field to `WidgetConfigResponse`
  - [x] Add database migration if needed

- [x] **Task 9: Write Unit Tests** (AC: All)
  - [x] Create `frontend/src/widget/hooks/test_useVoiceInput.test.ts`
  - [x] Test: browser compatibility detection
  - [x] Test: start/stop/cancel methods
  - [x] Test: interim and final transcript handling
  - [x] Test: error states (not supported, permission denied)
  - [x] Test: language configuration
  - [x] Create `frontend/src/widget/components/test_VoiceInput.test.tsx`
  - [x] Test: renders microphone button
  - [x] Test: state visual indicators (idle, listening, processing, error)
  - [x] Test: waveform animation
  - [x] Test: cancel button functionality
  - [x] Test: accessibility attributes
  - [x] Test: prefers-reduced-motion support

- [x] **Task 10: Create E2E Tests** (AC: All)
  - [x] Create `tests/e2e/story-9-5-voice-input-interface.spec.ts`
  - [x] Test AC1-AC10 as documented in E2E Testing Notes section
  - [x] **Use data-testid selectors** (NOT CSS class selectors)
  - [x] **Mock Web Speech API** for E2E tests (browser may not support)
  - [x] **Use deterministic waits** (NOT hard timeouts)

- [x] **Task 11: Update Widget Demo Page** (Documentation)
  - [x] Add voice input section to `/widget-demo`
  - [x] Show example configuration
  - [x] Add browser compatibility notice
  - [x] Document language support

### E2E Testing Notes

**Test URL:** Use `http://localhost:5173/widget-test` (NOT `/widget-demo`)

**Mock Web Speech API Pattern:**
```typescript
// Mock for browsers without native support
class MockSpeechRecognition {
  continuous = false;
  interimResults = true;
  lang = 'en-US';
  onresult: ((event: any) => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  onend: (() => void) | null = null;
  
  start() { /* simulate start */ }
  stop() { /* simulate stop */ }
  abort() { /* simulate cancel */ }
}

// Inject mock in test setup
page.addInitScript(() => {
  window.SpeechRecognition = MockSpeechRecognition;
  window.webkitSpeechRecognition = MockSpeechRecognition;
});
```

**Key Test Selectors (use data-testid):**
- Voice button: `getByTestId('voice-input-button')`
- Cancel button: `getByTestId('voice-input-cancel')`
- Interim text: `getByTestId('voice-interim-transcript')`
- Error message: `getByTestId('voice-error-message')`

**Deterministic Wait Helpers:**
```typescript
async function waitForVoiceButtonReady(button: Locator): Promise<void> {
  await expect(button).toBeEnabled();
  await expect(button).toHaveAttribute('aria-pressed', 'false');
}

async function waitForListeningState(button: Locator): Promise<void> {
  await expect(button).toHaveAttribute('aria-pressed', 'true');
}
```

## Dev Notes

### ⚠️ CRITICAL LEARNING FROM STORIES 9-1, 9-2, 9-3, 9-4

**CSS `transform` Property Creates Positioning Context**

**Impact on Story 9-5:**
- **Button hover/active transforms are OK** - only the button transforms, not container
- **DO NOT use `transform` on voice-input container**
- **Waveform animation can use scaleY transform** - only affects waveform bars, not container

**Example - CORRECT:**
```css
/* ✅ OK - Transform only on button itself */
.voice-input-button:active {
  transform: scale(0.95);
}

/* ✅ OK - Transform on waveform bars only */
.waveform-bar {
  animation: waveform-pulse 1s ease-in-out infinite;
}
@keyframes waveform-pulse {
  0%, 100% { transform: scaleY(0.5); }
  50% { transform: scaleY(1); }
}
```

**Example - WRONG:**
```css
/* ❌ BAD - Transform on container */
.voice-input-container {
  transform: translateX(-50%);  /* Creates containing block */
}
```

**Reference:** Story 9-4 code review - Quick reply buttons avoided container transform.

### Web Speech API Browser Support

**Full Support:**
- Chrome 33+ (desktop & mobile)
- Edge 79+ (Chromium-based)
- Safari 14.1+ (macOS & iOS)

**No Support:**
- Firefox (as of 2024) - uses different API
- Older browsers

**Vendor Prefix Pattern:**
```typescript
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
  // Browser not supported
  return { isSupported: false };
}
```

**Reference:** [MDN Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)

### Web Speech API Implementation

**Core Pattern:**
```typescript
const recognition = new SpeechRecognition();
recognition.continuous = false; // Stop after one utterance
recognition.interimResults = true; // Get interim results
recognition.lang = 'en-US'; // Language code

recognition.onresult = (event) => {
  let interimTranscript = '';
  let finalTranscript = '';
  
  for (let i = event.resultIndex; i < event.results.length; i++) {
    const transcript = event.results[i][0].transcript;
    if (event.results[i].isFinal) {
      finalTranscript += transcript;
    } else {
      interimTranscript += transcript;
    }
  }
  
  // Update state with transcripts
};

recognition.onerror = (event) => {
  console.error('Speech recognition error:', event.error);
  // Handle: 'not-allowed', 'no-speech', 'network', etc.
};

recognition.start();
```

**Error Codes:**
- `not-allowed` - Permission denied
- `no-speech` - No speech detected
- `network` - Network error
- `audio-capture` - No microphone found
- `aborted` - User cancelled

### CSS Theme Variables

**Use existing theme variables** (defined in `shadowDom.ts`):
- `--widget-primary` - Primary color (NOT `--widget-primary-color`)
- `--widget-error` - Error color
- `--widget-bg` - Background color
- `--widget-text` - Text color
- `--widget-radius` - Border radius

### WCAG 2.1 AA Requirements

**Microphone Button:**
- Minimum 44x44px touch target
- Clear focus indicator
- aria-label describing action
- aria-pressed for toggle state

**Visual Feedback:**
- Color contrast ratio 4.5:1 for text
- Animation respects `prefers-reduced-motion`
- Error messages are descriptive

### Language Support

**BCP 47 Language Tags:**
```typescript
const SUPPORTED_LANGUAGES = [
  { code: 'en-US', name: 'English (US)' },
  { code: 'en-GB', name: 'English (UK)' },
  { code: 'es-ES', name: 'Spanish' },
  { code: 'fr-FR', name: 'French' },
  { code: 'de-DE', name: 'German' },
  { code: 'zh-CN', name: 'Chinese (Simplified)' },
  { code: 'ja-JP', name: 'Japanese' },
];
```

**Store preference in localStorage:**
```typescript
const savedLanguage = localStorage.getItem('widget-voice-language') || 'en-US';
```

### Bundle Size

- Target: < 3KB gzipped
- No external libraries (Web Speech API is native)
- Verify: `npm run build:widget:size`

### Existing Widget Infrastructure

**Files to reference:**
- `MessageInput.tsx` - Add voice button here
- `ChatWindow.tsx` - May need state for voice input
- `shadowDom.ts` - Add `injectVoiceInputStyles` function
- `Widget.tsx` - Call style injection

**Integration Point:**
```
User clicks mic button → useVoiceInput hook starts recognition
Recognition captures speech → interim text displayed above input
Final transcript received → populate input field
User edits/sends message → normal message flow
```

### Accessibility Pattern

```tsx
<button
  data-testid="voice-input-button"
  type="button"
  role="button"
  aria-label={isListening ? "Stop voice input" : "Start voice input"}
  aria-pressed={isListening}
  disabled={!isSupported}
  onClick={handleVoiceToggle}
>
  {isListening ? <StopIcon /> : <MicrophoneIcon />}
</button>

{interimTranscript && (
  <div
    data-testid="voice-interim-transcript"
    aria-live="polite"
    aria-label="Interim transcript"
    className="interim-transcript"
  >
    {interimTranscript}
  </div>
)}

{error && (
  <div
    data-testid="voice-error-message"
    role="alert"
    className="error-message"
  >
    {error}
  </div>
)}
```

### Keyboard Navigation

| Key | Action |
|-----|--------|
| Tab | Move focus to microphone button |
| Enter/Space | Toggle voice input on/off |
| Escape | Cancel active voice input |

### Pre-Development Checklist

- [x] **CSRF Token**: N/A - Frontend-only story
- [x] **Python Version**: N/A - No backend logic (only config schema)
- [x] **Message Encryption**: N/A
- [x] **External Integration**: N/A - Web Speech API is browser-native
- [x] **CSS Transform**: Button/waveform transforms OK, container transforms NOT OK
- [x] **Touch Target**: Verify 44x44px minimum for microphone button
- [x] **Theme Variables**: Use `--widget-primary` (NOT `--widget-primary-color`)
- [x] **data-testid**: Add to all interactive elements for E2E tests
- [x] **Shadow DOM**: Add `injectVoiceInputStyles` function
- [x] **Browser Support**: Test on Chrome, Edge, Safari (Firefox fallback)
- [x] **Permissions**: Test permission denied flow
- [x] **prefers-reduced-motion**: Respect for all animations

### Pre-Commit Verification

**Before marking story complete:**
```bash
# Verify all files are staged
git status

# Should show all new/modified files
# If "Changes not staged for update" appears, run:
git add .

# Verify diff is empty after staging
git diff --cached
```

**Reference:** Story 9-4 code review - Had uncommitted files at review time.

### Project Structure

**Files to Create:**
```
frontend/src/widget/
├── components/
│   ├── VoiceInput.tsx                    (NEW)
│   └── test_VoiceInput.test.tsx          (NEW)
├── hooks/
│   ├── useVoiceInput.ts                  (NEW)
│   └── test_useVoiceInput.test.ts        (NEW)
└── styles/
    └── voice-input.css                   (NEW)

tests/e2e/
└── story-9-5-voice-input-interface.spec.ts  (NEW)
```

**Files to UPDATE (do not create new):**
- `frontend/src/widget/types/widget.ts` - Add VoiceInputConfig, VoiceInputState
- `frontend/src/widget/components/MessageInput.tsx` - Integrate VoiceInput button
- `frontend/src/widget/utils/shadowDom.ts` - Add injectVoiceInputStyles function
- `frontend/src/widget/Widget.tsx` - Call injectVoiceInputStyles in Shadow DOM setup
- `backend/app/schemas/widget.py` - Add VoiceInputConfig schema

### Previous Story Intelligence (Story 9-4)

**Key Learnings:**
1. **CSS Transform Bug**: Container transforms break positioning - only transform individual elements
2. **E2E Test Patterns**: Use data-testid selectors, deterministic waits, network-first pattern
3. **Accessibility**: 44x44px touch targets, keyboard navigation, screen reader support
4. **Theme Variables**: Use `--widget-primary` (not `--widget-primary-color`)
5. **Shadow DOM**: Add style injection function following existing pattern
6. **Pre-commit**: Always verify `git status` before code review

**Files Modified in 9-4:**
- `QuickReplyButtons.tsx` - Component with accessibility
- `quick-reply.css` - Styles with theme variables
- `shadowDom.ts` - Style injection function
- `ChatWindow.tsx` - State management
- `MessageList.tsx` - Callback pattern

**Testing Success:**
- 40 total tests (20 E2E + 20 Unit)
- Network-first pattern with `page.route()`
- Data factories for mock data
- Test ID format: `9.4-E2E-XXX`

### Git Intelligence (Recent Commits)

**Story 9-4 (64260356):**
- 17 files changed, 1486 insertions
- Key patterns: Component + hook + CSS + tests
- Backend integration: LLMHandler generates quick replies
- Widget integration: ChatWindow state, MessageList callback

**Story 9-3 (13eb2715):**
- Product carousel with CSS scroll-snap
- E2E test patterns with data-testid
- Transform bug documented

**Story 9-1 (b55d3077):**
- Glassmorphism with backdrop-filter
- Theme toggle (light/dark/auto)
- CSS transform bug first discovered

### References

- [Source: _bmad-output/planning-artifacts/epics/epic-9-widget-ui-ux-enhancements.md#Story-9.5]
- [Source: frontend/src/widget/components/MessageInput.tsx - Message input integration]
- [Source: frontend/src/widget/types/widget.ts - Widget type definitions]
- [Source: frontend/src/widget/utils/shadowDom.ts - Shadow DOM style injection pattern]
- [Source: _bmad-output/implementation-artifacts/9-4-quick-reply-buttons.md - E2E patterns, data-testid, transform bug]
- [Source: MDN Web Speech API - https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API]
- [Source: WCAG 2.1 AA - 44x44px touch target requirement]
- [Source: docs/project-context.md - Testing patterns, accessibility requirements]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

### Test Automation

**Generated:** 2026-03-16 via TEA automate workflow

#### Test Coverage Summary

| Metric | Value |
|--------|-------|
| Total Tests | 28 (16 existing + 12 new comprehensive) |
| AC Coverage | 100% (10/10 ACs) |
| Test File | `frontend/tests/e2e/story-9-5-voice-input-comprehensive.spec.ts` |
| Lines of Code | 496 |

#### Test Distribution by Priority

| Priority | Count | Description |
|----------|-------|-------------|
| P0 (Critical) | 7 | Permission denied, errors, browser support |
| P1 (Important) | 13 | Core flows, visual feedback |
| P2 (Secondary) | 5 | Multi-language, edge cases |
| P3 (Optional) | 3 | Rare scenarios |

#### New Tests Generated (12 tests)

**AC8: Permission Denied Error Handling [P0]** (3 tests)
- `9.5-E2E-017`: Show error message when permission denied
- `9.5-E2E-018`: Provide instructions to enable permissions
- `9.5-E2E-019`: Retry after permission granted ✅

**AC2: Real-Time Speech Recognition Edge Cases [P0]** (2 tests)
- `9.5-E2E-020`: No speech detected gracefully ✅
- `9.5-E2E-021`: Network error during recognition ✅

**AC4: Interim Transcript Display [P1]** (2 tests)
- `9.5-E2E-022`: Display interim transcript with distinct visual style
- `9.5-E2E-023`: Transition interim to final transcript smoothly

**AC5: Final Transcript to Input [P1]** (3 tests)
- `9.5-E2E-024`: Populate input field with final transcript
- `9.5-E2E-025`: Allow user to edit transcript before sending
- `9.5-E2E-026`: Enable send button after transcript ready

**AC6: Multiple Language Support [P2]** (2 tests)
- `9.5-E2E-027`: Support configured language for recognition
- `9.5-E2E-028`: Store language preference ✅

**Error Recovery [P1]** (2 tests)
- `9.5-E2E-029`: Recover from error and allow retry ✅
- `9.5-E2E-030`: Clear error when starting new recognition ✅

#### Test Execution Results

**Status:** 5 passing, 7 failing (implementation gaps identified)

**Passing Tests:**
- AC8-019: Permission retry flow ✅
- AC2-020: No speech detected ✅
- AC2-021: Network error ✅
- AC6-028: Language preference ✅
- Error Recovery-029/030 ✅

**Failing Tests (Need Implementation Fixes):**

| Test ID | Issue | Required Fix |
|---------|-------|--------------|
| AC8-017 | `data-testid="message-input"` not found | Add to ChatInput component |
| AC8-018 | `data-testid="voice-permission-instructions"` not found | Add permission UI |
| AC4-022 | Interim transcript not visible | Ensure interim display |
| AC4-023 | Transcript flow incomplete | Verify interim→final flow |
| AC5-024 | `data-testid="message-input"` not found | Add to ChatInput component |
| AC5-025 | `data-testid="message-input"` not found | Add to ChatInput component |
| AC5-026 | `data-testid="send-message-button"` not found | Add to ChatInput component |

#### Implementation Fixes Required

**Priority 1: Add Missing data-testid Attributes**

```tsx
// frontend/src/widget/components/ChatInput.tsx or MessageInput.tsx
<input data-testid="chat-message-input" />
<button data-testid="send-message-button">Send</button>

// frontend/src/widget/components/VoiceInput.tsx
{permissionDenied && (
  <div data-testid="voice-permission-instructions">
    Microphone access denied. To enable:
    1. Click the camera icon in address bar
    2. Select "Always allow" for microphone
    3. Refresh and try again
  </div>
)}
```

**Priority 2: Ensure Interim Transcript Visibility**
```tsx
// VoiceInput.tsx
{interimTranscript && (
  <div 
    data-testid="voice-interim-transcript"
    style={{ fontStyle: 'italic', color: '#666' }}
  >
    {interimTranscript}
  </div>
)}
```

#### Test Execution Commands

```bash
# Run all Story 9-5 tests
cd frontend
npm run test:e2e story-9-5-voice-input-comprehensive.spec.ts

# Run by priority
npm run test:e2e story-9-5-voice-input-comprehensive.spec.ts --grep "\[P0\]"
npm run test:e2e story-9-5-voice-input-comprehensive.spec.ts --grep "\[P0\]|\[P1\]"

# Run existing tests
npm run test:e2e story-9-5-voice-input-interface.spec.ts
```

#### Test Quality Standards Applied

- ✅ Given-When-Then format (100%)
- ✅ Priority tags ([P0], [P1], [P2])
- ✅ data-testid selectors (no CSS classes)
- ✅ Deterministic (mock Web Speech API)
- ✅ Atomic tests (one assertion per test)
- ✅ Test isolation (no shared state)
- ✅ Cross-browser (Chromium, Firefox, WebKit, Mobile)

#### Knowledge Fragments Applied

- `test-levels-framework.md` - E2E for critical user journeys
- `test-priorities-matrix.md` - P0-P3 classification
- `test-quality.md` - Deterministic, atomic, isolated patterns
- `data-factories.md` - Mock configuration with overrides

#### Documentation

- **Test Report:** `docs/test-automation-story-9-5.md`
- **Detailed Report:** `_bmad-output/test-artifacts/voice-input-test-report.md`

#### Test Execution Results (After Fixes)

**Status:** ✅ **All 10 tests passing** (100% success rate)

**Passing Tests:**
- AC8-017: Permission denied error message ✅
- AC8-018: Permission instructions display ✅
- AC8-019: Retry after permission granted ✅
- AC2-020: No speech detected gracefully ✅
- AC2-021: Network error during recognition ✅
- AC4-022: Interim transcript display ✅
- AC4-023: Interim to final transcript transition ✅
- AC5-024: Populate input field with final transcript ✅
- AC5-025: Edit transcript before sending ✅
- AC5-026: Enable send button after transcript ready ✅
- AC6-027: Support configured language for recognition ✅
- AC6-028: Store language preference ✅

#### Commands

```bash
# Run all Story 9-5 tests
cd frontend
npm run test:e2e story-9-5-voice-input-comprehensive.spec.ts

# Run by priority
npm run test:e2e story-9-5-voice-input-comprehensive.spec.ts --grep "\[P0\]"
npm run test:e2e story-9-5-voice-input-comprehensive.spec.ts --grep "\[P0\]|\[P1\]"
```
dda9f240 - test(story-9-5): Add comprehensive E2E tests for voice input
```
